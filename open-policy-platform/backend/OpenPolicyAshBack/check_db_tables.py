#!/usr/bin/env python3

from src.database.config import get_database_url
from sqlalchemy import create_engine, text

def check_database_tables():
    """Check what tables exist in the database"""
    engine = create_engine(get_database_url())
    
    print("🔍 Checking database tables...")
    
    with engine.connect() as conn:
        # Get all tables from all schemas
        result = conn.execute(text("""
            SELECT schemaname, tablename 
            FROM pg_tables 
            WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
            ORDER BY schemaname, tablename;
        """))
        tables = [(row[0], row[1]) for row in result]
        
        print(f"📊 Found {len(tables)} tables:")
        for schema, table in tables:
            print(f"  - {schema}.{table}")
        
        # Check jurisdictions table specifically
        print("\n🔍 Checking for jurisdictions table:")
        result = conn.execute(text("""
            SELECT schemaname, tablename 
            FROM pg_tables 
            WHERE tablename = 'jurisdictions';
        """))
        jurisdictions = [(row[0], row[1]) for row in result]
        
        if jurisdictions:
            print("✅ Jurisdictions table found:")
            for schema, table in jurisdictions:
                print(f"  - {schema}.{table}")
                
                # Check table structure
                result = conn.execute(text(f"""
                    SELECT column_name, data_type, is_nullable 
                    FROM information_schema.columns 
                    WHERE table_schema = '{schema}' AND table_name = '{table}'
                    ORDER BY ordinal_position;
                """))
                columns = [(row[0], row[1], row[2]) for row in result]
                
                print(f"    Columns:")
                for col_name, data_type, is_nullable in columns:
                    print(f"      - {col_name}: {data_type} ({'NULL' if is_nullable == 'YES' else 'NOT NULL'})")
        else:
            print("❌ Jurisdictions table not found in any schema!")
            
            # Check if there are any tables with similar names
            result = conn.execute(text("""
                SELECT schemaname, tablename 
                FROM pg_tables 
                WHERE tablename LIKE '%jurisdiction%';
            """))
            similar = [(row[0], row[1]) for row in result]
            
            if similar:
                print("🔍 Found similar tables:")
                for schema, table in similar:
                    print(f"  - {schema}.{table}")

if __name__ == "__main__":
    check_database_tables()
