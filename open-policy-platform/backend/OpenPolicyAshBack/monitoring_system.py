#!/usr/bin/env python3
"""
Comprehensive Monitoring System for OpenPolicy Platform
=======================================================

This system provides continuous monitoring of:
1. Scraper performance and success rates
2. Data quality and integrity
3. System health and resource usage
4. Database connectivity and performance
5. Error tracking and alerting

Features:
- Real-time monitoring dashboard
- Automated alerts for failures
- Performance metrics tracking
- Data quality validation
- System health checks
"""

import os
import sys
import json
import time
import logging
import asyncio
import threading
import schedule
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import psutil
import requests
from pathlib import Path

# Add project paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scrapers'))

from src.database.models import (
    Base, Jurisdiction, Representative, ScrapingRun, DataQualityIssue,
    JurisdictionType, RepresentativeRole
)
from src.database.config import get_database_url, SessionLocal

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('monitoring.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class MonitoringStatus(Enum):
    """Monitoring status"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    OFFLINE = "offline"


@dataclass
class SystemMetrics:
    """System performance metrics"""
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, float]
    timestamp: datetime


@dataclass
class ScraperMetrics:
    """Scraper performance metrics"""
    scraper_name: str
    success_rate: float
    records_collected: int
    records_inserted: int
    execution_time: float
    last_run: datetime
    status: MonitoringStatus
    error_count: int = 0


@dataclass
class DataQualityMetrics:
    """Data quality metrics"""
    total_records: int
    complete_records: int
    missing_data_count: int
    duplicate_records: int
    invalid_records: int
    quality_score: float


class MonitoringSystem:
    """Comprehensive monitoring system for OpenPolicy platform"""
    
    def __init__(self, database_url: str, alert_webhook: Optional[str] = None):
        self.database_url = database_url
        self.alert_webhook = alert_webhook
        self.metrics_history: List[SystemMetrics] = []
        self.scraper_metrics: Dict[str, ScraperMetrics] = {}
        self.data_quality_metrics: Optional[DataQualityMetrics] = None
        self.monitoring_interval = 300  # 5 minutes
        self.alert_thresholds = {
            'cpu_usage': 80.0,
            'memory_usage': 85.0,
            'disk_usage': 90.0,
            'success_rate': 80.0,
            'data_quality': 85.0
        }
        
    def collect_system_metrics(self) -> SystemMetrics:
        """Collect current system performance metrics"""
        try:
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
            network_metrics = {
                'bytes_sent': network_io.bytes_sent,
                'bytes_recv': network_io.bytes_recv,
                'packets_sent': network_io.packets_sent,
                'packets_recv': network_io.packets_recv
            }
            
            metrics = SystemMetrics(
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                disk_usage=disk_usage,
                network_io=network_metrics,
                timestamp=datetime.utcnow()
            )
            
            self.metrics_history.append(metrics)
            
            # Keep only last 24 hours of metrics
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            self.metrics_history = [
                m for m in self.metrics_history 
                if m.timestamp > cutoff_time
            ]
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {str(e)}")
            return SystemMetrics(0.0, 0.0, 0.0, {}, datetime.utcnow())
    
    def collect_scraper_metrics(self) -> Dict[str, ScraperMetrics]:
        """Collect scraper performance metrics from database"""
        try:
            engine = sa.create_engine(self.database_url)
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            session = SessionLocal()
            
            # Get recent scraping runs
            recent_runs = session.query(ScrapingRun).filter(
                ScrapingRun.start_time >= datetime.utcnow() - timedelta(hours=24)
            ).all()
            
            scraper_metrics = {}
            
            for run in recent_runs:
                if run.scraper_name not in scraper_metrics:
                    scraper_metrics[run.scraper_name] = ScraperMetrics(
                        scraper_name=run.scraper_name,
                        success_rate=0.0,
                        records_collected=0,
                        records_inserted=0,
                        execution_time=0.0,
                        last_run=run.start_time,
                        status=MonitoringStatus.HEALTHY,
                        error_count=0
                    )
                
                metrics = scraper_metrics[run.scraper_name]
                metrics.records_collected += run.records_processed
                metrics.records_inserted += run.records_created
                
                if run.status == 'completed':
                    metrics.success_rate = 100.0
                elif run.status == 'failed':
                    metrics.error_count += 1
                    metrics.success_rate = 0.0
                
                if run.end_time and run.start_time:
                    execution_time = (run.end_time - run.start_time).total_seconds()
                    metrics.execution_time = max(metrics.execution_time, execution_time)
                
                # Update status based on success rate
                if metrics.success_rate >= 90:
                    metrics.status = MonitoringStatus.HEALTHY
                elif metrics.success_rate >= 70:
                    metrics.status = MonitoringStatus.WARNING
                else:
                    metrics.status = MonitoringStatus.CRITICAL
            
            session.close()
            self.scraper_metrics = scraper_metrics
            return scraper_metrics
            
        except Exception as e:
            logger.error(f"Failed to collect scraper metrics: {str(e)}")
            return {}
    
    def collect_data_quality_metrics(self) -> DataQualityMetrics:
        """Collect data quality metrics from database"""
        try:
            engine = sa.create_engine(self.database_url)
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            session = SessionLocal()
            
            # Total records
            total_records = session.query(Representative).count()
            
            # Complete records (have all required fields)
            complete_records = session.query(Representative).filter(
                Representative.name.isnot(None),
                Representative.role.isnot(None),
                Representative.jurisdiction_id.isnot(None)
            ).count()
            
            # Missing data count
            missing_data_count = total_records - complete_records
            
            # Duplicate records (same name and jurisdiction)
            duplicate_records = session.query(Representative).filter(
                Representative.name.isnot(None)
            ).group_by(Representative.name, Representative.jurisdiction_id).having(
                sa.func.count(Representative.id) > 1
            ).count()
            
            # Invalid records (missing required fields)
            invalid_records = session.query(Representative).filter(
                sa.or_(
                    Representative.name.is_(None),
                    Representative.role.is_(None),
                    Representative.jurisdiction_id.is_(None)
                )
            ).count()
            
            # Calculate quality score
            if total_records > 0:
                quality_score = (complete_records / total_records) * 100
            else:
                quality_score = 0.0
            
            metrics = DataQualityMetrics(
                total_records=total_records,
                complete_records=complete_records,
                missing_data_count=missing_data_count,
                duplicate_records=duplicate_records,
                invalid_records=invalid_records,
                quality_score=quality_score
            )
            
            session.close()
            self.data_quality_metrics = metrics
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to collect data quality metrics: {str(e)}")
            return DataQualityMetrics(0, 0, 0, 0, 0, 0.0)
    
    def check_database_health(self) -> MonitoringStatus:
        """Check database connectivity and health"""
        try:
            import sqlalchemy as sa
            from sqlalchemy.orm import sessionmaker
            
            # Import database config
            sys.path.insert(0, str(self.project_root / 'src'))
            from database.config import get_engine, get_session
            
            engine = get_engine()
            session = get_session()
            
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
    
    def generate_monitoring_report(self) -> Dict[str, Any]:
        """Generate comprehensive monitoring report"""
        system_metrics = self.collect_system_metrics()
        scraper_metrics = self.collect_scraper_metrics()
        data_quality_metrics = self.collect_data_quality_metrics()
        database_status = self.check_database_health()
        
        # Calculate overall system status
        overall_status = MonitoringStatus.HEALTHY
        
        if (system_metrics.cpu_usage > self.alert_thresholds['cpu_usage'] or
            system_metrics.memory_usage > self.alert_thresholds['memory_usage'] or
            system_metrics.disk_usage > self.alert_thresholds['disk_usage']):
            overall_status = MonitoringStatus.WARNING
        
        if (data_quality_metrics.quality_score < self.alert_thresholds['data_quality'] or
            database_status == MonitoringStatus.CRITICAL):
            overall_status = MonitoringStatus.CRITICAL
        
        # Calculate average success rate
        if scraper_metrics:
            avg_success_rate = sum(m.success_rate for m in scraper_metrics.values()) / len(scraper_metrics)
        else:
            avg_success_rate = 0.0
        
        report = {
            'timestamp': datetime.utcnow().isoformat(),
            'overall_status': overall_status.value,
            'system_metrics': {
                'cpu_usage': system_metrics.cpu_usage,
                'memory_usage': system_metrics.memory_usage,
                'disk_usage': system_metrics.disk_usage,
                'network_io': system_metrics.network_io
            },
            'scraper_metrics': {
                'total_scrapers': len(scraper_metrics),
                'average_success_rate': avg_success_rate,
                'scrapers_by_status': {
                    'healthy': sum(1 for m in scraper_metrics.values() if m.status == MonitoringStatus.HEALTHY),
                    'warning': sum(1 for m in scraper_metrics.values() if m.status == MonitoringStatus.WARNING),
                    'critical': sum(1 for m in scraper_metrics.values() if m.status == MonitoringStatus.CRITICAL)
                }
            },
            'data_quality_metrics': {
                'total_records': data_quality_metrics.total_records,
                'complete_records': data_quality_metrics.complete_records,
                'missing_data_count': data_quality_metrics.missing_data_count,
                'duplicate_records': data_quality_metrics.duplicate_records,
                'invalid_records': data_quality_metrics.invalid_records,
                'quality_score': data_quality_metrics.quality_score
            },
            'database_status': database_status.value,
            'alerts': self.generate_alerts(system_metrics, scraper_metrics, data_quality_metrics)
        }
        
        return report
    
    def generate_alerts(self, system_metrics: SystemMetrics, 
                       scraper_metrics: Dict[str, ScraperMetrics],
                       data_quality_metrics: DataQualityMetrics) -> List[Dict[str, Any]]:
        """Generate alerts based on thresholds"""
        alerts = []
        
        # System alerts
        if system_metrics.cpu_usage > self.alert_thresholds['cpu_usage']:
            alerts.append({
                'type': 'system',
                'severity': 'warning',
                'message': f"High CPU usage: {system_metrics.cpu_usage:.1f}%"
            })
        
        if system_metrics.memory_usage > self.alert_thresholds['memory_usage']:
            alerts.append({
                'type': 'system',
                'severity': 'warning',
                'message': f"High memory usage: {system_metrics.memory_usage:.1f}%"
            })
        
        if system_metrics.disk_usage > self.alert_thresholds['disk_usage']:
            alerts.append({
                'type': 'system',
                'severity': 'critical',
                'message': f"High disk usage: {system_metrics.disk_usage:.1f}%"
            })
        
        # Scraper alerts
        for scraper_name, metrics in scraper_metrics.items():
            if metrics.success_rate < self.alert_thresholds['success_rate']:
                alerts.append({
                    'type': 'scraper',
                    'severity': 'warning',
                    'message': f"Low success rate for {scraper_name}: {metrics.success_rate:.1f}%"
                })
        
        # Data quality alerts
        if data_quality_metrics.quality_score < self.alert_thresholds['data_quality']:
            alerts.append({
                'type': 'data_quality',
                'severity': 'warning',
                'message': f"Low data quality score: {data_quality_metrics.quality_score:.1f}%"
            })
        
        return alerts
    
    def send_alert(self, alert: Dict[str, Any]):
        """Send alert via webhook or other notification method"""
        if self.alert_webhook:
            try:
                response = requests.post(
                    self.alert_webhook,
                    json=alert,
                    headers={'Content-Type': 'application/json'},
                    timeout=10
                )
                if response.status_code == 200:
                    logger.info(f"Alert sent successfully: {alert['message']}")
                else:
                    logger.error(f"Failed to send alert: {response.status_code}")
            except Exception as e:
                logger.error(f"Failed to send alert: {str(e)}")
        else:
            logger.warning(f"Alert (no webhook configured): {alert['message']}")
    
    def run_monitoring_cycle(self):
        """Run a complete monitoring cycle"""
        logger.info("🔄 Starting monitoring cycle...")
        
        # Collect metrics
        system_metrics = self.collect_system_metrics()
        scraper_metrics = self.collect_scraper_metrics()
        data_quality_metrics = self.collect_data_quality_metrics()
        
        # Generate report
        report = self.generate_monitoring_report()
        
        # Send alerts
        for alert in report['alerts']:
            self.send_alert(alert)
        
        # Save report
        self.save_monitoring_report(report)
        
        logger.info(f"✅ Monitoring cycle completed. Status: {report['overall_status']}")
        return report
    
    def save_monitoring_report(self, report: Dict[str, Any]):
        """Save monitoring report to file"""
        try:
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            filename = f"monitoring_report_{timestamp}.json"
            
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            logger.info(f"📄 Monitoring report saved to {filename}")
            
        except Exception as e:
            logger.error(f"Failed to save monitoring report: {str(e)}")
    
    def start_continuous_monitoring(self):
        """Start continuous monitoring with scheduled intervals"""
        logger.info("🚀 Starting continuous monitoring system...")
        
        # Schedule monitoring every 5 minutes
        schedule.every(self.monitoring_interval).seconds.do(self.run_monitoring_cycle)
        
        # Run initial monitoring cycle
        self.run_monitoring_cycle()
        
        # Start continuous monitoring
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except KeyboardInterrupt:
                logger.info("🛑 Monitoring system stopped by user")
                break
            except Exception as e:
                logger.error(f"Monitoring cycle failed: {str(e)}")
                time.sleep(60)


def main():
    """Main function to run monitoring system"""
    # Database URL
    database_url = os.getenv('DATABASE_URL', 'postgresql://user:pass@localhost/openpolicy')
    
    # Alert webhook (optional)
    alert_webhook = os.getenv('ALERT_WEBHOOK')
    
    # Create monitoring system
    monitoring_system = MonitoringSystem(
        database_url=database_url,
        alert_webhook=alert_webhook
    )
    
    try:
        # Start continuous monitoring
        monitoring_system.start_continuous_monitoring()
    except Exception as e:
        logger.error(f"Monitoring system error: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
