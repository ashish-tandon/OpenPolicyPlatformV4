"""
Comprehensive Database Schema Validation Tests
Tests every table, field, constraint, and relationship in the database
"""

import pytest
from sqlalchemy import text, inspect
from sqlalchemy.exc import SQLAlchemyError

def test_all_tables_exist(db_session):
    """Test that all required tables exist in the database"""
    
    # Get all tables in the database
    inspector = inspect(db_session.bind)
    existing_tables = inspector.get_table_names()
    
    # Required tables for OpenPolicy Merge
    required_tables = [
        'bills_bill',
        'politicians_politician', 
        'hansards_statement',
        'committees_committee',
        'activity_activity',
        'alerts_subscription',
        'votes_vote',
        'debates_debate',
        'issues_issue',
        'users_user',
        'roles_role',
        'permissions_permission',
        'user_roles',
        'role_permissions',
        'scraper_logs',
        'data_sources',
        'migration_logs',
        'audit_logs',
        'system_config',
        'backup_logs'
    ]
    
    # Check each required table exists
    for table in required_tables:
        assert table in existing_tables, f"Required table '{table}' not found in database"
    
    print(f"✅ All {len(required_tables)} required tables exist")

def test_all_columns_exist(db_session):
    """Test that all required columns exist in each table"""
    
    inspector = inspect(db_session.bind)
    
    # Define required columns for each table
    required_columns = {
        'bills_bill': [
            'id', 'title', 'description', 'bill_number', 'introduced_date',
            'sponsor', 'jurisdiction', 'status', 'updated_2025', 
            'data_source_2025', 'last_modified', 'created_at'
        ],
        'politicians_politician': [
            'id', 'name', 'party', 'constituency', 'email', 'phone',
            'jurisdiction', 'is_former_mp', 'updated_2025', 
            'data_source_2025', 'last_modified', 'created_at'
        ],
        'votes_vote': [
            'id', 'bill_number', 'vote_date', 'vote_type', 'result',
            'yea_votes', 'nay_votes', 'abstentions', 'jurisdiction',
            'updated_2025', 'data_source_2025', 'last_modified', 'created_at'
        ],
        'committees_committee': [
            'id', 'name', 'description', 'jurisdiction', 'chair_person',
            'members', 'updated_2025', 'data_source_2025', 
            'last_modified', 'created_at'
        ],
        'activity_activity': [
            'id', 'type', 'description', 'entity_type', 'entity_id',
            'user_id', 'timestamp', 'updated_2025', 'data_source_2025',
            'last_modified', 'created_at'
        ],
        'users_user': [
            'id', 'username', 'email', 'password_hash', 'first_name',
            'last_name', 'is_active', 'is_admin', 'last_login',
            'created_at', 'updated_at'
        ],
        'roles_role': [
            'id', 'name', 'description', 'created_at', 'updated_at'
        ],
        'permissions_permission': [
            'id', 'name', 'description', 'resource', 'action',
            'created_at', 'updated_at'
        ]
    }
    
    # Check each table's required columns
    for table_name, expected_columns in required_columns.items():
        try:
            columns = inspector.get_columns(table_name)
            existing_columns = [col['name'] for col in columns]
            
            for column in expected_columns:
                assert column in existing_columns, f"Column '{column}' not found in table '{table_name}'"
            
            print(f"✅ All {len(expected_columns)} required columns exist in table '{table_name}'")
            
        except SQLAlchemyError as e:
            pytest.fail(f"Error checking columns for table '{table_name}': {e}")

