#!/usr/bin/env python3

from src.database.config import get_database_url
from sqlalchemy import create_engine, text

def check_jurisdictions_table():
    """Check the jurisdictions table structure"""
    engine = create_engine(get_database_url())
    
    print("🔍 Checking jurisdictions table structure...")
    
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_schema = 'public' AND table_name = 'jurisdictions' 
            ORDER BY ordinal_position;
        """))
        columns = [(row[0], row[1], row[2]) for row in result]
        
        print("📊 Jurisdictions table columns:")
        for col_name, data_type, is_nullable in columns:
            print(f"  - {col_name}: {data_type} ({'NULL' if is_nullable == 'YES' else 'NOT NULL'})")
        
        # Check if code column exists
        code_column = [col for col in columns if col[0] == 'code']
        if code_column:
            print("\n✅ Code column exists!")
        else:
            print("\n❌ Code column missing!")

if __name__ == "__main__":
    check_jurisdictions_table()
