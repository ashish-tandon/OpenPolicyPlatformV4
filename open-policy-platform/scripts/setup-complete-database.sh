#!/bin/bash

# Setup complete database schema for OpenPolicyPlatform V4
# This script creates all necessary tables in both test and production databases

set -e

echo "🗄️  OpenPolicyPlatform V4 - Complete Database Setup"
echo "=================================================="

# Database configuration
DB_HOST="localhost"
DB_USER="openpolicy"
DB_PASS="openpolicy123"
TEST_DB="openpolicy_test"
MAIN_DB="openpolicy"
TEST_PORT="5433"
MAIN_PORT="5432"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to execute SQL on a specific database
execute_sql() {
    local port=$1
    local db=$2
    local sql_file=$3
    local description=$4
    
    echo -e "${YELLOW}Setting up $description on $db (port $port)...${NC}"
    
    PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $port -U $DB_USER -d $db -f $sql_file
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ $description setup complete on $db${NC}"
    else
        echo -e "${RED}❌ Failed to setup $description on $db${NC}"
        return 1
    fi
}

# Function to check database connection
check_db_connection() {
    local port=$1
    local db=$2
    
    PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $port -U $DB_USER -d $db -c "SELECT 1" > /dev/null 2>&1
    return $?
}

# Function to count tables
count_tables() {
    local port=$1
    local db=$2
    
    local count=$(PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $port -U $DB_USER -d $db -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';")
    echo $count
}

echo "🔍 Checking database connections..."

# Check test database
if check_db_connection $TEST_PORT $TEST_DB; then
    echo -e "${GREEN}✅ Test database connection successful${NC}"
else
    echo -e "${RED}❌ Cannot connect to test database on port $TEST_PORT${NC}"
    echo "Please ensure PostgreSQL is running and the database exists"
    exit 1
fi

# Check main database
if check_db_connection $MAIN_PORT $MAIN_DB; then
    echo -e "${GREEN}✅ Main database connection successful${NC}"
else
    echo -e "${RED}❌ Cannot connect to main database on port $MAIN_PORT${NC}"
    echo "Please ensure PostgreSQL is running and the database exists"
    exit 1
fi

# Count existing tables before setup
echo ""
echo "📊 Current table count:"
TEST_TABLES_BEFORE=$(count_tables $TEST_PORT $TEST_DB)
MAIN_TABLES_BEFORE=$(count_tables $MAIN_PORT $MAIN_DB)
echo "  Test database: $TEST_TABLES_BEFORE tables"
echo "  Main database: $MAIN_TABLES_BEFORE tables"

# Setup schema files
SCHEMA_DIR="$(dirname "$0")/../database"
SECURITY_SCHEMA="$SCHEMA_DIR/database_security_setup.sql"
COMPLETE_SCHEMA="$SCHEMA_DIR/complete-schema-setup.sql"

# Check if schema files exist
if [ ! -f "$SECURITY_SCHEMA" ]; then
    echo -e "${RED}❌ Security schema file not found: $SECURITY_SCHEMA${NC}"
    exit 1
fi

if [ ! -f "$COMPLETE_SCHEMA" ]; then
    echo -e "${RED}❌ Complete schema file not found: $COMPLETE_SCHEMA${NC}"
    exit 1
fi

echo ""
echo "🚀 Starting database setup..."
echo ""

# Setup test database
echo "=== TEST DATABASE SETUP ==="
execute_sql $TEST_PORT $TEST_DB $SECURITY_SCHEMA "security schema"
execute_sql $TEST_PORT $TEST_DB $COMPLETE_SCHEMA "complete schema"

echo ""
echo "=== MAIN DATABASE SETUP ==="
# Setup main database
execute_sql $MAIN_PORT $MAIN_DB $SECURITY_SCHEMA "security schema"
execute_sql $MAIN_PORT $MAIN_DB $COMPLETE_SCHEMA "complete schema"

# Count tables after setup
echo ""
echo "📊 Final table count:"
TEST_TABLES_AFTER=$(count_tables $TEST_PORT $TEST_DB)
MAIN_TABLES_AFTER=$(count_tables $MAIN_PORT $MAIN_DB)
echo "  Test database: $TEST_TABLES_BEFORE → $TEST_TABLES_AFTER tables"
echo "  Main database: $MAIN_TABLES_BEFORE → $MAIN_TABLES_AFTER tables"

# Create a verification report
echo ""
echo "📋 Creating verification report..."

REPORT_FILE="$SCHEMA_DIR/setup-report-$(date +%Y%m%d-%H%M%S).txt"

cat > $REPORT_FILE << EOF
OpenPolicyPlatform V4 - Database Setup Report
Generated: $(date)

TEST DATABASE ($TEST_DB on port $TEST_PORT):
- Tables before: $TEST_TABLES_BEFORE
- Tables after: $TEST_TABLES_AFTER
- New tables created: $((TEST_TABLES_AFTER - TEST_TABLES_BEFORE))

MAIN DATABASE ($MAIN_DB on port $MAIN_PORT):
- Tables before: $MAIN_TABLES_BEFORE
- Tables after: $MAIN_TABLES_AFTER
- New tables created: $((MAIN_TABLES_AFTER - MAIN_TABLES_BEFORE))

TABLES CREATED:
EOF

# List all tables in the report
PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $TEST_PORT -U $DB_USER -d $TEST_DB -t -c "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE' ORDER BY table_name;" >> $REPORT_FILE

echo -e "${GREEN}✅ Report saved to: $REPORT_FILE${NC}"

# Test scraper table access
echo ""
echo "🧪 Testing scraper table access..."

# Test inserting a scraper run
PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $TEST_PORT -U $DB_USER -d $TEST_DB << EOF
INSERT INTO scraper_runs (scraper_name, run_type, status) 
VALUES ('test_scraper', 'manual', 'completed')
RETURNING id;
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Scraper tables are accessible and working${NC}"
else
    echo -e "${RED}❌ Failed to access scraper tables${NC}"
fi

echo ""
echo "🎉 Database setup complete!"
echo ""
echo "Next steps:"
echo "1. Review the setup report: $REPORT_FILE"
echo "2. Test scrapers can write to the test database (port $TEST_PORT)"
echo "3. Validate data quality before migrating to main database (port $MAIN_PORT)"
echo "4. Run scrapers with: ./scripts/run-scrapers.sh"
echo ""
echo "Database access:"
echo "  Test: psql -h localhost -p $TEST_PORT -U $DB_USER -d $TEST_DB"
echo "  Main: psql -h localhost -p $MAIN_PORT -U $DB_USER -d $MAIN_DB"