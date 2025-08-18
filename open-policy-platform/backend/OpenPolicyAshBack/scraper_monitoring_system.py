#!/usr/bin/env python3
"""
Scraper Monitoring System
=========================

This system runs scrapers in the background, monitors their status,
handles failures with automatic retries, and provides comprehensive
monitoring and alerting capabilities.

Features:
- Background scraper execution
- Automatic retry on failure
- Real-time monitoring
- Error tracking and reporting
- Performance metrics
- Scheduled execution
"""

import os
import sys
import json
import time
import logging
import asyncio
import threading
import schedule
import signal
import traceback
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, asdict
from enum import Enum
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import psutil
import requests

# Add project paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scrapers'))

from src.database.models import (
    Base, Jurisdiction, Representative, Bill, Committee, Event, Vote,
    ScrapingRun, DataQualityIssue, JurisdictionType, RepresentativeRole
)
from src.database.config import create_engine_from_config, get_session_factory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper_monitoring.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ScraperStatus(Enum):
    """Scraper execution status"""
    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"
    STOPPED = "stopped"


class ScraperPriority(Enum):
    """Scraper priority levels"""
    HIGH = "high"      # Parliamentary, critical data
    MEDIUM = "medium"  # Provincial, major cities
    LOW = "low"        # Municipal, smaller cities


@dataclass
class ScraperJob:
    """Scraper job configuration"""
    name: str
    path: str
    category: str
    priority: ScraperPriority
    schedule: str  # Cron-like schedule
    max_retries: int = 3
    retry_delay: int = 300  # seconds
    timeout: int = 1800  # 30 minutes
    enabled: bool = True


@dataclass
class ScraperExecution:
    """Scraper execution result"""
    job: ScraperJob
    status: ScraperStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    records_collected: int = 0
    records_inserted: int = 0
    error_message: Optional[str] = None
    retry_count: int = 0
    execution_time: Optional[float] = None
    memory_usage: Optional[float] = None
    cpu_usage: Optional[float] = None


