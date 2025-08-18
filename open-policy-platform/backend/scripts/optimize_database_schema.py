"""
Database Schema Optimization Script
Optimizes database schema for better performance and data integrity
"""

import os
import sys
import logging
from datetime import datetime
from sqlalchemy import text, create_engine, inspect
from sqlalchemy.orm import sessionmaker
import psycopg2
from psycopg2.extras import RealDictCursor

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db_config

logger = logging.getLogger(__name__)

class DatabaseSchemaOptimizer:
    """Handles database schema optimization"""
    
    def __init__(self):
        self.engine = create_engine(db_config.get_url())
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.inspector = inspect(self.engine)
        
    def optimize_table_structures(self):
        """Optimize table structures for better performance"""
        logger.info("Starting table structure optimization")
        
        with self.engine.connect() as conn:
            # Optimize bills_bill table
            optimizations = [
                # Add proper data types and constraints
                """
                ALTER TABLE bills_bill 
                ALTER COLUMN title TYPE VARCHAR(500),
                ALTER COLUMN description TYPE TEXT,
                ALTER COLUMN bill_number TYPE VARCHAR(20),
                ALTER COLUMN sponsor TYPE VARCHAR(200),
                ALTER COLUMN jurisdiction TYPE VARCHAR(50),
                ALTER COLUMN status TYPE VARCHAR(50)
                """,
                
                # Add check constraints for data validation
                """
                ALTER TABLE bills_bill 
                ADD CONSTRAINT check_bill_number_format 
                CHECK (bill_number ~ '^[A-Z]-[0-9]+$')
                """,
                
                """
                ALTER TABLE bills_bill 
                ADD CONSTRAINT check_jurisdiction 
                CHECK (jurisdiction IN ('federal', 'provincial', 'municipal'))
                """,
                
                """
                ALTER TABLE bills_bill 
                ADD CONSTRAINT check_status 
                CHECK (status IN ('introduced', 'passed', 'defeated', 'withdrawn'))
                """,
                
                # Optimize politicians_politician table
                """
                ALTER TABLE politicians_politician 
                ALTER COLUMN name TYPE VARCHAR(200),
                ALTER COLUMN party TYPE VARCHAR(100),
                ALTER COLUMN constituency TYPE VARCHAR(200),
                ALTER COLUMN jurisdiction TYPE VARCHAR(50),
                ALTER COLUMN email TYPE VARCHAR(255),
                ALTER COLUMN phone TYPE VARCHAR(20)
                """,
                
                """
                ALTER TABLE politicians_politician 
                ADD CONSTRAINT check_email_format 
                CHECK (email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
                """,
                
                # Optimize votes_vote table
                """
                ALTER TABLE votes_vote 
                ALTER COLUMN bill_number TYPE VARCHAR(20),
                ALTER COLUMN vote_type TYPE VARCHAR(50),
                ALTER COLUMN result TYPE VARCHAR(50),
                ALTER COLUMN jurisdiction TYPE VARCHAR(50)
                """,
                
                """
                ALTER TABLE votes_vote 
                ADD CONSTRAINT check_vote_type 
                CHECK (vote_type IN ('yea', 'nay', 'abstain'))
                """,
                
                """
                ALTER TABLE votes_vote 
                ADD CONSTRAINT check_vote_result 
                CHECK (result IN ('passed', 'defeated', 'tied'))
                """
            ]
            
            for optimization in optimizations:
                try:
                    conn.execute(text(optimization))
                    conn.commit()
                    logger.info("Applied table structure optimization")
                except Exception as e:
                    logger.warning(f"Optimization warning: {e}")
                    conn.rollback()
    
    def add_missing_indexes(self):
        """Add missing indexes for better query performance"""
        logger.info("Adding missing indexes")
        
        with self.engine.connect() as conn:
            # Indexes for bills_bill table
            bill_indexes = [
                "CREATE INDEX IF NOT EXISTS idx_bills_jurisdiction ON bills_bill(jurisdiction)",
                "CREATE INDEX IF NOT EXISTS idx_bills_status ON bills_bill(status)",
                "CREATE INDEX IF NOT EXISTS idx_bills_introduced_date ON bills_bill(introduced_date)",
                "CREATE INDEX IF NOT EXISTS idx_bills_sponsor ON bills_bill(sponsor)",
                "CREATE INDEX IF NOT EXISTS idx_bills_jurisdiction_status ON bills_bill(jurisdiction, status)",
                "CREATE INDEX IF NOT EXISTS idx_bills_date_jurisdiction ON bills_bill(introduced_date, jurisdiction)"
            ]
            
            # Indexes for politicians_politician table
            politician_indexes = [
                "CREATE INDEX IF NOT EXISTS idx_politicians_jurisdiction ON politicians_politician(jurisdiction)",
                "CREATE INDEX IF NOT EXISTS idx_politicians_party ON politicians_politician(party)",
                "CREATE INDEX IF NOT EXISTS idx_politicians_constituency ON politicians_politician(constituency)",
                "CREATE INDEX IF NOT EXISTS idx_politicians_name ON politicians_politician(name)",
                "CREATE INDEX IF NOT EXISTS idx_politicians_jurisdiction_party ON politicians_politician(jurisdiction, party)"
            ]
            
            # Indexes for votes_vote table
            vote_indexes = [
                "CREATE INDEX IF NOT EXISTS idx_votes_bill_number ON votes_vote(bill_number)",
                "CREATE INDEX IF NOT EXISTS idx_votes_vote_date ON votes_vote(vote_date)",
                "CREATE INDEX IF NOT EXISTS idx_votes_result ON votes_vote(result)",
                "CREATE INDEX IF NOT EXISTS idx_votes_jurisdiction ON votes_vote(jurisdiction)",
                "CREATE INDEX IF NOT EXISTS idx_votes_bill_date ON votes_vote(bill_number, vote_date)"
            ]
            
            # Indexes for hansards_statement table
            hansard_indexes = [
                "CREATE INDEX IF NOT EXISTS idx_hansards_speaker ON hansards_statement(speaker)",
                "CREATE INDEX IF NOT EXISTS idx_hansards_date ON hansards_statement(date)",
                "CREATE INDEX IF NOT EXISTS idx_hansards_jurisdiction ON hansards_statement(jurisdiction)",
                "CREATE INDEX IF NOT EXISTS idx_hansards_speaker_date ON hansards_statement(speaker, date)"
            ]
            
            # Indexes for committees_committee table
            committee_indexes = [
                "CREATE INDEX IF NOT EXISTS idx_committees_jurisdiction ON committees_committee(jurisdiction)",
                "CREATE INDEX IF NOT EXISTS idx_committees_name ON committees_committee(name)"
            ]
            
            all_indexes = bill_indexes + politician_indexes + vote_indexes + hansard_indexes + committee_indexes
            
            for index_sql in all_indexes:
                try:
                    conn.execute(text(index_sql))
                    conn.commit()
                    logger.info(f"Created index: {index_sql}")
                except Exception as e:
                    logger.warning(f"Index creation warning: {e}")
                    conn.rollback()
    
    def implement_proper_constraints(self):
        """Implement proper database constraints"""
        logger.info("Implementing proper constraints")
        
        with self.engine.connect() as conn:
            # Foreign key constraints
            fk_constraints = [
                """
                ALTER TABLE votes_vote 
                ADD CONSTRAINT fk_votes_bill 
                FOREIGN KEY (bill_number) REFERENCES bills_bill(bill_number)
                ON DELETE CASCADE
                """,
                
                """
                ALTER TABLE hansards_statement 
                ADD CONSTRAINT fk_hansards_speaker 
                FOREIGN KEY (speaker) REFERENCES politicians_politician(name)
                ON DELETE SET NULL
                """,
                
                """
                ALTER TABLE committees_committee 
                ADD CONSTRAINT fk_committees_members 
                FOREIGN KEY (members) REFERENCES politicians_politician(id)
                ON DELETE SET NULL
                """
            ]
            
            # Unique constraints
            unique_constraints = [
                "ALTER TABLE bills_bill ADD CONSTRAINT uk_bill_number UNIQUE (bill_number)",
                "ALTER TABLE politicians_politician ADD CONSTRAINT uk_politician_name UNIQUE (name)",
                "ALTER TABLE votes_vote ADD CONSTRAINT uk_vote_bill_date UNIQUE (bill_number, vote_date)"
            ]
            
            # Not null constraints
            not_null_constraints = [
                "ALTER TABLE bills_bill ALTER COLUMN title SET NOT NULL",
                "ALTER TABLE bills_bill ALTER COLUMN bill_number SET NOT NULL",
                "ALTER TABLE bills_bill ALTER COLUMN jurisdiction SET NOT NULL",
                "ALTER TABLE politicians_politician ALTER COLUMN name SET NOT NULL",
                "ALTER TABLE politicians_politician ALTER COLUMN jurisdiction SET NOT NULL",
                "ALTER TABLE votes_vote ALTER COLUMN bill_number SET NOT NULL",
                "ALTER TABLE votes_vote ALTER COLUMN vote_date SET NOT NULL"
            ]
            
            all_constraints = fk_constraints + unique_constraints + not_null_constraints
            
            for constraint_sql in all_constraints:
                try:
                    conn.execute(text(constraint_sql))
                    conn.commit()
                    logger.info(f"Applied constraint: {constraint_sql[:50]}...")
                except Exception as e:
                    logger.warning(f"Constraint application warning: {e}")
                    conn.rollback()
    
    def add_data_validation_triggers(self):
        """Add data validation triggers"""
        logger.info("Adding data validation triggers")
        
        with self.engine.connect() as conn:
            # Trigger function for bill number validation
            trigger_functions = [
                """
                CREATE OR REPLACE FUNCTION validate_bill_number()
                RETURNS TRIGGER AS $$
                BEGIN
                    IF NEW.bill_number !~ '^[A-Z]-[0-9]+$' THEN
                        RAISE EXCEPTION 'Invalid bill number format. Expected format: X-123';
                    END IF;
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;
                """,
                
                """
                CREATE OR REPLACE FUNCTION validate_email()
                RETURNS TRIGGER AS $$
                BEGIN
                    IF NEW.email IS NOT NULL AND NEW.email !~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$' THEN
                        RAISE EXCEPTION 'Invalid email format';
                    END IF;
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;
                """,
                
                """
                CREATE OR REPLACE FUNCTION validate_vote_counts()
                RETURNS TRIGGER AS $$
                BEGIN
                    IF NEW.yea_votes < 0 OR NEW.nay_votes < 0 OR NEW.abstentions < 0 THEN
                        RAISE EXCEPTION 'Vote counts cannot be negative';
                    END IF;
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;
                """
            ]
            
            # Create trigger functions
            for function_sql in trigger_functions:
                try:
                    conn.execute(text(function_sql))
                    conn.commit()
                    logger.info("Created trigger function")
                except Exception as e:
                    logger.warning(f"Trigger function creation warning: {e}")
                    conn.rollback()
            
            # Create triggers
            triggers = [
                """
                CREATE TRIGGER trigger_validate_bill_number
                BEFORE INSERT OR UPDATE ON bills_bill
                FOR EACH ROW EXECUTE FUNCTION validate_bill_number();
                """,
                
                """
                CREATE TRIGGER trigger_validate_email
                BEFORE INSERT OR UPDATE ON politicians_politician
                FOR EACH ROW EXECUTE FUNCTION validate_email();
                """,
                
                """
                CREATE TRIGGER trigger_validate_vote_counts
                BEFORE INSERT OR UPDATE ON votes_vote
                FOR EACH ROW EXECUTE FUNCTION validate_vote_counts();
                """
            ]
            
            for trigger_sql in triggers:
                try:
                    conn.execute(text(trigger_sql))
                    conn.commit()
                    logger.info("Created trigger")
                except Exception as e:
                    logger.warning(f"Trigger creation warning: {e}")
                    conn.rollback()
    
    def optimize_query_performance(self):
        """Optimize query performance with query analysis"""
        logger.info("Optimizing query performance")
        
        with self.engine.connect() as conn:
            # Analyze table statistics
            analyze_queries = [
                "ANALYZE bills_bill",
                "ANALYZE politicians_politician",
                "ANALYZE votes_vote",
                "ANALYZE hansards_statement",
                "ANALYZE committees_committee"
            ]
            
            for analyze_sql in analyze_queries:
                try:
                    conn.execute(text(analyze_sql))
                    conn.commit()
                    logger.info(f"Analyzed table: {analyze_sql}")
                except Exception as e:
                    logger.warning(f"Table analysis warning: {e}")
                    conn.rollback()
            
            # Optimize common queries with materialized views
            materialized_views = [
                """
                CREATE MATERIALIZED VIEW IF NOT EXISTS mv_bills_summary AS
                SELECT 
                    jurisdiction,
                    status,
                    COUNT(*) as bill_count,
                    MIN(introduced_date) as earliest_date,
                    MAX(introduced_date) as latest_date
                FROM bills_bill
                GROUP BY jurisdiction, status
                """,
                
                """
                CREATE MATERIALIZED VIEW IF NOT EXISTS mv_politicians_summary AS
                SELECT 
                    jurisdiction,
                    party,
                    COUNT(*) as politician_count
                FROM politicians_politician
                GROUP BY jurisdiction, party
                """,
                
                """
                CREATE MATERIALIZED VIEW IF NOT EXISTS mv_votes_summary AS
                SELECT 
                    bill_number,
                    COUNT(*) as vote_count,
                    SUM(CASE WHEN result = 'passed' THEN 1 ELSE 0 END) as passed_count,
                    SUM(CASE WHEN result = 'defeated' THEN 1 ELSE 0 END) as defeated_count
                FROM votes_vote
                GROUP BY bill_number
                """
            ]
            
            for view_sql in materialized_views:
                try:
                    conn.execute(text(view_sql))
                    conn.commit()
                    logger.info("Created materialized view")
                except Exception as e:
                    logger.warning(f"Materialized view creation warning: {e}")
                    conn.rollback()
            
            # Create indexes on materialized views
            view_indexes = [
                "CREATE INDEX IF NOT EXISTS idx_mv_bills_jurisdiction ON mv_bills_summary(jurisdiction)",
                "CREATE INDEX IF NOT EXISTS idx_mv_politicians_jurisdiction ON mv_politicians_summary(jurisdiction)",
                "CREATE INDEX IF NOT EXISTS idx_mv_votes_bill ON mv_votes_summary(bill_number)"
            ]
            
            for index_sql in view_indexes:
                try:
                    conn.execute(text(index_sql))
                    conn.commit()
                    logger.info("Created index on materialized view")
                except Exception as e:
                    logger.warning(f"View index creation warning: {e}")
                    conn.rollback()
    
    def run_optimization(self):
        """Run complete schema optimization"""
        logger.info("Starting complete database schema optimization")
        
        try:
            self.optimize_table_structures()
            self.add_missing_indexes()
            self.implement_proper_constraints()
            self.add_data_validation_triggers()
            self.optimize_query_performance()
            
            logger.info("Database schema optimization completed successfully")
            
        except Exception as e:
            logger.error(f"Schema optimization failed: {e}")
            raise

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run optimization
    optimizer = DatabaseSchemaOptimizer()
    optimizer.run_optimization()
