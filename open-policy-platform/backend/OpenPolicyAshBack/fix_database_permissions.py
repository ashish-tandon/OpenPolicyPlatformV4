#!/usr/bin/env python3

from src.database.config import get_database_url
from sqlalchemy import create_engine, text

def fix_database_permissions():
    """Fix database permissions and add missing columns"""
    engine = create_engine(get_database_url())
    
    print("🔧 Fixing database permissions and adding missing columns...")
    
    try:
        with engine.connect() as conn:
            # First, let's check what user we are
            print("🔍 Checking current user...")
            result = conn.execute(text("SELECT current_user;"))
            current_user = result.fetchone()[0]
            print(f"📊 Current user: {current_user}")
            
            # Check if we're a superuser
            result = conn.execute(text("SELECT rolname, rolsuper FROM pg_roles WHERE rolname = current_user;"))
            user_info = result.fetchone()
            if user_info and user_info[1]:
                print("✅ User has superuser privileges")
            else:
                print("⚠️ User does not have superuser privileges")
            
            # Check if the jurisdictions table exists
            print("\n🔍 Checking jurisdictions table...")
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'jurisdictions'
                );
            """))
            table_exists = result.fetchone()[0]
            
            if not table_exists:
                print("❌ Jurisdictions table does not exist!")
                return
            
            print("✅ Jurisdictions table exists")
            
            # Check current table structure
            print("\n📊 Current table structure:")
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_schema = 'public' AND table_name = 'jurisdictions' 
                ORDER BY ordinal_position;
            """))
            columns = [(row[0], row[1], row[2]) for row in result]
            
            for col_name, data_type, is_nullable in columns:
                print(f"  - {col_name}: {data_type} ({'NULL' if is_nullable == 'YES' else 'NOT NULL'})")
            
            # Check if code column already exists
            code_column = [col for col in columns if col[0] == 'code']
            if code_column:
                print("\n✅ Code column already exists!")
                return
            
            # Try to add the code column with proper error handling
            print("\n🔧 Adding code column...")
            try:
                # First try to add the column without constraints
                conn.execute(text("""
                    ALTER TABLE jurisdictions 
                    ADD COLUMN code VARCHAR(50);
                """))
                print("✅ Code column added successfully!")
                
                # Now try to add the unique constraint
                try:
                    conn.execute(text("""
                        ALTER TABLE jurisdictions 
                        ADD CONSTRAINT jurisdictions_code_unique UNIQUE (code);
                    """))
                    print("✅ Unique constraint added successfully!")
                except Exception as e:
                    print(f"⚠️ Could not add unique constraint: {e}")
                
                # Now try to add NOT NULL constraint
                try:
                    conn.execute(text("""
                        ALTER TABLE jurisdictions 
                        ALTER COLUMN code SET NOT NULL;
                    """))
                    print("✅ NOT NULL constraint added successfully!")
                except Exception as e:
                    print(f"⚠️ Could not add NOT NULL constraint: {e}")
                
                conn.commit()
                
            except Exception as e:
                print(f"❌ Error adding code column: {e}")
                # Try alternative approach - check if we can at least add the column
                try:
                    conn.execute(text("""
                        ALTER TABLE jurisdictions 
                        ADD COLUMN IF NOT EXISTS code VARCHAR(50);
                    """))
                    conn.commit()
                    print("✅ Code column added using IF NOT EXISTS!")
                except Exception as e2:
                    print(f"❌ Alternative approach also failed: {e2}")
                    return
            
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
        print(f"❌ Error fixing database permissions: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_database_permissions()
