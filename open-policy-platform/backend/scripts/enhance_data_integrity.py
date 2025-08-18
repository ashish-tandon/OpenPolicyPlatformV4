"""
Data Integrity Enhancement Script
Implements comprehensive data validation, consistency checks, and quality monitoring
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from sqlalchemy import text, create_engine, inspect
from sqlalchemy.orm import sessionmaker
import psycopg2
from psycopg2.extras import RealDictCursor

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db_config

logger = logging.getLogger(__name__)

class DataIntegrityEnhancer:
    """Handles data integrity enhancement"""
    
    def __init__(self):
        self.engine = create_engine(db_config.get_url())
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.inspector = inspect(self.engine)
        
    def implement_data_validation_rules(self):
        """Implement comprehensive data validation rules"""
        logger.info("Implementing data validation rules")
        
        with self.engine.connect() as conn:
            # Create validation rules table
            validation_rules = [
                """
                CREATE TABLE IF NOT EXISTS data_validation_rules (
                    id SERIAL PRIMARY KEY,
                    table_name VARCHAR(100) NOT NULL,
                    column_name VARCHAR(100) NOT NULL,
                    rule_type VARCHAR(50) NOT NULL,
                    rule_definition TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """,
                
                # Insert validation rules
                """
                INSERT INTO data_validation_rules (table_name, column_name, rule_type, rule_definition)
                VALUES 
                ('bills_bill', 'bill_number', 'format', '^[A-Z]-[0-9]+$'),
                ('bills_bill', 'jurisdiction', 'enum', 'federal,provincial,municipal'),
                ('bills_bill', 'status', 'enum', 'introduced,passed,defeated,withdrawn'),
                ('politicians_politician', 'email', 'format', '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
                ('politicians_politician', 'jurisdiction', 'enum', 'federal,provincial,municipal'),
                ('votes_vote', 'vote_type', 'enum', 'yea,nay,abstain'),
                ('votes_vote', 'result', 'enum', 'passed,defeated,tied'),
                ('votes_vote', 'yea_votes', 'range', '>= 0'),
                ('votes_vote', 'nay_votes', 'range', '>= 0'),
                ('votes_vote', 'abstentions', 'range', '>= 0')
                ON CONFLICT DO NOTHING
                """
            ]
            
            for rule in validation_rules:
                try:
                    conn.execute(text(rule))
                    conn.commit()
                    logger.info("Applied data validation rule")
                except Exception as e:
                    logger.warning(f"Validation rule application warning: {e}")
                    conn.rollback()
            
            # Create validation functions
            validation_functions = [
                """
                CREATE OR REPLACE FUNCTION validate_data_rule(table_name TEXT, column_name TEXT, value TEXT)
                RETURNS BOOLEAN AS $$
                DECLARE
                    rule_def TEXT;
                    rule_type TEXT;
                BEGIN
                    SELECT rule_definition, rule_type INTO rule_def, rule_type
                    FROM data_validation_rules
                    WHERE table_name = $1 AND column_name = $2 AND is_active = TRUE;
                    
                    IF rule_def IS NULL THEN
                        RETURN TRUE; -- No rule defined, assume valid
                    END IF;
                    
                    CASE rule_type
                        WHEN 'format' THEN
                            RETURN value ~ rule_def;
                        WHEN 'enum' THEN
                            RETURN value = ANY(string_to_array(rule_def, ','));
                        WHEN 'range' THEN
                            -- Handle numeric range validation
                            IF rule_def LIKE '>= %' THEN
                                RETURN CAST(value AS INTEGER) >= CAST(substring(rule_def from 4) AS INTEGER);
                            ELSIF rule_def LIKE '<= %' THEN
                                RETURN CAST(value AS INTEGER) <= CAST(substring(rule_def from 4) AS INTEGER);
                            END IF;
                        ELSE
                            RETURN TRUE;
                    END CASE;
                END;
                $$ LANGUAGE plpgsql;
                """
            ]
            
            for function in validation_functions:
                try:
                    conn.execute(text(function))
                    conn.commit()
                    logger.info("Created validation function")
                except Exception as e:
                    logger.warning(f"Validation function creation warning: {e}")
                    conn.rollback()
    
    def add_data_consistency_checks(self):
        """Add data consistency checks"""
        logger.info("Adding data consistency checks")
        
        with self.engine.connect() as conn:
            # Create consistency checks table
            consistency_table = """
            CREATE TABLE IF NOT EXISTS data_consistency_checks (
                id SERIAL PRIMARY KEY,
                check_name VARCHAR(200) NOT NULL,
                check_query TEXT NOT NULL,
                expected_result TEXT,
                severity VARCHAR(20) DEFAULT 'warning',
                is_active BOOLEAN DEFAULT TRUE,
                last_run TIMESTAMP,
                last_result TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            
            try:
                conn.execute(text(consistency_table))
                conn.commit()
                logger.info("Created consistency checks table")
            except Exception as e:
                logger.warning(f"Consistency table creation warning: {e}")
                conn.rollback()
            
            # Insert consistency checks
            consistency_checks = [
                """
                INSERT INTO data_consistency_checks (check_name, check_query, expected_result, severity)
                VALUES 
                ('No orphaned votes', 'SELECT COUNT(*) FROM votes_vote v LEFT JOIN bills_bill b ON v.bill_number = b.bill_number WHERE b.bill_number IS NULL', '0', 'error'),
                ('No orphaned statements', 'SELECT COUNT(*) FROM hansards_statement h LEFT JOIN politicians_politician p ON h.speaker = p.name WHERE p.name IS NULL', '0', 'warning'),
                ('No duplicate bill numbers', 'SELECT COUNT(*) FROM bills_bill GROUP BY bill_number HAVING COUNT(*) > 1', '0', 'error'),
                ('No duplicate politician names', 'SELECT COUNT(*) FROM politicians_politician GROUP BY name HAVING COUNT(*) > 1', '0', 'error'),
                ('No future dates', 'SELECT COUNT(*) FROM bills_bill WHERE introduced_date > CURRENT_DATE', '0', 'warning'),
                ('No invalid vote counts', 'SELECT COUNT(*) FROM votes_vote WHERE yea_votes < 0 OR nay_votes < 0 OR abstentions < 0', '0', 'error'),
                ('No empty required fields', 'SELECT COUNT(*) FROM bills_bill WHERE title IS NULL OR bill_number IS NULL OR jurisdiction IS NULL', '0', 'error'),
                ('No invalid jurisdictions', 'SELECT COUNT(*) FROM bills_bill WHERE jurisdiction NOT IN (''federal'', ''provincial'', ''municipal'')', '0', 'error')
                ON CONFLICT DO NOTHING
                """
            ]
            
            for check in consistency_checks:
                try:
                    conn.execute(text(check))
                    conn.commit()
                    logger.info("Added consistency check")
                except Exception as e:
                    logger.warning(f"Consistency check addition warning: {e}")
                    conn.rollback()
    
    def implement_data_cleanup_procedures(self):
        """Implement data cleanup procedures"""
        logger.info("Implementing data cleanup procedures")
        
        with self.engine.connect() as conn:
            # Create cleanup procedures table
            cleanup_table = """
            CREATE TABLE IF NOT EXISTS data_cleanup_procedures (
                id SERIAL PRIMARY KEY,
                procedure_name VARCHAR(200) NOT NULL,
                cleanup_query TEXT NOT NULL,
                description TEXT,
                is_automatic BOOLEAN DEFAULT FALSE,
                last_run TIMESTAMP,
                records_affected INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            
            try:
                conn.execute(text(cleanup_table))
                conn.commit()
                logger.info("Created cleanup procedures table")
            except Exception as e:
                logger.warning(f"Cleanup table creation warning: {e}")
                conn.rollback()
            
            # Insert cleanup procedures
            cleanup_procedures = [
                """
                INSERT INTO data_cleanup_procedures (procedure_name, cleanup_query, description, is_automatic)
                VALUES 
                ('Remove orphaned votes', 'DELETE FROM votes_vote v WHERE NOT EXISTS (SELECT 1 FROM bills_bill b WHERE b.bill_number = v.bill_number)', 'Remove votes for non-existent bills', TRUE),
                ('Remove orphaned statements', 'DELETE FROM hansards_statement h WHERE NOT EXISTS (SELECT 1 FROM politicians_politician p WHERE p.name = h.speaker)', 'Remove statements by non-existent politicians', TRUE),
                ('Clean duplicate bill numbers', 'DELETE FROM bills_bill WHERE id NOT IN (SELECT MIN(id) FROM bills_bill GROUP BY bill_number)', 'Keep only the first occurrence of duplicate bill numbers', FALSE),
                ('Clean duplicate politician names', 'DELETE FROM politicians_politician WHERE id NOT IN (SELECT MIN(id) FROM politicians_politician GROUP BY name)', 'Keep only the first occurrence of duplicate politician names', FALSE),
                ('Remove future dates', 'UPDATE bills_bill SET introduced_date = CURRENT_DATE WHERE introduced_date > CURRENT_DATE', 'Set future dates to current date', TRUE),
                ('Fix negative vote counts', 'UPDATE votes_vote SET yea_votes = 0 WHERE yea_votes < 0', 'Set negative vote counts to zero', TRUE),
                ('Clean empty required fields', 'DELETE FROM bills_bill WHERE title IS NULL OR bill_number IS NULL OR jurisdiction IS NULL', 'Remove records with missing required fields', FALSE),
                ('Fix invalid jurisdictions', 'UPDATE bills_bill SET jurisdiction = ''federal'' WHERE jurisdiction NOT IN (''federal'', ''provincial'', ''municipal'')', 'Set invalid jurisdictions to federal', TRUE)
                ON CONFLICT DO NOTHING
                """
            ]
            
            for procedure in cleanup_procedures:
                try:
                    conn.execute(text(procedure))
                    conn.commit()
                    logger.info("Added cleanup procedure")
                except Exception as e:
                    logger.warning(f"Cleanup procedure addition warning: {e}")
                    conn.rollback()
    
    def add_data_quality_monitoring(self):
        """Add data quality monitoring"""
        logger.info("Adding data quality monitoring")
        
        with self.engine.connect() as conn:
            # Create quality monitoring table
            quality_table = """
            CREATE TABLE IF NOT EXISTS data_quality_metrics (
                id SERIAL PRIMARY KEY,
                metric_name VARCHAR(200) NOT NULL,
                metric_value DECIMAL(10,2),
                metric_date DATE DEFAULT CURRENT_DATE,
                table_name VARCHAR(100),
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            
            try:
                conn.execute(text(quality_table))
                conn.commit()
                logger.info("Created quality metrics table")
            except Exception as e:
                logger.warning(f"Quality table creation warning: {e}")
                conn.rollback()
            
            # Create quality monitoring function
            monitoring_function = """
            CREATE OR REPLACE FUNCTION calculate_quality_metrics()
            RETURNS VOID AS $$
            DECLARE
                total_bills INTEGER;
                total_politicians INTEGER;
                total_votes INTEGER;
                valid_bills INTEGER;
                valid_politicians INTEGER;
                valid_votes INTEGER;
                completeness_rate DECIMAL(5,2);
            BEGIN
                -- Calculate total records
                SELECT COUNT(*) INTO total_bills FROM bills_bill;
                SELECT COUNT(*) INTO total_politicians FROM politicians_politician;
                SELECT COUNT(*) INTO total_votes FROM votes_vote;
                
                -- Calculate valid records
                SELECT COUNT(*) INTO valid_bills FROM bills_bill 
                WHERE title IS NOT NULL AND bill_number IS NOT NULL AND jurisdiction IS NOT NULL;
                
                SELECT COUNT(*) INTO valid_politicians FROM politicians_politician 
                WHERE name IS NOT NULL AND jurisdiction IS NOT NULL;
                
                SELECT COUNT(*) INTO valid_votes FROM votes_vote 
                WHERE bill_number IS NOT NULL AND vote_date IS NOT NULL;
                
                -- Calculate completeness rates
                completeness_rate := CASE 
                    WHEN total_bills > 0 THEN (valid_bills::DECIMAL / total_bills::DECIMAL) * 100
                    ELSE 0 
                END;
                
                -- Insert metrics
                INSERT INTO data_quality_metrics (metric_name, metric_value, table_name, description)
                VALUES 
                ('bills_completeness', completeness_rate, 'bills_bill', 'Percentage of bills with all required fields'),
                ('total_bills', total_bills, 'bills_bill', 'Total number of bills'),
                ('valid_bills', valid_bills, 'bills_bill', 'Number of valid bills'),
                ('total_politicians', total_politicians, 'politicians_politician', 'Total number of politicians'),
                ('valid_politicians', valid_politicians, 'politicians_politician', 'Number of valid politicians'),
                ('total_votes', total_votes, 'votes_vote', 'Total number of votes'),
                ('valid_votes', valid_votes, 'votes_vote', 'Number of valid votes');
            END;
            $$ LANGUAGE plpgsql;
            """
            
            try:
                conn.execute(text(monitoring_function))
                conn.commit()
                logger.info("Created quality monitoring function")
            except Exception as e:
                logger.warning(f"Monitoring function creation warning: {e}")
                conn.rollback()
    
    def implement_backup_strategies(self):
        """Implement comprehensive backup strategies"""
        logger.info("Implementing backup strategies")
        
        with self.engine.connect() as conn:
            # Create backup tracking table
            backup_table = """
            CREATE TABLE IF NOT EXISTS backup_history (
                id SERIAL PRIMARY KEY,
                backup_name VARCHAR(200) NOT NULL,
                backup_type VARCHAR(50) NOT NULL,
                backup_size BIGINT,
                backup_path TEXT,
                status VARCHAR(20) DEFAULT 'pending',
                start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_time TIMESTAMP,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            
            try:
                conn.execute(text(backup_table))
                conn.commit()
                logger.info("Created backup history table")
            except Exception as e:
                logger.warning(f"Backup table creation warning: {e}")
                conn.rollback()
            
            # Create backup function
            backup_function = """
            CREATE OR REPLACE FUNCTION create_backup(backup_name TEXT, backup_type TEXT DEFAULT 'full')
            RETURNS TEXT AS $$
            DECLARE
                backup_path TEXT;
                backup_size BIGINT;
                backup_id INTEGER;
            BEGIN
                -- Insert backup record
                INSERT INTO backup_history (backup_name, backup_type, status)
                VALUES (backup_name, backup_type, 'in_progress')
                RETURNING id INTO backup_id;
                
                -- Generate backup path
                backup_path := '/backups/' || backup_name || '_' || CURRENT_TIMESTAMP::TEXT || '.sql';
                
                -- Create backup using pg_dump
                PERFORM pg_dump(
                    'host=' || current_setting('db_host') || 
                    ' port=' || current_setting('db_port') || 
                    ' dbname=' || current_database() || 
                    ' user=' || current_user,
                    backup_path
                );
                
                -- Get backup size
                SELECT pg_stat_file(backup_path) INTO backup_size;
                
                -- Update backup record
                UPDATE backup_history 
                SET backup_path = backup_path, 
                    backup_size = backup_size,
                    status = 'completed',
                    end_time = CURRENT_TIMESTAMP
                WHERE id = backup_id;
                
                RETURN backup_path;
            EXCEPTION
                WHEN OTHERS THEN
                    -- Update backup record with error
                    UPDATE backup_history 
                    SET status = 'failed',
                        error_message = SQLERRM,
                        end_time = CURRENT_TIMESTAMP
                    WHERE id = backup_id;
                    
                    RAISE EXCEPTION 'Backup failed: %', SQLERRM;
            END;
            $$ LANGUAGE plpgsql;
            """
            
            try:
                conn.execute(text(backup_function))
                conn.commit()
                logger.info("Created backup function")
            except Exception as e:
                logger.warning(f"Backup function creation warning: {e}")
                conn.rollback()
            
            # Create automated backup schedule
            schedule_function = """
            CREATE OR REPLACE FUNCTION schedule_automated_backups()
            RETURNS VOID AS $$
            BEGIN
                -- Create daily backup
                PERFORM create_backup('daily_backup_' || CURRENT_DATE::TEXT, 'daily');
                
                -- Create weekly backup on Sundays
                IF EXTRACT(DOW FROM CURRENT_DATE) = 0 THEN
                    PERFORM create_backup('weekly_backup_' || CURRENT_DATE::TEXT, 'weekly');
                END IF;
                
                -- Create monthly backup on first day of month
                IF EXTRACT(DAY FROM CURRENT_DATE) = 1 THEN
                    PERFORM create_backup('monthly_backup_' || CURRENT_DATE::TEXT, 'monthly');
                END IF;
            END;
            $$ LANGUAGE plpgsql;
            """
            
            try:
                conn.execute(text(schedule_function))
                conn.commit()
                logger.info("Created automated backup schedule")
            except Exception as e:
                logger.warning(f"Backup schedule creation warning: {e}")
                conn.rollback()
    
    def run_enhancement(self):
        """Run complete data integrity enhancement"""
        logger.info("Starting complete data integrity enhancement")
        
        try:
            self.implement_data_validation_rules()
            self.add_data_consistency_checks()
            self.implement_data_cleanup_procedures()
            self.add_data_quality_monitoring()
            self.implement_backup_strategies()
            
            logger.info("Data integrity enhancement completed successfully")
            
        except Exception as e:
            logger.error(f"Data integrity enhancement failed: {e}")
            raise

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run enhancement
    enhancer = DataIntegrityEnhancer()
    enhancer.run_enhancement()
