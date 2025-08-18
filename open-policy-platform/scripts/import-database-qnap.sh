#!/bin/bash

# Open Policy Platform V4 - Database Import Script for QNAP
# Imports database from local export to QNAP

set -e

# Configuration
QNAP_CONTAINER="openpolicy-qnap-postgres"
DB_NAME="openpolicy"
DB_USER="openpolicy"
IMPORT_FILE="$1"

if [ -z "$IMPORT_FILE" ]; then
    echo "❌ Error: Please specify the import file"
    echo "Usage: $0 <path_to_sql_file>"
    echo ""
    echo "Available export files:"
    ls -la ./database-exports/*.sql 2>/dev/null || echo "No export files found. Run export-database.sh first."
    exit 1
fi

if [ ! -f "$IMPORT_FILE" ]; then
    echo "❌ Error: Import file not found: $IMPORT_FILE"
    exit 1
fi

echo "🗄️  Open Policy Platform V4 - Database Import to QNAP"
echo "========================================================"
echo "📁 Import file: $IMPORT_FILE"
echo "🐳 QNAP container: $QNAP_CONTAINER"
echo "🗃️  Database: $DB_NAME"
echo "👤 User: $DB_USER"

# Check if QNAP container is running
if ! docker ps | grep -q "$QNAP_CONTAINER"; then
    echo "❌ Error: QNAP PostgreSQL container is not running"
    echo "Please start QNAP deployment first: ./deploy-qnap.sh"
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
echo "🔄 Starting database import..."

# Create database if it doesn't exist
echo "📋 Creating database if it doesn't exist..."
docker exec "$QNAP_CONTAINER" createdb -U "$DB_USER" "$DB_NAME" 2>/dev/null || echo "Database already exists"

# Import the SQL file
echo "📥 Importing database from $IMPORT_FILE..."
docker exec -i "$QNAP_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" < "$IMPORT_FILE"

echo ""
echo "✅ Database import completed successfully!"
echo "🗃️  Database: $DB_NAME"
echo "🐳 Container: $QNAP_CONTAINER"

# Verify import
echo ""
echo "🔍 Verifying import..."
docker exec "$QNAP_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -c "\dt" | head -20

echo ""
echo "🎯 Next steps:"
echo "1. Verify all tables were imported correctly"
echo "2. Check data integrity"
echo "3. Test platform functionality"
echo "4. Monitor performance"
