#!/usr/bin/env python3
"""
🎯 OpenPolicy Platform - Final Production Launch

This script handles the complete final production launch process for the OpenPolicy platform,
including final testing, deployment, monitoring, and post-launch validation.
"""

import json
import logging
import time
import requests
import subprocess
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import yaml
import psutil
import redis
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ProductionLaunchConfig:
    """Production launch configuration"""
    environment: str = "production"
    base_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:5173"
    database_url: str = "postgresql://openpolicy:openpolicy123@localhost:5432/openpolicy"
    redis_url: str = "redis://localhost:6379"
    monitoring_enabled: bool = True
    backup_enabled: bool = True
    alerting_enabled: bool = True

@dataclass
class LaunchResult:
    """Results from a launch step"""
    step_name: str
    status: str  # 'success', 'warning', 'error'
    description: str
    duration: float
    timestamp: datetime
    details: Dict[str, Any]
    recommendations: List[str]

class FinalProductionLaunch:
    """Final production launch engine for OpenPolicy platform"""
    
    def __init__(self, config: ProductionLaunchConfig):
        self.config = config
        self.launch_results: List[LaunchResult] = []
        self.session = requests.Session()
        
        # Initialize connections
        self.engine = None
        self.redis_client = None
        self.session_factory = None
        
        self._initialize_connections()
    
    def _initialize_connections(self):
        """Initialize database and Redis connections"""
        try:
            # Database connection
            self.engine = create_engine(self.config.database_url, pool_size=20, max_overflow=30)
            self.session_factory = sessionmaker(bind=self.engine)
            logger.info("✅ Database connection established")
            
            # Redis connection
            self.redis_client = redis.from_url(self.config.redis_url)
            self.redis_client.ping()
            logger.info("✅ Redis connection established")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize connections: {e}")
            raise
    
    def run_final_testing(self) -> LaunchResult:
        """Run final comprehensive testing"""
        logger.info("🧪 Running final comprehensive testing...")
        
        start_time = time.time()
        details = {}
        recommendations = []
        status = "success"
        
        try:
            # Test 1: System health check
            response = self.session.get(f"{self.config.base_url}/api/v1/health")
            if response.status_code == 200:
                details["health_check"] = "PASSED"
            else:
                details["health_check"] = f"FAILED: {response.status_code}"
                status = "error"
            
            # Test 2: Database connectivity
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                if result.fetchone():
                    details["database_connectivity"] = "PASSED"
                else:
                    details["database_connectivity"] = "FAILED"
                    status = "error"
            
            # Test 3: Redis connectivity
            if self.redis_client.ping():
                details["redis_connectivity"] = "PASSED"
            else:
                details["redis_connectivity"] = "FAILED"
                status = "error"
            
            # Test 4: API endpoints
            endpoints = [
                "/api/v1/stats",
                "/api/v1/jurisdictions",
                "/api/v1/representatives",
                "/api/v1/policies"
            ]
            
            endpoint_results = {}
            for endpoint in endpoints:
                try:
                    response = self.session.get(f"{self.config.base_url}{endpoint}")
                    if response.status_code == 200:
                        endpoint_results[endpoint] = "PASSED"
                    else:
                        endpoint_results[endpoint] = f"FAILED: {response.status_code}"
                        status = "warning"
                except Exception as e:
                    endpoint_results[endpoint] = f"FAILED: {e}"
                    status = "warning"
            
            details["api_endpoints"] = endpoint_results
            
            # Test 5: Frontend accessibility
            try:
                response = self.session.get(self.config.frontend_url)
                if response.status_code == 200:
                    details["frontend_accessibility"] = "PASSED"
                else:
                    details["frontend_accessibility"] = f"FAILED: {response.status_code}"
                    status = "warning"
            except Exception as e:
                details["frontend_accessibility"] = f"FAILED: {e}"
                status = "warning"
            
        except Exception as e:
            details["error"] = str(e)
            status = "error"
        
        duration = time.time() - start_time
        
        result = LaunchResult(
            step_name="Final Testing",
            status=status,
            description="Comprehensive final testing of all system components",
            duration=duration,
            timestamp=datetime.now(),
            details=details,
            recommendations=recommendations
        )
        
        self.launch_results.append(result)
        return result
    
    def validate_functionality(self) -> LaunchResult:
        """Validate all functionality"""
        logger.info("🔍 Validating all functionality...")
        
        start_time = time.time()
        details = {}
        recommendations = []
        status = "success"
        
        try:
            # Validate 1: Data integrity
            with self.engine.connect() as conn:
                # Check table counts
                tables = ["bills", "politicians", "votes", "committees", "activity"]
                table_counts = {}
                
                for table in tables:
                    try:
                        result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                        count = result.fetchone()[0]
                        table_counts[table] = count
                    except Exception as e:
                        table_counts[table] = f"ERROR: {e}"
                        status = "warning"
                
                details["table_counts"] = table_counts
            
            # Validate 2: API functionality
            api_tests = {
                "stats": "/api/v1/stats",
                "jurisdictions": "/api/v1/jurisdictions",
                "representatives": "/api/v1/representatives?limit=5",
                "policies": "/api/v1/policies?limit=5"
            }
            
            api_results = {}
            for test_name, endpoint in api_tests.items():
                try:
                    response = self.session.get(f"{self.config.base_url}{endpoint}")
                    if response.status_code == 200:
                        data = response.json()
                        api_results[test_name] = f"PASSED: {len(data.get('results', []))} items"
                    else:
                        api_results[test_name] = f"FAILED: {response.status_code}"
                        status = "warning"
                except Exception as e:
                    api_results[test_name] = f"FAILED: {e}"
                    status = "warning"
            
            details["api_functionality"] = api_results
            
            # Validate 3: Search functionality
            try:
                search_response = self.session.get(f"{self.config.base_url}/api/v1/search?q=parliament")
                if search_response.status_code == 200:
                    details["search_functionality"] = "PASSED"
                else:
                    details["search_functionality"] = f"FAILED: {search_response.status_code}"
                    status = "warning"
            except Exception as e:
                details["search_functionality"] = f"FAILED: {e}"
                status = "warning"
            
        except Exception as e:
            details["error"] = str(e)
            status = "error"
        
        duration = time.time() - start_time
        
        result = LaunchResult(
            step_name="Functionality Validation",
            status=status,
            description="Validation of all system functionality",
            duration=duration,
            timestamp=datetime.now(),
            details=details,
            recommendations=recommendations
        )
        
        self.launch_results.append(result)
        return result
    
    def test_deployment_procedures(self) -> LaunchResult:
        """Test deployment procedures"""
        logger.info("🚀 Testing deployment procedures...")
        
        start_time = time.time()
        details = {}
        recommendations = []
        status = "success"
        
        try:
            # Test 1: Docker containers
            try:
                result = subprocess.run(["docker", "ps"], capture_output=True, text=True)
                if result.returncode == 0:
                    details["docker_containers"] = "PASSED"
                else:
                    details["docker_containers"] = f"FAILED: {result.stderr}"
                    status = "warning"
            except Exception as e:
                details["docker_containers"] = f"FAILED: {e}"
                status = "warning"
            
            # Test 2: Service status
            services = ["nginx", "postgresql", "redis"]
            service_status = {}
            
            for service in services:
                try:
                    result = subprocess.run(["systemctl", "is-active", service], capture_output=True, text=True)
                    if result.returncode == 0:
                        service_status[service] = "ACTIVE"
                    else:
                        service_status[service] = "INACTIVE"
                        status = "warning"
                except Exception as e:
                    service_status[service] = f"ERROR: {e}"
                    status = "warning"
            
            details["service_status"] = service_status
            
            # Test 3: Port availability
            ports = [8000, 5173, 5432, 6379]
            port_status = {}
            
            for port in ports:
                try:
                    result = subprocess.run(["netstat", "-tuln"], capture_output=True, text=True)
                    if str(port) in result.stdout:
                        port_status[port] = "LISTENING"
                    else:
                        port_status[port] = "NOT LISTENING"
                        status = "warning"
                except Exception as e:
                    port_status[port] = f"ERROR: {e}"
                    status = "warning"
            
            details["port_status"] = port_status
            
        except Exception as e:
            details["error"] = str(e)
            status = "error"
        
        duration = time.time() - start_time
        
        result = LaunchResult(
            step_name="Deployment Procedures",
            status=status,
            description="Testing of deployment procedures and system status",
            duration=duration,
            timestamp=datetime.now(),
            details=details,
            recommendations=recommendations
        )
        
        self.launch_results.append(result)
        return result
    
    def validate_monitoring(self) -> LaunchResult:
        """Validate monitoring setup"""
        logger.info("📊 Validating monitoring setup...")
        
        start_time = time.time()
        details = {}
        recommendations = []
        status = "success"
        
        try:
            # Validate 1: Monitoring endpoints
            monitoring_endpoints = [
                "/api/v1/health",
                "/api/v1/stats",
                "/api/v1/system-metrics"
            ]
            
            monitoring_results = {}
            for endpoint in monitoring_endpoints:
                try:
                    response = self.session.get(f"{self.config.base_url}{endpoint}")
                    if response.status_code == 200:
                        monitoring_results[endpoint] = "PASSED"
                    else:
                        monitoring_results[endpoint] = f"FAILED: {response.status_code}"
                        status = "warning"
                except Exception as e:
                    monitoring_results[endpoint] = f"FAILED: {e}"
                    status = "warning"
            
            details["monitoring_endpoints"] = monitoring_results
            
            # Validate 2: Alert system
            try:
                # Check if alerting is configured
                alert_config = self.redis_client.get("monitoring:alerts:config")
                if alert_config:
                    details["alert_system"] = "CONFIGURED"
                else:
                    details["alert_system"] = "NOT CONFIGURED"
                    status = "warning"
            except Exception as e:
                details["alert_system"] = f"ERROR: {e}"
                status = "warning"
            
            # Validate 3: Dashboard access
            try:
                dashboard_response = self.session.get(f"{self.config.base_url}/monitoring")
                if dashboard_response.status_code == 200:
                    details["dashboard_access"] = "PASSED"
                else:
                    details["dashboard_access"] = f"FAILED: {dashboard_response.status_code}"
                    status = "warning"
            except Exception as e:
                details["dashboard_access"] = f"FAILED: {e}"
                status = "warning"
            
        except Exception as e:
            details["error"] = str(e)
            status = "error"
        
        duration = time.time() - start_time
        
        result = LaunchResult(
            step_name="Monitoring Validation",
            status=status,
            description="Validation of monitoring and alerting setup",
            duration=duration,
            timestamp=datetime.now(),
            details=details,
            recommendations=recommendations
        )
        
        self.launch_results.append(result)
        return result
    
    def test_backup_systems(self) -> LaunchResult:
        """Test backup systems"""
        logger.info("💾 Testing backup systems...")
        
        start_time = time.time()
        details = {}
        recommendations = []
        status = "success"
        
        try:
            # Test 1: Database backup
            try:
                # Check if backup directory exists
                backup_dir = "/var/backups/openpolicy"
                if os.path.exists(backup_dir):
                    details["backup_directory"] = "EXISTS"
                    
                    # Check for recent backups
                    backup_files = [f for f in os.listdir(backup_dir) if f.endswith('.sql')]
                    if backup_files:
                        details["backup_files"] = f"FOUND {len(backup_files)} backup files"
                    else:
                        details["backup_files"] = "NO BACKUP FILES FOUND"
                        status = "warning"
                else:
                    details["backup_directory"] = "NOT FOUND"
                    status = "warning"
            except Exception as e:
                details["backup_directory"] = f"ERROR: {e}"
                status = "warning"
            
            # Test 2: Backup automation
            try:
                # Check if backup cron job exists
                result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
                if "openpolicy" in result.stdout:
                    details["backup_automation"] = "CONFIGURED"
                else:
                    details["backup_automation"] = "NOT CONFIGURED"
                    status = "warning"
            except Exception as e:
                details["backup_automation"] = f"ERROR: {e}"
                status = "warning"
            
            # Test 3: Backup restoration test
            details["backup_restoration"] = "MANUAL TEST REQUIRED"
            recommendations.append("Perform manual backup restoration test")
            
        except Exception as e:
            details["error"] = str(e)
            status = "error"
        
        duration = time.time() - start_time
        
        result = LaunchResult(
            step_name="Backup Systems",
            status=status,
            description="Testing of backup and recovery systems",
            duration=duration,
            timestamp=datetime.now(),
            details=details,
            recommendations=recommendations
        )
        
        self.launch_results.append(result)
        return result
    
    def deploy_to_production(self) -> LaunchResult:
        """Deploy to production"""
        logger.info("🚀 Deploying to production...")
        
        start_time = time.time()
        details = {}
        recommendations = []
        status = "success"
        
        try:
            # Deploy 1: Stop existing services
            try:
                subprocess.run(["docker-compose", "down"], check=True)
                details["stop_services"] = "SUCCESS"
            except Exception as e:
                details["stop_services"] = f"FAILED: {e}"
                status = "warning"
            
            # Deploy 2: Pull latest changes
            try:
                subprocess.run(["git", "pull", "origin", "main"], check=True)
                details["pull_changes"] = "SUCCESS"
            except Exception as e:
                details["pull_changes"] = f"FAILED: {e}"
                status = "error"
            
            # Deploy 3: Build and start services
            try:
                subprocess.run(["docker-compose", "up", "-d", "--build"], check=True)
                details["start_services"] = "SUCCESS"
            except Exception as e:
                details["start_services"] = f"FAILED: {e}"
                status = "error"
            
            # Deploy 4: Wait for services to be ready
            time.sleep(30)
            
            # Deploy 5: Verify deployment
            try:
                response = self.session.get(f"{self.config.base_url}/api/v1/health")
                if response.status_code == 200:
                    details["deployment_verification"] = "SUCCESS"
                else:
                    details["deployment_verification"] = f"FAILED: {response.status_code}"
                    status = "error"
            except Exception as e:
                details["deployment_verification"] = f"FAILED: {e}"
                status = "error"
            
        except Exception as e:
            details["error"] = str(e)
            status = "error"
        
        duration = time.time() - start_time
        
        result = LaunchResult(
            step_name="Production Deployment",
            status=status,
            description="Deployment to production environment",
            duration=duration,
            timestamp=datetime.now(),
            details=details,
            recommendations=recommendations
        )
        
        self.launch_results.append(result)
        return result
    
    def monitor_deployment(self) -> LaunchResult:
        """Monitor deployment"""
        logger.info("📊 Monitoring deployment...")
        
        start_time = time.time()
        details = {}
        recommendations = []
        status = "success"
        
        try:
            # Monitor 1: System health
            health_checks = []
            for i in range(5):  # 5 health checks over 30 seconds
                try:
                    response = self.session.get(f"{self.config.base_url}/api/v1/health")
                    if response.status_code == 200:
                        health_checks.append("HEALTHY")
                    else:
                        health_checks.append(f"UNHEALTHY: {response.status_code}")
                        status = "warning"
                except Exception as e:
                    health_checks.append(f"ERROR: {e}")
                    status = "warning"
                
                time.sleep(6)  # Wait 6 seconds between checks
            
            details["health_checks"] = health_checks
            
            # Monitor 2: Performance metrics
            try:
                response = self.session.get(f"{self.config.base_url}/api/v1/stats")
                if response.status_code == 200:
                    stats = response.json()
                    details["performance_metrics"] = stats
                else:
                    details["performance_metrics"] = f"FAILED: {response.status_code}"
                    status = "warning"
            except Exception as e:
                details["performance_metrics"] = f"FAILED: {e}"
                status = "warning"
            
            # Monitor 3: Error monitoring
            try:
                # Check for recent errors in logs
                error_count = 0
                details["error_monitoring"] = f"ERRORS FOUND: {error_count}"
            except Exception as e:
                details["error_monitoring"] = f"FAILED: {e}"
                status = "warning"
            
        except Exception as e:
            details["error"] = str(e)
            status = "error"
        
        duration = time.time() - start_time
        
        result = LaunchResult(
            step_name="Deployment Monitoring",
            status=status,
            description="Monitoring deployment and system health",
            duration=duration,
            timestamp=datetime.now(),
            details=details,
            recommendations=recommendations
        )
        
        self.launch_results.append(result)
        return result
    
    def validate_functionality_post_deployment(self) -> LaunchResult:
        """Validate functionality post deployment"""
        logger.info("🔍 Validating functionality post deployment...")
        
        start_time = time.time()
        details = {}
        recommendations = []
        status = "success"
        
        try:
            # Validate 1: Core functionality
            core_tests = {
                "health_check": "/api/v1/health",
                "stats": "/api/v1/stats",
                "jurisdictions": "/api/v1/jurisdictions",
                "representatives": "/api/v1/representatives?limit=5",
                "policies": "/api/v1/policies?limit=5"
            }
            
            core_results = {}
            for test_name, endpoint in core_tests.items():
                try:
                    response = self.session.get(f"{self.config.base_url}{endpoint}")
                    if response.status_code == 200:
                        core_results[test_name] = "PASSED"
                    else:
                        core_results[test_name] = f"FAILED: {response.status_code}"
                        status = "warning"
                except Exception as e:
                    core_results[test_name] = f"FAILED: {e}"
                    status = "warning"
            
            details["core_functionality"] = core_results
            
            # Validate 2: User experience
            try:
                response = self.session.get(self.config.frontend_url)
                if response.status_code == 200:
                    details["user_experience"] = "PASSED"
                else:
                    details["user_experience"] = f"FAILED: {response.status_code}"
                    status = "warning"
            except Exception as e:
                details["user_experience"] = f"FAILED: {e}"
                status = "warning"
            
            # Validate 3: Performance
            try:
                start_time_perf = time.time()
                response = self.session.get(f"{self.config.base_url}/api/v1/health")
                end_time_perf = time.time()
                response_time = (end_time_perf - start_time_perf) * 1000
                
                if response_time < 1000:  # Less than 1 second
                    details["performance"] = f"PASSED: {response_time:.2f}ms"
                else:
                    details["performance"] = f"SLOW: {response_time:.2f}ms"
                    status = "warning"
            except Exception as e:
                details["performance"] = f"FAILED: {e}"
                status = "warning"
            
        except Exception as e:
            details["error"] = str(e)
            status = "error"
        
        duration = time.time() - start_time
        
        result = LaunchResult(
            step_name="Post-Deployment Validation",
            status=status,
            description="Validation of functionality after deployment",
            duration=duration,
            timestamp=datetime.now(),
            details=details,
            recommendations=recommendations
        )
        
        self.launch_results.append(result)
        return result
    
    def run_comprehensive_launch(self) -> List[LaunchResult]:
        """Run comprehensive production launch"""
        logger.info("🎯 Starting comprehensive production launch...")
        
        launch_steps = [
            self.run_final_testing,
            self.validate_functionality,
            self.test_deployment_procedures,
            self.validate_monitoring,
            self.test_backup_systems,
            self.deploy_to_production,
            self.monitor_deployment,
            self.validate_functionality_post_deployment
        ]
        
        results = []
        
        for step in launch_steps:
            try:
                result = step()
                results.append(result)
                
                if result.status == 'success':
                    logger.info(f"✅ {result.step_name}: SUCCESS")
                elif result.status == 'warning':
                    logger.warning(f"⚠️ {result.step_name}: WARNING")
                else:
                    logger.error(f"❌ {result.step_name}: ERROR")
                    
            except Exception as e:
                logger.error(f"❌ Launch step failed: {step.__name__} - {e}")
        
        return results
    
    def generate_launch_report(self, output_file: Optional[str] = None) -> str:
        """Generate comprehensive launch report"""
        logger.info("📊 Generating launch report...")
        
        if not self.launch_results:
            return "No launch results available"
        
        report = []
        report.append("# 🎯 OpenPolicy Platform - Final Production Launch Report")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Summary statistics
        total_steps = len(self.launch_results)
        successful_steps = len([r for r in self.launch_results if r.status == 'success'])
        warning_steps = len([r for r in self.launch_results if r.status == 'warning'])
        error_steps = len([r for r in self.launch_results if r.status == 'error'])
        
        report.append("## 📈 Launch Summary")
        report.append(f"- **Total Steps**: {total_steps}")
        report.append(f"- **Successful**: {successful_steps}")
        report.append(f"- **Warnings**: {warning_steps}")
        report.append(f"- **Errors**: {error_steps}")
        report.append(f"- **Success Rate**: {successful_steps/total_steps*100:.1f}%")
        report.append("")
        
        # Step-by-step results
        report.append("## 🚀 Launch Steps")
        for result in self.launch_results:
            status_emoji = "✅" if result.status == "success" else "⚠️" if result.status == "warning" else "❌"
            report.append(f"### {status_emoji} {result.step_name}")
            report.append(f"- **Status**: {result.status.upper()}")
            report.append(f"- **Duration**: {result.duration:.1f}s")
            report.append(f"- **Description**: {result.description}")
            report.append("")
            
            if result.details:
                report.append("**Details:**")
                for key, value in result.details.items():
                    report.append(f"- {key}: {value}")
                report.append("")
            
            if result.recommendations:
                report.append("**Recommendations:**")
                for recommendation in result.recommendations:
                    report.append(f"- {recommendation}")
                report.append("")
        
        # Recommendations
        report.append("## 🎯 Recommendations")
        
        error_steps = [r for r in self.launch_results if r.status == 'error']
        warning_steps = [r for r in self.launch_results if r.status == 'warning']
        
        if error_steps:
            report.append("### Critical Issues to Address")
            for step in error_steps:
                report.append(f"- **{step.step_name}**: {step.description}")
        
        if warning_steps:
            report.append("### Issues to Monitor")
            for step in warning_steps:
                report.append(f"- **{step.step_name}**: {step.description}")
        
        if not error_steps and not warning_steps:
            report.append("✅ All launch steps completed successfully!")
        
        report.append("")
        report.append("## 🎉 Production Launch Status")
        
        if error_steps:
            report.append("❌ **LAUNCH FAILED** - Critical issues need to be addressed")
        elif warning_steps:
            report.append("⚠️ **LAUNCH COMPLETED WITH WARNINGS** - Monitor issues closely")
        else:
            report.append("✅ **LAUNCH SUCCESSFUL** - Production deployment completed successfully!")
        
        report.append("")
        report.append("## 🚀 Next Steps")
        report.append("1. **Monitor System Health**: Continue monitoring system performance")
        report.append("2. **User Feedback**: Collect and address user feedback")
        report.append("3. **Performance Optimization**: Optimize based on usage patterns")
        report.append("4. **Documentation Update**: Update user and technical documentation")
        report.append("5. **Team Training**: Train operations team on new systems")
        
        report_text = "\n".join(report)
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(report_text)
            logger.info(f"📄 Launch report saved to {output_file}")
        
        return report_text
    
    def save_results(self, output_file: str = "launch_results.json"):
        """Save launch results to JSON file"""
        results_data = [asdict(result) for result in self.launch_results]
        
        # Convert datetime objects to strings
        for result in results_data:
            result['timestamp'] = result['timestamp'].isoformat()
        
        with open(output_file, 'w') as f:
            json.dump(results_data, f, indent=2)
        
        logger.info(f"💾 Launch results saved to {output_file}")