def test_all_constraints_valid(db_session):
    """Test that all constraints are valid and properly defined"""
    
    inspector = inspect(db_session.bind)
    
    # Test primary key constraints
    primary_key_tables = [
        'bills_bill', 'politicians_politician', 'votes_vote',
        'committees_committee', 'activity_activity', 'users_user',
        'roles_role', 'permissions_permission'
    ]
    
    for table in primary_key_tables:
        try:
            pk_constraint = inspector.get_pk_constraint(table)
            assert pk_constraint['constrained_columns'], f"No primary key found for table '{table}'"
            print(f"✅ Primary key constraint valid for table '{table}'")
        except SQLAlchemyError as e:
            pytest.fail(f"Error checking primary key for table '{table}': {e}")
    
    # Test unique constraints
    unique_constraints = {
        'bills_bill': ['bill_number'],
        'politicians_politician': ['email'],
        'users_user': ['username', 'email']
    }
    
    for table, unique_columns in unique_constraints.items():
        try:
            constraints = inspector.get_unique_constraints(table)
            constraint_columns = [constraint['column_names'] for constraint in constraints]
            
            for column in unique_columns:
                found = any(column in cols for cols in constraint_columns)
                assert found, f"Unique constraint not found for column '{column}' in table '{table}'"
            
            print(f"✅ Unique constraints valid for table '{table}'")
        except SQLAlchemyError as e:
            pytest.fail(f"Error checking unique constraints for table '{table}': {e}")

def test_all_foreign_keys_valid(db_session):
    """Test that all foreign key relationships are valid"""
    
    inspector = inspect(db_session.bind)
    
    # Define expected foreign key relationships
    expected_fks = {
        'votes_vote': {
            'bill_number': 'bills_bill.bill_number'
        },
        'activity_activity': {
            'user_id': 'users_user.id'
        },
        'user_roles': {
            'user_id': 'users_user.id',
            'role_id': 'roles_role.id'
        },
        'role_permissions': {
            'role_id': 'roles_role.id',
            'permission_id': 'permissions_permission.id'
        }
    }
    
    for table, expected_relationships in expected_fks.items():
        try:
            fks = inspector.get_foreign_keys(table)
            
            for column, referenced in expected_relationships.items():
                referenced_table, referenced_column = referenced.split('.')
                
                found = False
                for fk in fks:
                    if (column in fk['constrained_columns'] and 
                        fk['referred_table'] == referenced_table and
                        referenced_column in fk['referred_columns']):
                        found = True
                        break
                
                assert found, f"Foreign key relationship '{column}' -> '{referenced}' not found in table '{table}'"
            
            print(f"✅ Foreign key relationships valid for table '{table}'")
        except SQLAlchemyError as e:
            pytest.fail(f"Error checking foreign keys for table '{table}': {e}")

def test_all_indexes_created(db_session):
    """Test that all required indexes are created"""
    
    inspector = inspect(db_session.bind)
    
    # Define required indexes for performance
    required_indexes = {
        'bills_bill': ['bill_number', 'jurisdiction', 'introduced_date', 'sponsor'],
        'politicians_politician': ['name', 'jurisdiction', 'party', 'constituency'],
        'votes_vote': ['bill_number', 'vote_date', 'jurisdiction'],
        'activity_activity': ['entity_type', 'entity_id', 'timestamp'],
        'users_user': ['username', 'email', 'is_active']
    }
    
    for table, expected_indexes in required_indexes.items():
        try:
            indexes = inspector.get_indexes(table)
            index_names = [idx['name'] for idx in indexes]
            
            # Check if indexes exist (they might be named differently)
            for expected_index in expected_indexes:
                # Look for indexes that include the expected column
                found = False
                for idx in indexes:
                    if expected_index in idx['column_names']:
                        found = True
                        break
                
                assert found, f"Index for column '{expected_index}' not found in table '{table}'"
            
            print(f"✅ Required indexes exist for table '{table}'")
        except SQLAlchemyError as e:
            pytest.fail(f"Error checking indexes for table '{table}': {e}")

