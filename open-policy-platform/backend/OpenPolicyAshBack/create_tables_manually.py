#!/usr/bin/env python3

from src.database.config import get_database_url
from sqlalchemy import create_engine, text

def create_tables_manually():
    """Create tables manually using SQL"""
    print("🔧 Creating tables manually...")
    
    # Get database URL
    database_url = get_database_url()
    print(f"📊 Database URL: {database_url}")
    
    # Create engine
    engine = create_engine(database_url)
    
    # Test connection
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("✅ Database connection successful")
    
    # Create jurisdictions table manually
    print("🔨 Creating jurisdictions table...")
    
    create_jurisdictions_sql = """
    CREATE TABLE IF NOT EXISTS jurisdictions (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        name VARCHAR(255) NOT NULL,
        jurisdiction_type VARCHAR(10) NOT NULL,
        website VARCHAR(500),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    try:
        with engine.connect() as conn:
            conn.execute(text(create_jurisdictions_sql))
            conn.commit()
            print("✅ Jurisdictions table created successfully!")
    except Exception as e:
        print(f"❌ Error creating jurisdictions table: {e}")
        return
    
    # Create representatives table
    print("🔨 Creating representatives table...")
    
    create_representatives_sql = """
    CREATE TABLE IF NOT EXISTS representatives (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        jurisdiction_id UUID NOT NULL REFERENCES jurisdictions(id),
        name VARCHAR(255) NOT NULL,
        role VARCHAR(14) NOT NULL,
        party VARCHAR(255),
        riding VARCHAR(255),
        email VARCHAR(255),
        phone VARCHAR(50),
        website VARCHAR(500),
        bio TEXT,
        image_url VARCHAR(500),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    try:
        with engine.connect() as conn:
            conn.execute(text(create_representatives_sql))
            conn.commit()
            print("✅ Representatives table created successfully!")
    except Exception as e:
        print(f"❌ Error creating representatives table: {e}")
    
    # Verify tables were created
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """))
        tables = [row[0] for row in result]
        
        print(f"\n📊 Found {len(tables)} tables:")
        for table in tables:
            print(f"  - {table}")
        
        # Check jurisdictions table structure
        if 'jurisdictions' in tables:
            print("\n✅ Jurisdictions table exists!")
            
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
    create_tables_manually()
