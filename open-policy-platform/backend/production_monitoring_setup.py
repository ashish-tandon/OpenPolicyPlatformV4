#!/usr/bin/env python3
"""
🎯 OpenPolicy Platform - Production Monitoring Setup

This script sets up comprehensive production monitoring for the OpenPolicy platform,
including system monitoring, application monitoring, alerting, and dashboard setup.
"""

import json
import logging
import time
import requests
import psutil
import redis
import sqlalchemy
from sqlalchemy import text, create_engine
from sqlalchemy.orm import sessionmaker
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import threading
from dataclasses import dataclass, asdict
import yaml
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MonitoringConfig:
    """Monitoring configuration"""
    system_monitoring: bool = True
    application_monitoring: bool = True
    database_monitoring: bool = True
    alerting: bool = True
    dashboard: bool = True
    log_monitoring: bool = True
    performance_monitoring: bool = True
    security_monitoring: bool = True

@dataclass
class AlertRule:
    """Alert rule configuration"""
    name: str
    condition: str
    threshold: float
    severity: str  # 'critical', 'warning', 'info'
    description: str
    enabled: bool = True

class ProductionMonitoringSetup:
    """Production monitoring setup engine for OpenPolicy platform"""
    
    def __init__(self, 
                 base_url: str = "http://localhost:8000",
                 database_url: str = "postgresql://openpolicy:openpolicy123@localhost:5432/openpolicy",
                 redis_url: str = "redis://localhost:6379"):
        self.base_url = base_url
        self.database_url = database_url
        self.redis_url = redis_url
        self.config = MonitoringConfig()
        self.alert_rules: List[AlertRule] = []
        self.monitoring_data: Dict[str, Any] = {}
        
        # Initialize connections
        self.engine = None
        self.redis_client = None
        self.session_factory = None
        
        self._initialize_connections()
        self._setup_alert_rules()
    
    def _initialize_connections(self):
        """Initialize database and Redis connections"""
        try:
            # Database connection
            self.engine = create_engine(self.database_url, pool_size=20, max_overflow=30)
            self.session_factory = sessionmaker(bind=self.engine)
            logger.info("✅ Database connection established")
            
            # Redis connection
            self.redis_client = redis.from_url(self.redis_url)
            self.redis_client.ping()
            logger.info("✅ Redis connection established")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize connections: {e}")
            raise
    
    def _setup_alert_rules(self):
        """Setup default alert rules"""
        self.alert_rules = [
            AlertRule(
                name="High CPU Usage",
                condition="cpu_percent > 80",
                threshold=80.0,
                severity="warning",
                description="CPU usage is above 80%"
            ),
            AlertRule(
                name="High Memory Usage",
                condition="memory_percent > 85",
                threshold=85.0,
                severity="warning",
                description="Memory usage is above 85%"
            ),
            AlertRule(
                name="High Disk Usage",
                condition="disk_percent > 90",
                threshold=90.0,
                severity="critical",
                description="Disk usage is above 90%"
            ),
            AlertRule(
                name="High Error Rate",
                condition="error_rate > 5",
                threshold=5.0,
                severity="critical",
                description="Error rate is above 5%"
            ),
            AlertRule(
                name="Slow Response Time",
                condition="response_time > 1000",
                threshold=1000.0,
                severity="warning",
                description="Response time is above 1 second"
            ),
            AlertRule(
                name="Database Connection Issues",
                condition="db_connections > 80",
                threshold=80.0,
                severity="warning",
                description="Database connections are above 80%"
            ),
            AlertRule(
                name="API Endpoint Down",
                condition="endpoint_status != 200",
                threshold=0.0,
                severity="critical",
                description="API endpoint is not responding"
            )
        ]
    
    def setup_system_monitoring(self) -> Dict[str, Any]:
        """Setup system monitoring"""
        logger.info("🔧 Setting up system monitoring...")
        
        try:
            # Create system monitoring configuration
            system_config = {
                "cpu_monitoring": {
                    "enabled": True,
                    "interval": 60,
                    "thresholds": {
                        "warning": 80.0,
                        "critical": 95.0
                    }
                },
                "memory_monitoring": {
                    "enabled": True,
                    "interval": 60,
                    "thresholds": {
                        "warning": 85.0,
                        "critical": 95.0
                    }
                },
                "disk_monitoring": {
                    "enabled": True,
                    "interval": 300,
                    "thresholds": {
                        "warning": 85.0,
                        "critical": 95.0
                    }
                },
                "network_monitoring": {
                    "enabled": True,
                    "interval": 60,
                    "thresholds": {
                        "warning": 80.0,
                        "critical": 95.0
                    }
                }
            }
            
            # Store configuration in Redis
            self.redis_client.setex(
                "monitoring:system:config",
                3600,
                json.dumps(system_config)
            )
            
            logger.info("✅ System monitoring configured")
            return system_config
            
        except Exception as e:
            logger.error(f"❌ System monitoring setup failed: {e}")
            raise
    
    def setup_application_monitoring(self) -> Dict[str, Any]:
        """Setup application monitoring"""
        logger.info("🔧 Setting up application monitoring...")
        
        try:
            # Create application monitoring configuration
            app_config = {
                "api_monitoring": {
                    "enabled": True,
                    "endpoints": [
                        "/api/v1/health",
                        "/api/v1/stats",
                        "/api/v1/jurisdictions",
                        "/api/v1/representatives",
                        "/api/v1/policies"
                    ],
                    "interval": 30,
                    "timeout": 10
                },
                "performance_monitoring": {
                    "enabled": True,
                    "metrics": [
                        "response_time",
                        "throughput",
                        "error_rate",
                        "availability"
                    ],
                    "interval": 60
                },
                "error_monitoring": {
                    "enabled": True,
                    "log_levels": ["ERROR", "CRITICAL"],
                    "alert_threshold": 5
                }
            }
            
            # Store configuration in Redis
            self.redis_client.setex(
                "monitoring:application:config",
                3600,
                json.dumps(app_config)
            )
            
            logger.info("✅ Application monitoring configured")
            return app_config
            
        except Exception as e:
            logger.error(f"❌ Application monitoring setup failed: {e}")
            raise
    
    def setup_database_monitoring(self) -> Dict[str, Any]:
        """Setup database monitoring"""
        logger.info("🔧 Setting up database monitoring...")
        
        try:
            # Create database monitoring configuration
            db_config = {
                "connection_monitoring": {
                    "enabled": True,
                    "interval": 60,
                    "thresholds": {
                        "warning": 80.0,
                        "critical": 95.0
                    }
                },
                "query_monitoring": {
                    "enabled": True,
                    "slow_query_threshold": 1000,
                    "interval": 300
                },
                "performance_monitoring": {
                    "enabled": True,
                    "metrics": [
                        "query_time",
                        "connections",
                        "locks",
                        "cache_hit_ratio"
                    ],
                    "interval": 60
                }
            }
            
            # Store configuration in Redis
            self.redis_client.setex(
                "monitoring:database:config",
                3600,
                json.dumps(db_config)
            )
            
            logger.info("✅ Database monitoring configured")
            return db_config
            
        except Exception as e:
            logger.error(f"❌ Database monitoring setup failed: {e}")
            raise
    
    def setup_alerting(self) -> Dict[str, Any]:
        """Setup alerting system"""
        logger.info("🔧 Setting up alerting system...")
        
        try:
            # Create alerting configuration
            alert_config = {
                "email_alerts": {
                    "enabled": True,
                    "smtp_server": "localhost",
                    "smtp_port": 587,
                    "from_email": "alerts@openpolicy.com",
                    "to_emails": ["admin@openpolicy.com"]
                },
                "webhook_alerts": {
                    "enabled": True,
                    "webhook_url": "https://hooks.slack.com/services/xxx/yyy/zzz",
                    "timeout": 10
                },
                "alert_rules": [asdict(rule) for rule in self.alert_rules]
            }
            
            # Store configuration in Redis
            self.redis_client.setex(
                "monitoring:alerts:config",
                3600,
                json.dumps(alert_config)
            )
            
            logger.info("✅ Alerting system configured")
            return alert_config
            
        except Exception as e:
            logger.error(f"❌ Alerting setup failed: {e}")
            raise
    
    def setup_dashboard(self) -> Dict[str, Any]:
        """Setup monitoring dashboard"""
        logger.info("🔧 Setting up monitoring dashboard...")
        
        try:
            # Create dashboard configuration
            dashboard_config = {
                "dashboard_url": f"{self.base_url}/monitoring",
                "refresh_interval": 30,
                "widgets": [
                    {
                        "name": "System Health",
                        "type": "gauge",
                        "metrics": ["cpu", "memory", "disk"]
                    },
                    {
                        "name": "API Performance",
                        "type": "line",
                        "metrics": ["response_time", "throughput"]
                    },
                    {
                        "name": "Error Rate",
                        "type": "bar",
                        "metrics": ["error_rate"]
                    },
                    {
                        "name": "Database Performance",
                        "type": "line",
                        "metrics": ["query_time", "connections"]
                    }
                ]
            }
            
            # Store configuration in Redis
            self.redis_client.setex(
                "monitoring:dashboard:config",
                3600,
                json.dumps(dashboard_config)
            )
            
            logger.info("✅ Monitoring dashboard configured")
            return dashboard_config
            
        except Exception as e:
            logger.error(f"❌ Dashboard setup failed: {e}")
            raise
    
    def setup_log_monitoring(self) -> Dict[str, Any]:
        """Setup log monitoring"""
        logger.info("🔧 Setting up log monitoring...")
        
        try:
            # Create log monitoring configuration
            log_config = {
                "log_collection": {
                    "enabled": True,
                    "log_paths": [
                        "/var/log/openpolicy/application.log",
                        "/var/log/openpolicy/error.log",
                        "/var/log/openpolicy/access.log"
                    ],
                    "interval": 60
                },
                "log_analysis": {
                    "enabled": True,
                    "patterns": [
                        "ERROR",
                        "CRITICAL",
                        "WARNING",
                        "Exception"
                    ],
                    "alert_threshold": 10
                }
            }
            
            # Store configuration in Redis
            self.redis_client.setex(
                "monitoring:logs:config",
                3600,
                json.dumps(log_config)
            )
            
            logger.info("✅ Log monitoring configured")
            return log_config
            
        except Exception as e:
            logger.error(f"❌ Log monitoring setup failed: {e}")
            raise
    
    def setup_performance_monitoring(self) -> Dict[str, Any]:
        """Setup performance monitoring"""
        logger.info("🔧 Setting up performance monitoring...")
        
        try:
            # Create performance monitoring configuration
            perf_config = {
                "metrics_collection": {
                    "enabled": True,
                    "interval": 60,
                    "metrics": [
                        "response_time",
                        "throughput",
                        "error_rate",
                        "availability",
                        "cpu_usage",
                        "memory_usage",
                        "disk_usage"
                    ]
                },
                "performance_alerts": {
                    "enabled": True,
                    "thresholds": {
                        "response_time": 1000,
                        "error_rate": 5.0,
                        "availability": 99.9
                    }
                }
            }
            
            # Store configuration in Redis
            self.redis_client.setex(
                "monitoring:performance:config",
                3600,
                json.dumps(perf_config)
            )
            
            logger.info("✅ Performance monitoring configured")
            return perf_config
            
        except Exception as e:
            logger.error(f"❌ Performance monitoring setup failed: {e}")
            raise
    
    def setup_security_monitoring(self) -> Dict[str, Any]:
        """Setup security monitoring"""
        logger.info("🔧 Setting up security monitoring...")
        
        try:
            # Create security monitoring configuration
            security_config = {
                "security_alerts": {
                    "enabled": True,
                    "patterns": [
                        "SQL injection",
                        "XSS attack",
                        "Authentication failure",
                        "Authorization failure"
                    ],
                    "alert_threshold": 1
                },
                "access_monitoring": {
                    "enabled": True,
                    "log_failed_attempts": True,
                    "alert_threshold": 5
                }
            }
            
            # Store configuration in Redis
            self.redis_client.setex(
                "monitoring:security:config",
                3600,
                json.dumps(security_config)
            )
            
            logger.info("✅ Security monitoring configured")
            return security_config
            
        except Exception as e:
            logger.error(f"❌ Security monitoring setup failed: {e}")
            raise
    
    def create_monitoring_scripts(self) -> Dict[str, str]:
        """Create monitoring scripts"""
        logger.info("🔧 Creating monitoring scripts...")
        
        scripts = {}
        
        # System monitoring script
        system_script = '''#!/usr/bin/env python3
"""
System monitoring script for OpenPolicy platform
"""

import psutil
import json
import redis
import time
from datetime import datetime

def get_system_metrics():
    """Get system metrics"""
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    return {
        'timestamp': datetime.now().isoformat(),
        'cpu_percent': cpu_percent,
        'memory_percent': memory.percent,
        'memory_available': memory.available,
        'disk_percent': disk.percent,
        'disk_free': disk.free
    }

def main():
    """Main function"""
    # Connect to Redis
    r = redis.from_url('redis://localhost:6379')
    
    while True:
        try:
            metrics = get_system_metrics()
            r.setex('monitoring:system:current', 300, json.dumps(metrics))
            time.sleep(60)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()
'''
        
        scripts['system_monitoring.py'] = system_script
        
        # Application monitoring script
        app_script = '''#!/usr/bin/env python3
"""
Application monitoring script for OpenPolicy platform
"""

import requests
import json
import redis
import time
from datetime import datetime

def check_endpoint(url, timeout=10):
    """Check endpoint health"""
    try:
        start_time = time.time()
        response = requests.get(url, timeout=timeout)
        end_time = time.time()
        
        return {
            'url': url,
            'status_code': response.status_code,
            'response_time': (end_time - start_time) * 1000,
            'success': 200 <= response.status_code < 400
        }
    except Exception as e:
        return {
            'url': url,
            'status_code': 0,
            'response_time': 0,
            'success': False,
            'error': str(e)
        }

def main():
    """Main function"""
    # Connect to Redis
    r = redis.from_url('redis://localhost:6379')
    
    endpoints = [
        'http://localhost:8000/api/v1/health',
        'http://localhost:8000/api/v1/stats',
        'http://localhost:8000/api/v1/jurisdictions',
        'http://localhost:8000/api/v1/representatives'
    ]
    
    while True:
        try:
            results = []
            for endpoint in endpoints:
                result = check_endpoint(endpoint)
                results.append(result)
            
            metrics = {
                'timestamp': datetime.now().isoformat(),
                'endpoints': results,
                'overall_health': all(r['success'] for r in results)
            }
            
            r.setex('monitoring:application:current', 300, json.dumps(metrics))
            time.sleep(30)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(30)

if __name__ == "__main__":
    main()
'''
        
        scripts['application_monitoring.py'] = app_script
        
        # Alerting script
        alert_script = '''#!/usr/bin/env python3
"""
Alerting script for OpenPolicy platform
"""

import json
import redis
import time
from datetime import datetime

def check_alerts():
    """Check for alerts"""
    r = redis.from_url('redis://localhost:6379')
    
    # Get current metrics
    system_metrics = r.get('monitoring:system:current')
    app_metrics = r.get('monitoring:application:current')
    
    alerts = []
    
    if system_metrics:
        system_data = json.loads(system_metrics)
        
        # Check CPU usage
        if system_data.get('cpu_percent', 0) > 80:
            alerts.append({
                'name': 'High CPU Usage',
                'severity': 'warning',
                'message': f"CPU usage is {system_data['cpu_percent']}%",
                'timestamp': datetime.now().isoformat()
            })
        
        # Check memory usage
        if system_data.get('memory_percent', 0) > 85:
            alerts.append({
                'name': 'High Memory Usage',
                'severity': 'warning',
                'message': f"Memory usage is {system_data['memory_percent']}%",
                'timestamp': datetime.now().isoformat()
            })
    
    if app_metrics:
        app_data = json.loads(app_metrics)
        
        # Check endpoint health
        for endpoint in app_data.get('endpoints', []):
            if not endpoint.get('success', False):
                alerts.append({
                    'name': 'Endpoint Down',
                    'severity': 'critical',
                    'message': f"Endpoint {endpoint['url']} is not responding",
                    'timestamp': datetime.now().isoformat()
                })
    
    return alerts

def main():
    """Main function"""
    r = redis.from_url('redis://localhost:6379')
    
    while True:
        try:
            alerts = check_alerts()
            
            if alerts:
                r.setex('monitoring:alerts:current', 3600, json.dumps(alerts))
                print(f"Generated {len(alerts)} alerts")
            
            time.sleep(60)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()
'''
        
        scripts['alerting.py'] = alert_script
        
        logger.info("✅ Monitoring scripts created")
        return scripts
    
    def run_comprehensive_setup(self) -> Dict[str, Any]:
        """Run comprehensive monitoring setup"""
        logger.info("🎯 Starting comprehensive monitoring setup...")
        
        setup_results = {}
        
        try:
            # Setup system monitoring
            if self.config.system_monitoring:
                setup_results['system_monitoring'] = self.setup_system_monitoring()
            
            # Setup application monitoring
            if self.config.application_monitoring:
                setup_results['application_monitoring'] = self.setup_application_monitoring()
            
            # Setup database monitoring
            if self.config.database_monitoring:
                setup_results['database_monitoring'] = self.setup_database_monitoring()
            
            # Setup alerting
            if self.config.alerting:
                setup_results['alerting'] = self.setup_alerting()
            
            # Setup dashboard
            if self.config.dashboard:
                setup_results['dashboard'] = self.setup_dashboard()
            
            # Setup log monitoring
            if self.config.log_monitoring:
                setup_results['log_monitoring'] = self.setup_log_monitoring()
            
            # Setup performance monitoring
            if self.config.performance_monitoring:
                setup_results['performance_monitoring'] = self.setup_performance_monitoring()
            
            # Setup security monitoring
            if self.config.security_monitoring:
                setup_results['security_monitoring'] = self.setup_security_monitoring()
            
            # Create monitoring scripts
            setup_results['scripts'] = self.create_monitoring_scripts()
            
            logger.info("✅ Comprehensive monitoring setup completed")
            return setup_results
            
        except Exception as e:
            logger.error(f"❌ Monitoring setup failed: {e}")
            raise
    
    def generate_setup_report(self, output_file: Optional[str] = None) -> str:
        """Generate monitoring setup report"""
        logger.info("📊 Generating monitoring setup report...")
        
        report = []
        report.append("# 🎯 OpenPolicy Platform - Production Monitoring Setup Report")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        report.append("## 🔧 Monitoring Components Configured")
        report.append("")
        
        components = [
            ("System Monitoring", "CPU, memory, disk, network monitoring"),
            ("Application Monitoring", "API endpoints, performance, error tracking"),
            ("Database Monitoring", "Connection monitoring, query performance"),
            ("Alerting System", "Email and webhook alerts"),
            ("Monitoring Dashboard", "Real-time monitoring dashboard"),
            ("Log Monitoring", "Log collection and analysis"),
            ("Performance Monitoring", "Performance metrics and alerts"),
            ("Security Monitoring", "Security alerts and access monitoring")
        ]
        
        for component, description in components:
            report.append(f"### ✅ {component}")
            report.append(f"- **Description**: {description}")
            report.append(f"- **Status**: Configured")
            report.append("")
        
        report.append("## 🚀 Next Steps")
        report.append("1. **Start Monitoring Scripts**: Run the monitoring scripts")
        report.append("2. **Configure Alerts**: Set up email and webhook alerts")
        report.append("3. **Access Dashboard**: Access the monitoring dashboard")
        report.append("4. **Test Monitoring**: Test all monitoring components")
        report.append("5. **Documentation**: Update monitoring documentation")
        
        report_text = "\n".join(report)
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(report_text)
            logger.info(f"📄 Setup report saved to {output_file}")
        
        return report_text
    
    def save_configuration(self, output_file: str = "monitoring_config.json"):
        """Save monitoring configuration to JSON file"""
        config_data = {
            "monitoring_config": asdict(self.config),
            "alert_rules": [asdict(rule) for rule in self.alert_rules],
            "setup_timestamp": datetime.now().isoformat()
        }
        
        with open(output_file, 'w') as f:
            json.dump(config_data, f, indent=2)
        
        logger.info(f"💾 Monitoring configuration saved to {output_file}")