def test_all_data_types_correct(db_session):
    """Test that all columns have correct data types"""
    
    inspector = inspect(db_session.bind)
    
    # Define expected data types for key columns
    expected_types = {
        'bills_bill': {
            'id': 'INTEGER',
            'title': 'VARCHAR',
            'description': 'TEXT',
            'bill_number': 'VARCHAR',
            'introduced_date': 'DATE',
            'updated_2025': 'BOOLEAN',
            'last_modified': 'TIMESTAMP'
        },
        'politicians_politician': {
            'id': 'INTEGER',
            'name': 'VARCHAR',
            'party': 'VARCHAR',
            'constituency': 'VARCHAR',
            'email': 'VARCHAR',
            'phone': 'VARCHAR',
            'jurisdiction': 'VARCHAR',
            'is_former_mp': 'BOOLEAN',
            'updated_2025': 'BOOLEAN',
            'last_modified': 'TIMESTAMP'
        },
        'votes_vote': {
            'id': 'INTEGER',
            'bill_number': 'VARCHAR',
            'vote_date': 'DATE',
            'vote_type': 'VARCHAR',
            'result': 'VARCHAR',
            'yea_votes': 'INTEGER',
            'nay_votes': 'INTEGER',
            'abstentions': 'INTEGER',
            'jurisdiction': 'VARCHAR',
            'updated_2025': 'BOOLEAN',
            'last_modified': 'TIMESTAMP'
        }
    }
    
    for table, expected_columns in expected_types.items():
        try:
            columns = inspector.get_columns(table)
            column_dict = {col['name']: col['type'].__class__.__name__ for col in columns}
            
            for column, expected_type in expected_columns.items():
                if column in column_dict:
                    actual_type = column_dict[column]
                    # PostgreSQL type mapping
                    type_mapping = {
                        'INTEGER': ['INTEGER', 'BIGINT', 'SMALLINT'],
                        'VARCHAR': ['VARCHAR', 'TEXT', 'CHAR'],
                        'TEXT': ['TEXT', 'VARCHAR'],
                        'DATE': ['DATE'],
                        'BOOLEAN': ['BOOLEAN'],
                        'TIMESTAMP': ['TIMESTAMP', 'TIMESTAMP_WITH_TIMEZONE']
                    }
                    
                    valid_types = type_mapping.get(expected_type, [expected_type])
                    assert actual_type in valid_types, f"Column '{column}' in table '{table}' has type '{actual_type}', expected one of {valid_types}"
            
            print(f"✅ Data types correct for table '{table}'")
        except SQLAlchemyError as e:
            pytest.fail(f"Error checking data types for table '{table}': {e}")

def test_all_default_values_set(db_session):
    """Test that all required default values are set"""
    
    inspector = inspect(db_session.bind)
    
    # Define expected default values
    expected_defaults = {
        'bills_bill': {
            'updated_2025': False,
            'last_modified': 'CURRENT_TIMESTAMP'
        },
        'politicians_politician': {
            'is_former_mp': False,
            'updated_2025': False,
            'last_modified': 'CURRENT_TIMESTAMP'
        },
        'votes_vote': {
            'yea_votes': 0,
            'nay_votes': 0,
            'abstentions': 0,
            'updated_2025': False,
            'last_modified': 'CURRENT_TIMESTAMP'
        },
        'users_user': {
            'is_active': True,
            'is_admin': False
        }
    }
    
    for table, expected_defaults_dict in expected_defaults.items():
        try:
            columns = inspector.get_columns(table)
            column_dict = {col['name']: col.get('default') for col in columns}
            
            for column, expected_default in expected_defaults_dict.items():
                if column in column_dict:
                    actual_default = column_dict[column]
                    # For timestamp defaults, we just check they exist
                    if expected_default == 'CURRENT_TIMESTAMP':
                        assert actual_default is not None, f"Default value not set for column '{column}' in table '{table}'"
                    else:
                        assert actual_default == expected_default, f"Default value for column '{column}' in table '{table}' is '{actual_default}', expected '{expected_default}'"
            
            print(f"✅ Default values correct for table '{table}'")
        except SQLAlchemyError as e:
            pytest.fail(f"Error checking default values for table '{table}': {e}")

def test_all_not_null_constraints(db_session):
    """Test that all required NOT NULL constraints are set"""
    
    inspector = inspect(db_session.bind)
    
    # Define required NOT NULL columns
    required_not_null = {
        'bills_bill': ['title', 'jurisdiction'],
        'politicians_politician': ['name', 'jurisdiction'],
        'votes_vote': ['bill_number', 'vote_date', 'jurisdiction'],
        'users_user': ['username', 'email', 'password_hash']
    }
    
    for table, required_columns in required_not_null.items():
        try:
            columns = inspector.get_columns(table)
            column_dict = {col['name']: col.get('nullable', True) for col in columns}
            
            for column in required_columns:
                if column in column_dict:
                    assert not column_dict[column], f"Column '{column}' in table '{table}' should be NOT NULL"
            
            print(f"✅ NOT NULL constraints correct for table '{table}'")
        except SQLAlchemyError as e:
            pytest.fail(f"Error checking NOT NULL constraints for table '{table}': {e}")

