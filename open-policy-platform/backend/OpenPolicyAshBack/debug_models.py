#!/usr/bin/env python3

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.database.models import Base

def debug_models():
    """Debug the models to see what tables are defined"""
    print("🔍 Debugging SQLAlchemy models...")
    
    # Check what tables are defined in Base
    tables = Base.metadata.tables
    
    print(f"📊 Found {len(tables)} tables defined in Base:")
    for table_name in sorted(tables.keys()):
        print(f"  - {table_name}")
        
        # Show columns for each table
        table = tables[table_name]
        print(f"    Columns:")
        for column in table.columns:
            print(f"      - {column.name}: {column.type}")
    
    # Check if Jurisdiction table is defined
    if 'jurisdictions' in tables:
        print("\n✅ 'jurisdictions' table is defined in Base.metadata.")
    else:
        print("\n❌ 'jurisdictions' table is NOT defined in Base.metadata.")

if __name__ == "__main__":
    debug_models()
