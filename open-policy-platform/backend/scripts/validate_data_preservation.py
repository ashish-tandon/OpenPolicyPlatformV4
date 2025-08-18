"""
Data Preservation Validation Script
Ensures NO data is ever dropped and all information is collected and preserved
"""

import os
import sys
import logging
import json
from datetime import datetime, timedelta
from sqlalchemy import text, create_engine, inspect
from sqlalchemy.orm import sessionmaker
import psycopg2
from psycopg2.extras import RealDictCursor

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db_config

logger = logging.getLogger(__name__)

class DataPreservationValidator:
    """Validates that NO data is ever dropped and all information is preserved"""
    
    def __init__(self):
        self.engine = create_engine(db_config.get_url())
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.inspector = inspect(self.engine)
        self.preservation_log = {}
        self.data_snapshots = {}
        
    def create_data_snapshot(self):
        """Create a complete snapshot of all data"""
        logger.info("Creating complete data snapshot")
        
        with self.engine.connect() as conn:
            # Get all tables
            tables = self.inspector.get_table_names()
            
            snapshot = {
                'timestamp': datetime.now().isoformat(),
                'tables': {}
            }
            
            for table in tables:
                try:
                    # Get row count
                    count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    row_count = count_result.fetchone()[0]
                    
                    # Get sample data (first 10 rows)
                    sample_result = conn.execute(text(f"SELECT * FROM {table} LIMIT 10"))
                    sample_data = [dict(row) for row in sample_result.fetchall()]
                    
                    # Get table structure
                    columns = self.inspector.get_columns(table)
                    column_info = [{'name': col['name'], 'type': str(col['type'])} for col in columns]
                    
                    snapshot['tables'][table] = {
                        'row_count': row_count,
                        'sample_data': sample_data,
                        'columns': column_info,
                        'last_modified': datetime.now().isoformat()
                    }
                    
                    logger.info(f"Snapshot created for {table}: {row_count} rows")
                    
                except Exception as e:
                    logger.error(f"Failed to create snapshot for {table}: {e}")
                    snapshot['tables'][table] = {
                        'error': str(e),
                        'last_modified': datetime.now().isoformat()
                    }
            
            # Save snapshot
            snapshot_path = f"data_snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(snapshot_path, 'w') as f:
                json.dump(snapshot, f, indent=2, default=str)
            
            self.data_snapshots[snapshot_path] = snapshot
            logger.info(f"Data snapshot saved: {snapshot_path}")
            
            return snapshot
    
    def validate_no_data_dropped(self, before_snapshot, after_snapshot):
        """Validate that no data was dropped between snapshots"""
        logger.info("Validating no data was dropped")
        
        validation_results = {
            'timestamp': datetime.now().isoformat(),
            'data_preserved': True,
            'issues': [],
            'table_comparisons': {}
        }
        
        # Compare each table
        for table_name in before_snapshot['tables']:
            if table_name in after_snapshot['tables']:
                before_count = before_snapshot['tables'][table_name].get('row_count', 0)
                after_count = after_snapshot['tables'][table_name].get('row_count', 0)
                
                comparison = {
                    'before_count': before_count,
                    'after_count': after_count,
                    'difference': after_count - before_count,
                    'data_preserved': after_count >= before_count
                }
                
                validation_results['table_comparisons'][table_name] = comparison
                
                if after_count < before_count:
                    validation_results['data_preserved'] = False
                    validation_results['issues'].append(f"DATA LOSS in {table_name}: {before_count} -> {after_count} (lost {before_count - after_count} rows)")
                    logger.error(f"DATA LOSS DETECTED in {table_name}: {before_count} -> {after_count}")
                else:
                    logger.info(f"Data preserved in {table_name}: {before_count} -> {after_count}")
            else:
                validation_results['data_preserved'] = False
                validation_results['issues'].append(f"TABLE MISSING: {table_name} was dropped")
                logger.error(f"TABLE DROPPED: {table_name}")
        
        # Check for new tables (this is good)
        for table_name in after_snapshot['tables']:
            if table_name not in before_snapshot['tables']:
                logger.info(f"NEW TABLE CREATED: {table_name}")
                validation_results['table_comparisons'][table_name] = {
                    'before_count': 0,
                    'after_count': after_snapshot['tables'][table_name].get('row_count', 0),
                    'difference': after_snapshot['tables'][table_name].get('row_count', 0),
                    'data_preserved': True,
                    'new_table': True
                }
        
        return validation_results
    
    def validate_schema_changes(self, before_snapshot, after_snapshot):
        """Validate schema changes don't lose data"""
        logger.info("Validating schema changes")
        
        schema_results = {
            'timestamp': datetime.now().isoformat(),
            'schema_preserved': True,
            'changes': [],
            'table_schemas': {}
        }
        
        for table_name in before_snapshot['tables']:
            if table_name in after_snapshot['tables']:
                before_columns = {col['name']: col['type'] for col in before_snapshot['tables'][table_name].get('columns', [])}
                after_columns = {col['name']: col['type'] for col in after_snapshot['tables'][table_name].get('columns', [])}
                
                # Check for dropped columns
                dropped_columns = set(before_columns.keys()) - set(after_columns.keys())
                if dropped_columns:
                    schema_results['schema_preserved'] = False
                    schema_results['changes'].append(f"COLUMNS DROPPED in {table_name}: {dropped_columns}")
                    logger.error(f"COLUMNS DROPPED in {table_name}: {dropped_columns}")
                
                # Check for added columns (this is good)
                added_columns = set(after_columns.keys()) - set(before_columns.keys())
                if added_columns:
                    logger.info(f"COLUMNS ADDED in {table_name}: {added_columns}")
                
                # Check for type changes
                type_changes = []
                for col_name in set(before_columns.keys()) & set(after_columns.keys()):
                    if before_columns[col_name] != after_columns[col_name]:
                        type_changes.append(f"{col_name}: {before_columns[col_name]} -> {after_columns[col_name]}")
                
                if type_changes:
                    logger.info(f"TYPE CHANGES in {table_name}: {type_changes}")
                
                schema_results['table_schemas'][table_name] = {
                    'dropped_columns': list(dropped_columns),
                    'added_columns': list(added_columns),
                    'type_changes': type_changes
                }
        
        return schema_results
    
    def create_data_preservation_triggers(self):
        """Create triggers to prevent data deletion"""
        logger.info("Creating data preservation triggers")
        
        with self.engine.connect() as conn:
            # Create audit table for deletions
            audit_table = """
            CREATE TABLE IF NOT EXISTS data_deletion_audit (
                id SERIAL PRIMARY KEY,
                table_name VARCHAR(100) NOT NULL,
                operation VARCHAR(20) NOT NULL,
                deleted_data JSONB,
                deleted_count INTEGER,
                user_name VARCHAR(100),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ip_address INET,
                session_id VARCHAR(100)
            )
            """
            
            try:
                conn.execute(text(audit_table))
                conn.commit()
                logger.info("Created data deletion audit table")
            except Exception as e:
                logger.warning(f"Audit table creation warning: {e}")
                conn.rollback()
            
            # Create trigger function to log deletions
            trigger_function = """
            CREATE OR REPLACE FUNCTION log_data_deletion()
            RETURNS TRIGGER AS $$
            BEGIN
                INSERT INTO data_deletion_audit (
                    table_name, operation, deleted_data, deleted_count, 
                    user_name, ip_address, session_id
                ) VALUES (
                    TG_TABLE_NAME, TG_OP, to_jsonb(OLD), 1,
                    current_user, inet_client_addr(), current_setting('application_name', true)
                );
                
                -- Prevent deletion by raising exception
                RAISE EXCEPTION 'DATA DELETION PREVENTED: Table % is protected from deletion', TG_TABLE_NAME;
                
                RETURN OLD;
            END;
            $$ LANGUAGE plpgsql;
            """
            
            try:
                conn.execute(text(trigger_function))
                conn.commit()
                logger.info("Created data deletion prevention trigger function")
            except Exception as e:
                logger.warning(f"Trigger function creation warning: {e}")
                conn.rollback()
            
            # Create triggers on all tables
            tables = ['bills_bill', 'politicians_politician', 'votes_vote', 
                     'hansards_statement', 'committees_committee', 'activity_activity']
            
            for table in tables:
                try:
                    trigger_sql = f"""
                    CREATE TRIGGER prevent_data_deletion_{table}
                    BEFORE DELETE ON {table}
                    FOR EACH ROW EXECUTE FUNCTION log_data_deletion();
                    """
                    
                    conn.execute(text(trigger_sql))
                    conn.commit()
                    logger.info(f"Created deletion prevention trigger on {table}")
                    
                except Exception as e:
                    logger.warning(f"Failed to create trigger on {table}: {e}")
                    conn.rollback()
    
    def create_data_backup_strategy(self):
        """Create comprehensive data backup strategy"""
        logger.info("Creating comprehensive data backup strategy")
        
        with self.engine.connect() as conn:
            # Create backup configuration table
            backup_config = """
            CREATE TABLE IF NOT EXISTS data_backup_config (
                id SERIAL PRIMARY KEY,
                backup_type VARCHAR(50) NOT NULL,
                frequency VARCHAR(20) NOT NULL,
                retention_days INTEGER NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                last_backup TIMESTAMP,
                next_backup TIMESTAMP,
                backup_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            
            try:
                conn.execute(text(backup_config))
                conn.commit()
                logger.info("Created backup configuration table")
            except Exception as e:
                logger.warning(f"Backup config table creation warning: {e}")
                conn.rollback()
            
            # Insert backup configurations
            backup_configs = [
                ("full_backup", "daily", 30, True),
                ("incremental_backup", "hourly", 7, True),
                ("schema_backup", "weekly", 90, True),
                ("data_snapshot", "daily", 365, True)
            ]
            
            for backup_type, frequency, retention, is_active in backup_configs:
                try:
                    insert_sql = """
                    INSERT INTO data_backup_config (backup_type, frequency, retention_days, is_active)
                    VALUES (:backup_type, :frequency, :retention, :is_active)
                    ON CONFLICT (backup_type) DO UPDATE SET
                    frequency = :frequency,
                    retention_days = :retention,
                    is_active = :is_active
                    """
                    
                    conn.execute(text(insert_sql), {
                        'backup_type': backup_type,
                        'frequency': frequency,
                        'retention': retention,
                        'is_active': is_active
                    })
                    conn.commit()
                    logger.info(f"Configured {backup_type} backup")
                    
                except Exception as e:
                    logger.warning(f"Failed to configure {backup_type} backup: {e}")
                    conn.rollback()
    
    def create_data_validation_rules(self):
        """Create data validation rules to ensure data quality"""
        logger.info("Creating data validation rules")
        
        with self.engine.connect() as conn:
            # Create validation rules table
            validation_rules = """
            CREATE TABLE IF NOT EXISTS data_validation_rules (
                id SERIAL PRIMARY KEY,
                rule_name VARCHAR(200) NOT NULL,
                table_name VARCHAR(100) NOT NULL,
                column_name VARCHAR(100),
                rule_type VARCHAR(50) NOT NULL,
                rule_definition TEXT NOT NULL,
                severity VARCHAR(20) DEFAULT 'warning',
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            
            try:
                conn.execute(text(validation_rules))
                conn.commit()
                logger.info("Created data validation rules table")
            except Exception as e:
                logger.warning(f"Validation rules table creation warning: {e}")
                conn.rollback()
            
            # Insert comprehensive validation rules
            rules = [
                ("no_null_titles", "bills_bill", "title", "not_null", "title IS NOT NULL", "error"),
                ("no_null_names", "politicians_politician", "name", "not_null", "name IS NOT NULL", "error"),
                ("no_null_bill_numbers", "votes_vote", "bill_number", "not_null", "bill_number IS NOT NULL", "error"),
                ("valid_jurisdictions", "bills_bill", "jurisdiction", "enum", "jurisdiction IN ('federal', 'provincial', 'municipal')", "error"),
                ("valid_bill_format", "bills_bill", "bill_number", "format", "^[A-Z]-[0-9]+$", "error"),
                ("valid_email_format", "politicians_politician", "email", "format", "^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$", "warning"),
                ("no_future_dates", "bills_bill", "introduced_date", "date_range", "introduced_date <= CURRENT_DATE", "warning"),
                ("positive_vote_counts", "votes_vote", "yea_votes", "range", ">= 0", "error"),
                ("positive_vote_counts", "votes_vote", "nay_votes", "range", ">= 0", "error"),
                ("positive_vote_counts", "votes_vote", "abstentions", "range", ">= 0", "error")
            ]
            
            for rule_name, table_name, column_name, rule_type, rule_definition, severity in rules:
                try:
                    insert_sql = """
                    INSERT INTO data_validation_rules (rule_name, table_name, column_name, rule_type, rule_definition, severity)
                    VALUES (:rule_name, :table_name, :column_name, :rule_type, :rule_definition, :severity)
                    ON CONFLICT (rule_name) DO UPDATE SET
                    rule_definition = :rule_definition,
                    severity = :severity,
                    is_active = TRUE
                    """
                    
                    conn.execute(text(insert_sql), {
                        'rule_name': rule_name,
                        'table_name': table_name,
                        'column_name': column_name,
                        'rule_type': rule_type,
                        'rule_definition': rule_definition,
                        'severity': severity
                    })
                    conn.commit()
                    logger.info(f"Created validation rule: {rule_name}")
                    
                except Exception as e:
                    logger.warning(f"Failed to create validation rule {rule_name}: {e}")
                    conn.rollback()
    
    def run_comprehensive_validation(self):
        """Run comprehensive data preservation validation"""
        logger.info("Starting comprehensive data preservation validation")
        
        try:
            # Create initial snapshot
            logger.info("Creating initial data snapshot...")
            initial_snapshot = self.create_data_snapshot()
            
            # Create data preservation mechanisms
            logger.info("Creating data preservation mechanisms...")
            self.create_data_preservation_triggers()
            self.create_data_backup_strategy()
            self.create_data_validation_rules()
            
            # Create final snapshot
            logger.info("Creating final data snapshot...")
            final_snapshot = self.create_data_snapshot()
            
            # Validate no data was dropped
            logger.info("Validating data preservation...")
            preservation_results = self.validate_no_data_dropped(initial_snapshot, final_snapshot)
            schema_results = self.validate_schema_changes(initial_snapshot, final_snapshot)
            
            # Generate comprehensive report
            self.generate_preservation_report(preservation_results, schema_results)
            
            logger.info("Comprehensive data preservation validation completed")
            
            return preservation_results['data_preserved'] and schema_results['schema_preserved']
            
        except Exception as e:
            logger.error(f"Data preservation validation failed: {e}")
            raise
    
    def generate_preservation_report(self, preservation_results, schema_results):
        """Generate comprehensive data preservation report"""
        logger.info("Generating data preservation report")
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'data_preservation': {
                'overall_preserved': preservation_results['data_preserved'],
                'issues': preservation_results['issues'],
                'table_comparisons': preservation_results['table_comparisons']
            },
            'schema_preservation': {
                'overall_preserved': schema_results['schema_preserved'],
                'changes': schema_results['changes'],
                'table_schemas': schema_results['table_schemas']
            },
            'recommendations': self.generate_preservation_recommendations(preservation_results, schema_results)
        }
        
        # Save report
        report_path = f"data_preservation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Data preservation report saved: {report_path}")
        
        # Print summary
        print("\n" + "="*60)
        print("DATA PRESERVATION VALIDATION REPORT")
        print("="*60)
        print(f"Data preserved: {preservation_results['data_preserved']}")
        print(f"Schema preserved: {schema_results['schema_preserved']}")
        print(f"Total issues: {len(preservation_results['issues']) + len(schema_results['changes'])}")
        print("="*60)
        
        if preservation_results['issues']:
            print("DATA PRESERVATION ISSUES:")
            for issue in preservation_results['issues']:
                print(f"  ❌ {issue}")
        
        if schema_results['changes']:
            print("SCHEMA CHANGES:")
            for change in schema_results['changes']:
                print(f"  ⚠️  {change}")
        
        if not preservation_results['issues'] and not schema_results['changes']:
            print("✅ ALL DATA PRESERVED - NO LOSSES DETECTED")
    
    def generate_preservation_recommendations(self, preservation_results, schema_results):
        """Generate recommendations for data preservation"""
        recommendations = []
        
        if not preservation_results['data_preserved']:
            recommendations.append("IMMEDIATE ACTION REQUIRED: Data loss detected - investigate and restore immediately")
        
        if not schema_results['schema_preserved']:
            recommendations.append("SCHEMA ISSUES: Columns or tables were dropped - review schema changes")
        
        if preservation_results['issues']:
            recommendations.append(f"Address {len(preservation_results['issues'])} data preservation issues")
        
        if schema_results['changes']:
            recommendations.append(f"Review {len(schema_results['changes'])} schema changes")
        
        # Check for tables with low data counts
        for table_name, comparison in preservation_results['table_comparisons'].items():
            if comparison['after_count'] < 100:  # Arbitrary threshold
                recommendations.append(f"Investigate low data count in {table_name}: {comparison['after_count']} rows")
        
        if not recommendations:
            recommendations.append("All data preservation mechanisms working correctly - no immediate action required")
        
        return recommendations

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run comprehensive validation
    validator = DataPreservationValidator()
    success = validator.run_comprehensive_validation()
    
    if success:
        print("\n🎉 DATA PRESERVATION VALIDATION PASSED - NO DATA LOSS DETECTED")
    else:
        print("\n❌ DATA PRESERVATION VALIDATION FAILED - DATA LOSS DETECTED")
        sys.exit(1)
