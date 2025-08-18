"""
Comprehensive Scraper Testing Script
Tests all scrapers, validates data ingestion, and ensures no data is lost
"""

import os
import sys
import logging
import time
import json
from datetime import datetime, timedelta
from sqlalchemy import text, create_engine, inspect
from sqlalchemy.orm import sessionmaker
import psycopg2
from psycopg2.extras import RealDictCursor

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db_config

logger = logging.getLogger(__name__)

class ComprehensiveScraperTester:
    """Comprehensive scraper testing and data ingestion validation"""
    
    def __init__(self):
        self.engine = create_engine(db_config.get_url())
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.inspector = inspect(self.engine)
        self.test_results = {}
        self.data_preservation_log = {}
        
    def test_federal_parliament_scraper(self):
        """Test federal parliament scraper with data preservation validation"""
        logger.info("Testing Federal Parliament Scraper")
        
        try:
            # Record data before scraping
            pre_scrape_counts = self.get_table_counts()
            logger.info(f"Pre-scrape counts: {pre_scrape_counts}")
            
            # Import and run federal scraper
            from scrapers.federal_parliament_scraper import FederalParliamentScraper
            scraper = FederalParliamentScraper()
            
            # Test individual scraper methods
            logger.info("Testing bills scraping...")
            bills_data = scraper.scrape_bills()
            logger.info(f"Scraped {len(bills_data)} bills")
            
            logger.info("Testing MPs scraping...")
            mps_data = scraper.scrape_mps()
            logger.info(f"Scraped {len(mps_data)} MPs")
            
            logger.info("Testing votes scraping...")
            votes_data = scraper.scrape_votes()
            logger.info(f"Scraped {len(votes_data)} votes")
            
            # Test comprehensive scraping
            logger.info("Testing comprehensive scraping...")
            all_data = scraper.scrape_all()
            logger.info(f"Comprehensive scrape results: {len(all_data.get('bills', []))} bills, {len(all_data.get('mps', []))} MPs, {len(all_data.get('votes', []))} votes")
            
            # Validate data quality
            bills_valid = scraper.validate_data({'bills': bills_data})
            mps_valid = scraper.validate_data({'mps': mps_data})
            votes_valid = scraper.validate_data({'votes': votes_data})
            
            # Store test results
            self.test_results['federal_parliament'] = {
                'status': 'success',
                'bills_scraped': len(bills_data),
                'mps_scraped': len(mps_data),
                'votes_scraped': len(votes_data),
                'bills_valid': bills_valid,
                'mps_valid': mps_valid,
                'votes_valid': votes_valid,
                'pre_scrape_counts': pre_scrape_counts,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info("Federal Parliament Scraper test completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Federal Parliament Scraper test failed: {e}")
            self.test_results['federal_parliament'] = {
                'status': 'failed',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            return False
    
    def test_provincial_scrapers(self):
        """Test all provincial scrapers"""
        logger.info("Testing Provincial Scrapers")
        
        provinces = [
            'ontario', 'quebec', 'british_columbia', 'alberta', 
            'manitoba', 'saskatchewan', 'nova_scotia', 'new_brunswick',
            'newfoundland', 'prince_edward_island', 'northwest_territories',
            'nunavut', 'yukon'
        ]
        
        for province in provinces:
            try:
                logger.info(f"Testing {province} scraper...")
                
                # Record data before scraping
                pre_scrape_counts = self.get_table_counts()
                
                # Import provincial scraper (if exists)
                scraper_module = f"scrapers.{province}_scraper"
                try:
                    scraper_class = getattr(__import__(scraper_module, fromlist=[f"{province.capitalize()}Scraper"]), f"{province.capitalize()}Scraper")
                    scraper = scraper_class()
                    
                    # Test scraping
                    data = scraper.scrape_all()
                    
                    # Validate data
                    data_valid = scraper.validate_data(data)
                    
                    self.test_results[f'{province}_scraper'] = {
                        'status': 'success',
                        'data_scraped': len(data),
                        'data_valid': data_valid,
                        'pre_scrape_counts': pre_scrape_counts,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    logger.info(f"{province} scraper test completed successfully")
                    
                except ImportError:
                    logger.warning(f"{province} scraper not implemented yet")
                    self.test_results[f'{province}_scraper'] = {
                        'status': 'not_implemented',
                        'timestamp': datetime.now().isoformat()
                    }
                    
            except Exception as e:
                logger.error(f"{province} scraper test failed: {e}")
                self.test_results[f'{province}_scraper'] = {
                    'status': 'failed',
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
    
    def test_municipal_scrapers(self):
        """Test all municipal scrapers"""
        logger.info("Testing Municipal Scrapers")
        
        cities = [
            'toronto', 'montreal', 'vancouver', 'calgary', 'edmonton',
            'ottawa', 'winnipeg', 'quebec_city', 'hamilton', 'kitchener'
        ]
        
        for city in cities:
            try:
                logger.info(f"Testing {city} scraper...")
                
                # Record data before scraping
                pre_scrape_counts = self.get_table_counts()
                
                # Import municipal scraper (if exists)
                scraper_module = f"scrapers.{city}_scraper"
                try:
                    scraper_class = getattr(__import__(scraper_module, fromlist=[f"{city.capitalize()}Scraper"]), f"{city.capitalize()}Scraper")
                    scraper = scraper_class()
                    
                    # Test scraping
                    data = scraper.scrape_all()
                    
                    # Validate data
                    data_valid = scraper.validate_data(data)
                    
                    self.test_results[f'{city}_scraper'] = {
                        'status': 'success',
                        'data_scraped': len(data),
                        'data_valid': data_valid,
                        'pre_scrape_counts': pre_scrape_counts,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    logger.info(f"{city} scraper test completed successfully")
                    
                except ImportError:
                    logger.warning(f"{city} scraper not implemented yet")
                    self.test_results[f'{city}_scraper'] = {
                        'status': 'not_implemented',
                        'timestamp': datetime.now().isoformat()
                    }
                    
            except Exception as e:
                logger.error(f"{city} scraper test failed: {e}")
                self.test_results[f'{city}_scraper'] = {
                    'status': 'failed',
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
    
    def validate_data_ingestion(self):
        """Validate that scraped data is properly ingested into database"""
        logger.info("Validating data ingestion")
        
        with self.engine.connect() as conn:
            # Check data preservation
            for scraper_name, result in self.test_results.items():
                if result['status'] == 'success' and 'pre_scrape_counts' in result:
                    pre_counts = result['pre_scrape_counts']
                    post_counts = self.get_table_counts()
                    
                    # Verify no data was lost
                    data_preserved = True
                    for table, pre_count in pre_counts.items():
                        post_count = post_counts.get(table, 0)
                        if post_count < pre_count:
                            data_preserved = False
                            logger.error(f"DATA LOSS DETECTED in {table}: {pre_count} -> {post_count}")
                    
                    result['data_preserved'] = data_preserved
                    result['post_scrape_counts'] = post_counts
                    
                    if data_preserved:
                        logger.info(f"Data preservation verified for {scraper_name}")
                    else:
                        logger.error(f"Data loss detected for {scraper_name}")
            
            # Check data quality
            quality_checks = [
                "SELECT COUNT(*) FROM bills_bill WHERE title IS NULL OR title = ''",
                "SELECT COUNT(*) FROM politicians_politician WHERE name IS NULL OR name = ''",
                "SELECT COUNT(*) FROM votes_vote WHERE bill_number IS NULL",
                "SELECT COUNT(*) FROM bills_bill WHERE jurisdiction NOT IN ('federal', 'provincial', 'municipal')",
                "SELECT COUNT(*) FROM bills_bill WHERE introduced_date > CURRENT_DATE"
            ]
            
            quality_results = {}
            for i, check in enumerate(quality_checks):
                try:
                    result = conn.execute(text(check))
                    count = result.fetchone()[0]
                    quality_results[f'quality_check_{i+1}'] = count
                    
                    if count > 0:
                        logger.warning(f"Quality issue detected: {count} records with issues")
                    else:
                        logger.info(f"Quality check {i+1} passed")
                        
                except Exception as e:
                    logger.error(f"Quality check {i+1} failed: {e}")
            
            self.test_results['data_quality'] = quality_results
    
    def get_table_counts(self):
        """Get current record counts for all tables"""
        with self.engine.connect() as conn:
            tables = ['bills_bill', 'politicians_politician', 'votes_vote', 
                     'hansards_statement', 'committees_committee', 'activity_activity']
            
            counts = {}
            for table in tables:
                try:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.fetchone()[0]
                    counts[table] = count
                except Exception as e:
                    logger.warning(f"Could not get count for {table}: {e}")
                    counts[table] = 0
            
            return counts
    
    def create_daily_scheduler(self):
        """Create daily scheduler for scrapers"""
        logger.info("Creating daily scheduler for scrapers")
        
        with self.engine.connect() as conn:
            # Create scheduler table
            scheduler_table = """
            CREATE TABLE IF NOT EXISTS scraper_schedule (
                id SERIAL PRIMARY KEY,
                scraper_name VARCHAR(100) NOT NULL,
                schedule_type VARCHAR(20) DEFAULT 'daily',
                last_run TIMESTAMP,
                next_run TIMESTAMP,
                status VARCHAR(20) DEFAULT 'pending',
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            
            try:
                conn.execute(text(scheduler_table))
                conn.commit()
                logger.info("Created scraper schedule table")
            except Exception as e:
                logger.warning(f"Scheduler table creation warning: {e}")
                conn.rollback()
            
            # Insert daily schedule for all scrapers
            scrapers = [
                'federal_parliament',
                'ontario', 'quebec', 'british_columbia', 'alberta',
                'manitoba', 'saskatchewan', 'nova_scotia', 'new_brunswick',
                'toronto', 'montreal', 'vancouver', 'calgary', 'edmonton'
            ]
            
            for scraper in scrapers:
                try:
                    # Set next run to tomorrow at 2 AM
                    next_run = datetime.now().replace(hour=2, minute=0, second=0, microsecond=0) + timedelta(days=1)
                    
                    insert_sql = """
                    INSERT INTO scraper_schedule (scraper_name, schedule_type, next_run)
                    VALUES (:scraper_name, 'daily', :next_run)
                    ON CONFLICT (scraper_name) DO UPDATE SET
                    next_run = :next_run,
                    is_active = TRUE
                    """
                    
                    conn.execute(text(insert_sql), {
                        'scraper_name': scraper,
                        'next_run': next_run
                    })
                    conn.commit()
                    logger.info(f"Scheduled {scraper} scraper for daily execution")
                    
                except Exception as e:
                    logger.warning(f"Failed to schedule {scraper}: {e}")
                    conn.rollback()
    
    def create_daily_execution_script(self):
        """Create daily execution script for scrapers"""
        logger.info("Creating daily execution script")
        
        script_content = """#!/bin/bash

# Daily Scraper Execution Script
# This script runs all active scrapers according to their schedule

set -e

echo "Starting daily scraper execution at $(date)"

# Activate virtual environment
source backend/venv/bin/activate

# Set environment variables
export PYTHONPATH="${PYTHONPATH}:$(pwd)/backend"

# Run scraper execution script
cd backend
python scripts/execute_daily_scrapers.py

echo "Daily scraper execution completed at $(date)"
"""
        
        script_path = "scripts/run_daily_scrapers.sh"
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        # Make script executable
        os.chmod(script_path, 0o755)
        logger.info(f"Created daily execution script: {script_path}")
    
    def create_execution_script(self):
        """Create the Python execution script for daily scrapers"""
        logger.info("Creating Python execution script for daily scrapers")
        
        script_content = '''
"""
Daily Scraper Execution Script
Executes all scheduled scrapers and validates data ingestion
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from sqlalchemy import text, create_engine

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db_config

logger = logging.getLogger(__name__)

class DailyScraperExecutor:
    """Executes daily scraper tasks"""
    
    def __init__(self):
        self.engine = create_engine(db_config.get_url())
    
    def get_scheduled_scrapers(self):
        """Get scrapers scheduled to run today"""
        with self.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT scraper_name, schedule_type 
                FROM scraper_schedule 
                WHERE is_active = TRUE 
                AND next_run <= CURRENT_TIMESTAMP
            """))
            return result.fetchall()
    
    def execute_scraper(self, scraper_name):
        """Execute a specific scraper"""
        logger.info(f"Executing {scraper_name} scraper")
        
        try:
            # Record pre-execution counts
            pre_counts = self.get_table_counts()
            
            # Import and execute scraper
            if scraper_name == 'federal_parliament':
                from scrapers.federal_parliament_scraper import FederalParliamentScraper
                scraper = FederalParliamentScraper()
                data = scraper.scrape_all()
            else:
                # Handle other scrapers
                logger.warning(f"Scraper {scraper_name} not implemented yet")
                return False
            
            # Record post-execution counts
            post_counts = self.get_table_counts()
            
            # Validate data preservation
            data_preserved = True
            for table, pre_count in pre_counts.items():
                post_count = post_counts.get(table, 0)
                if post_count < pre_count:
                    data_preserved = False
                    logger.error(f"DATA LOSS DETECTED in {table}: {pre_count} -> {post_count}")
            
            # Update schedule
            next_run = datetime.now() + timedelta(days=1)
            with self.engine.connect() as conn:
                conn.execute(text("""
                    UPDATE scraper_schedule 
                    SET last_run = CURRENT_TIMESTAMP,
                        next_run = :next_run,
                        status = :status
                    WHERE scraper_name = :scraper_name
                """), {
                    'scraper_name': scraper_name,
                    'next_run': next_run,
                    'status': 'completed' if data_preserved else 'failed'
                })
                conn.commit()
            
            logger.info(f"{scraper_name} scraper execution completed")
            return data_preserved
            
        except Exception as e:
            logger.error(f"{scraper_name} scraper execution failed: {e}")
            
            # Update schedule with failure
            with self.engine.connect() as conn:
                conn.execute(text("""
                    UPDATE scraper_schedule 
                    SET last_run = CURRENT_TIMESTAMP,
                        status = 'failed'
                    WHERE scraper_name = :scraper_name
                """), {'scraper_name': scraper_name})
                conn.commit()
            
            return False
    
    def get_table_counts(self):
        """Get current record counts"""
        with self.engine.connect() as conn:
            tables = ['bills_bill', 'politicians_politician', 'votes_vote', 
                     'hansards_statement', 'committees_committee', 'activity_activity']
            
            counts = {}
            for table in tables:
                try:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.fetchone()[0]
                    counts[table] = count
                except Exception as e:
                    counts[table] = 0
            
            return counts
    
    def run_daily_execution(self):
        """Run daily scraper execution"""
        logger.info("Starting daily scraper execution")
        
        scheduled_scrapers = self.get_scheduled_scrapers()
        logger.info(f"Found {len(scheduled_scrapers)} scrapers scheduled for execution")
        
        results = {}
        for scraper_name, schedule_type in scheduled_scrapers:
            success = self.execute_scraper(scraper_name)
            results[scraper_name] = success
        
        # Log results
        successful = sum(1 for success in results.values() if success)
        total = len(results)
        
        logger.info(f"Daily execution completed: {successful}/{total} scrapers successful")
        
        return results

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    executor = DailyScraperExecutor()
    executor.run_daily_execution()
'''
        
        script_path = "backend/scripts/execute_daily_scrapers.py"
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        logger.info(f"Created Python execution script: {script_path}")
    
    def run_comprehensive_test(self):
        """Run comprehensive scraper testing"""
        logger.info("Starting comprehensive scraper testing")
        
        try:
            # Test all scrapers
            self.test_federal_parliament_scraper()
            self.test_provincial_scrapers()
            self.test_municipal_scrapers()
            
            # Validate data ingestion
            self.validate_data_ingestion()
            
            # Create daily scheduler
            self.create_daily_scheduler()
            
            # Create execution scripts
            self.create_daily_execution_script()
            self.create_execution_script()
            
            # Generate test report
            self.generate_test_report()
            
            logger.info("Comprehensive scraper testing completed")
            
        except Exception as e:
            logger.error(f"Comprehensive testing failed: {e}")
            raise
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        logger.info("Generating test report")
        
        report = {
            'test_timestamp': datetime.now().isoformat(),
            'summary': {
                'total_scrapers_tested': len(self.test_results),
                'successful_scrapers': sum(1 for r in self.test_results.values() if r.get('status') == 'success'),
                'failed_scrapers': sum(1 for r in self.test_results.values() if r.get('status') == 'failed'),
                'not_implemented': sum(1 for r in self.test_results.values() if r.get('status') == 'not_implemented')
            },
            'detailed_results': self.test_results,
            'recommendations': self.generate_recommendations()
        }
        
        # Save report
        report_path = f"scraper_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Test report saved: {report_path}")
        
        # Print summary
        print("\n" + "="*60)
        print("COMPREHENSIVE SCRAPER TEST REPORT")
        print("="*60)
        print(f"Total scrapers tested: {report['summary']['total_scrapers_tested']}")
        print(f"Successful: {report['summary']['successful_scrapers']}")
        print(f"Failed: {report['summary']['failed_scrapers']}")
        print(f"Not implemented: {report['summary']['not_implemented']}")
        print("="*60)
        
        # Print detailed results
        for scraper_name, result in self.test_results.items():
            status = result.get('status', 'unknown')
            print(f"{scraper_name}: {status}")
            if status == 'failed':
                print(f"  Error: {result.get('error', 'Unknown error')}")
            elif status == 'success':
                print(f"  Data scraped: {result.get('bills_scraped', 0)} bills, {result.get('mps_scraped', 0)} MPs, {result.get('votes_scraped', 0)} votes")
                print(f"  Data preserved: {result.get('data_preserved', False)}")
    
    def generate_recommendations(self):
        """Generate recommendations based on test results"""
        recommendations = []
        
        # Check for failed scrapers
        failed_scrapers = [name for name, result in self.test_results.items() if result.get('status') == 'failed']
        if failed_scrapers:
            recommendations.append(f"Fix failed scrapers: {', '.join(failed_scrapers)}")
        
        # Check for data loss
        data_loss_scrapers = [name for name, result in self.test_results.items() 
                            if result.get('status') == 'success' and not result.get('data_preserved', True)]
        if data_loss_scrapers:
            recommendations.append(f"Investigate data loss in scrapers: {', '.join(data_loss_scrapers)}")
        
        # Check for not implemented scrapers
        not_implemented = [name for name, result in self.test_results.items() if result.get('status') == 'not_implemented']
        if not_implemented:
            recommendations.append(f"Implement missing scrapers: {', '.join(not_implemented)}")
        
        # Check data quality
        if 'data_quality' in self.test_results:
            quality_issues = sum(1 for count in self.test_results['data_quality'].values() if count > 0)
            if quality_issues > 0:
                recommendations.append(f"Address {quality_issues} data quality issues")
        
        if not recommendations:
            recommendations.append("All scrapers working correctly - no immediate action required")
        
        return recommendations

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run comprehensive testing
    tester = ComprehensiveScraperTester()
    tester.run_comprehensive_test()
