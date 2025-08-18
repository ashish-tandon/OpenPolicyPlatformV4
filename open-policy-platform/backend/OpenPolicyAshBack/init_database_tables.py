#!/usr/bin/env python3
"""
Database Table Initialization
============================

This script creates all the database tables based on the SQLAlchemy models.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.database.config import get_database_url
from src.database.models import Base, create_all_tables
from sqlalchemy import create_engine, text

def init_database():
    """Initialize database tables."""
    print("🚀 Initializing database tables...")
    
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
        
        # Create all tables
        print("🔨 Creating database tables...")
        create_all_tables(engine)
        
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
        
        print("🎉 Database initialization completed successfully!")
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        raise

if __name__ == "__main__":
    init_database()
