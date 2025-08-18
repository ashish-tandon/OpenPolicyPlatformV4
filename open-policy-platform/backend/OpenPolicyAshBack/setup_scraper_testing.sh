#!/bin/bash
# Setup Script for Scraper Testing Environment
# ===========================================
# This script sets up the environment for testing scrapers
# with centralized dependency management

set -e  # Exit on any error

echo "🚀 Setting up Scraper Testing Environment"
echo "========================================"

# Check Python version
if command -v python3 &> /dev/null; then
    echo "✅ Python 3 found: $(python3 --version)"
else
    echo "❌ Python 3 not found. Please install Python 3.8+"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "🔧 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Find the centralized requirements.txt file
REQUIREMENTS_FILE=""
if [ -f "../../requirements.txt" ]; then
    REQUIREMENTS_FILE="../../requirements.txt"
elif [ -f "../requirements.txt" ]; then
    REQUIREMENTS_FILE="../requirements.txt"
elif [ -f "requirements.txt" ]; then
    REQUIREMENTS_FILE="requirements.txt"
else
    echo "❌ No requirements.txt found. Creating basic requirements..."
    cat > requirements.txt << EOF
# Core Framework
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
sqlalchemy>=2.0.0
psycopg2-binary>=2.9.0

# Scraping & Data Collection
requests>=2.31.0
beautifulsoup4>=4.12.0
pupa>=2.4.0
opencivicdata>=3.0.0

# Testing
pytest>=7.4.0
pytest-asyncio>=0.21.0

# Utilities
python-dotenv>=1.0.0
psutil>=5.9.0
EOF
    REQUIREMENTS_FILE="requirements.txt"
fi

echo "📥 Installing dependencies from $REQUIREMENTS_FILE..."

# Install core dependencies (excluding optional sections)
if [ -f "$REQUIREMENTS_FILE" ]; then
    # Extract core dependencies (before [dev] and [prod] sections)
    grep -v '^\[dev\]\|^\[prod\]' "$REQUIREMENTS_FILE" | grep -v '^#' | grep -v '^$' > temp_requirements.txt
    pip install -r temp_requirements.txt
    rm temp_requirements.txt
else
    echo "❌ Requirements file not found"
    exit 1
fi

# Install specific scraper dependencies
echo "📥 Installing scraper-specific dependencies..."
pip install pupa opencivicdata

# Install additional testing dependencies
echo "📥 Installing testing dependencies..."
pip install pytest pytest-asyncio pytest-cov psutil

# Check database connectivity
echo "🔍 Checking database connectivity..."
if [ -z "$DATABASE_URL" ]; then
    echo "⚠️  DATABASE_URL not set. Using default..."
    export DATABASE_URL="postgresql://user:pass@localhost/openpolicy"
fi

# Test database connection
python3 -c "
import os
import sys
try:
    import psycopg2
    print('✅ psycopg2 installed successfully')
except ImportError:
    print('❌ psycopg2 not installed')
    sys.exit(1)

try:
    import sqlalchemy
    print('✅ sqlalchemy installed successfully')
except ImportError:
    print('❌ sqlalchemy not installed')
    sys.exit(1)

try:
    import requests
    print('✅ requests installed successfully')
except ImportError:
    print('❌ requests not installed')
    sys.exit(1)

try:
    import pupa
    print('✅ pupa installed successfully')
except ImportError:
    print('❌ pupa not installed')
    sys.exit(1)

print('✅ All core dependencies installed successfully')
"

echo ""
echo "🎉 Environment setup complete!"
echo ""
echo "📋 Next steps:"
echo "  1. Configure your DATABASE_URL environment variable"
echo "  2. Run: python3 scraper_testing_framework.py"
echo "  3. Or run: ./quick_start_scrapers.sh"
echo ""
echo "🔧 Available commands:"
echo "  - python3 scraper_testing_framework.py          # Run comprehensive scraper testing"
echo "  - python3 run_scraper_tests.py                  # Run quick scraper tests"
echo "  - python3 scraper_monitoring_system.py          # Start background monitoring"
echo ""
