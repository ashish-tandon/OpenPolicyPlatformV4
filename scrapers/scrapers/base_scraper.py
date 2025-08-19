"""
Base Scraper Class
Provides common functionality for all scrapers
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, List
import psycopg2
from psycopg2.extras import RealDictCursor
import redis
import requests
from tenacity import retry, stop_after_attempt, wait_exponential
from datetime import datetime


class BaseScraper(ABC):
    """Base class for all scrapers"""
    
    def __init__(self, db_config: Dict, redis_client: redis.Redis):
        self.db_config = db_config
        self.redis_client = redis_client
        self.logger = logging.getLogger(self.__class__.__name__)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'OpenPolicyPlatform/1.0 (Parliamentary Data Scraper)'
        })
        
    def get_db_connection(self):
        """Get database connection"""
        return psycopg2.connect(**self.db_config)
        
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def fetch_url(self, url: str, **kwargs) -> requests.Response:
        """Fetch URL with retry logic"""
        self.logger.debug(f"Fetching: {url}")
        response = self.session.get(url, **kwargs)
        response.raise_for_status()
        return response
        
    def save_to_cache(self, key: str, data: Any, ttl: int = 3600):
        """Save data to Redis cache"""
        try:
            if isinstance(data, (dict, list)):
                import json
                data = json.dumps(data)
            self.redis_client.setex(key, ttl, data)
        except Exception as e:
            self.logger.error(f"Failed to save to cache: {e}")
            
    def get_from_cache(self, key: str) -> Any:
        """Get data from Redis cache"""
        try:
            data = self.redis_client.get(key)
            if data:
                try:
                    import json
                    return json.loads(data)
                except:
                    return data
        except Exception as e:
            self.logger.error(f"Failed to get from cache: {e}")
        return None
        
    def log_activity(self, message: str, level: str = "INFO", details: Dict = None):
        """Log scraper activity"""
        getattr(self.logger, level.lower())(message)
        
        # Also log to database
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO scraper_logs (scraper_name, log_level, message, details)
                VALUES (%s, %s, %s, %s::jsonb)
            """, (
                self.__class__.__name__,
                level,
                message,
                json.dumps(details) if details else None
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            self.logger.error(f"Failed to log to database: {e}")
            
    @abstractmethod
    def scrape(self) -> Dict[str, Any]:
        """Main scraping logic - must be implemented by subclasses"""
        pass
        
    def run(self) -> Dict[str, Any]:
        """Run the scraper"""
        start_time = time.time()
        records_scraped = 0
        
        try:
            self.log_activity(f"Starting {self.__class__.__name__}")
            
            # Run the scraping logic
            result = self.scrape()
            
            records_scraped = result.get('records_scraped', 0)
            duration = time.time() - start_time
            
            self.log_activity(
                f"Completed successfully in {duration:.2f} seconds",
                details={
                    'duration': duration,
                    'records_scraped': records_scraped
                }
            )
            
            return {
                'success': True,
                'records_scraped': records_scraped,
                'duration': duration,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_activity(
                f"Failed with error: {str(e)}",
                level="ERROR",
                details={
                    'error': str(e),
                    'duration': duration
                }
            )
            
            return {
                'success': False,
                'error': str(e),
                'duration': duration,
                'timestamp': datetime.now().isoformat()
            }
            
    def upsert_record(self, table: str, data: Dict, conflict_columns: List[str]) -> bool:
        """Upsert a record into the database"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Build the INSERT query
            columns = list(data.keys())
            values = list(data.values())
            placeholders = [f'%s' for _ in values]
            
            # Build the UPDATE clause
            update_columns = [f"{col} = EXCLUDED.{col}" for col in columns if col not in conflict_columns]
            
            query = f"""
                INSERT INTO {table} ({', '.join(columns)})
                VALUES ({', '.join(placeholders)})
                ON CONFLICT ({', '.join(conflict_columns)})
                DO UPDATE SET {', '.join(update_columns)}, updated_at = CURRENT_TIMESTAMP
            """
            
            cursor.execute(query, values)
            conn.commit()
            cursor.close()
            conn.close()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to upsert record: {e}")
            return False