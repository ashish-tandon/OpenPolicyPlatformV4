#!/usr/bin/env python3
"""
Enhanced Scraper Testing Framework with Continuous Data Collection
"""

import os
import sys
import time
import json
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import psutil

# Add scrapers to path
sys.path.insert(0, "../../scrapers")

class EnhancedScraperFramework:
    def __init__(self):
        self.setup_logging()
        self.failure_log = []
        self.success_log = []
        self.data_collection_log = []
        
    def setup_logging(self):
        """Setup comprehensive logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'enhanced_scraper_run_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def run_continuous_collection(self, max_records=1000, interval=3600):
        """Run continuous data collection"""
        self.logger.info("🚀 Starting continuous data collection...")
        
        while True:
            try:
                self.run_comprehensive_test(max_records)
                self.save_collection_report()
                self.logger.info(f"⏰ Waiting {interval} seconds before next collection...")
                time.sleep(interval)
            except KeyboardInterrupt:
                self.logger.info("🛑 Continuous collection stopped by user")
                break
            except Exception as e:
                self.logger.error(f"❌ Error in continuous collection: {e}")
                time.sleep(300)  # Wait 5 minutes before retry
    
    def run_comprehensive_test(self, max_records=1000):
        """Run comprehensive scraper test with detailed logging"""
        start_time = time.time()
        
        # Import and run existing framework
        try:
            from scraper_testing_framework import run_scraper_tests
            results = run_scraper_tests(max_records=max_records)
            
            # Log results
            self.log_success(results)
            
        except Exception as e:
            self.log_failure(f"Framework execution error: {e}")
    
    def log_success(self, results):
        """Log successful scraper runs"""
        timestamp = datetime.now().isoformat()
        self.success_log.append({
            'timestamp': timestamp,
            'results': results
        })
        self.logger.info(f"✅ Success: {results}")
    
    def log_failure(self, error):
        """Log scraper failures with details"""
        timestamp = datetime.now().isoformat()
        failure_entry = {
            'timestamp': timestamp,
            'error': error,
            'system_info': {
                'cpu_percent': psutil.cpu_percent(),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_usage': psutil.disk_usage('/').percent
            }
        }
        self.failure_log.append(failure_entry)
        self.logger.error(f"❌ Failure: {error}")
    
    def save_collection_report(self):
        """Save comprehensive collection report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'success_count': len(self.success_log),
            'failure_count': len(self.failure_log),
            'recent_successes': self.success_log[-10:] if self.success_log else [],
            'recent_failures': self.failure_log[-10:] if self.failure_log else [],
            'system_stats': {
                'cpu_percent': psutil.cpu_percent(),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_usage': psutil.disk_usage('/').percent
            }
        }
        
        report_file = f'collection_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.logger.info(f"📊 Collection report saved to {report_file}")

if __name__ == "__main__":
    framework = EnhancedScraperFramework()
    framework.run_continuous_collection()
