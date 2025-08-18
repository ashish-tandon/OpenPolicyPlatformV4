#!/bin/bash

# Open Policy Platform V4 - Database Import Script for Azure
# Imports database from local export to Azure Database for PostgreSQL

set -e

# Configuration
IMPORT_FILE="$1"
AZURE_HOST="$2"
AZURE_DB="openpolicy"
AZURE_USER="openpolicy"
AZURE_PASSWORD="$3"

if [ -z "$IMPORT_FILE" ] || [ -z "$AZURE_HOST" ] || [ -z "$AZURE_PASSWORD" ]; then
    echo "❌ Error: Missing required parameters"
    echo "Usage: $0 <path_to_sql_file> <azure_host> <azure_password>"
    echo ""
    echo "Example:"
    echo "  $0 ./database-exports/full_database_20240818_123456.sql your-server.postgres.database.azure.com your_password"
    echo ""
    echo "Available export files:"
    ls -la ./database-exports/*.sql 2>/dev/null || echo "No export files found. Run export-database.sh first."
    exit 1
fi

if [ ! -f "$IMPORT_FILE" ]; then
    echo "❌ Error: Import file not found: $IMPORT_FILE"
    exit 1
fi

echo "🗄️  Open Policy Platform V4 - Database Import to Azure"
echo "========================================================"
echo "📁 Import file: $IMPORT_FILE"
echo "☁️  Azure host: $AZURE_HOST"
echo "🗃️  Database: $AZURE_DB"
echo "👤 User: $AZURE_USER"

# Check if psql is available
if ! command -v psql &> /dev/null; then
    echo "❌ Error: psql command not found"
    echo "Please install PostgreSQL client tools:"
    echo "  macOS: brew install postgresql"
    echo "  Ubuntu: sudo apt-get install postgresql-client"
    echo "  Windows: Download from https://www.postgresql.org/download/windows/"
    exit 1
fi

# Confirm import
echo ""
read -p "⚠️  This will overwrite the existing database. Continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Import cancelled"
    exit 1
fi

echo ""
echo "🔄 Starting database import to Azure..."

# Test connection first
echo "🔌 Testing Azure connection..."
if ! psql "host=$AZURE_HOST port=5432 dbname=postgres user=$AZURE_USER password=$AZURE_PASSWORD sslmode=require" -c "SELECT 1;" > /dev/null 2>&1; then
    echo "❌ Error: Cannot connect to Azure PostgreSQL"
    echo "Please check:"
    echo "  - Host: $AZURE_HOST"
    echo "  - Username: $AZURE_USER"
    echo "  - Password: $AZURE_PASSWORD"
    echo "  - Firewall rules allow your IP"
    echo "  - SSL is enabled"
    exit 1
fi

echo "✅ Azure connection successful!"

# Create database if it doesn't exist
echo "📋 Creating database if it doesn't exist..."
psql "host=$AZURE_HOST port=5432 dbname=postgres user=$AZURE_USER password=$AZURE_PASSWORD sslmode=require" -c "CREATE DATABASE $AZURE_DB;" 2>/dev/null || echo "Database already exists"

# Import the SQL file
echo "📥 Importing database from $IMPORT_FILE..."
psql "host=$AZURE_HOST port=5432 dbname=$AZURE_DB user=$AZURE_USER password=$AZURE_PASSWORD sslmode=require" < "$IMPORT_FILE"

echo ""
echo "✅ Database import completed successfully!"
echo "☁️  Azure host: $AZURE_HOST"
echo "🗃️  Database: $AZURE_DB"

# Verify import
echo ""
echo "🔍 Verifying import..."
psql "host=$AZURE_HOST port=5432 dbname=$AZURE_DB user=$AZURE_USER password=$AZURE_PASSWORD sslmode=require" -c "\dt" | head -20

echo ""
echo "🎯 Next steps:"
echo "1. Verify all tables were imported correctly"
echo "2. Check data integrity"
echo "3. Test platform functionality"
echo "4. Monitor performance"
echo "5. Update Azure environment variables with new connection details"
