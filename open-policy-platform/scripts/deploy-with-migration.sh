#!/bin/bash

# OpenPolicy Merge - Deployment with Migration Script
# This script deploys the platform with 2023 to 2025 data migration

set -e  # Exit on any error

echo "🚀 OpenPolicy Merge - Deployment with Migration"
echo "==============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Check prerequisites
check_prerequisites() {
    print_status "Checking deployment prerequisites..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        exit 1
    fi
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        print_error "Node.js is not installed"
        exit 1
    fi
    
    # Check PostgreSQL
    if ! command -v psql &> /dev/null; then
        print_error "PostgreSQL is not installed"
        exit 1
    fi
    
    # Check if PostgreSQL is running
    if ! pg_isready -q; then
        print_error "PostgreSQL is not running"
        exit 1
    fi
    
    # Check Docker (optional)
    if ! command -v docker &> /dev/null; then
        print_warning "Docker not found - will use local deployment"
    fi
    
    print_success "Prerequisites check completed"
}

# Setup database
setup_database() {
    print_status "Setting up database..."
    
    # Check if database exists
    if psql -lqt | cut -d \| -f 1 | grep -qw openpolicy; then
        print_warning "Database 'openpolicy' already exists"
        read -p "Do you want to recreate it? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            dropdb openpolicy
            createdb openpolicy
            print_success "Database recreated"
        else
            print_status "Using existing database"
        fi
    else
        createdb openpolicy
        print_success "Database created"
    fi
    
    # Import initial data if available
    if [ -f "openparliament.public.sql" ]; then
        print_status "Importing initial database dump..."
        psql openpolicy < openparliament.public.sql
        print_success "Initial data imported"
    else
        print_warning "No initial database dump found"
    fi
}

# Setup backend
setup_backend() {
    print_status "Setting up backend..."
    
    cd backend
    
    # Create virtual environment
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        print_success "Virtual environment created"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install dependencies
    pip install -r requirements.txt
    print_success "Backend dependencies installed"
    
    # Create .env file if it doesn't exist
    if [ ! -f ".env" ]; then
        cp ../env.example .env
        print_success "Environment file created"
    fi
    
    cd ..
}

# Run database migration
run_migration() {
    print_status "Running 2023 to 2025 database migration..."
    
    cd backend
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Run migration script
    python scripts/migrate_2023_to_2025.py
    
    cd ..
    
    print_success "Database migration completed"
}

# Setup scrapers
setup_scrapers() {
    print_status "Setting up scrapers..."
    
    cd backend
    source venv/bin/activate
    
    # Test scrapers
    print_status "Testing federal scraper..."
    python -c "
from scrapers.federal_parliament_scraper import FederalParliamentScraper
scraper = FederalParliamentScraper()
data = scraper.scrape_all()
print(f'Federal scraper test: {len(data[\"bills\"])} bills, {len(data[\"mps\"])} MPs')
"
    
    cd ..
    
    print_success "Scrapers setup completed"
}

# Setup web application
setup_web() {
    print_status "Setting up web application..."
    
    cd web
    
    # Install dependencies
    if [ ! -d "node_modules" ]; then
        npm install
        print_success "Web dependencies installed"
    fi
    
    # Create .env file if it doesn't exist
    if [ ! -f ".env" ]; then
        cp ../env.example .env
        print_success "Web environment file created"
    fi
    
    cd ..
}

# Run tests
run_tests() {
    print_status "Running comprehensive tests..."
    
    # Run test script
    ./scripts/run-tests.sh
    
    print_success "Tests completed"
}

# Start services
start_services() {
    print_status "Starting services..."
    
    # Start backend
    print_status "Starting backend..."
    cd backend
    source venv/bin/activate
    cd api
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
    BACKEND_PID=$!
    cd ../..
    
    # Wait for backend to start
    sleep 5
    
    # Start web application
    print_status "Starting web application..."
    cd web
    npm run dev &
    WEB_PID=$!
    cd ..
    
    print_success "Services started"
    echo ""
    echo "🎉 Deployment completed successfully!"
    echo "====================================="
    echo ""
    echo "📊 Services:"
    echo "  - Backend API: http://localhost:8000"
    echo "  - API Documentation: http://localhost:8000/docs"
    echo "  - Web Interface: http://localhost:5173"
    echo "  - Admin Interface: http://localhost:5173/admin"
    echo ""
    echo "🔧 Management:"
    echo "  - Backend PID: $BACKEND_PID"
    echo "  - Web PID: $WEB_PID"
    echo "  - To stop: kill $BACKEND_PID $WEB_PID"
    echo ""
    echo "📋 Test Results:"
    echo "  - Database migration: ✅"
    echo "  - Scraper setup: ✅"
    echo "  - API tests: ✅"
    echo "  - Integration tests: ✅"
    echo ""
    echo "🚀 Platform ready for use!"
}

# Main deployment function
main() {
    echo "Starting OpenPolicy Merge deployment with migration..."
    echo ""
    
    check_prerequisites
    setup_database
    setup_backend
    run_migration
    setup_scrapers
    setup_web
    run_tests
    start_services
}

# Run main function
main "$@"
