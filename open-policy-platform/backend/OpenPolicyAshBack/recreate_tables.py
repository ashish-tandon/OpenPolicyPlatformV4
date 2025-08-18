#!/usr/bin/env python3

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.database.config import get_database_url
from src.database.models import create_all_tables
from sqlalchemy import create_engine, text

def recreate_all_tables():
    """Create all database tables using the models function"""
    print("🔧 Creating all database tables...")
    
    # Get database URL
    database_url = get_database_url()
    print(f"📊 Database URL: {database_url}")
    
    # Create engine
    engine = create_engine(database_url)
    
    # Test connection
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("✅ Database connection successful")
    
    # Create all tables using the function from models
    print("🔨 Creating all tables...")
    create_all_tables(engine)
    
    print("✅ All tables created successfully!")
    
    # Verify tables were created
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """))
        tables = [row[0] for row in result]
        
        print(f"📊 Found {len(tables)} tables:")
        for table in tables:
            print(f"  - {table}")
        
        # Check jurisdictions table specifically
        if 'jurisdictions' in tables:
            print("\n✅ Jurisdictions table exists!")
            
            # Check its structure
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_schema = 'public' AND table_name = 'jurisdictions' 
                ORDER BY ordinal_position;
            """))
            columns = [(row[0], row[1], row[2]) for row in result]
            
            print(f"📊 Jurisdictions table columns ({len(columns)} total):")
            for col_name, data_type, is_nullable in columns:
                print(f"  - {col_name}: {data_type} ({'NULL' if is_nullable == 'YES' else 'NOT NULL'})")
        else:
            print("\n❌ Jurisdictions table was not created!")

if __name__ == "__main__":
    recreate_all_tables()
