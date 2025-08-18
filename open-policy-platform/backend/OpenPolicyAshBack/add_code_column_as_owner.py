#!/usr/bin/env python3

import os
from sqlalchemy import create_engine, text

def add_code_column_as_owner():
    """Add the missing code column to the jurisdictions table as the owner"""
    
    # Connect as the owner (ashishtandon) - no password needed for local connections
    database_url = "postgresql://ashishtandon@localhost:5432/openpolicy"
    engine = create_engine(database_url)
    
    print("🔧 Adding code column to jurisdictions table as owner...")
    
    try:
        with engine.connect() as conn:
            # Check if column already exists
            print("🔍 Checking if code column already exists...")
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = 'jurisdictions' 
                AND column_name = 'code';
            """))
            
            if result.fetchone():
                print("✅ Code column already exists!")
                return
            
            # Add the code column
            print("📝 Adding code column...")
            conn.execute(text("""
                ALTER TABLE jurisdictions 
                ADD COLUMN code VARCHAR(50);
            """))
            
            # Populate existing rows with unique codes
            print("📝 Populating existing rows with unique codes...")
            
            # First, get all jurisdictions
            result = conn.execute(text("SELECT id, name FROM jurisdictions ORDER BY name"))
            jurisdictions = result.fetchall()
            
            # Create unique codes for each jurisdiction
            used_codes = set()
            for jurisdiction_id, name in jurisdictions:
                # Generate base code
                base_code = name.lower().replace(' ', '_').replace(',', '').replace('.', '').replace('-', '_')
                
                # Make it unique
                code = base_code
                counter = 1
                while code in used_codes:
                    code = f"{base_code}_{counter}"
                    counter += 1
                
                used_codes.add(code)
                
                # Update the jurisdiction
                conn.execute(text("""
                    UPDATE jurisdictions 
                    SET code = :code
                    WHERE id = :id
                """), {"code": code, "id": jurisdiction_id})
                
                print(f"  - {name}: {code}")
            
            # Add unique constraint
            print("📝 Adding unique constraint...")
            try:
                conn.execute(text("""
                    ALTER TABLE jurisdictions 
                    ADD CONSTRAINT jurisdictions_code_unique UNIQUE (code);
                """))
                print("✅ Unique constraint added successfully!")
            except Exception as e:
                print(f"⚠️ Could not add unique constraint: {e}")
            
            # Add NOT NULL constraint
            print("📝 Adding NOT NULL constraint...")
            try:
                conn.execute(text("""
                    ALTER TABLE jurisdictions 
                    ALTER COLUMN code SET NOT NULL;
                """))
                print("✅ NOT NULL constraint added successfully!")
            except Exception as e:
                print(f"⚠️ Could not add NOT NULL constraint: {e}")
            
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
                
                # Show some sample data
                print("\n📊 Sample jurisdictions with codes:")
                result = conn.execute(text("""
                    SELECT name, code 
                    FROM jurisdictions 
                    LIMIT 5;
                """))
                for row in result:
                    print(f"  - {row[0]}: {row[1]}")
            else:
                print("\n❌ Code column still missing!")
                
    except Exception as e:
        print(f"❌ Error adding code column: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    add_code_column_as_owner()