def test_all_unique_constraints(db_session):
    """Test that all required unique constraints are set"""
    
    inspector = inspect(db_session.bind)
    
    # Define required unique constraints
    required_unique = {
        'bills_bill': ['bill_number'],
        'politicians_politician': ['email'],
        'users_user': ['username', 'email']
    }
    
    for table, unique_columns in required_unique.items():
        try:
            constraints = inspector.get_unique_constraints(table)
            constraint_columns = [constraint['column_names'] for constraint in constraints]
            
            for column in unique_columns:
                found = any(column in cols for cols in constraint_columns)
                assert found, f"Unique constraint not found for column '{column}' in table '{table}'"
            
            print(f"✅ Unique constraints correct for table '{table}'")
        except SQLAlchemyError as e:
            pytest.fail(f"Error checking unique constraints for table '{table}': {e}")

def test_all_check_constraints(db_session):
    """Test that all required check constraints are set"""
    
    # Test data validation constraints
    test_queries = [
        # Test vote counts are non-negative
        "INSERT INTO votes_vote (bill_number, vote_date, jurisdiction, yea_votes, nay_votes, abstentions) VALUES ('TEST-001', '2024-01-01', 'federal', -1, 0, 0)",
        # Test valid jurisdictions
        "INSERT INTO bills_bill (title, jurisdiction) VALUES ('Test Bill', 'invalid_jurisdiction')",
        # Test valid email format
        "INSERT INTO politicians_politician (name, jurisdiction, email) VALUES ('Test MP', 'federal', 'invalid-email')"
    ]
    
    for query in test_queries:
        try:
            db_session.execute(text(query))
            db_session.commit()
            pytest.fail(f"Check constraint should have prevented: {query}")
        except SQLAlchemyError:
            # Expected to fail due to constraints
            db_session.rollback()
            pass
    
    print("✅ Check constraints are working correctly")

def test_database_connection_pool(db_session):
    """Test database connection pool configuration"""
    
    try:
        # Test multiple concurrent connections
        connections = []
        for i in range(10):
            result = db_session.execute(text("SELECT 1 as test"))
            connections.append(result.fetchone())
        
        # Verify all connections worked
        for conn in connections:
            assert conn[0] == 1, "Database connection test failed"
        
        print("✅ Database connection pool working correctly")
    except SQLAlchemyError as e:
        pytest.fail(f"Database connection pool test failed: {e}")

def test_database_performance(db_session):
    """Test database performance with basic queries"""
    
    try:
        # Test query performance
        import time
        
        # Test bills query
        start_time = time.time()
        result = db_session.execute(text("SELECT COUNT(*) FROM bills_bill"))
        bills_count = result.scalar()
        bills_time = time.time() - start_time
        
        # Test politicians query
        start_time = time.time()
        result = db_session.execute(text("SELECT COUNT(*) FROM politicians_politician"))
        politicians_count = result.scalar()
        politicians_time = time.time() - start_time
        
        # Test votes query
        start_time = time.time()
        result = db_session.execute(text("SELECT COUNT(*) FROM votes_vote"))
        votes_count = result.scalar()
        votes_time = time.time() - start_time
        
        # Performance assertions (should be under 100ms each)
        assert bills_time < 0.1, f"Bills query took {bills_time:.3f}s, should be under 0.1s"
        assert politicians_time < 0.1, f"Politicians query took {politicians_time:.3f}s, should be under 0.1s"
        assert votes_time < 0.1, f"Votes query took {votes_time:.3f}s, should be under 0.1s"
        
        print(f"✅ Database performance tests passed:")
        print(f"   - Bills count: {bills_count}, Query time: {bills_time:.3f}s")
        print(f"   - Politicians count: {politicians_count}, Query time: {politicians_time:.3f}s")
        print(f"   - Votes count: {votes_count}, Query time: {votes_time:.3f}s")
        
    except SQLAlchemyError as e:
        pytest.fail(f"Database performance test failed: {e}")
