#!/usr/bin/env python3

from src.database.config import get_database_url
from sqlalchemy import create_engine, text

def check_all_schemas():
    """Check all schemas for the jurisdictions table"""
    print("🔍 Checking all schemas for jurisdictions table...")
    
    engine = create_engine(get_database_url())
    
    with engine.connect() as conn:
        # Check all schemas
        result = conn.execute(text("""
            SELECT schemaname, tablename 
            FROM pg_tables 
            WHERE tablename = 'jurisdictions'
            ORDER BY schemaname;
        """))
        jurisdictions = [(row[0], row[1]) for row in result]
        
        if jurisdictions:
            print("✅ Jurisdictions table found in:")
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
            
            # Check what schemas exist
            result = conn.execute(text("""
                SELECT DISTINCT schemaname 
                FROM pg_tables 
                WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
                ORDER BY schemaname;
            """))
            schemas = [row[0] for row in result]
            
            print(f"📊 Available schemas: {schemas}")
            
            # Check what tables exist in each schema
            for schema in schemas:
                result = conn.execute(text(f"""
                    SELECT tablename 
                    FROM pg_tables 
                    WHERE schemaname = '{schema}'
                    ORDER BY tablename;
                """))
                tables = [row[0] for row in result]
                
                print(f"📊 Tables in {schema}: {tables}")

if __name__ == "__main__":
    check_all_schemas()
