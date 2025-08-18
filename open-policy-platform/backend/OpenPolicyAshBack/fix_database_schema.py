#!/usr/bin/env python3
"""
Fix Database Schema
==================

This script directly creates all database tables using Base.metadata.create_all
to ensure all tables are properly created.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.database.config import get_database_url
from src.database.models import Base
from sqlalchemy import create_engine, text

def fix_database_schema():
    """Fix the database schema by creating all tables"""
    print("🔧 Fixing database schema...")
    
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
        
        # Create all tables (without dropping existing ones)
        print("🔨 Creating all tables...")
        Base.metadata.create_all(engine)
        
        # Verify tables were created
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """))
            tables = [row[0] for row in result.fetchall()]
            
            print("✅ Database tables created:")
            for table in tables:
                print(f"   - {table}")
        
        # Check jurisdictions table specifically
        print("\n🔍 Checking jurisdictions table structure:")
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'jurisdictions' 
                ORDER BY ordinal_position;
            """))
            columns = [(row[0], row[1], row[2]) for row in result.fetchall()]
            
            for col_name, data_type, is_nullable in columns:
                print(f"   - {col_name}: {data_type} ({'NULL' if is_nullable == 'YES' else 'NOT NULL'})")
        
        print("🎉 Database schema fixed successfully!")
        
    except Exception as e:
        print(f"❌ Error fixing database schema: {e}")
        raise

if __name__ == "__main__":
    fix_database_schema()
