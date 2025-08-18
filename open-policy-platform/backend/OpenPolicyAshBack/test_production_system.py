#!/usr/bin/env python3
"""
OpenPolicy Platform Production System Test
=========================================

This script performs comprehensive testing of all production components:
1. Database connectivity and health
2. Monitoring system functionality
3. Dashboard accessibility
4. Data quality validation
5. System performance metrics

Usage:
    python3 test_production_system.py [--full]
"""

import os
import sys
import json
import time
import requests
import subprocess
import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('production_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ProductionSystemTester:
    """Comprehensive testing of production system components"""
    
    def __init__(self, full_test: bool = False):
        self.full_test = full_test
        self.project_root = Path(__file__).parent
        self.test_results = {}
        self.start_time = datetime.utcnow()
        
    def test_database_connectivity(self) -> bool:
        """Test database connectivity and health"""
        logger.info("🔍 Testing database connectivity...")
        
        try:
            import sqlalchemy as sa
            from sqlalchemy.orm import sessionmaker
            
            # Import database config
            sys.path.insert(0, str(self.project_root / 'src'))
            from database.config import get_database_url
            
            database_url = get_database_url()
            engine = sa.create_engine(database_url)
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            session = SessionLocal()
            
            # Test connection
            result = session.execute(sa.text("SELECT 1"))
            if result.fetchone()[0] == 1:
                logger.info("✅ Database connection successful")
                
                # Check table counts
                from database.models import Representative, Jurisdiction
                rep_count = session.query(Representative).count()
                jur_count = session.query(Jurisdiction).count()
                
                logger.info(f"📊 Database stats: {rep_count} representatives, {jur_count} jurisdictions")
                session.close()
                
                self.test_results['database'] = {
                    'status': 'success',
                    'representatives': rep_count,
                    'jurisdictions': jur_count
                }
                return True
            else:
                logger.error("❌ Database connection test failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Database connectivity test failed: {str(e)}")
            self.test_results['database'] = {'status': 'failed', 'error': str(e)}
            return False
    
    def test_monitoring_system(self) -> bool:
        """Test monitoring system functionality"""
        logger.info("🔍 Testing monitoring system...")
        
        try:
            monitoring_script = self.project_root / 'monitoring_system.py'
            
            if not monitoring_script.exists():
                logger.error("❌ Monitoring system script not found")
                self.test_results['monitoring'] = {'status': 'failed', 'error': 'Script not found'}
                return False
            
            # Test monitoring system import
            sys.path.insert(0, str(self.project_root))
            from monitoring_system import MonitoringSystem
            
            # Create monitoring system instance
            monitoring = MonitoringSystem(
                database_url=os.getenv('DATABASE_URL', 'postgresql://openpolicy:openpolicy123@localhost:5432/openpolicy')
            )
            
            # Test metrics collection
            system_metrics = monitoring.collect_system_metrics()
            scraper_metrics = monitoring.collect_scraper_metrics()
            data_quality_metrics = monitoring.collect_data_quality_metrics()
            
            logger.info("✅ Monitoring system test successful")
            logger.info(f"📊 System metrics: CPU {system_metrics.cpu_usage:.1f}%, Memory {system_metrics.memory_usage:.1f}%")
            
            self.test_results['monitoring'] = {
                'status': 'success',
                'system_metrics': {
                    'cpu_usage': system_metrics.cpu_usage,
                    'memory_usage': system_metrics.memory_usage,
                    'disk_usage': system_metrics.disk_usage
                },
                'scraper_metrics': len(scraper_metrics),
                'data_quality': data_quality_metrics.quality_score
            }
            return True
            
        except Exception as e:
            logger.error(f"❌ Monitoring system test failed: {str(e)}")
            self.test_results['monitoring'] = {'status': 'failed', 'error': str(e)}
            return False
    
    def test_dashboard(self) -> bool:
        """Test dashboard functionality"""
        logger.info("🔍 Testing dashboard...")
        
        try:
            dashboard_script = self.project_root / 'dashboard.py'
            
            if not dashboard_script.exists():
                logger.error("❌ Dashboard script not found")
                self.test_results['dashboard'] = {'status': 'failed', 'error': 'Script not found'}
                return False
            
            # Test dashboard import
            sys.path.insert(0, str(self.project_root))
            from dashboard import app
            
            # Test dashboard routes
            with app.test_client() as client:
                # Test main dashboard
                response = client.get('/')
                if response.status_code == 200:
                    logger.info("✅ Dashboard main page accessible")
                else:
                    logger.error(f"❌ Dashboard main page failed: {response.status_code}")
                    return False
                
                # Test API endpoints
                api_endpoints = [
                    '/api/system-metrics',
                    '/api/scraper-metrics', 
                    '/api/data-quality',
                    '/api/database-health'
                ]
                
                for endpoint in api_endpoints:
                    response = client.get(endpoint)
                    if response.status_code == 200:
                        logger.info(f"✅ API endpoint {endpoint} accessible")
                    else:
                        logger.warning(f"⚠️ API endpoint {endpoint} returned {response.status_code}")
            
            self.test_results['dashboard'] = {'status': 'success'}
            return True
            
        except Exception as e:
            logger.error(f"❌ Dashboard test failed: {str(e)}")
            self.test_results['dashboard'] = {'status': 'failed', 'error': str(e)}
            return False
    
    def test_data_quality(self) -> bool:
        """Test data quality metrics"""
        logger.info("🔍 Testing data quality...")
        
        try:
            import sqlalchemy as sa
            from sqlalchemy.orm import sessionmaker
            
            sys.path.insert(0, str(self.project_root / 'src'))
            from database.config import get_database_url
            from database.models import Representative, Jurisdiction
            
            database_url = get_database_url()
            engine = sa.create_engine(database_url)
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            session = SessionLocal()
            
            # Calculate data quality metrics
            total_records = session.query(Representative).count()
            complete_records = session.query(Representative).filter(
                Representative.name.isnot(None),
                Representative.role.isnot(None),
                Representative.jurisdiction_id.isnot(None)
            ).count()
            
            quality_score = (complete_records / total_records * 100) if total_records > 0 else 0
            
            logger.info(f"✅ Data quality test successful: {quality_score:.1f}% quality score")
            logger.info(f"📊 Data stats: {complete_records}/{total_records} complete records")
            
            self.test_results['data_quality'] = {
                'status': 'success',
                'quality_score': quality_score,
                'total_records': total_records,
                'complete_records': complete_records
            }
            
            session.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ Data quality test failed: {str(e)}")
            self.test_results['data_quality'] = {'status': 'failed', 'error': str(e)}
            return False
    
    def test_system_performance(self) -> bool:
        """Test system performance metrics"""
        logger.info("🔍 Testing system performance...")
        
        try:
            import psutil
            
            # Collect system metrics
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            logger.info(f"✅ System performance test successful")
            logger.info(f"📊 Performance: CPU {cpu_usage:.1f}%, Memory {memory.percent:.1f}%, Disk {disk.percent:.1f}%")
            
            self.test_results['system_performance'] = {
                'status': 'success',
                'cpu_usage': cpu_usage,
                'memory_usage': memory.percent,
                'disk_usage': disk.percent
            }
            return True
            
        except Exception as e:
            logger.error(f"❌ System performance test failed: {str(e)}")
            self.test_results['system_performance'] = {'status': 'failed', 'error': str(e)}
            return False
    
    def test_deployment_scripts(self) -> bool:
        """Test deployment scripts"""
        logger.info("🔍 Testing deployment scripts...")
        
        try:
            # Test deploy script
            deploy_script = self.project_root / 'deploy.py'
            if deploy_script.exists():
                result = subprocess.run([
                    sys.executable, str(deploy_script), '--help'
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    logger.info("✅ Deploy script test successful")
                else:
                    logger.error(f"❌ Deploy script test failed: {result.stderr}")
                    return False
            
            # Test production startup script
            startup_script = self.project_root / 'start_production.py'
            if startup_script.exists():
                result = subprocess.run([
                    sys.executable, str(startup_script), '--help'
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    logger.info("✅ Production startup script test successful")
                else:
                    logger.error(f"❌ Production startup script test failed: {result.stderr}")
                    return False
            
            self.test_results['deployment_scripts'] = {'status': 'success'}
            return True
            
        except Exception as e:
            logger.error(f"❌ Deployment scripts test failed: {str(e)}")
            self.test_results['deployment_scripts'] = {'status': 'failed', 'error': str(e)}
            return False
    
    def run_comprehensive_test(self) -> bool:
        """Run comprehensive production system test"""
        logger.info("🚀 Starting comprehensive production system test...")
        
        tests = [
            ('Database Connectivity', self.test_database_connectivity),
            ('Monitoring System', self.test_monitoring_system),
            ('Dashboard', self.test_dashboard),
            ('Data Quality', self.test_data_quality),
            ('System Performance', self.test_system_performance),
            ('Deployment Scripts', self.test_deployment_scripts)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            logger.info(f"\n{'='*50}")
            logger.info(f"Running {test_name} test...")
            logger.info(f"{'='*50}")
            
            try:
                if test_func():
                    passed_tests += 1
                    logger.info(f"✅ {test_name} test PASSED")
                else:
                    logger.error(f"❌ {test_name} test FAILED")
            except Exception as e:
                logger.error(f"❌ {test_name} test ERROR: {str(e)}")
        
        # Calculate overall success rate
        success_rate = (passed_tests / total_tests) * 100
        
        logger.info(f"\n{'='*50}")
        logger.info(f"🎯 TEST RESULTS SUMMARY")
        logger.info(f"{'='*50}")
        logger.info(f"Tests Passed: {passed_tests}/{total_tests}")
        logger.info(f"Success Rate: {success_rate:.1f}%")
        logger.info(f"Overall Status: {'✅ PASSED' if success_rate >= 80 else '❌ FAILED'}")
        
        # Save test results
        self.save_test_results()
        
        return success_rate >= 80
    
    def save_test_results(self):
        """Save test results to file"""
        try:
            results = {
                'timestamp': self.start_time.isoformat(),
                'duration': (datetime.utcnow() - self.start_time).total_seconds(),
                'test_results': self.test_results,
                'summary': {
                    'total_tests': len(self.test_results),
                    'passed_tests': sum(1 for r in self.test_results.values() if r.get('status') == 'success'),
                    'failed_tests': sum(1 for r in self.test_results.values() if r.get('status') == 'failed')
                }
            }
            
            results_file = self.project_root / f'production_test_results_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.json'
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2)
            
            logger.info(f"📄 Test results saved to: {results_file}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save test results: {str(e)}")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='OpenPolicy Platform Production System Test')
    parser.add_argument('--full', action='store_true', help='Run full comprehensive test')
    
    args = parser.parse_args()
    
    # Create tester
    tester = ProductionSystemTester(full_test=args.full)
    
    # Run tests
    success = tester.run_comprehensive_test()
    
    if success:
        logger.info("\n🎉 Production system test completed successfully!")
        logger.info("🚀 OpenPolicy Platform is ready for production deployment!")
        return 0
    else:
        logger.error("\n❌ Production system test failed!")
        logger.error("🔧 Please review the test results and fix any issues before deployment.")
        return 1


if __name__ == "__main__":
    exit(main())
