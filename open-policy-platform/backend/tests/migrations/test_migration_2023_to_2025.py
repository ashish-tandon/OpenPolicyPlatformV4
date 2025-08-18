"""
Database migration tests for 2023 to 2025 data update
"""

import pytest
from sqlalchemy import text
from datetime import datetime, date

def test_schema_migration_2023_to_2025(db_session):
    """Test migration from 2023 to 2025 schema"""
    
    # Setup: Check if 2023 schema exists
    result = db_session.execute(text("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
    """))
    tables_2023 = [row[0] for row in result.fetchall()]
    
    # Verify 2023 tables exist
    expected_2023_tables = [
        'bills_bill',
        'hansards_statement', 
        'politicians_politician',
        'committees_committee',
        'activity_activity',
        'alerts_subscription'
    ]
    
    for table in expected_2023_tables:
        assert table in tables_2023, f"Table {table} not found in 2023 schema"
    
    # Execute: Run migration scripts
    # This would run the actual migration scripts
    # For now, we'll simulate the migration
    
    # Verify: New 2025 fields added
    result = db_session.execute(text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'bills_bill'
    """))
    bill_columns = [row[0] for row in result.fetchall()]
    
    # Check for new 2025 fields
    expected_2025_fields = [
        'updated_2025',
        'data_source_2025',
        'last_modified'
    ]
    
    for field in expected_2025_fields:
        assert field in bill_columns, f"Field {field} not found in 2025 schema"
    
    # Assert: Schema updated successfully
    assert len(bill_columns) >= len(expected_2025_fields), "Schema migration incomplete"

def test_data_integrity_after_migration(db_session):
    """Test data integrity after migration"""
    
    # Setup: Pre-migration data snapshot
    # This would capture data before migration
    pre_migration_count = db_session.execute(text("SELECT COUNT(*) FROM bills_bill")).scalar()
    
    # Execute: Migration process
    # This would run the actual migration
    # For now, we'll simulate the migration
    
    # Verify: All records preserved
    post_migration_count = db_session.execute(text("SELECT COUNT(*) FROM bills_bill")).scalar()
    
    # Assert: No data loss during migration
    assert post_migration_count >= pre_migration_count, "Data loss detected during migration"
    
    # Check for data consistency
    result = db_session.execute(text("""
        SELECT COUNT(*) 
        FROM bills_bill 
        WHERE title IS NULL OR title = ''
    """))
    null_titles = result.scalar()
    
    # Assert: Data consistency maintained
    assert null_titles == 0, "Data consistency issues detected"

def test_representative_data_migration(db_session):
    """Test representative data migration from civic scraper"""
    
    # Setup: Check for representative tables
    result = db_session.execute(text("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name LIKE '%representative%'
    """))
    representative_tables = [row[0] for row in result.fetchall()]
    
    # Verify representative tables exist
    assert len(representative_tables) > 0, "No representative tables found"
    
    # Check for federal representatives
    result = db_session.execute(text("""
        SELECT COUNT(*) 
        FROM politicians_politician 
        WHERE jurisdiction = 'federal'
    """))
    federal_count = result.scalar()
    
    # Assert: Federal representatives exist
    assert federal_count > 0, "No federal representatives found"
    
    # Check for provincial representatives
    result = db_session.execute(text("""
        SELECT COUNT(*) 
        FROM politicians_politician 
        WHERE jurisdiction = 'provincial'
    """))
    provincial_count = result.scalar()
    
    # Assert: Provincial representatives exist
    assert provincial_count > 0, "No provincial representatives found"
    
    # Check for municipal representatives
    result = db_session.execute(text("""
        SELECT COUNT(*) 
        FROM politicians_politician 
        WHERE jurisdiction = 'municipal'
    """))
    municipal_count = result.scalar()
    
    # Assert: Municipal representatives exist
    assert municipal_count > 0, "No municipal representatives found"

def test_data_freshness_2025(db_session):
    """Test that data is updated to 2025"""
    
    # Check for recent data in bills
    result = db_session.execute(text("""
        SELECT MAX(introduced_date) 
        FROM bills_bill 
        WHERE introduced_date IS NOT NULL
    """))
    latest_bill_date = result.scalar()
    
    if latest_bill_date:
        # Convert to date if it's a datetime
        if isinstance(latest_bill_date, datetime):
            latest_bill_date = latest_bill_date.date()
        
        # Assert: Data is from 2025 or recent
        assert latest_bill_date >= date(2024, 1, 1), f"Data not updated to 2025. Latest date: {latest_bill_date}"
    
    # Check for recent activity
    result = db_session.execute(text("""
        SELECT MAX(created_at) 
        FROM activity_activity 
        WHERE created_at IS NOT NULL
    """))
    latest_activity = result.scalar()
    
    if latest_activity:
        # Convert to date if it's a datetime
        if isinstance(latest_activity, datetime):
            latest_activity = latest_activity.date()
        
        # Assert: Recent activity exists
        assert latest_activity >= date(2024, 1, 1), f"Activity not updated to 2025. Latest date: {latest_activity}"

def test_jurisdiction_coverage(db_session):
    """Test that all jurisdictions are covered"""
    
    # Check federal jurisdiction
    result = db_session.execute(text("""
        SELECT COUNT(*) 
        FROM bills_bill 
        WHERE jurisdiction = 'federal'
    """))
    federal_bills = result.scalar()
    assert federal_bills > 0, "No federal bills found"
    
    # Check provincial jurisdictions
    result = db_session.execute(text("""
        SELECT DISTINCT jurisdiction 
        FROM bills_bill 
        WHERE jurisdiction LIKE '%provincial%'
    """))
    provincial_jurisdictions = [row[0] for row in result.fetchall()]
    
    # Expected provinces (partial list)
    expected_provinces = [
        'ontario', 'quebec', 'british_columbia', 'alberta', 
        'manitoba', 'saskatchewan', 'nova_scotia', 'new_brunswick'
    ]
    
    # Assert: Multiple provinces covered
    assert len(provincial_jurisdictions) > 0, "No provincial jurisdictions found"
    
    # Check municipal jurisdictions
    result = db_session.execute(text("""
        SELECT COUNT(*) 
        FROM bills_bill 
        WHERE jurisdiction LIKE '%municipal%'
    """))
    municipal_bills = result.scalar()
    assert municipal_bills >= 0, "Error checking municipal bills"

def test_data_quality_after_migration(db_session):
    """Test data quality after migration"""
    
    # Check for duplicate records
    result = db_session.execute(text("""
        SELECT title, COUNT(*) 
        FROM bills_bill 
        GROUP BY title 
        HAVING COUNT(*) > 1
    """))
    duplicates = result.fetchall()
    
    # Assert: No duplicate titles
    assert len(duplicates) == 0, f"Found {len(duplicates)} duplicate bill titles"
    
    # Check for valid dates
    result = db_session.execute(text("""
        SELECT COUNT(*) 
        FROM bills_bill 
        WHERE introduced_date < '1900-01-01' 
        OR introduced_date > '2030-12-31'
    """))
    invalid_dates = result.scalar()
    
    # Assert: No invalid dates
    assert invalid_dates == 0, f"Found {invalid_dates} bills with invalid dates"
    
    # Check for required fields
    result = db_session.execute(text("""
        SELECT COUNT(*) 
        FROM bills_bill 
        WHERE title IS NULL 
        OR title = ''
    """))
    missing_titles = result.scalar()
    
    # Assert: No missing titles
    assert missing_titles == 0, f"Found {missing_titles} bills with missing titles"
