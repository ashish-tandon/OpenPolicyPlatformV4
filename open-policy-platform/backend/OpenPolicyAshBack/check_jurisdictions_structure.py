#!/usr/bin/env python3

from src.database.config import get_database_url
from sqlalchemy import create_engine, text

def check_jurisdictions_structure():
    """Check the jurisdictions table structure"""
    engine = create_engine(get_database_url())
    
    print("🔍 Checking jurisdictions table structure...")
    
    with engine.connect() as conn:
        # Check if table exists
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'jurisdictions'
            );
        """))
        exists = result.fetchone()[0]
        
        if not exists:
            print("❌ Jurisdictions table does not exist!")
            return
        
        print("✅ Jurisdictions table exists")
        
        # Get table structure
        result = conn.execute(text("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_schema = 'public' AND table_name = 'jurisdictions' 
            ORDER BY ordinal_position;
        """))
        columns = [(row[0], row[1], row[2]) for row in result]
        
        print(f"📊 Jurisdictions table has {len(columns)} columns:")
        for col_name, data_type, is_nullable in columns:
            print(f"  - {col_name}: {data_type} ({'NULL' if is_nullable == 'YES' else 'NOT NULL'})")
        
        # Check for specific columns
        column_names = [col[0] for col in columns]
        
        if 'website' in column_names:
            print("\n✅ Website column exists")
        else:
            print("\n❌ Website column missing")
            
        if 'code' in column_names:
            print("✅ Code column exists")
        else:
            print("❌ Code column missing")

if __name__ == "__main__":
    check_jurisdictions_structure()
