#!/bin/bash

# ========================================
# DUAL DATABASE MIGRATION SCRIPT
# ========================================
# This script migrates data from the old database to the new dual-database setup:
# - postgres-test:5433 (for scraper validation)
# - postgres:5432 (for production data)
# ========================================

set -e

echo "🗄️  DUAL DATABASE MIGRATION STARTING..."
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
check_docker() {
    print_status "Checking Docker status..."
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker Desktop first."
        exit 1
    fi
    print_success "Docker is running"
}

# Check if old database exists and has data
check_old_database() {
    print_status "Checking for existing database data..."
    
    # Check if there's a large SQL file
    if [ -f "openparliament.public.sql" ]; then
        OLD_DB_SIZE=$(du -h openparliament.public.sql | cut -f1)
        print_success "Found existing database dump: openparliament.public.sql (${OLD_DB_SIZE})"
        return 0
    fi
    
    # Check if there are other database files
    if [ -f "*.sql" ]; then
        print_success "Found SQL files for migration"
        return 0
    fi
    
    print_warning "No existing database files found. Starting with fresh databases."
    return 1
}

# Start the dual database setup
start_databases() {
    print_status "Starting dual database setup..."
    
    # Start only the database services first
    docker-compose -f docker-compose.complete.yml up -d postgres-test postgres redis
    
    print_status "Waiting for databases to be ready..."
    sleep 15
    
    # Check database health
    if docker exec open-policy-platform-postgres-test-1 pg_isready -U openpolicy -d openpolicy_test; then
        print_success "Test database is ready"
    else
        print_error "Test database failed to start"
        exit 1
    fi
    
    if docker exec open-policy-platform-postgres-1 pg_isready -U openpolicy -d openpolicy; then
        print_success "Main database is ready"
    else
        print_error "Main database failed to start"
        exit 1
    fi
}

# Create database schemas
create_schemas() {
    print_status "Creating database schemas..."
    
    # Test database schema
    docker exec open-policy-platform-postgres-test-1 psql -U openpolicy -d openpolicy_test -c "
        CREATE SCHEMA IF NOT EXISTS public;
        CREATE SCHEMA IF NOT EXISTS scrapers;
        CREATE SCHEMA IF NOT EXISTS analytics;
        CREATE SCHEMA IF NOT EXISTS policies;
        CREATE SCHEMA IF NOT EXISTS users;
        CREATE SCHEMA IF NOT EXISTS audit;
    "
    
    # Main database schema
    docker exec open-policy-platform-postgres-1 psql -U openpolicy -d openpolicy -c "
        CREATE SCHEMA IF NOT EXISTS public;
        CREATE SCHEMA IF NOT EXISTS scrapers;
        CREATE SCHEMA IF NOT EXISTS analytics;
        CREATE SCHEMA IF NOT EXISTS policies;
        CREATE SCHEMA IF NOT EXISTS users;
        CREATE SCHEMA IF NOT EXISTS audit;
    "
    
    print_success "Database schemas created"
}

# Migrate data from old database
migrate_data() {
    print_status "Starting data migration..."
    
    if [ -f "openparliament.public.sql" ]; then
        print_status "Migrating data from openparliament.public.sql..."
        
        # First, migrate to test database for validation
        print_status "Migrating to TEST database for validation..."
        docker exec -i open-policy-platform-postgres-test-1 psql -U openpolicy -d openpolicy_test < openparliament.public.sql
        
        # Check migration success
        TEST_TABLES=$(docker exec open-policy-platform-postgres-test-1 psql -U openpolicy -d openpolicy_test -t -c "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';")
        print_success "Test database now has ${TEST_TABLES} tables"
        
        # Show table list
        print_status "Tables in test database:"
        docker exec open-policy-platform-postgres-test-1 psql -U openpolicy -d openpolicy_test -c "\dt"
        
        # Ask user if migration was successful
        echo ""
        read -p "✅ Does the test database migration look correct? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_status "Migrating to MAIN database..."
            docker exec -i open-policy-platform-postgres-1 psql -U openpolicy -d openpolicy < openparliament.public.sql
            
            MAIN_TABLES=$(docker exec open-policy-platform-postgres-1 psql -U openpolicy -d openpolicy -t -c "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';")
            print_success "Main database now has ${MAIN_TABLES} tables"
        else
            print_warning "Migration to main database skipped. Please verify test database first."
        fi
    else
        print_warning "No existing database file found. Starting with empty databases."
    fi
}

