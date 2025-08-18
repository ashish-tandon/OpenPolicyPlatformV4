#!/usr/bin/env python3

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.database.config import get_database_url
from src.database.models import Base, Jurisdiction
from sqlalchemy import create_engine, text

def test_table_creation():
    """Test table creation directly"""
    print("🧪 Testing table creation...")
    
    try:
        # Get database URL
        database_url = get_database_url()
        print(f"📊 Database URL: {database_url}")
        
        # Create engine
        engine = create_engine(database_url)
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ Database connection successful")
        
        # Check what tables exist before
        print("\n📋 Tables before creation:")
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """))
            tables = [row[0] for row in result.fetchall()]
            for table in tables:
                print(f"  - {table}")
        
        # Try to create the jurisdictions table with explicit SQL
        print("\n🔨 Creating jurisdictions table with explicit SQL...")
        create_sql = """
        CREATE TABLE IF NOT EXISTS jurisdictions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(255) NOT NULL,
            jurisdiction_type VARCHAR(10) NOT NULL,
            code VARCHAR(50) UNIQUE NOT NULL,
            website VARCHAR(500),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        try:
            with engine.connect() as conn:
                conn.execute(text(create_sql))
                conn.commit()
                print("✅ Jurisdictions table created successfully!")
        except Exception as e:
            print(f"❌ Error creating jurisdictions table: {e}")
        
        # Check what tables exist after
        print("\n📋 Tables after creation:")
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """))
            tables = [row[0] for row in result.fetchall()]
            for table in tables:
                print(f"  - {table}")
        
        # Check jurisdictions table structure
        if 'jurisdictions' in tables:
            print("\n🔍 Jurisdictions table structure:")
            with engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT column_name, data_type, is_nullable 
                    FROM information_schema.columns 
                    WHERE table_name = 'jurisdictions' 
                    ORDER BY ordinal_position;
                """))
                columns = [(row[0], row[1], row[2]) for row in result.fetchall()]
                
                for col_name, data_type, is_nullable in columns:
                    print(f"  - {col_name}: {data_type} ({'NULL' if is_nullable == 'YES' else 'NOT NULL'})")
        else:
            print("\n❌ Jurisdictions table was not created!")
        
    except Exception as e:
        print(f"❌ Error testing table creation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_table_creation()
