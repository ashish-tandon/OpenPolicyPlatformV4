"""
Database Migration Script: 2023 to 2025
Updates the database schema and data to 2025 standards
"""

import os
import sys
import logging
from datetime import datetime, date
from sqlalchemy import text, create_engine
from sqlalchemy.orm import sessionmaker
import psycopg2
from psycopg2.extras import RealDictCursor

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db_config

logger = logging.getLogger(__name__)

class DatabaseMigration2023To2025:
    """Handles migration from 2023 to 2025 database schema and data"""
    
    def __init__(self):
        self.engine = create_engine(db_config.get_url())
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
    def run_migration(self):
        """Run the complete migration process"""
        logger.info("Starting 2023 to 2025 database migration")
        
        try:
            # Step 1: Backup current data
            self.backup_current_data()
            
            # Step 2: Update schema
            self.update_schema()
            
            # Step 3: Migrate data
            self.migrate_data()
            
            # Step 4: Update data to 2025
            self.update_data_to_2025()
            
            # Step 5: Validate migration
            self.validate_migration()
            
            logger.info("Migration completed successfully")
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            # Attempt rollback
            self.rollback_migration()
            raise
    
    def backup_current_data(self):
        """Create backup of current data"""
        logger.info("Creating backup of current data")
        
        backup_file = f"backup_2023_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
        
        try:
            # Create backup using pg_dump
            os.system(f"pg_dump -h {db_config.host} -p {db_config.port} -U {db_config.username} -d {db_config.database} > {backup_file}")
            logger.info(f"Backup created: {backup_file}")
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            raise
    
    def update_schema(self):
        """Update database schema for 2025"""
        logger.info("Updating database schema")
        
        with self.engine.connect() as conn:
            # Add new columns for 2025
            schema_updates = [
                """
                ALTER TABLE bills_bill 
                ADD COLUMN IF NOT EXISTS updated_2025 BOOLEAN DEFAULT FALSE,
                ADD COLUMN IF NOT EXISTS data_source_2025 VARCHAR(100),
                ADD COLUMN IF NOT EXISTS last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                """,
                
                """
                ALTER TABLE politicians_politician 
                ADD COLUMN IF NOT EXISTS updated_2025 BOOLEAN DEFAULT FALSE,
                ADD COLUMN IF NOT EXISTS data_source_2025 VARCHAR(100),
                ADD COLUMN IF NOT EXISTS last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                """,
                
                """
                ALTER TABLE hansards_statement 
                ADD COLUMN IF NOT EXISTS updated_2025 BOOLEAN DEFAULT FALSE,
                ADD COLUMN IF NOT EXISTS data_source_2025 VARCHAR(100),
                ADD COLUMN IF NOT EXISTS last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                """,
                
                """
                ALTER TABLE committees_committee 
                ADD COLUMN IF NOT EXISTS updated_2025 BOOLEAN DEFAULT FALSE,
                ADD COLUMN IF NOT EXISTS data_source_2025 VARCHAR(100),
                ADD COLUMN IF NOT EXISTS last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                """,
                
                """
                ALTER TABLE activity_activity 
                ADD COLUMN IF NOT EXISTS updated_2025 BOOLEAN DEFAULT FALSE,
                ADD COLUMN IF NOT EXISTS data_source_2025 VARCHAR(100),
                ADD COLUMN IF NOT EXISTS last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                """
            ]
            
            for update in schema_updates:
                try:
                    conn.execute(text(update))
                    conn.commit()
                except Exception as e:
                    logger.warning(f"Schema update warning: {e}")
                    conn.rollback()
    
    def migrate_data(self):
        """Migrate existing data to new schema"""
        logger.info("Migrating existing data")
        
        with self.engine.connect() as conn:
            # Update data source for existing records
            data_source_updates = [
                """
                UPDATE bills_bill 
                SET data_source_2025 = 'openparliament_legacy',
                updated_2025 = TRUE,
                last_modified = CURRENT_TIMESTAMP
                WHERE data_source_2025 IS NULL
                """,
                
                """
                UPDATE politicians_politician 
                SET data_source_2025 = 'openparliament_legacy',
                updated_2025 = TRUE,
                last_modified = CURRENT_TIMESTAMP
                WHERE data_source_2025 IS NULL
                """,
                
                """
                UPDATE hansards_statement 
                SET data_source_2025 = 'openparliament_legacy',
                updated_2025 = TRUE,
                last_modified = CURRENT_TIMESTAMP
                WHERE data_source_2025 IS NULL
                """,
                
                """
                UPDATE committees_committee 
                SET data_source_2025 = 'openparliament_legacy',
                updated_2025 = TRUE,
                last_modified = CURRENT_TIMESTAMP
                WHERE data_source_2025 IS NULL
                """,
                
                """
                UPDATE activity_activity 
                SET data_source_2025 = 'openparliament_legacy',
                updated_2025 = TRUE,
                last_modified = CURRENT_TIMESTAMP
                WHERE data_source_2025 IS NULL
                """
            ]
            
            for update in data_source_updates:
                try:
                    result = conn.execute(text(update))
                    conn.commit()
                    logger.info(f"Updated {result.rowcount} records")
                except Exception as e:
                    logger.error(f"Data migration error: {e}")
                    conn.rollback()
    
    def update_data_to_2025(self):
        """Update data to 2025 standards"""
        logger.info("Updating data to 2025 standards")
        
        # Import scrapers
        from scrapers.federal_parliament_scraper import FederalParliamentScraper
        
        # Initialize scrapers
        federal_scraper = FederalParliamentScraper()
        
        try:
            # Scrape fresh federal data
            logger.info("Scraping fresh federal data")
            federal_data = federal_scraper.scrape_all()
            
            # Update database with fresh data
            self.update_federal_data(federal_data)
            
            # Update data sources
            self.update_data_sources()
            
        except Exception as e:
            logger.error(f"Error updating data to 2025: {e}")
            raise
    
    def update_federal_data(self, federal_data):
        """Update federal data in database"""
        logger.info("Updating federal data in database")
        
        with self.engine.connect() as conn:
            # Update bills
            if federal_data.get('bills'):
                for bill in federal_data['bills']:
                    try:
                        # Check if bill exists
                        existing = conn.execute(
                            text("SELECT id FROM bills_bill WHERE title = :title"),
                            {"title": bill['title']}
                        ).fetchone()
                        
                        if existing:
                            # Update existing bill
                            conn.execute(
                                text("""
                                    UPDATE bills_bill 
                                    SET description = :description,
                                        introduced_date = :introduced_date,
                                        sponsor = :sponsor,
                                        updated_2025 = TRUE,
                                        data_source_2025 = 'federal_scraper_2025',
                                        last_modified = CURRENT_TIMESTAMP
                                    WHERE title = :title
                                """),
                                bill
                            )
                        else:
                            # Insert new bill
                            conn.execute(
                                text("""
                                    INSERT INTO bills_bill 
                                    (title, description, introduced_date, sponsor, jurisdiction, 
                                     updated_2025, data_source_2025, last_modified)
                                    VALUES (:title, :description, :introduced_date, :sponsor, :jurisdiction,
                                            TRUE, 'federal_scraper_2025', CURRENT_TIMESTAMP)
                                """),
                                bill
                            )
                    except Exception as e:
                        logger.error(f"Error updating bill {bill.get('title')}: {e}")
                        continue
                
                conn.commit()
                logger.info(f"Updated {len(federal_data['bills'])} bills")
            
            # Update MPs
            if federal_data.get('mps'):
                for mp in federal_data['mps']:
                    try:
                        # Check if MP exists
                        existing = conn.execute(
                            text("SELECT id FROM politicians_politician WHERE name = :name"),
                            {"name": mp['name']}
                        ).fetchone()
                        
                        if existing:
                            # Update existing MP
                            conn.execute(
                                text("""
                                    UPDATE politicians_politician 
                                    SET party = :party,
                                        constituency = :constituency,
                                        email = :email,
                                        phone = :phone,
                                        updated_2025 = TRUE,
                                        data_source_2025 = 'federal_scraper_2025',
                                        last_modified = CURRENT_TIMESTAMP
                                    WHERE name = :name
                                """),
                                mp
                            )
                        else:
                            # Insert new MP
                            conn.execute(
                                text("""
                                    INSERT INTO politicians_politician 
                                    (name, party, constituency, email, phone, jurisdiction,
                                     updated_2025, data_source_2025, last_modified)
                                    VALUES (:name, :party, :constituency, :email, :phone, :jurisdiction,
                                            TRUE, 'federal_scraper_2025', CURRENT_TIMESTAMP)
                                """),
                                mp
                            )
                    except Exception as e:
                        logger.error(f"Error updating MP {mp.get('name')}: {e}")
                        continue
                
                conn.commit()
                logger.info(f"Updated {len(federal_data['mps'])} MPs")
    
    def update_data_sources(self):
        """Update data sources for all records"""
        logger.info("Updating data sources")
        
        with self.engine.connect() as conn:
            # Update data sources based on jurisdiction
            source_updates = [
                """
                UPDATE bills_bill 
                SET data_source_2025 = 'federal_scraper_2025'
                WHERE jurisdiction = 'federal' AND data_source_2025 = 'openparliament_legacy'
                """,
                
                """
                UPDATE politicians_politician 
                SET data_source_2025 = 'federal_scraper_2025'
                WHERE jurisdiction = 'federal' AND data_source_2025 = 'openparliament_legacy'
                """,
                
                """
                UPDATE bills_bill 
                SET data_source_2025 = 'provincial_scraper_2025'
                WHERE jurisdiction LIKE '%provincial%' AND data_source_2025 = 'openparliament_legacy'
                """,
                
                """
                UPDATE politicians_politician 
                SET data_source_2025 = 'provincial_scraper_2025'
                WHERE jurisdiction LIKE '%provincial%' AND data_source_2025 = 'openparliament_legacy'
                """,
                
                """
                UPDATE bills_bill 
                SET data_source_2025 = 'municipal_scraper_2025'
                WHERE jurisdiction LIKE '%municipal%' AND data_source_2025 = 'openparliament_legacy'
                """,
                
                """
                UPDATE politicians_politician 
                SET data_source_2025 = 'municipal_scraper_2025'
                WHERE jurisdiction LIKE '%municipal%' AND data_source_2025 = 'openparliament_legacy'
                """
            ]
            
            for update in source_updates:
                try:
                    result = conn.execute(text(update))
                    conn.commit()
                    logger.info(f"Updated {result.rowcount} records with new data source")
                except Exception as e:
                    logger.error(f"Data source update error: {e}")
                    conn.rollback()
    
    def validate_migration(self):
        """Validate the migration was successful"""
        logger.info("Validating migration")
        
        with self.engine.connect() as conn:
            # Check schema updates
            schema_checks = [
                "SELECT COUNT(*) FROM bills_bill WHERE updated_2025 = TRUE",
                "SELECT COUNT(*) FROM politicians_politician WHERE updated_2025 = TRUE",
                "SELECT COUNT(*) FROM bills_bill WHERE data_source_2025 IS NOT NULL",
                "SELECT COUNT(*) FROM politicians_politician WHERE data_source_2025 IS NOT NULL"
            ]
            
            for check in schema_checks:
                try:
                    result = conn.execute(text(check)).scalar()
                    logger.info(f"Validation check: {result} records")
                except Exception as e:
                    logger.error(f"Validation check failed: {e}")
            
            # Check data freshness
            try:
                latest_bill = conn.execute(
                    text("SELECT MAX(last_modified) FROM bills_bill")
                ).scalar()
                
                if latest_bill:
                    logger.info(f"Latest bill update: {latest_bill}")
                
                latest_mp = conn.execute(
                    text("SELECT MAX(last_modified) FROM politicians_politician")
                ).scalar()
                
                if latest_mp:
                    logger.info(f"Latest MP update: {latest_mp}")
                    
            except Exception as e:
                logger.error(f"Data freshness check failed: {e}")
    
    def rollback_migration(self):
        """Rollback migration in case of failure"""
        logger.info("Starting migration rollback")
        
        try:
            # Restore from backup if available
            backup_files = [f for f in os.listdir('.') if f.startswith('backup_2023_')]
            if backup_files:
                latest_backup = max(backup_files)
                logger.info(f"Restoring from backup: {latest_backup}")
                
                # Restore database from backup
                os.system(f"psql -h {db_config.host} -p {db_config.port} -U {db_config.username} -d {db_config.database} < {latest_backup}")
                
                logger.info("Database restored from backup")
            else:
                logger.warning("No backup file found for rollback")
                
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            raise
    
    def add_progress_tracking(self):
        """Add progress tracking to migration"""
        logger.info("Adding progress tracking")
        
        with self.engine.connect() as conn:
            # Create progress tracking table
            progress_table = """
            CREATE TABLE IF NOT EXISTS migration_progress (
                id SERIAL PRIMARY KEY,
                step_name VARCHAR(100) NOT NULL,
                status VARCHAR(20) NOT NULL,
                start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_time TIMESTAMP,
                records_processed INTEGER DEFAULT 0,
                error_message TEXT
            )
            """
            
            try:
                conn.execute(text(progress_table))
                conn.commit()
                logger.info("Created migration progress tracking table")
            except Exception as e:
                logger.warning(f"Progress table creation warning: {e}")
                conn.rollback()
    
    def track_progress(self, step_name, status, records_processed=0, error_message=None):
        """Track migration progress"""
        with self.engine.connect() as conn:
            if status == 'started':
                insert_sql = """
                INSERT INTO migration_progress (step_name, status, start_time)
                VALUES (:step_name, :status, CURRENT_TIMESTAMP)
                """
                conn.execute(text(insert_sql), {"step_name": step_name, "status": status})
            else:
                update_sql = """
                UPDATE migration_progress 
                SET status = :status, end_time = CURRENT_TIMESTAMP, 
                    records_processed = :records_processed, error_message = :error_message
                WHERE step_name = :step_name AND status = 'started'
                ORDER BY start_time DESC LIMIT 1
                """
                conn.execute(text(update_sql), {
                    "step_name": step_name, 
                    "status": status, 
                    "records_processed": records_processed,
                    "error_message": error_message
                })
            
            conn.commit()
    
    def add_data_validation(self):
        """Add comprehensive data validation"""
        logger.info("Adding data validation")
        
        with self.engine.connect() as conn:
            # Validate bill data
            validation_queries = [
                """
                SELECT COUNT(*) as invalid_bills
                FROM bills_bill 
                WHERE bill_number IS NULL OR title IS NULL OR jurisdiction IS NULL
                """,
                
                """
                SELECT COUNT(*) as invalid_politicians
                FROM politicians_politician 
                WHERE name IS NULL OR jurisdiction IS NULL
                """,
                
                """
                SELECT COUNT(*) as invalid_votes
                FROM votes_vote 
                WHERE bill_number IS NULL OR vote_date IS NULL
                """,
                
                """
                SELECT COUNT(*) as orphaned_votes
                FROM votes_vote v
                LEFT JOIN bills_bill b ON v.bill_number = b.bill_number
                WHERE b.bill_number IS NULL
                """
            ]
            
            for query in validation_queries:
                try:
                    result = conn.execute(text(query))
                    count = result.fetchone()[0]
                    if count > 0:
                        logger.warning(f"Data validation found {count} issues")
                    else:
                        logger.info("Data validation passed")
                except Exception as e:
                    logger.error(f"Data validation error: {e}")
                    conn.rollback()

def main():
    """Main migration function"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        migration = DatabaseMigration2023To2025()
        migration.run_migration()
        print("Migration completed successfully!")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
