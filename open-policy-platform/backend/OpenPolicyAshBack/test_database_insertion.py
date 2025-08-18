#!/usr/bin/env python3
"""
Test Database Insertion Script
==============================

This script tests the database insertion functionality to ensure that
the collected data can be properly stored in the database.
"""

import os
import sys
from datetime import datetime
from typing import Dict, List, Optional

# Add project paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scrapers'))

from src.database.models import (
    Base, Jurisdiction, Representative, JurisdictionType, RepresentativeRole
)
from src.database.config import get_database_url, SessionLocal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def test_database_insertion():
    """Test database insertion with sample data"""
    
    # Get database URL
    database_url = get_database_url()
    print(f"🔗 Database URL: {database_url}")
    
    try:
        # Create engine and session
        engine = create_engine(database_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = SessionLocal()
        
        print("✅ Database connection successful")
        
        # Test jurisdiction creation
        test_jurisdiction = Jurisdiction(
            name="Test City, ON",
            jurisdiction_type=JurisdictionType.MUNICIPAL
        )
        
        # Check if jurisdiction already exists
        existing_jurisdiction = session.query(Jurisdiction).filter(
            Jurisdiction.name == "Test City, ON"
        ).first()
        
        if existing_jurisdiction:
            print(f"✅ Found existing jurisdiction: {existing_jurisdiction.name}")
            jurisdiction = existing_jurisdiction
        else:
            session.add(test_jurisdiction)
            session.flush()
            print(f"✅ Created new jurisdiction: {test_jurisdiction.name}")
            jurisdiction = test_jurisdiction
        
        # Test representative creation
        test_representative = Representative(
            jurisdiction_id=jurisdiction.id,
            name="John Doe",
            role=RepresentativeRole.COUNCILLOR,
            party="Independent",
            riding="Ward 1",
            email="john.doe@testcity.ca",
            phone="555-1234",
            bio="Test representative for database insertion testing",
            image_url="https://example.com/photo.jpg"
        )
        
        session.add(test_representative)
        session.commit()
        
        print(f"✅ Successfully inserted test representative: {test_representative.name}")
        
        # Query to verify insertion
        representative = session.query(Representative).filter(
            Representative.name == "John Doe"
        ).first()
        
        if representative:
            print(f"✅ Verified representative in database: {representative.name} ({representative.role.value})")
            print(f"   Jurisdiction: {jurisdiction.name}")
            print(f"   Party: {representative.party}")
            print(f"   Riding: {representative.riding}")
            print(f"   Email: {representative.email}")
        else:
            print("❌ Failed to find inserted representative")
        
        session.close()
        return True
        
    except Exception as e:
        print(f"❌ Database insertion test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Testing Database Insertion...")
    success = test_database_insertion()
    
    if success:
        print("\n✅ Database insertion test completed successfully!")
    else:
        print("\n❌ Database insertion test failed!")
        sys.exit(1)