# Create data validation tables
create_validation_tables() {
    print_status "Creating data validation tables..."
    
    # Test database validation tables
    docker exec open-policy-platform-postgres-test-1 psql -U openpolicy -d openpolicy_test -c "
        -- Scraper validation table
        CREATE TABLE IF NOT EXISTS scraper_validations (
            id SERIAL PRIMARY KEY,
            scraper_name VARCHAR(255) NOT NULL,
            run_id VARCHAR(255),
            validation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_quality_score INTEGER CHECK (data_quality_score >= 0 AND data_quality_score <= 100),
            record_count INTEGER,
            error_count INTEGER,
            validation_status VARCHAR(50) DEFAULT 'pending',
            validation_notes TEXT,
            validated_by VARCHAR(255),
            approved_for_production BOOLEAN DEFAULT FALSE
        );
        
        -- Data quality metrics
        CREATE TABLE IF NOT EXISTS data_quality_metrics (
            id SERIAL PRIMARY KEY,
            table_name VARCHAR(255) NOT NULL,
            column_name VARCHAR(255),
            metric_type VARCHAR(100),
            metric_value NUMERIC,
            threshold_value NUMERIC,
            is_acceptable BOOLEAN,
            check_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Migration audit log
        CREATE TABLE IF NOT EXISTS migration_audit (
            id SERIAL PRIMARY KEY,
            migration_type VARCHAR(100),
            source_database VARCHAR(255),
            target_database VARCHAR(255),
            table_count INTEGER,
            record_count BIGINT,
            start_time TIMESTAMP,
            end_time TIMESTAMP,
            status VARCHAR(50),
            error_message TEXT
        );
    "
    
    print_success "Validation tables created in test database"
}

# Start all services
start_all_services() {
    print_status "Starting all Open Policy Platform services..."
    
    docker-compose -f docker-compose.complete.yml up -d
    
    print_status "Waiting for all services to start..."
    sleep 30
    
    # Check service health
    print_status "Checking service health..."
    docker-compose -f docker-compose.complete.yml ps
    
    print_success "All services started"
}

# Test scraper functionality
test_scrapers() {
    print_status "Testing scraper functionality..."
    
    # Wait for scraper service to be ready
    sleep 10
    
    # Test scraper health
    if curl -s http://localhost:9008/health | grep -q "healthy"; then
        print_success "Scraper service is healthy"
    else
        print_error "Scraper service health check failed"
        return 1
    fi
    
    # Test database connectivity
    print_status "Testing database connectivity..."
    
    # Test database connection from scraper service
    if docker exec open-policy-platform-scraper-service-1 curl -s http://localhost:9008/health | grep -q "healthy"; then
        print_success "Scraper can connect to test database"
    else
        print_warning "Scraper database connectivity needs verification"
    fi
}

# Show final status
show_final_status() {
    echo ""
    echo "========================================"
    echo "🗄️  DUAL DATABASE MIGRATION COMPLETE"
    echo "========================================"
    echo ""
    echo "✅ DATABASES:"
    echo "   - Test Database: localhost:5433 (openpolicy_test)"
    echo "   - Main Database: localhost:5432 (openpolicy)"
    echo ""
    echo "🔗 CONNECTION STRINGS:"
    echo "   - Test: postgresql://openpolicy:openpolicy123@localhost:5433/openpolicy_test"
    echo "   - Main: postgresql://openpolicy:openpolicy123@localhost:5432/openpolicy"
    echo ""
    echo "🌐 ACCESS POINTS:"
    echo "   - Web Interface: http://localhost:3000"
    echo "   - API Gateway: http://localhost:9000"
    echo "   - Kibana: http://localhost:5601"
    echo "   - Grafana: http://localhost:3001"
    echo ""
    echo "📊 NEXT STEPS:"
    echo "   1. Verify data in test database"
    echo "   2. Run scrapers to test data flow"
    echo "   3. Validate data quality"
    echo "   4. Approve for production migration"
    echo ""
}

# Main execution
main() {
    echo "🚀 Starting Open Policy Platform Dual Database Migration..."
    echo "========================================"
    
    check_docker
    check_old_database
    start_databases
    create_schemas
    migrate_data
    create_validation_tables
    start_all_services
    test_scrapers
    show_final_status
    
    print_success "Migration completed successfully!"
}

# Run main function
main "$@"
