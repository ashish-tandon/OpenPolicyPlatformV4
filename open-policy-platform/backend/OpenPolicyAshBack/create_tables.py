#!/usr/bin/env python3

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.database.config import get_database_url
from src.database.models import Base
from sqlalchemy import create_engine, text

def create_all_tables():
    """Create all database tables"""
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
    
    # Create all tables
    print("🔨 Creating all tables...")
    Base.metadata.create_all(engine)
    
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
        
        print(f"📊 Created {len(tables)} tables:")
        for table in tables:
            print(f"  - {table}")

if __name__ == "__main__":
    create_all_tables()
