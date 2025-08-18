#!/usr/bin/env python3

from src.database.config import get_database_url
from sqlalchemy import create_engine, text

def add_code_column():
    """Add the missing code column to the jurisdictions table"""
    engine = create_engine(get_database_url())
    
    print("🔧 Adding code column to jurisdictions table...")
    
    try:
        with engine.connect() as conn:
            # Add the code column
            print("📝 Adding code column...")
            conn.execute(text("""
                ALTER TABLE jurisdictions 
                ADD COLUMN code VARCHAR(50) UNIQUE;
            """))
            
            # Add NOT NULL constraint after adding the column
            print("📝 Adding NOT NULL constraint...")
            conn.execute(text("""
                ALTER TABLE jurisdictions 
                ALTER COLUMN code SET NOT NULL;
            """))
            
            conn.commit()
            print("✅ Code column added successfully!")
            
            # Verify the column was added
            print("\n🔍 Verifying jurisdictions table structure:")
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
                print("\n✅ Code column successfully added!")
            else:
                print("\n❌ Code column still missing!")
                
    except Exception as e:
        print(f"❌ Error adding code column: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    add_code_column()
