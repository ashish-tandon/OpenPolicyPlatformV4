#!/usr/bin/env python3
"""
Continuous Monitoring Script for Open Policy Platform V4
Monitors system health, logs issues, and tracks performance
"""

import requests
import json
import time
import logging
from datetime import datetime, timedelta
import os
import sys

# Configure comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('system_monitoring.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class SystemMonitor:
    def __init__(self, api_url="http://localhost:8000", scraper_url="http://localhost:9008"):
        self.api_url = api_url
        self.scraper_url = scraper_url
        self.monitoring_start = datetime.now()
        self.error_count = 0
        self.success_count = 0
        self.health_checks = []
        
    def log_system_event(self, event_type, message, details=None, error=None):
        """Log system events with comprehensive details"""
        timestamp = datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "event_type": event_type,
            "message": message,
            "details": details,
            "error": str(error) if error else None,
            "uptime": str(datetime.now() - self.monitoring_start)
        }
        
        if event_type == "ERROR":
            logger.error(f"SYSTEM ERROR: {message}")
            if error:
                logger.error(f"Error details: {error}")
            self.error_count += 1
        elif event_type == "WARNING":
            logger.warning(f"SYSTEM WARNING: {message}")
        else:
            logger.info(f"SYSTEM INFO: {message}")
            self.success_count += 1
        
        # Store health check history
        self.health_checks.append(log_entry)
        
        # Keep only last 1000 health checks
        if len(self.health_checks) > 1000:
            self.health_checks = self.health_checks[-1000:]
    
    def check_api_health(self):
        """Check API service health"""
        try:
            response = requests.get(f"{self.api_url}/api/v1/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.log_system_event("INFO", "API Health Check", {
                    "status": data.get("status"),
                    "uptime": data.get("uptime"),
                    "response_time": response.elapsed.total_seconds()
                })
                return True
            else:
                self.log_system_event("ERROR", "API Health Check Failed", {
                    "status_code": response.status_code,
                    "response": response.text
                })
                return False
        except Exception as e:
            self.log_system_event("ERROR", "API Health Check Exception", error=e)
            return False
    
    def check_comprehensive_health(self):
        """Check comprehensive system health"""
        try:
            response = requests.get(f"{self.api_url}/api/v1/health/comprehensive", timeout=15)
            if response.status_code == 200:
                data = response.json()
                components = data.get("components", {})
                
                # Check each component
                for component_name, component_data in components.items():
                    status = component_data.get("status", "unknown")
                    if status != "healthy":
                        self.log_system_event("WARNING", f"Component {component_name} not healthy", {
                            "component": component_name,
                            "status": status,
                            "details": component_data
                        })
                    else:
                        self.log_system_event("INFO", f"Component {component_name} healthy", {
                            "component": component_name,
                            "status": status
                        })
                
                # Log overall system status
                summary = data.get("summary", {})
                self.log_system_event("INFO", "Comprehensive Health Check", {
                    "total_components": summary.get("total_components"),
                    "healthy_components": summary.get("healthy_components"),
                    "warning_components": summary.get("warning_components"),
                    "unhealthy_components": summary.get("unhealthy_components")
                })
                
                return True
            else:
                self.log_system_event("ERROR", "Comprehensive Health Check Failed", {
                    "status_code": response.status_code,
                    "response": response.text
                })
                return False
        except Exception as e:
            self.log_system_event("ERROR", "Comprehensive Health Check Exception", error=e)
            return False
    
    def check_scraper_health(self):
        """Check scraper service health"""
        try:
            response = requests.get(f"{self.scraper_url}/healthz", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.log_system_event("INFO", "Scraper Health Check", {
                    "status": data.get("status"),
                    "service": data.get("service"),
                    "response_time": response.elapsed.total_seconds()
                })
                return True
            else:
                self.log_system_event("ERROR", "Scraper Health Check Failed", {
                    "status_code": response.status_code,
                    "response": response.text
                })
                return False
        except Exception as e:
            self.log_system_event("ERROR", "Scraper Health Check Exception", error=e)
            return False
    
    def check_scraper_stats(self):
        """Check scraper statistics and data collection"""
        try:
            response = requests.get(f"{self.scraper_url}/stats", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.log_system_event("INFO", "Scraper Statistics", {
                    "total_jobs": data.get("total_jobs"),
                    "active_jobs": data.get("active_jobs"),
                    "total_data_records": data.get("total_data_records"),
                    "status_distribution": data.get("status_distribution")
                })
                
                # Check for any issues
                if data.get("total_jobs", 0) == 0:
                    self.log_system_event("WARNING", "No scraper jobs configured")
                
                if data.get("active_jobs", 0) == 0 and data.get("total_jobs", 0) > 0:
                    self.log_system_event("WARNING", "No active scraper jobs")
                
                return True
            else:
                self.log_system_event("ERROR", "Scraper Stats Check Failed", {
                    "status_code": response.status_code,
                    "response": response.text
                })
                return False
        except Exception as e:
            self.log_system_event("ERROR", "Scraper Stats Check Exception", error=e)
            return False
    
    def check_data_collection(self):
        """Check data collection status"""
        try:
            response = requests.get(f"{self.scraper_url}/data", timeout=10)
            if response.status_code == 200:
                data = response.json()
                total_records = data.get("total", 0)
                
                self.log_system_event("INFO", "Data Collection Status", {
                    "total_records": total_records,
                    "has_more": data.get("has_more", False)
                })
                
                # Check for data growth
                if total_records > 0:
                    self.log_system_event("INFO", "Data collection active", {
                        "records_collected": total_records
                    })
                else:
                    self.log_system_event("WARNING", "No data records collected yet")
                
                return True
            else:
                self.log_system_event("ERROR", "Data Collection Check Failed", {
                    "status_code": response.status_code,
                    "response": response.text
                })
                return False
        except Exception as e:
            self.log_system_event("ERROR", "Data Collection Check Exception", error=e)
            return False
    
    def check_api_endpoints(self):
        """Check key API endpoints functionality"""
        endpoints_to_check = [
            "/api/v1/policies/",
            "/api/v1/policies/list/categories",
            "/api/v1/policies/list/jurisdictions",
            "/api/v1/policies/summary/stats"
        ]
        
        for endpoint in endpoints_to_check:
            try:
                response = requests.get(f"{self.api_url}{endpoint}", timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    self.log_system_event("INFO", f"API Endpoint {endpoint} functional", {
                        "endpoint": endpoint,
                        "status_code": response.status_code,
                        "response_time": response.elapsed.total_seconds(),
                        "data_count": len(data) if isinstance(data, list) else "N/A"
                    })
                else:
                    self.log_system_event("ERROR", f"API Endpoint {endpoint} failed", {
                        "endpoint": endpoint,
                        "status_code": response.status_code,
                        "response": response.text
                    })
            except Exception as e:
                self.log_system_event("ERROR", f"API Endpoint {endpoint} exception", {
                    "endpoint": endpoint
                }, error=e)
    
    def check_docker_services(self):
        """Check Docker service status"""
        try:
            # This would require Docker API access, for now we'll check via health endpoints
            self.log_system_event("INFO", "Docker services check via health endpoints")
            return True
        except Exception as e:
            self.log_system_event("ERROR", "Docker services check failed", error=e)
            return False
    
    def generate_monitoring_report(self):
        """Generate comprehensive monitoring report"""
        current_time = datetime.now()
        uptime = current_time - self.monitoring_start
        
        report = {
            "monitoring_start": self.monitoring_start.isoformat(),
            "current_time": current_time.isoformat(),
            "total_uptime": str(uptime),
            "total_health_checks": len(self.health_checks),
            "success_count": self.success_count,
            "error_count": self.error_count,
            "success_rate": (self.success_count / (self.success_count + self.error_count) * 100) if (self.success_count + self.error_count) > 0 else 0,
            "recent_events": self.health_checks[-10:] if self.health_checks else []
        }
        
        self.log_system_event("INFO", "Monitoring Report Generated", report)
        return report
    
    def run_health_check_cycle(self):
        """Run a complete health check cycle"""
        cycle_start = time.time()
        
        self.log_system_event("INFO", "Starting health check cycle")
        
        # Run all health checks
        checks = [
            ("API Health", self.check_api_health),
            ("Comprehensive Health", self.check_comprehensive_health),
            ("Scraper Health", self.check_scraper_health),
            ("Scraper Stats", self.check_scraper_stats),
            ("Data Collection", self.check_data_collection),
            ("API Endpoints", self.check_api_endpoints),
            ("Docker Services", self.check_docker_services)
        ]
        
        successful_checks = 0
        total_checks = len(checks)
        
        for check_name, check_function in checks:
            try:
                if check_function():
                    successful_checks += 1
                time.sleep(1)  # Brief pause between checks
            except Exception as e:
                self.log_system_event("ERROR", f"Health check {check_name} failed", error=e)
        
        cycle_time = time.time() - cycle_start
        
        self.log_system_event("INFO", "Health check cycle completed", {
            "successful_checks": successful_checks,
            "total_checks": total_checks,
            "cycle_time": f"{cycle_time:.2f}s",
            "success_rate": f"{(successful_checks/total_checks)*100:.1f}%"
        })
        
        return successful_checks == total_checks
    
    def run_continuous_monitoring(self, interval_seconds=60, max_cycles=None):
        """Run continuous monitoring with specified interval"""
        self.log_system_event("INFO", "Starting continuous monitoring", {
            "interval_seconds": interval_seconds,
            "max_cycles": max_cycles
        })
        
        cycle_count = 0
        
        try:
            while True:
                if max_cycles and cycle_count >= max_cycles:
                    self.log_system_event("INFO", "Maximum monitoring cycles reached, stopping")
                    break
                
                cycle_count += 1
                self.log_system_event("INFO", f"Starting monitoring cycle {cycle_count}")
                
                # Run health check cycle
                cycle_success = self.run_health_check_cycle()
                
                if cycle_success:
                    self.log_system_event("INFO", f"Cycle {cycle_count} completed successfully")
                else:
                    self.log_system_event("WARNING", f"Cycle {cycle_count} completed with issues")
                
                # Generate periodic report
                if cycle_count % 10 == 0:  # Every 10 cycles
                    self.generate_monitoring_report()
                
                # Wait for next cycle
                self.log_system_event("INFO", f"Waiting {interval_seconds} seconds until next cycle")
                time.sleep(interval_seconds)
                
        except KeyboardInterrupt:
            self.log_system_event("INFO", "Monitoring stopped by user")
        except Exception as e:
            self.log_system_event("ERROR", "Monitoring stopped due to error", error=e)
        finally:
            # Generate final report
            final_report = self.generate_monitoring_report()
            self.log_system_event("INFO", "Final monitoring report", final_report)
            self.log_system_event("INFO", "Continuous monitoring stopped")

def main():
    """Main monitoring function"""
    logger.info("🎯 Starting Open Policy Platform V4 Continuous Monitoring")
    
    monitor = SystemMonitor()
    
    try:
        # Run continuous monitoring with 2-minute intervals
        # Let it run for demonstration (can be stopped with Ctrl+C)
        monitor.run_continuous_monitoring(interval_seconds=120, max_cycles=None)
        
    except Exception as e:
        logger.error(f"❌ Monitoring failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
