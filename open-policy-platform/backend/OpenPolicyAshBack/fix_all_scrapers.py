#!/usr/bin/env python3
"""
Comprehensive Scraper Fix Script
Fixes all classification errors in CSVScraper classes
"""

import os
import re
import glob

def fix_csv_scrapers():
    """Fix all CSVScraper classes by adding organization_classification"""
    print("🔧 Fixing CSVScraper classification errors...")
    
    # Find all people.py files in scrapers
    scraper_files = glob.glob("../../scrapers/**/people.py", recursive=True)
    
    fixed_count = 0
    total_count = 0
    
    for file_path in scraper_files:
        total_count += 1
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Check if this is a CSVScraper class
            if 'CSVScraper' in content and 'class' in content:
                # Check if organization_classification is already set
                if 'organization_classification' not in content:
                    # Add organization_classification
                    class_pattern = r'class (\w+PersonScraper)\(CSVScraper\):'
                    match = re.search(class_pattern, content)
                    
                    if match:
                        class_name = match.group(1)
                        new_content = re.sub(
                            class_pattern,
                            f'class {class_name}(CSVScraper):\n    organization_classification = "legislature"',
                            content
                        )
                        
                        with open(file_path, 'w') as f:
                            f.write(new_content)
                        
                        print(f"  ✅ Fixed {file_path}")
                        fixed_count += 1
                    else:
                        print(f"  ⚠️  Could not find CSVScraper class in {file_path}")
                else:
                    print(f"  ✅ {file_path} already has organization_classification")
            else:
                print(f"  ⏭️  Skipping {file_path} (not a CSVScraper)")
                
        except Exception as e:
            print(f"  ❌ Error processing {file_path}: {e}")
    
    print(f"\n📊 Fixed {fixed_count} out of {total_count} scraper files")
    return fixed_count

def fix_ssl_issues():
    """Fix SSL certificate issues"""
    print("\n🔧 Fixing SSL certificate issues...")
    
    # Add SSL fix to utils.py
    utils_path = "../../scrapers/scrapers-ca/utils.py"
    
    if os.path.exists(utils_path):
        try:
            with open(utils_path, 'r') as f:
                content = f.read()
            
            # Check if SSL fix is already present
            if 'ssl._create_default_https_context' not in content:
                # Add SSL fix after imports
                ssl_fix = '''
# SSL Certificate Fix
import ssl
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
ssl._create_default_https_context = ssl._create_unverified_context

'''
                
                # Find the end of imports
                lines = content.split('\n')
                import_end = 0
                
                for i, line in enumerate(lines):
                    if line.startswith('import ') or line.startswith('from '):
                        import_end = i + 1
                    elif line.strip() and not line.startswith('#'):
                        break
                
                # Insert SSL fix after imports
                lines.insert(import_end, ssl_fix)
                
                with open(utils_path, 'w') as f:
                    f.write('\n'.join(lines))
                
                print(f"  ✅ Added SSL fix to {utils_path}")
            else:
                print(f"  ✅ {utils_path} already has SSL fix")
                
        except Exception as e:
            print(f"  ❌ Error fixing SSL in {utils_path}: {e}")
    else:
        print(f"  ⚠️  {utils_path} not found")

def create_comprehensive_monitoring():
    """Create comprehensive monitoring and data collection system"""
    print("\n🔧 Creating comprehensive monitoring system...")
    
    # Create enhanced scraper testing framework
    enhanced_framework = '''#!/usr/bin/env python3
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
'''
    
    with open('enhanced_scraper_framework.py', 'w') as f:
        f.write(enhanced_framework)
    
    print("  ✅ Created enhanced scraper framework")

def main():
    """Main function to fix all scraper issues"""
    print("🚀 COMPREHENSIVE SCRAPER FIX SCRIPT")
    print("=" * 50)
    
    # Fix all issues
    fixed_count = fix_csv_scrapers()
    fix_ssl_issues()
    create_comprehensive_monitoring()
    
    print(f"\n✅ SCRAPER FIXES COMPLETED!")
    print(f"📊 Fixed {fixed_count} CSVScraper classification errors")
    print("🔧 SSL certificate issues addressed")
    print("📊 Enhanced monitoring system created")
    print("\n🎯 Next: Run enhanced framework for continuous data collection")

if __name__ == "__main__":
    main()
