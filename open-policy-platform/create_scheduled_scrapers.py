#!/usr/bin/env python3
"""
Create Scheduled Scrapers Script for Open Policy Platform V4
Sets up continuous data collection with scheduled scraper jobs
"""

import requests
import json
import time
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ScheduledScraperCreator:
    def __init__(self, scraper_url="http://localhost:9008"):
        self.scraper_url = scraper_url
        
    def create_scheduled_job(self, name, description, target_urls, scraping_rules, schedule, data_storage):
        """Create a scheduled scraper job"""
        try:
            job_data = {
                "name": name,
                "description": description,
                "target_urls": target_urls,
                "scraping_rules": scraping_rules,
                "data_storage": data_storage,
                "schedule": schedule,  # cron expression
                "rate_limit": 0.5
            }
            
            response = requests.post(
                f"{self.scraper_url}/jobs/public",
                headers={"Content-Type": "application/json"},
                json=job_data,
                timeout=30
            )
            
            if response.status_code == 201:
                job = response.json()["job"]
                logger.info(f"✅ Created scheduled job: {job['id']} - {job['name']}")
                return job
            else:
                logger.error(f"❌ Failed to create job: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error creating scheduled job: {e}")
            return None
    
    def create_continuous_data_collection_jobs(self):
        """Create jobs for continuous data collection"""
        logger.info("🚀 Creating continuous data collection jobs...")
        
        jobs_created = []
        
        # 1. Daily Parliamentary Bills Update (every 6 hours)
        parliamentary_job = self.create_scheduled_job(
            name="Daily Parliamentary Bills Update",
            description="Update parliamentary bills every 6 hours",
            target_urls=[
                "https://openparliament.ca/bills/",
                "https://www.parl.ca/legisinfo/en/bills"
            ],
            scraping_rules=[
                {
                    "name": "bill_titles",
                    "selector": "h1, h2, h3, .bill-title",
                    "data_type": "text"
                },
                {
                    "name": "bill_links",
                    "selector": "a[href*=\"/bills/\"]",
                    "data_type": "link"
                },
                {
                    "name": "bill_status",
                    "selector": ".bill-status, .status",
                    "data_type": "text"
                }
            ],
            schedule="0 */6 * * *",  # Every 6 hours
            data_storage={
                "type": "database",
                "connection": "postgresql",
                "table": "parliamentary_bills"
            }
        )
        
        if parliamentary_job:
            jobs_created.append(parliamentary_job)
        
        # 2. Hourly Municipal Updates (every hour)
        municipal_job = self.create_scheduled_job(
            name="Hourly Municipal Government Updates",
            description="Update municipal government data every hour",
            target_urls=[
                "https://www.toronto.ca/city-government/",
                "https://montreal.ca/en/",
                "https://vancouver.ca/"
            ],
            scraping_rules=[
                {
                    "name": "meeting_dates",
                    "selector": ".meeting-date, .date",
                    "data_type": "text"
                },
                {
                    "name": "agenda_items",
                    "selector": ".agenda-item, .item",
                    "data_type": "text"
                },
                {
                    "name": "announcements",
                    "selector": ".announcement, .news",
                    "data_type": "text"
                }
            ],
            schedule="0 * * * *",  # Every hour
            data_storage={
                "type": "database",
                "connection": "postgresql",
                "table": "municipal_updates"
            }
        )
        
        if municipal_job:
            jobs_created.append(municipal_job)
        
        # 3. Daily Politician Updates (daily at 2 AM)
        politician_job = self.create_scheduled_job(
            name="Daily Politician Information Update",
            description="Update politician information daily",
            target_urls=[
                "https://openparliament.ca/politicians/",
                "https://openparliament.ca/parties/"
            ],
            scraping_rules=[
                {
                    "name": "politician_names",
                    "selector": ".politician-name, .name",
                    "data_type": "text"
                },
                {
                    "name": "party_affiliations",
                    "selector": ".party-name, .party",
                    "data_type": "text"
                },
                {
                    "name": "riding_information",
                    "selector": ".riding, .constituency",
                    "data_type": "text"
                }
            ],
            schedule="0 2 * * *",  # Daily at 2 AM
            data_storage={
                "type": "database",
                "connection": "postgresql",
                "table": "politician_updates"
            }
        )
        
        if politician_job:
            jobs_created.append(politician_job)
        
        # 4. Weekly Policy Analysis (weekly on Sunday at 3 AM)
        policy_analysis_job = self.create_scheduled_job(
            name="Weekly Policy Analysis Update",
            description="Weekly comprehensive policy analysis",
            target_urls=[
                "https://www.parl.ca/legisinfo/en/bills",
                "https://www.ourcommons.ca/Parliamentarians/en/bills"
            ],
            scraping_rules=[
                {
                    "name": "policy_summaries",
                    "selector": ".summary, .description",
                    "data_type": "text"
                },
                {
                    "name": "voting_records",
                    "selector": ".vote, .voting",
                    "data_type": "text"
                },
                {
                    "name": "committee_reports",
                    "selector": ".report, .committee",
                    "data_type": "text"
                }
            ],
            schedule="0 3 * * 0",  # Weekly on Sunday at 3 AM
            data_storage={
                "type": "database",
                "connection": "postgresql",
                "table": "policy_analysis"
            }
        )
        
        if policy_analysis_job:
            jobs_created.append(policy_analysis_job)
        
        logger.info(f"✅ Successfully created {len(jobs_created)} scheduled jobs")
        return jobs_created
    
    def verify_jobs_created(self):
        """Verify that the scheduled jobs were created successfully"""
        try:
            response = requests.get(f"{self.scraper_url}/jobs", timeout=10)
            if response.status_code == 200:
                jobs_data = response.json()
                total_jobs = jobs_data.get("total", 0)
                jobs = jobs_data.get("jobs", [])
                
                logger.info(f"📊 Current Job Status:")
                logger.info(f"   - Total Jobs: {total_jobs}")
                
                # Count scheduled jobs
                scheduled_jobs = [job for job in jobs if job.get("schedule")]
                logger.info(f"   - Scheduled Jobs: {len(scheduled_jobs)}")
                
                # Show job details
                for job in jobs:
                    if job.get("schedule"):
                        logger.info(f"   📅 {job['name']} - Schedule: {job['schedule']}")
                
                return total_jobs, len(scheduled_jobs)
            else:
                logger.error(f"Failed to get jobs: {response.status_code}")
                return 0, 0
                
        except Exception as e:
            logger.error(f"Error verifying jobs: {e}")
            return 0, 0

def main():
    """Main function to create scheduled scrapers"""
    logger.info("🎯 Starting Scheduled Scraper Creation Process...")
    
    creator = ScheduledScraperCreator()
    
    try:
        # Create continuous data collection jobs
        jobs_created = creator.create_continuous_data_collection_jobs()
        
        if jobs_created:
            logger.info("✅ Scheduled jobs created successfully!")
            
            # Wait a moment for jobs to be processed
            time.sleep(5)
            
            # Verify jobs were created
            total_jobs, scheduled_jobs = creator.verify_jobs_created()
            
            logger.info("🎉 SCHEDULED SCRAPER CREATION COMPLETED!")
            logger.info(f"📊 Total Jobs: {total_jobs}")
            logger.info(f"📅 Scheduled Jobs: {scheduled_jobs}")
            logger.info("🔄 Data will now be collected automatically on schedule")
            
        else:
            logger.error("❌ Failed to create scheduled jobs")
            return 1
            
    except Exception as e:
        logger.error(f"❌ Scheduled scraper creation failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
