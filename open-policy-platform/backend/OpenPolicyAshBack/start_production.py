#!/usr/bin/env python3
"""
OpenPolicy Platform Production Startup Script
============================================

This script initializes and starts all production services:
1. Database connection and health check
2. Monitoring system startup
3. Dashboard startup
4. Health monitoring and alerting
5. Service management

Usage:
    python3 start_production.py [--config production|staging|development]
"""

import os
import sys
import json
import time
import signal
import subprocess
import threading
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
        logging.FileHandler('production.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ProductionManager:
    """Manages production services for OpenPolicy platform"""
    
    def __init__(self, config: str = 'production'):
        self.config = config
        self.project_root = Path(__file__).parent
        self.services = {}
        self.running = True
        
        # Load configuration
        self.load_config()
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def load_config(self):
        """Load production configuration"""
        config_file = self.project_root / f'config/{self.config}.json'
        
        if config_file.exists():
            with open(config_file, 'r') as f:
                self.config_data = json.load(f)
        else:
            # Default configuration
            self.config_data = {
                'database': {
                    'url': os.getenv('DATABASE_URL', 'postgresql://openpolicy:openpolicy123@localhost:5432/openpolicy')
                },
                'services': {
                    'monitoring_interval': 300,
                    'dashboard_port': 5000,
                    'api_port': 8000
                },
                'alerts': {
                    'webhook_url': os.getenv('ALERT_WEBHOOK'),
                    'email': os.getenv('ALERT_EMAIL')
                }
            }
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"🛑 Received signal {signum}, shutting down...")
        self.running = False
        self.shutdown()
    
    def check_database(self) -> bool:
        """Check database connectivity"""
        try:
            import sqlalchemy as sa
            from sqlalchemy.orm import sessionmaker
            
            engine = sa.create_engine(self.config_data['database']['url'])
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            session = SessionLocal()
            
            # Test connection
            session.execute(sa.text("SELECT 1"))
            session.close()
            
            logger.info("✅ Database connection successful")
            return True
            
        except Exception as e:
            logger.error(f"❌ Database connection failed: {str(e)}")
            return False
    
    def start_monitoring_system(self) -> bool:
        """Start the monitoring system"""
        try:
            monitoring_script = self.project_root / 'monitoring_system.py'
            
            if not monitoring_script.exists():
                logger.error("❌ Monitoring system script not found")
                return False
            
            # Start monitoring system in background
            process = subprocess.Popen([
                sys.executable, str(monitoring_script)
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait a moment to check if it started successfully
            time.sleep(2)
            
            if process.poll() is None:
                self.services['monitoring'] = process
                logger.info("✅ Monitoring system started successfully")
                return True
            else:
                logger.error("❌ Monitoring system failed to start")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to start monitoring system: {str(e)}")
            return False
    
    def start_dashboard(self) -> bool:
        """Start the web dashboard"""
        try:
            dashboard_script = self.project_root / 'dashboard.py'
            
            if not dashboard_script.exists():
                logger.error("❌ Dashboard script not found")
                return False
            
            # Start dashboard in background
            process = subprocess.Popen([
                sys.executable, str(dashboard_script)
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait a moment to check if it started successfully
            time.sleep(3)
            
            if process.poll() is None:
                self.services['dashboard'] = process
                logger.info(f"✅ Dashboard started successfully on port {self.config_data['services']['dashboard_port']}")
                return True
            else:
                logger.error("❌ Dashboard failed to start")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to start dashboard: {str(e)}")
            return False
    
    def run_health_monitor(self):
        """Run continuous health monitoring"""
        while self.running:
            try:
                # Check database
                if not self.check_database():
                    logger.warning("⚠️ Database health check failed")
                
                # Check services
                for service_name, process in self.services.items():
                    if process.poll() is not None:
                        logger.error(f"❌ {service_name} service stopped unexpectedly")
                        # Restart service
                        self.restart_service(service_name)
                
                # Wait before next check
                time.sleep(60)
                
            except Exception as e:
                logger.error(f"❌ Health monitoring error: {str(e)}")
                time.sleep(60)
    
    def restart_service(self, service_name: str):
        """Restart a failed service"""
        try:
            logger.info(f"🔄 Restarting {service_name} service...")
            
            if service_name == 'monitoring':
                success = self.start_monitoring_system()
            elif service_name == 'dashboard':
                success = self.start_dashboard()
            else:
                logger.error(f"❌ Unknown service: {service_name}")
                return
            
            if success:
                logger.info(f"✅ {service_name} service restarted successfully")
            else:
                logger.error(f"❌ Failed to restart {service_name} service")
                
        except Exception as e:
            logger.error(f"❌ Failed to restart {service_name}: {str(e)}")
    
    def start_services(self) -> bool:
        """Start all production services"""
        logger.info("🚀 Starting production services...")
        
        # Step 1: Check database
        if not self.check_database():
            logger.error("❌ Database check failed")
            return False
        
        # Step 2: Start monitoring system
        if not self.start_monitoring_system():
            logger.error("❌ Monitoring system startup failed")
            return False
        
        # Step 3: Start dashboard
        if not self.start_dashboard():
            logger.error("❌ Dashboard startup failed")
            return False
        
        logger.info("✅ All production services started successfully")
        return True
    
    def shutdown(self):
        """Shutdown all services gracefully"""
        logger.info("🛑 Shutting down production services...")
        
        # Stop all services
        for service_name, process in self.services.items():
            try:
                logger.info(f"🛑 Stopping {service_name} service...")
                process.terminate()
                
                # Wait for graceful shutdown
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    logger.warning(f"⚠️ {service_name} service did not stop gracefully, forcing...")
                    process.kill()
                
                logger.info(f"✅ {service_name} service stopped")
                
            except Exception as e:
                logger.error(f"❌ Failed to stop {service_name}: {str(e)}")
        
        logger.info("🎯 Production shutdown completed")
    
    def run(self):
        """Run the production manager"""
        logger.info(f"🎯 Starting OpenPolicy Platform in {self.config} mode...")
        
        # Start services
        if not self.start_services():
            logger.error("❌ Failed to start production services")
            return False
        
        # Start health monitoring in background
        health_thread = threading.Thread(target=self.run_health_monitor, daemon=True)
        health_thread.start()
        
        logger.info("🎉 OpenPolicy Platform is now running!")
        logger.info(f"🌐 Dashboard: http://localhost:{self.config_data['services']['dashboard_port']}")
        logger.info("📊 Monitoring: Active")
        logger.info("🔍 Health checks: Active")
        
        # Keep running until shutdown signal
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("🛑 Received keyboard interrupt")
        
        # Shutdown
        self.shutdown()
        return True


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='OpenPolicy Platform Production Startup')
    parser.add_argument('--config', choices=['production', 'staging', 'development'], 
                       default='production', help='Configuration environment')
    
    args = parser.parse_args()
    
    # Create production manager
    manager = ProductionManager(args.config)
    
    # Run production manager
    success = manager.run()
    
    if success:
        logger.info("🎯 Production startup completed successfully!")
        return 0
    else:
        logger.error("❌ Production startup failed!")
        return 1


if __name__ == "__main__":
    exit(main())