def main():
    """Main function to run monitoring setup"""
    import argparse
    
    parser = argparse.ArgumentParser(description="OpenPolicy Platform Production Monitoring Setup")
    parser.add_argument("--base-url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--database-url", default="postgresql://openpolicy:openpolicy123@localhost:5432/openpolicy",
                       help="Database connection URL")
    parser.add_argument("--redis-url", default="redis://localhost:6379", help="Redis connection URL")
    parser.add_argument("--output", default="monitoring_setup_report.md", help="Output report file")
    parser.add_argument("--config", default="monitoring_config.json", help="Configuration JSON file")
    
    args = parser.parse_args()
    
    # Initialize monitoring setup
    monitoring_setup = ProductionMonitoringSetup(
        base_url=args.base_url,
        database_url=args.database_url,
        redis_url=args.redis_url
    )
    
    try:
        # Run comprehensive setup
        results = monitoring_setup.run_comprehensive_setup()
        
        # Generate and save report
        report = monitoring_setup.generate_setup_report(args.output)
        monitoring_setup.save_configuration(args.config)
        
        print("\n" + "="*80)
        print("🎯 PRODUCTION MONITORING SETUP COMPLETE")
        print("="*80)
        
        print("✅ Monitoring components configured:")
        for component in results.keys():
            if component != 'scripts':
                print(f"  - {component.replace('_', ' ').title()}")
        
        print(f"📄 Setup report: {args.output}")
        print(f"💾 Configuration: {args.config}")
        print("="*80)
        
    except KeyboardInterrupt:
        logger.info("⚠️ Monitoring setup interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"❌ Monitoring setup failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