class ScraperMonitoringSystem:
    """Comprehensive scraper monitoring system"""
    
    def __init__(self, database_url: str, config_file: str = "scraper_jobs.json"):
        self.database_url = database_url
        self.config_file = config_file
        self.engine = create_engine_from_config(database_url)
        self.SessionLocal = get_session_factory(self.engine)
        
        # Monitoring state
        self.jobs: Dict[str, ScraperJob] = {}
        self.executions: Dict[str, ScraperExecution] = {}
        self.running_jobs: Dict[str, threading.Thread] = {}
        self.stop_event = threading.Event()
        
        # Performance tracking
        self.performance_metrics = {
            'total_executions': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'total_records_collected': 0,
            'total_records_inserted': 0,
            'average_execution_time': 0.0,
            'system_memory_usage': 0.0,
            'system_cpu_usage': 0.0,
        }
        
        # Load configuration
        self.load_configuration()
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def load_configuration(self):
        """Load scraper job configuration"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            
            for job_config in config.get('jobs', []):
                job = ScraperJob(
                    name=job_config['name'],
                    path=job_config['path'],
                    category=job_config['category'],
                    priority=ScraperPriority(job_config['priority']),
                    schedule=job_config['schedule'],
                    max_retries=job_config.get('max_retries', 3),
                    retry_delay=job_config.get('retry_delay', 300),
                    timeout=job_config.get('timeout', 1800),
                    enabled=job_config.get('enabled', True)
                )
                self.jobs[job.name] = job
        else:
            # Create default configuration
            self.create_default_configuration()
    
    def create_default_configuration(self):
        """Create default scraper job configuration"""
        default_jobs = [
            # Parliamentary scrapers (HIGH PRIORITY)
            {
                'name': 'federal_parliament',
                'path': 'scrapers/openparliament',
                'category': 'parliamentary',
                'priority': 'high',
                'schedule': '0 2 * * *',  # Daily at 2 AM
                'max_retries': 3,
                'retry_delay': 300,
                'timeout': 1800,
                'enabled': True
            },
            
            # Provincial scrapers (MEDIUM PRIORITY)
            {
                'name': 'ontario_legislature',
                'path': 'scrapers/scrapers-ca/ca_on',
                'category': 'provincial',
                'priority': 'medium',
                'schedule': '0 3 * * *',  # Daily at 3 AM
                'max_retries': 3,
                'retry_delay': 300,
                'timeout': 1200,
                'enabled': True
            },
            {
                'name': 'quebec_legislature',
                'path': 'scrapers/scrapers-ca/ca_qc',
                'category': 'provincial',
                'priority': 'medium',
                'schedule': '0 4 * * *',  # Daily at 4 AM
                'max_retries': 3,
                'retry_delay': 300,
                'timeout': 1200,
                'enabled': True
            },
            {
                'name': 'british_columbia_legislature',
                'path': 'scrapers/scrapers-ca/ca_bc',
                'category': 'provincial',
                'priority': 'medium',
                'schedule': '0 5 * * *',  # Daily at 5 AM
                'max_retries': 3,
                'retry_delay': 300,
                'timeout': 1200,
                'enabled': True
            },
            
            # Major municipal scrapers (MEDIUM PRIORITY)
            {
                'name': 'toronto_city_council',
                'path': 'scrapers/scrapers-ca/ca_on_toronto',
                'category': 'municipal',
                'priority': 'medium',
                'schedule': '0 6 * * *',  # Daily at 6 AM
                'max_retries': 3,
                'retry_delay': 300,
                'timeout': 900,
                'enabled': True
            },
            {
                'name': 'montreal_city_council',
                'path': 'scrapers/scrapers-ca/ca_qc_montreal',
                'category': 'municipal',
                'priority': 'medium',
                'schedule': '0 7 * * *',  # Daily at 7 AM
                'max_retries': 3,
                'retry_delay': 300,
                'timeout': 900,
                'enabled': True
            },
            {
                'name': 'vancouver_city_council',
                'path': 'scrapers/scrapers-ca/ca_bc_vancouver',
                'category': 'municipal',
                'priority': 'medium',
                'schedule': '0 8 * * *',  # Daily at 8 AM
                'max_retries': 3,
                'retry_delay': 300,
                'timeout': 900,
                'enabled': True
            },
            
            # Civic scrapers (LOW PRIORITY)
            {
                'name': 'civic_data',
                'path': 'scrapers/civic-scraper',
                'category': 'civic',
                'priority': 'low',
                'schedule': '0 9 * * *',  # Daily at 9 AM
                'max_retries': 3,
                'retry_delay': 300,
                'timeout': 600,
                'enabled': True
            },
        ]
        
        config = {'jobs': default_jobs}
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        # Load the configuration
        self.load_configuration()
        logger.info(f"Created default configuration: {self.config_file}")
    
    def run_scraper_job(self, job: ScraperJob) -> ScraperExecution:
        """Run a single scraper job"""
        execution = ScraperExecution(
            job=job,
            status=ScraperStatus.RUNNING,
            start_time=datetime.utcnow()
        )
        
        try:
            logger.info(f"🚀 Starting scraper: {job.name}")
            
            # Record start in database
            self.record_scraping_run_start(job, execution)
            
            # Import and run scraper
            scraper_module = self.import_scraper_module(job.path)
            if not scraper_module:
                raise Exception(f"Failed to import scraper module: {job.path}")
            
            # Create scraper instance
            scraper_class = self.find_scraper_class(scraper_module)
            if not scraper_class:
                raise Exception(f"No scraper class found in {job.path}")
            
            scraper = scraper_class('jurisdiction-id')
            
            # Collect data with timeout
            data = []
            start_time = time.time()
            
            for person in scraper.scrape():
                # Check timeout
                if time.time() - start_time > job.timeout:
                    logger.warning(f"Scraper {job.name} timed out after {job.timeout}s")
                    break
                
                # Extract person data
                person_data = self.extract_person_data(person)
                data.append(person_data)
            
            # Insert data to database
            inserted_count = self.insert_data_to_database(job, data)
            
            # Update execution result
            execution.status = ScraperStatus.SUCCESS
            execution.records_collected = len(data)
            execution.records_inserted = inserted_count
            execution.end_time = datetime.utcnow()
            execution.execution_time = time.time() - start_time
            
            # Record system metrics
            execution.memory_usage = psutil.virtual_memory().percent
            execution.cpu_usage = psutil.cpu_percent()
            
            # Update performance metrics
            self.update_performance_metrics(execution)
            
            # Record completion in database
            self.record_scraping_run_complete(job, execution)
            
            logger.info(f"✅ {job.name}: Collected {len(data)} records, inserted {inserted_count} in {execution.execution_time:.2f}s")
            
        except Exception as e:
            execution.status = ScraperStatus.FAILED
            execution.error_message = str(e)
            execution.end_time = datetime.utcnow()
            execution.execution_time = time.time() - start_time if 'start_time' in locals() else 0
            
            # Record failure in database
            self.record_scraping_run_failed(job, execution)
            
            logger.error(f"❌ {job.name}: Failed - {str(e)}")
            logger.error(traceback.format_exc())
        
        return execution
    
    def import_scraper_module(self, scraper_path: str):
        """Import scraper module"""
        try:
            people_file = Path(scraper_path) / 'people.py'
            if not people_file.exists():
                return None
            
            spec = importlib.util.spec_from_file_location("scraper_module", people_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
            
        except Exception as e:
            logger.error(f"Error importing scraper {scraper_path}: {str(e)}")
            return None
    
    def find_scraper_class(self, module):
        """Find scraper class in module"""
        for name in dir(module):
            obj = getattr(module, name)
            if (isinstance(obj, type) and 
                name.endswith('PersonScraper') and 
                name != 'CanadianScraper' and 
                name != 'CSVScraper'):
                return obj
        return None
    
    def extract_person_data(self, person) -> Dict[str, Any]:
        """Extract data from person object"""
        person_data = {
            'name': getattr(person, 'name', 'Unknown'),
            'role': getattr(person, 'role', None),
            'party': getattr(person, 'party', None),
            'district': getattr(person, 'district', None),
            'email': None,
            'phone': None,
            'image': getattr(person, 'image', None)
        }
        
        # Extract contact information
        if hasattr(person, 'contact_details'):
            for contact in person.contact_details:
                if contact.type == 'email':
                    person_data['email'] = contact.value
                elif contact.type == 'voice':
                    person_data['phone'] = contact.value
        
        return person_data
    
    def insert_data_to_database(self, job: ScraperJob, data: List[Dict]) -> int:
        """Insert data into database"""
        if not data:
            return 0
        
        try:
            with self.SessionLocal() as session:
                # Create or get jurisdiction
                jurisdiction = session.query(Jurisdiction).filter(
                    Jurisdiction.name == job.name
                ).first()
                
                if not jurisdiction:
                    jurisdiction = Jurisdiction(
                        name=job.name,
                        jurisdiction_type=self._get_jurisdiction_type(job.category),
                        code=job.name.lower().replace(' ', '_'),
                        website=f"https://{job.name.lower().replace(' ', '')}.ca"
                    )
                    session.add(jurisdiction)
                    session.flush()
                
                # Insert representatives
                inserted_count = 0
                for person_data in data:
                    if person_data.get('name') and person_data['name'] != 'Unknown':
                        representative = Representative(
                            jurisdiction_id=jurisdiction.id,
                            name=person_data['name'],
                            role=self._get_representative_role(person_data.get('role')),
                            party=person_data.get('party'),
                            riding=person_data.get('district'),
                            email=person_data.get('email'),
                            phone=person_data.get('phone'),
                            image_url=person_data.get('image'),
                            bio=f"Data from {job.name} scraper"
                        )
                        session.add(representative)
                        inserted_count += 1
                
                session.commit()
                return inserted_count
                
        except SQLAlchemyError as e:
            logger.error(f"Database error for {job.name}: {str(e)}")
            return 0
    
    def _get_jurisdiction_type(self, category: str) -> JurisdictionType:
        """Map category to jurisdiction type"""
        mapping = {
            'parliamentary': JurisdictionType.FEDERAL,
            'provincial': JurisdictionType.PROVINCIAL,
            'municipal': JurisdictionType.MUNICIPAL,
            'civic': JurisdictionType.MUNICIPAL,
        }
        return mapping.get(category, JurisdictionType.MUNICIPAL)
    
    def _get_representative_role(self, role_str: Optional[str]) -> RepresentativeRole:
        """Map role string to RepresentativeRole enum"""
        if not role_str:
            return RepresentativeRole.COUNCILLOR
        
        role_lower = role_str.lower()
        if 'mp' in role_lower:
            return RepresentativeRole.MP
        elif 'mla' in role_lower:
            return RepresentativeRole.MLA
        elif 'mpp' in role_lower:
            return RepresentativeRole.MPP
        elif 'mayor' in role_lower:
            return RepresentativeRole.MAYOR
        elif 'premier' in role_lower:
            return RepresentativeRole.PREMIER
        elif 'prime' in role_lower and 'minister' in role_lower:
            return RepresentativeRole.PRIME_MINISTER
        else:
            return RepresentativeRole.COUNCILLOR
    
    def record_scraping_run_start(self, job: ScraperJob, execution: ScraperExecution):
        """Record scraping run start in database"""
        try:
            with self.SessionLocal() as session:
                scraping_run = ScrapingRun(
                    jurisdiction_id=self._get_jurisdiction_id(job.name, session),
                    scraper_name=job.name,
                    start_time=execution.start_time,
                    status='running',
                    records_processed=0,
                    records_created=0,
                    records_updated=0
                )
                session.add(scraping_run)
                session.commit()
        except Exception as e:
            logger.error(f"Error recording scraping run start: {str(e)}")
    
    def record_scraping_run_complete(self, job: ScraperJob, execution: ScraperExecution):
        """Record successful scraping run completion"""
        try:
            with self.SessionLocal() as session:
                scraping_run = session.query(ScrapingRun).filter(
                    ScrapingRun.scraper_name == job.name,
                    ScrapingRun.start_time == execution.start_time
                ).first()
                
                if scraping_run:
                    scraping_run.end_time = execution.end_time
                    scraping_run.status = 'completed'
                    scraping_run.records_processed = execution.records_collected
                    scraping_run.records_created = execution.records_inserted
                    session.commit()
        except Exception as e:
            logger.error(f"Error recording scraping run completion: {str(e)}")
    
    def record_scraping_run_failed(self, job: ScraperJob, execution: ScraperExecution):
        """Record failed scraping run"""
        try:
            with self.SessionLocal() as session:
                scraping_run = session.query(ScrapingRun).filter(
                    ScrapingRun.scraper_name == job.name,
                    ScrapingRun.start_time == execution.start_time
                ).first()
                
                if scraping_run:
                    scraping_run.end_time = execution.end_time
                    scraping_run.status = 'failed'
                    scraping_run.error_message = execution.error_message
                    session.commit()
                
                # Record data quality issue
                if execution.error_message:
                    data_issue = DataQualityIssue(
                        jurisdiction_id=self._get_jurisdiction_id(job.name, session),
                        issue_type='scraper_failure',
                        severity='high' if job.priority == ScraperPriority.HIGH else 'medium',
                        description=f"Scraper {job.name} failed: {execution.error_message}",
                        affected_records=0
                    )
                    session.add(data_issue)
                    session.commit()
        except Exception as e:
            logger.error(f"Error recording scraping run failure: {str(e)}")
    
    def _get_jurisdiction_id(self, job_name: str, session) -> str:
        """Get or create jurisdiction ID"""
        jurisdiction = session.query(Jurisdiction).filter(
            Jurisdiction.name == job_name
        ).first()
        
        if not jurisdiction:
            jurisdiction = Jurisdiction(
                name=job_name,
                jurisdiction_type=JurisdictionType.MUNICIPAL,  # Default
                code=job_name.lower().replace(' ', '_'),
                website=f"https://{job_name.lower().replace(' ', '')}.ca"
            )
            session.add(jurisdiction)
            session.flush()
        
        return jurisdiction.id
    
    def update_performance_metrics(self, execution: ScraperExecution):
        """Update performance metrics"""
        self.performance_metrics['total_executions'] += 1
        
        if execution.status == ScraperStatus.SUCCESS:
            self.performance_metrics['successful_executions'] += 1
            self.performance_metrics['total_records_collected'] += execution.records_collected
            self.performance_metrics['total_records_inserted'] += execution.records_inserted
            
            # Update average execution time
            total_time = self.performance_metrics['average_execution_time'] * (self.performance_metrics['total_executions'] - 1)
            total_time += execution.execution_time or 0
            self.performance_metrics['average_execution_time'] = total_time / self.performance_metrics['total_executions']
        else:
            self.performance_metrics['failed_executions'] += 1
        
        # Update system metrics
        self.performance_metrics['system_memory_usage'] = psutil.virtual_memory().percent
        self.performance_metrics['system_cpu_usage'] = psutil.cpu_percent()
    
    def run_job_with_retry(self, job: ScraperJob):
        """Run job with automatic retry on failure"""
        execution = None
        retry_count = 0
        
        while retry_count <= job.max_retries and not self.stop_event.is_set():
            try:
                execution = self.run_scraper_job(job)
                
                if execution.status == ScraperStatus.SUCCESS:
                    break
                else:
                    retry_count += 1
                    execution.retry_count = retry_count
                    
                    if retry_count <= job.max_retries:
                        logger.warning(f"Retrying {job.name} in {job.retry_delay}s (attempt {retry_count}/{job.max_retries})")
                        time.sleep(job.retry_delay)
                    else:
                        logger.error(f"Job {job.name} failed after {job.max_retries} retries")
                        
            except Exception as e:
                retry_count += 1
                logger.error(f"Error running job {job.name}: {str(e)}")
                
                if retry_count <= job.max_retries:
                    time.sleep(job.retry_delay)
        
        # Store execution result
        if execution:
            self.executions[job.name] = execution
        
        # Remove from running jobs
        if job.name in self.running_jobs:
            del self.running_jobs[job.name]
    
    def schedule_jobs(self):
        """Schedule all jobs"""
        for job in self.jobs.values():
            if not job.enabled:
                continue
            
            # Parse cron schedule (minute hour * * *)
            try:
                cron_parts = job.schedule.split()
                if len(cron_parts) >= 2:
                    minute = cron_parts[0]
                    hour = cron_parts[1]
                    # Convert to HH:MM format for schedule library
                    time_str = f"{hour.zfill(2)}:{minute.zfill(2)}"
                    schedule.every().day.at(time_str).do(
                        self.run_job_with_retry, job
                    )
                    logger.info(f"Scheduled {job.name} to run at {time_str}")
                else:
                    logger.warning(f"Invalid schedule format for {job.name}: {job.schedule}")
            except Exception as e:
                logger.error(f"Error scheduling {job.name}: {str(e)}")
    
    def run_scheduler(self):
        """Run the job scheduler"""
        logger.info("🕐 Starting job scheduler")
        
        while not self.stop_event.is_set():
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def start_monitoring(self):
        """Start the monitoring system"""
        logger.info("🚀 Starting Scraper Monitoring System")
        
        # Schedule all jobs
        self.schedule_jobs()
        
        # Start scheduler in background thread
        scheduler_thread = threading.Thread(target=self.run_scheduler, daemon=True)
        scheduler_thread.start()
        
        # Start performance monitoring
        self.start_performance_monitoring()
        
        # Keep main thread alive
        try:
            while not self.stop_event.is_set():
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received interrupt signal, shutting down...")
            self.stop()
    
    def start_performance_monitoring(self):
        """Start performance monitoring in background"""
        def monitor_performance():
            while not self.stop_event.is_set():
                try:
                    # Update system metrics
                    self.performance_metrics['system_memory_usage'] = psutil.virtual_memory().percent
                    self.performance_metrics['system_cpu_usage'] = psutil.cpu_percent()
                    
                    # Log performance every 5 minutes
                    if int(time.time()) % 300 == 0:
                        logger.info(f"Performance: CPU {self.performance_metrics['system_cpu_usage']:.1f}%, "
                                  f"Memory {self.performance_metrics['system_memory_usage']:.1f}%, "
                                  f"Running jobs: {len(self.running_jobs)}")
                    
                    time.sleep(60)
                except Exception as e:
                    logger.error(f"Performance monitoring error: {str(e)}")
        
        monitor_thread = threading.Thread(target=monitor_performance, daemon=True)
        monitor_thread.start()
    
    def get_status_report(self) -> Dict[str, Any]:
        """Get current status report"""
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'jobs': {
                name: {
                    'enabled': job.enabled,
                    'priority': job.priority.value,
                    'schedule': job.schedule,
                    'last_execution': self.executions.get(name, None)
                }
                for name, job in self.jobs.items()
            },
            'running_jobs': list(self.running_jobs.keys()),
            'performance_metrics': self.performance_metrics,
            'system_health': {
                'memory_usage': psutil.virtual_memory().percent,
                'cpu_usage': psutil.cpu_percent(),
                'disk_usage': psutil.disk_usage('/').percent
            }
        }
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
    
    def stop(self):
        """Stop the monitoring system"""
        logger.info("🛑 Stopping Scraper Monitoring System")
        self.stop_event.set()
        
        # Wait for running jobs to complete
        for job_name, thread in self.running_jobs.items():
            logger.info(f"Waiting for {job_name} to complete...")
            thread.join(timeout=30)
        
        # Save final status report
        self.save_status_report()
        
        logger.info("✅ Scraper Monitoring System stopped")
    
    def save_status_report(self, filename: str = None):
        """Save status report to file"""
        if filename is None:
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            filename = f'scraper_status_report_{timestamp}.json'
        
        report = self.get_status_report()
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📄 Status report saved to {filename}")


def main():
    """Main function to run scraper monitoring system"""
    # Database URL - update this for your environment
    database_url = os.getenv('DATABASE_URL', 'postgresql://user:pass@localhost/openpolicy')
    
    # Create monitoring system
    monitoring_system = ScraperMonitoringSystem(database_url)
    
    try:
        # Start monitoring
        monitoring_system.start_monitoring()
    except Exception as e:
        logger.error(f"Monitoring system error: {str(e)}")
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
