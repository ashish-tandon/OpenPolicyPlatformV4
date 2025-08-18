"""
Enhanced Database Schema Validation Tests
Tests that verify all database schema components are properly configured
"""

import pytest
from sqlalchemy import text, inspect
from sqlalchemy.exc import SQLAlchemyError

class TestEnhancedDatabaseSchema:
    """Test enhanced database schema validation"""
    
    def test_all_tables_exist(self, db_session):
        """Test that all required tables exist in the database"""
        
        # Setup: Get inspector for database
        inspector = inspect(db_session.bind)
        existing_tables = inspector.get_table_names()
        
        # Define required tables based on OpenParliament schema
        required_tables = [
            'bills_bill',
            'politicians_politician', 
            'votes_vote',
            'committees_committee',
            'hansards_statement',
            'activity_activity',
            'alerts_subscription',
            'auth_user',
            'django_content_type',
            'django_migrations',
            'django_session'
        ]
        
        # Execute: Check each required table
        missing_tables = []
        for table in required_tables:
            if table not in existing_tables:
                missing_tables.append(table)
        
        # Verify: All required tables exist
        assert len(missing_tables) == 0, f"Missing tables: {missing_tables}"
        
        # Additional verification: Check table counts
        assert len(existing_tables) >= len(required_tables), f"Expected at least {len(required_tables)} tables, found {len(existing_tables)}"
    
    def test_all_columns_exist(self, db_session):
        """Test that all required columns exist in each table"""
        
        # Setup: Get inspector for database
        inspector = inspect(db_session.bind)
        
        # Define required columns for key tables
        required_columns = {
            'bills_bill': [
                'id', 'title', 'description', 'bill_number', 'introduced_date',
                'sponsor', 'jurisdiction', 'status', 'updated_2025', 'data_source_2025', 'last_modified'
            ],
            'politicians_politician': [
                'id', 'name', 'party', 'constituency', 'jurisdiction', 'email', 'phone',
                'updated_2025', 'data_source_2025', 'last_modified'
            ],
            'votes_vote': [
                'id', 'bill_number', 'vote_date', 'vote_type', 'result',
                'yea_votes', 'nay_votes', 'abstentions', 'jurisdiction',
                'updated_2025', 'data_source_2025', 'last_modified'
            ],
            'committees_committee': [
                'id', 'name', 'description', 'jurisdiction', 'members',
                'updated_2025', 'data_source_2025', 'last_modified'
            ],
            'hansards_statement': [
                'id', 'speaker', 'content', 'date', 'session', 'jurisdiction',
                'updated_2025', 'data_source_2025', 'last_modified'
            ]
        }
        
        # Execute: Check columns for each table
        missing_columns = {}
        for table_name, expected_columns in required_columns.items():
            try:
                columns = inspector.get_columns(table_name)
                existing_column_names = [col['name'] for col in columns]
                
                table_missing = []
                for column in expected_columns:
                    if column not in existing_column_names:
                        table_missing.append(column)
                
                if table_missing:
                    missing_columns[table_name] = table_missing
            except Exception as e:
                missing_columns[table_name] = [f"Error accessing table: {str(e)}"]
        
        # Verify: All required columns exist
        assert len(missing_columns) == 0, f"Missing columns: {missing_columns}"
    
    def test_all_constraints_valid(self, db_session):
        """Test that all database constraints are valid"""
        
        # Setup: Get inspector for database
        inspector = inspect(db_session.bind)
        
        # Execute: Check constraints for key tables
        constraint_issues = []
        
        # Check primary key constraints
        for table_name in ['bills_bill', 'politicians_politician', 'votes_vote']:
            try:
                pk_constraint = inspector.get_pk_constraint(table_name)
                if not pk_constraint['constrained_columns']:
                    constraint_issues.append(f"No primary key on {table_name}")
            except Exception as e:
                constraint_issues.append(f"Error checking primary key on {table_name}: {str(e)}")
        
        # Check unique constraints
        unique_constraints_to_check = [
            ('bills_bill', 'bill_number'),
            ('politicians_politician', 'name'),
            ('votes_vote', ['bill_number', 'vote_date'])
        ]
        
        for table_name, column_name in unique_constraints_to_check:
            try:
                unique_constraints = inspector.get_unique_constraints(table_name)
                found = False
                for constraint in unique_constraints:
                    if column_name in constraint['column_names']:
                        found = True
                        break
                if not found:
                    constraint_issues.append(f"No unique constraint on {table_name}.{column_name}")
            except Exception as e:
                constraint_issues.append(f"Error checking unique constraint on {table_name}.{column_name}: {str(e)}")
        
        # Check not null constraints
        not_null_columns = [
            ('bills_bill', 'title'),
            ('bills_bill', 'bill_number'),
            ('politicians_politician', 'name'),
            ('votes_vote', 'bill_number'),
            ('votes_vote', 'vote_date')
        ]
        
        for table_name, column_name in not_null_columns:
            try:
                columns = inspector.get_columns(table_name)
                for col in columns:
                    if col['name'] == column_name:
                        if col.get('nullable', True):
                            constraint_issues.append(f"Column {table_name}.{column_name} should be NOT NULL")
                        break
            except Exception as e:
                constraint_issues.append(f"Error checking NOT NULL constraint on {table_name}.{column_name}: {str(e)}")
        
        # Verify: All constraints are valid
        assert len(constraint_issues) == 0, f"Constraint issues found: {constraint_issues}"
    
    def test_all_foreign_keys_valid(self, db_session):
        """Test that all foreign key relationships are valid"""
        
        # Setup: Get inspector for database
        inspector = inspect(db_session.bind)
        
        # Execute: Check foreign key relationships
        fk_issues = []
        
        # Define expected foreign key relationships
        expected_fks = [
            ('votes_vote', 'bill_number', 'bills_bill', 'bill_number'),
            ('hansards_statement', 'speaker', 'politicians_politician', 'name'),
            ('committees_committee', 'members', 'politicians_politician', 'id')
        ]
        
        for table_name, fk_column, referenced_table, referenced_column in expected_fks:
            try:
                fks = inspector.get_foreign_keys(table_name)
                found = False
                for fk in fks:
                    if fk_column in fk['constrained_columns'] and fk['referred_table'] == referenced_table:
                        found = True
                        break
                if not found:
                    fk_issues.append(f"Missing FK: {table_name}.{fk_column} -> {referenced_table}.{referenced_column}")
            except Exception as e:
                fk_issues.append(f"Error checking FK {table_name}.{fk_column}: {str(e)}")
        
        # Check for orphaned records (data integrity)
        orphan_checks = [
            """
            SELECT COUNT(*) FROM votes_vote v 
            LEFT JOIN bills_bill b ON v.bill_number = b.bill_number 
            WHERE b.bill_number IS NULL
            """,
            """
            SELECT COUNT(*) FROM hansards_statement h 
            LEFT JOIN politicians_politician p ON h.speaker = p.name 
            WHERE p.name IS NULL
            """
        ]
        
        for check_query in orphan_checks:
            try:
                result = db_session.execute(text(check_query))
                orphan_count = result.fetchone()[0]
                if orphan_count > 0:
                    fk_issues.append(f"Found {orphan_count} orphaned records")
            except Exception as e:
                fk_issues.append(f"Error checking orphaned records: {str(e)}")
        
        # Verify: All foreign keys are valid
        assert len(fk_issues) == 0, f"Foreign key issues found: {fk_issues}"
    
    def test_all_indexes_created(self, db_session):
        """Test that all required indexes are created for performance"""
        
        # Setup: Get inspector for database
        inspector = inspect(db_session.bind)
        
        # Execute: Check indexes for key tables
        missing_indexes = []
        
        # Define required indexes for performance
        required_indexes = {
            'bills_bill': [
                'bill_number',
                'jurisdiction',
                'introduced_date',
                'sponsor'
            ],
            'politicians_politician': [
                'name',
                'jurisdiction',
                'party',
                'constituency'
            ],
            'votes_vote': [
                'bill_number',
                'vote_date',
                'jurisdiction',
                'result'
            ],
            'hansards_statement': [
                'speaker',
                'date',
                'jurisdiction'
            ],
            'committees_committee': [
                'name',
                'jurisdiction'
            ]
        }
        
        for table_name, expected_index_columns in required_indexes.items():
            try:
                indexes = inspector.get_indexes(table_name)
                existing_index_columns = []
                for index in indexes:
                    existing_index_columns.extend(index['column_names'])
                
                for column in expected_index_columns:
                    if column not in existing_index_columns:
                        missing_indexes.append(f"Missing index on {table_name}.{column}")
            except Exception as e:
                missing_indexes.append(f"Error checking indexes on {table_name}: {str(e)}")
        
        # Check for composite indexes
        composite_indexes = [
            ('bills_bill', ['jurisdiction', 'introduced_date']),
            ('votes_vote', ['bill_number', 'vote_date']),
            ('politicians_politician', ['jurisdiction', 'party'])
        ]
        
        for table_name, expected_columns in composite_indexes:
            try:
                indexes = inspector.get_indexes(table_name)
                found = False
                for index in indexes:
                    if set(expected_columns) == set(index['column_names']):
                        found = True
                        break
                if not found:
                    missing_indexes.append(f"Missing composite index on {table_name}: {expected_columns}")
            except Exception as e:
                missing_indexes.append(f"Error checking composite index on {table_name}: {str(e)}")
        
        # Verify: All required indexes exist
        assert len(missing_indexes) == 0, f"Missing indexes: {missing_indexes}"
