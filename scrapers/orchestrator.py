#!/usr/bin/env python3
"""
Scraper Orchestrator for OpenPolicy Platform
Manages and coordinates all parliamentary data scrapers
"""

import os
import sys
import time
import logging
import schedule
import threading
from datetime import datetime
from typing import Dict, List, Any
import psycopg2
from psycopg2.extras import RealDictCursor
import redis
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/orchestrator.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Import scrapers
from scrapers.parliament_scraper import ParliamentScraper
from scrapers.bills_scraper import BillsScraper
from scrapers.committees_scraper import CommitteesScraper
from scrapers.representatives_scraper import RepresentativesScraper
from scrapers.votes_scraper import VotesScraper
from scrapers.debates_scraper import DebatesScraper


class ScraperOrchestrator:
    """Orchestrates all scraping activities"""
    
    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST', 'postgres'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_DATABASE', 'openpolicy'),
            'user': os.getenv('DB_USERNAME', 'openpolicy'),
            'password': os.getenv('DB_PASSWORD', 'openpolicy123')
        }
        
        self.redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'redis'),
            port=int(os.getenv('REDIS_PORT', '6379')),
            decode_responses=True
        )
        
        self.scrapers = {
            'parliament': ParliamentScraper(self.db_config, self.redis_client),
            'bills': BillsScraper(self.db_config, self.redis_client),
            'committees': CommitteesScraper(self.db_config, self.redis_client),
            'representatives': RepresentativesScraper(self.db_config, self.redis_client),
            'votes': VotesScraper(self.db_config, self.redis_client),
            'debates': DebatesScraper(self.db_config, self.redis_client)
        }
        
        self.scraper_interval = int(os.getenv('SCRAPER_INTERVAL', '3600'))  # Default 1 hour
        
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def check_database_connection(self):
        """Check if database is accessible"""
        try:
            conn = psycopg2.connect(**self.db_config)
            conn.close()
            logger.info("Database connection successful")
            return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise
            
    def initialize_database_tables(self):
        """Ensure all required tables exist"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Create scraper_status table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scraper_status (
                    id SERIAL PRIMARY KEY,
                    scraper_name VARCHAR(100) UNIQUE NOT NULL,
                    last_run TIMESTAMP,
                    last_success TIMESTAMP,
                    last_error TEXT,
                    records_scraped INTEGER DEFAULT 0,
                    status VARCHAR(50) DEFAULT 'idle',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create scraper_logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scraper_logs (
                    id SERIAL PRIMARY KEY,
                    scraper_name VARCHAR(100) NOT NULL,
                    log_level VARCHAR(20),
                    message TEXT,
                    details JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Initialize scraper status for each scraper
            for scraper_name in self.scrapers.keys():
                cursor.execute("""
                    INSERT INTO scraper_status (scraper_name, status)
                    VALUES (%s, 'initialized')
                    ON CONFLICT (scraper_name) DO UPDATE
                    SET updated_at = CURRENT_TIMESTAMP
                """, (scraper_name,))
            
            conn.commit()
            cursor.close()
            conn.close()
            logger.info("Database tables initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database tables: {e}")
            raise
            
    def update_scraper_status(self, scraper_name: str, status: str, error: str = None, records: int = 0):
        """Update scraper status in database"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            if status == 'success':
                cursor.execute("""
                    UPDATE scraper_status
                    SET status = %s, last_run = CURRENT_TIMESTAMP, 
                        last_success = CURRENT_TIMESTAMP, last_error = NULL,
                        records_scraped = records_scraped + %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE scraper_name = %s
                """, (status, records, scraper_name))
            else:
                cursor.execute("""
                    UPDATE scraper_status
                    SET status = %s, last_run = CURRENT_TIMESTAMP,
                        last_error = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE scraper_name = %s
                """, (status, error, scraper_name))
                
            conn.commit()
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to update scraper status: {e}")
            
    def log_to_database(self, scraper_name: str, level: str, message: str, details: Dict = None):
        """Log scraper activity to database"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO scraper_logs (scraper_name, log_level, message, details)
                VALUES (%s, %s, %s, %s::jsonb)
            """, (scraper_name, level, message, json.dumps(details) if details else None))
            
            conn.commit()
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to log to database: {e}")
            
    def run_scraper(self, scraper_name: str):
        """Run a specific scraper"""
        logger.info(f"Starting {scraper_name} scraper")
        self.update_scraper_status(scraper_name, 'running')
        
        try:
            scraper = self.scrapers[scraper_name]
            start_time = time.time()
            
            # Run the scraper
            result = scraper.run()
            
            duration = time.time() - start_time
            logger.info(f"{scraper_name} scraper completed in {duration:.2f} seconds")
            
            # Update status
            self.update_scraper_status(
                scraper_name, 
                'success', 
                records=result.get('records_scraped', 0)
            )
            
            # Log success
            self.log_to_database(
                scraper_name,
                'INFO',
                f'Scraper completed successfully',
                {
                    'duration': duration,
                    'records_scraped': result.get('records_scraped', 0)
                }
            )
            
            # Update Redis cache
            self.redis_client.hset(
                f'scraper:{scraper_name}',
                mapping={
                    'last_run': datetime.now().isoformat(),
                    'status': 'success',
                    'records': result.get('records_scraped', 0)
                }
            )
            
        except Exception as e:
            logger.error(f"Error running {scraper_name} scraper: {e}")
            self.update_scraper_status(scraper_name, 'error', str(e))
            self.log_to_database(
                scraper_name,
                'ERROR',
                f'Scraper failed with error',
                {'error': str(e)}
            )
            
    def run_all_scrapers(self):
        """Run all scrapers in sequence"""
        logger.info("Starting all scrapers")
        
        # Order matters - representatives first, then bills, then votes
        scraper_order = [
            'parliament',
            'representatives', 
            'committees',
            'bills',
            'votes',
            'debates'
        ]
        
        for scraper_name in scraper_order:
            if scraper_name in self.scrapers:
                self.run_scraper(scraper_name)
                # Small delay between scrapers
                time.sleep(5)
                
        logger.info("All scrapers completed")
        
    def run_priority_scrapers(self):
        """Run only high-priority scrapers (more frequent updates)"""
        priority_scrapers = ['bills', 'votes']
        
        for scraper_name in priority_scrapers:
            if scraper_name in self.scrapers:
                self.run_scraper(scraper_name)
                
    def get_scraper_status(self) -> List[Dict]:
        """Get status of all scrapers"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT scraper_name, status, last_run, last_success, 
                       last_error, records_scraped
                FROM scraper_status
                ORDER BY scraper_name
            """)
            
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to get scraper status: {e}")
            return []
            
    def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        health = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'scrapers': {}
        }
        
        try:
            # Check database
            self.check_database_connection()
            
            # Check Redis
            self.redis_client.ping()
            
            # Get scraper statuses
            statuses = self.get_scraper_status()
            for status in statuses:
                health['scrapers'][status['scraper_name']] = {
                    'status': status['status'],
                    'last_run': status['last_run'].isoformat() if status['last_run'] else None
                }
                
        except Exception as e:
            health['status'] = 'unhealthy'
            health['error'] = str(e)
            
        return health
        
    def schedule_scrapers(self):
        """Schedule scraper runs"""
        # Run all scrapers every hour
        schedule.every(self.scraper_interval).seconds.do(self.run_all_scrapers)
        
        # Run priority scrapers every 30 minutes
        schedule.every(30).minutes.do(self.run_priority_scrapers)
        
        # Daily maintenance at 3 AM
        schedule.every().day.at("03:00").do(self.cleanup_old_logs)
        
        logger.info(f"Scrapers scheduled - Full run every {self.scraper_interval} seconds")
        
    def cleanup_old_logs(self):
        """Clean up old scraper logs"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Delete logs older than 30 days
            cursor.execute("""
                DELETE FROM scraper_logs
                WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '30 days'
            """)
            
            deleted = cursor.rowcount
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"Cleaned up {deleted} old log entries")
            
        except Exception as e:
            logger.error(f"Failed to cleanup old logs: {e}")
            
    def run(self):
        """Main orchestrator loop"""
        logger.info("Starting Scraper Orchestrator")
        
        # Initialize
        self.check_database_connection()
        self.initialize_database_tables()
        
        # Run scrapers immediately on startup
        self.run_all_scrapers()
        
        # Schedule future runs
        self.schedule_scrapers()
        
        # Keep running
        while True:
            try:
                schedule.run_pending()
                time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Orchestrator stopped by user")
                break
            except Exception as e:
                logger.error(f"Orchestrator error: {e}")
                time.sleep(60)  # Wait a minute before retrying


if __name__ == "__main__":
    orchestrator = ScraperOrchestrator()
    orchestrator.run()