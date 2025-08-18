#!/usr/bin/env python3
"""Test database connection"""

from sqlalchemy import text
from src.database.config import engine

print("Testing database connection...")
try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("✅ Database connection successful!")
except Exception as e:
    print(f"❌ Database connection failed: {e}")
