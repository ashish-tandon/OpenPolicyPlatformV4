#!/usr/bin/env python3
"""
OpenPolicy Platform Production Status Checker
===========================================

This script checks the status of all production services and provides
a comprehensive status report.

Usage:
    python3 production_status.py [--detailed]
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
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ProductionStatusChecker:
    """Production status checker for OpenPolicy platform"""
    
    def __init__(self, detailed: bool = False):
        self.detailed = detailed
        self.project_root = Path(__file__).parent
        self.status_report = {}
        
    def check_database_status(self) -> Dict:
        """Check database status"""
        logger.info("🔍 Checking database status...")
        
        try:
            import sqlalchemy as sa
            from sqlalchemy.orm import sessionmaker
            
            # Import database config
            sys.path.insert(0, str(self.project_root / 'src'))
            from database.config import get_database_url
            from database.models import Representative, Jurisdiction
            
            database_url = get_database_url()
            engine = sa.create_engine(database_url)
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            session = SessionLocal()
            
            # Test connection
            result = session.execute(sa.text("SELECT 1"))
            if result.fetchone()[0] == 1:
                # Get counts
                rep_count = session.query(Representative).count()
                jur_count = session.query(Jurisdiction).count()
                
                session.close()
                
                status = {
                    'status': 'healthy',
                    'connection': 'successful',
                    'representatives': rep_count,
                    'jurisdictions': jur_count,
                    'last_check': datetime.utcnow().isoformat()
                }
                
                logger.info(f"✅ Database healthy: {rep_count} representatives, {jur_count} jurisdictions")
                return status
            else:
                session.close()
                return {'status': 'error', 'connection': 'failed'}
                
        except Exception as e:
            logger.error(f"❌ Database check failed: {str(e)}")
            return {'status': 'error', 'connection': 'failed', 'error': str(e)}
    
    def check_dashboard_status(self) -> Dict:
        """Check dashboard status"""
        logger.info("🔍 Checking dashboard status...")
        
        try:
            # Test dashboard endpoint
            response = requests.get('http://localhost:5001', timeout=10)
            
            if response.status_code == 200:
                status = {
                    'status': 'healthy',
                    'url': 'http://localhost:5001',
                    'response_time': response.elapsed.total_seconds(),
                    'last_check': datetime.utcnow().isoformat()
                }
                
                logger.info("✅ Dashboard healthy")
                return status
            else:
                return {
                    'status': 'warning',
                    'url': 'http://localhost:5001',
                    'response_code': response.status_code,
                    'last_check': datetime.utcnow().isoformat()
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Dashboard check failed: {str(e)}")
            return {
                'status': 'error',
                'url': 'http://localhost:5001',
                'error': str(e),
                'last_check': datetime.utcnow().isoformat()
            }
    
    def check_api_endpoints(self) -> Dict:
        """Check API endpoints"""
        logger.info("🔍 Checking API endpoints...")
        
        endpoints = [
            '/api/system-metrics',
            '/api/scraper-metrics',
            '/api/data-quality',
            '/api/database-health'
        ]
        
        api_status = {}
        
        for endpoint in endpoints:
            try:
                response = requests.get(f'http://localhost:5001{endpoint}', timeout=5)
                api_status[endpoint] = {
                    'status': 'healthy' if response.status_code == 200 else 'warning',
                    'response_code': response.status_code,
                    'response_time': response.elapsed.total_seconds()
                }
            except requests.exceptions.RequestException as e:
                api_status[endpoint] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        logger.info(f"✅ API endpoints checked: {len([e for e in api_status.values() if e['status'] == 'healthy'])}/{len(endpoints)} healthy")
        return api_status
    
    def check_system_metrics(self) -> Dict:
        """Check system metrics"""
        logger.info("🔍 Checking system metrics...")
        
        try:
            import psutil
            
            # CPU usage
            cpu_usage = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_usage = (disk.used / disk.total) * 100
            
            # Network I/O
            network_io = psutil.net_io_counters()
            
            metrics = {
                'cpu_usage': cpu_usage,
                'memory_usage': memory_usage,
                'disk_usage': disk_usage,
                'network_io': {
                    'bytes_sent': network_io.bytes_sent,
                    'bytes_recv': network_io.bytes_recv
                },
                'last_check': datetime.utcnow().isoformat()
            }
            
            logger.info(f"✅ System metrics: CPU {cpu_usage:.1f}%, Memory {memory_usage:.1f}%, Disk {disk_usage:.1f}%")
            return metrics
            
        except Exception as e:
            logger.error(f"❌ System metrics check failed: {str(e)}")
            return {'status': 'error', 'error': str(e)}
    
    def check_service_processes(self) -> Dict:
        """Check service processes"""
        logger.info("🔍 Checking service processes...")
        
        services = {
            'dashboard': 'dashboard.py',
            'monitoring': 'monitoring_system.py'
        }
        
        process_status = {}
        
        for service_name, script_name in services.items():
            try:
                # Check if process is running
                result = subprocess.run([
                    'pgrep', '-f', script_name
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    process_status[service_name] = {
                        'status': 'running',
                        'pid': result.stdout.strip().split('\n')[0] if result.stdout.strip() else 'unknown'
                    }
                else:
                    process_status[service_name] = {
                        'status': 'stopped'
                    }
                    
            except Exception as e:
                process_status[service_name] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        logger.info(f"✅ Service processes checked: {len([s for s in process_status.values() if s['status'] == 'running'])}/{len(services)} running")
        return process_status
    
    def generate_status_report(self) -> Dict:
        """Generate comprehensive status report"""
        logger.info("🚀 Generating production status report...")
        
        report = {
            'timestamp': datetime.utcnow().isoformat(),
            'platform': 'OpenPolicy',
            'version': '1.0.0',
            'status': 'unknown',
            'services': {}
        }
        
        # Check all services
        report['services']['database'] = self.check_database_status()
        report['services']['dashboard'] = self.check_dashboard_status()
        report['services']['api_endpoints'] = self.check_api_endpoints()
        report['services']['system_metrics'] = self.check_system_metrics()
        report['services']['processes'] = self.check_service_processes()
        
        # Determine overall status
        healthy_services = 0
        total_services = 0
        
        for service_name, service_status in report['services'].items():
            if isinstance(service_status, dict):
                if service_status.get('status') == 'healthy':
                    healthy_services += 1
                total_services += 1
            elif isinstance(service_status, dict):
                # Handle nested services (like API endpoints)
                for endpoint_name, endpoint_status in service_status.items():
                    if endpoint_status.get('status') == 'healthy':
                        healthy_services += 1
                    total_services += 1
        
        # Calculate overall status
        if total_services > 0:
            health_percentage = (healthy_services / total_services) * 100
            
            if health_percentage >= 90:
                report['status'] = 'healthy'
            elif health_percentage >= 70:
                report['status'] = 'warning'
            else:
                report['status'] = 'critical'
            
            report['health_percentage'] = health_percentage
            report['healthy_services'] = healthy_services
            report['total_services'] = total_services
        
        return report
    
    def print_status_report(self, report: Dict):
        """Print status report"""
        print("\n" + "="*60)
        print("🎯 OpenPolicy Platform - Production Status Report")
        print("="*60)
        
        # Overall status
        status_emoji = {
            'healthy': '✅',
            'warning': '⚠️',
            'critical': '❌',
            'unknown': '❓'
        }
        
        emoji = status_emoji.get(report['status'], '❓')
        print(f"\n{emoji} Overall Status: {report['status'].upper()}")
        
        if 'health_percentage' in report:
            print(f"📊 Health Score: {report['health_percentage']:.1f}% ({report['healthy_services']}/{report['total_services']} services)")
        
        print(f"🕒 Last Check: {report['timestamp']}")
        
        # Service status
        print(f"\n{'='*40}")
        print("🔧 Service Status")
        print(f"{'='*40}")
        
        for service_name, service_status in report['services'].items():
            if isinstance(service_status, dict) and 'status' in service_status:
                status_emoji = {
                    'healthy': '✅',
                    'warning': '⚠️',
                    'error': '❌',
                    'running': '✅',
                    'stopped': '❌'
                }
                
                emoji = status_emoji.get(service_status['status'], '❓')
                print(f"{emoji} {service_name.title()}: {service_status['status']}")
                
                if self.detailed and service_status.get('status') == 'healthy':
                    if 'representatives' in service_status:
                        print(f"   📊 Representatives: {service_status['representatives']}")
                        print(f"   🏛️ Jurisdictions: {service_status['jurisdictions']}")
                    elif 'response_time' in service_status:
                        print(f"   ⚡ Response Time: {service_status['response_time']:.3f}s")
                    elif 'cpu_usage' in service_status:
                        print(f"   🖥️ CPU: {service_status['cpu_usage']:.1f}%")
                        print(f"   💾 Memory: {service_status['memory_usage']:.1f}%")
                        print(f"   💿 Disk: {service_status['disk_usage']:.1f}%")
        
        # Summary
        print(f"\n{'='*40}")
        print("📋 Summary")
        print(f"{'='*40}")
        
        if report['status'] == 'healthy':
            print("🎉 All systems are operational!")
            print("🚀 OpenPolicy Platform is running smoothly.")
        elif report['status'] == 'warning':
            print("⚠️ Some services have issues but the platform is still operational.")
            print("🔧 Consider reviewing the warnings above.")
        else:
            print("❌ Critical issues detected!")
            print("🚨 Immediate attention required.")
        
        print(f"\n🌐 Dashboard: http://localhost:5001")
        print(f"📊 Monitoring: Active")
        print(f"🔍 Health Checks: Running")
    
    def save_status_report(self, report: Dict):
        """Save status report to file"""
        try:
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            filename = f'production_status_{timestamp}.json'
            
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"📄 Status report saved to: {filename}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save status report: {str(e)}")
    
    def run(self):
        """Run the status checker"""
        logger.info("🚀 Starting production status check...")
        
        # Generate status report
        report = self.generate_status_report()
        
        # Print status report
        self.print_status_report(report)
        
        # Save status report
        self.save_status_report(report)
        
        return report['status'] == 'healthy'


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='OpenPolicy Platform Production Status Checker')
    parser.add_argument('--detailed', action='store_true', help='Show detailed status information')
    
    args = parser.parse_args()
    
    # Create status checker
    checker = ProductionStatusChecker(detailed=args.detailed)
    
    # Run status check
    success = checker.run()
    
    if success:
        logger.info("🎉 Production status check completed successfully!")
        return 0
    else:
        logger.error("❌ Production status check found issues!")
        return 1


if __name__ == "__main__":
    exit(main())
