#!/usr/bin/env python3
"""
Fix Database Configuration Script
Resolves database connection issues for testing
"""

import os
import sys
import subprocess
import psycopg2
from sqlalchemy import create_engine, text

def check_database_connection():
    """Check if we can connect to the main database"""
    try:
        # Try connecting with openpolicy user
        conn = psycopg2.connect(
            host="localhost",
            port="5432",
            database="openpolicy",
            user="openpolicy",
            password="openpolicy123"
        )
        print("✅ Successfully connected to main database")
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Failed to connect to main database: {e}")
        return False

def create_test_database():
    """Create test database if it doesn't exist"""
    try:
        # Connect to postgres database to create test database
        conn = psycopg2.connect(
            host="localhost",
            port="5432",
            database="postgres",
            user="openpolicy",
            password="openpolicy123"
        )
        
        cursor = conn.cursor()
        
        # Check if test database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'openpolicy_test'")
        exists = cursor.fetchone()
        
        if not exists:
            print("📝 Creating test database...")
            cursor.execute("CREATE DATABASE openpolicy_test")
            conn.commit()
            print("✅ Test database created successfully")
        else:
            print("✅ Test database already exists")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Failed to create test database: {e}")
        return False

def test_database_connection():
    """Test connection to test database"""
    try:
        conn = psycopg2.connect(
            host="localhost",
            port="5432",
            database="openpolicy_test",
            user="openpolicy",
            password="openpolicy123"
        )
        print("✅ Successfully connected to test database")
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Failed to connect to test database: {e}")
        return False

def update_test_configuration():
    """Update test configuration files to use correct database"""
    print("📝 Updating test configuration...")
    
    # Update conftest.py
    conftest_path = "tests/conftest.py"
    if os.path.exists(conftest_path):
        with open(conftest_path, 'r') as f:
            content = f.read()
        
        # Replace database URL
        content = content.replace(
            'TEST_DATABASE_URL = "postgresql://postgres@localhost:5432/openpolicy_test"',
            'TEST_DATABASE_URL = "postgresql://openpolicy:openpolicy123@localhost:5432/openpolicy_test"'
        )
        
        with open(conftest_path, 'w') as f:
            f.write(content)
        
        print("✅ Updated tests/conftest.py")
    
    # Update any other test configuration files
    test_configs = [
        "tests/database/test_schema_validation.py",
        "tests/database/test_enhanced_schema_validation.py"
    ]
    
    for config_file in test_configs:
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                content = f.read()
            
            # Replace any postgres user references
            content = content.replace(
                'user="postgres"',
                'user="openpolicy"'
            )
            content = content.replace(
                'password="postgres"',
                'password="openpolicy123"'
            )
            
            with open(config_file, 'w') as f:
                f.write(content)
            
            print(f"✅ Updated {config_file}")

def create_coverage_config():
    """Create .coveragerc file for test coverage"""
    print("📝 Creating coverage configuration...")
    
    coverage_config = """[run]
source = api,config,models,services,scripts
omit = 
    */tests/*
    */venv/*
    */__pycache__/*
    */migrations/*
    */alembic/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    if self.debug:
    if settings.DEBUG
    raise AssertionError
    raise NotImplementedError
    if 0:
    if __name__ == .__main__.:
    class .*\\bProtocol\\):
    @(abc\\.)?abstractmethod

[html]
directory = reports/htmlcov

[xml]
output = reports/coverage.xml
"""
    
    with open(".coveragerc", 'w') as f:
        f.write(coverage_config)
    
    print("✅ Created .coveragerc file")

def setup_test_directories():
    """Create test report directories"""
    print("📝 Setting up test directories...")
    
    directories = [
        "reports",
        "reports/coverage",
        "reports/test-results",
        "reports/performance",
        "reports/accessibility",
        "reports/htmlcov"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Created {directory}")

def verify_api_server():
    """Verify API server is running"""
    print("📝 Checking API server status...")
    
    try:
        import requests
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ API server is running and responding")
            return True
        else:
            print(f"⚠️ API server responded with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API server not responding: {e}")
        print("💡 Start API server with: python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload")
        return False

def main():
    """Main function to fix database configuration"""
    print("🔧 FIXING DATABASE CONFIGURATION")
    print("=" * 50)
    
    # Step 1: Check main database connection
    if not check_database_connection():
        print("❌ Cannot proceed without main database connection")
        return False
    
    # Step 2: Create test database
    if not create_test_database():
        print("❌ Cannot proceed without test database")
        return False
    
    # Step 3: Test test database connection
    if not test_database_connection():
        print("❌ Cannot proceed without test database connection")
        return False
    
    # Step 4: Update test configuration
    update_test_configuration()
    
    # Step 5: Create coverage configuration
    create_coverage_config()
    
    # Step 6: Setup test directories
    setup_test_directories()
    
    # Step 7: Verify API server
    verify_api_server()
    
    print("\n✅ DATABASE CONFIGURATION FIXED!")
    print("📊 Next steps:")
    print("  1. Start API server if not running")
    print("  2. Run tests: python -m pytest tests/ -v")
    print("  3. Check coverage: python -m pytest tests/ --cov=api --cov-report=html")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