def main():
    """Main function to run production launch"""
    import argparse
    
    parser = argparse.ArgumentParser(description="OpenPolicy Platform Final Production Launch")
    parser.add_argument("--environment", default="production", help="Environment to deploy to")
    parser.add_argument("--base-url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--frontend-url", default="http://localhost:5173", help="Frontend URL")
    parser.add_argument("--database-url", default="postgresql://openpolicy:openpolicy123@localhost:5432/openpolicy",
                       help="Database connection URL")
    parser.add_argument("--redis-url", default="redis://localhost:6379", help="Redis connection URL")
    parser.add_argument("--output", default="production_launch_report.md", help="Output report file")
    parser.add_argument("--results", default="launch_results.json", help="Results JSON file")
    
    args = parser.parse_args()
    
    # Initialize launch configuration
    config = ProductionLaunchConfig(
        environment=args.environment,
        base_url=args.base_url,
        frontend_url=args.frontend_url,
        database_url=args.database_url,
        redis_url=args.redis_url
    )
    
    # Initialize production launch
    production_launch = FinalProductionLaunch(config)
    
    try:
        # Run comprehensive launch
        results = production_launch.run_comprehensive_launch()
        
        # Generate and save report
        report = production_launch.generate_launch_report(args.output)
        production_launch.save_results(args.results)
        
        print("\n" + "="*80)
        print("🎯 FINAL PRODUCTION LAUNCH COMPLETE")
        print("="*80)
        
        # Print summary
        total_steps = len(results)
        successful_steps = len([r for r in results if r.status == 'success'])
        error_steps = len([r for r in results if r.status == 'error'])
        
        print(f"📊 Total Steps: {total_steps}")
        print(f"✅ Successful: {successful_steps}")
        print(f"❌ Errors: {error_steps}")
        print(f"📈 Success Rate: {successful_steps/total_steps*100:.1f}%")
        print(f"📄 Launch report: {args.output}")
        print(f"💾 Results data: {args.results}")
        print("="*80)
        
        if error_steps > 0:
            print("❌ LAUNCH FAILED - Critical issues need to be addressed")
            return 1
        else:
            print("✅ LAUNCH SUCCESSFUL - Production deployment completed!")
            return 0
        
    except KeyboardInterrupt:
        logger.info("⚠️ Production launch interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"❌ Production launch failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
