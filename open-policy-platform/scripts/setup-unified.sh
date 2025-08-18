#!/bin/bash

# Open Policy Platform - Unified Setup Script
# This script sets up the entire unified platform

set -e  # Exit on any error

echo "🚀 Open Policy Platform - Unified Setup"
echo "======================================"

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
    print_status "Checking prerequisites..."
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        print_error "Node.js is not installed. Please install Node.js v18+"
        exit 1
    fi
    
    NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
    if [ "$NODE_VERSION" -lt 18 ]; then
        print_error "Node.js version 18+ is required. Current version: $(node -v)"
        exit 1
    fi
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed. Please install Python 3.8+"
        exit 1
    fi
    
    # Check PostgreSQL
    if ! command -v psql &> /dev/null; then
        print_error "PostgreSQL is not installed. Please install PostgreSQL"
        exit 1
    fi
    
    # Check if PostgreSQL is running
    if ! pg_isready -q; then
        print_error "PostgreSQL is not running. Please start PostgreSQL service"
        exit 1
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
            print_status "Dropping existing database..."
            dropdb openpolicy
        else
            print_status "Using existing database"
            return
        fi
    fi
    
    # Create database
    print_status "Creating database..."
    createdb openpolicy
    
    # Check if database dump exists
    if [ -f "openparliament.public.sql" ]; then
        print_status "Importing database dump (this may take a while)..."
        psql openpolicy < openparliament.public.sql
        print_success "Database import completed"
    else
        print_warning "Database dump not found. Creating empty database."
    fi
}

# Setup backend
setup_backend() {
    print_status "Setting up unified backend..."
    
    cd backend
    
    # Create virtual environment
    if [ ! -d "venv" ]; then
        print_status "Creating Python virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install dependencies
    print_status "Installing Python dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # Create .env file
    if [ ! -f ".env" ]; then
        print_status "Creating backend environment file..."
        cat > .env << EOF
# Database Configuration
DATABASE_URL=postgresql://postgres@localhost:5432/openpolicy
REDIS_URL=redis://localhost:6379

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

# Security
SECRET_KEY=your-secret-key-change-in-production
ALLOWED_HOSTS=localhost,127.0.0.1

# External Services
OPENAI_API_KEY=your-openai-api-key-here

# Logging
LOG_LEVEL=INFO
EOF
        print_success "Created backend .env file"
    fi
    
    cd ..
    print_success "Backend setup completed"
}

# Setup web application
setup_web() {
    print_status "Setting up unified web application..."
    
    cd web
    
    # Install dependencies
    print_status "Installing Node.js dependencies..."
    npm install
    
    # Create .env file
    if [ ! -f ".env" ]; then
        print_status "Creating web environment file..."
        cat > .env << EOF
# API Configuration
VITE_API_URL=http://localhost:8000
VITE_ENVIRONMENT=development

# Feature Flags
VITE_ENABLE_ANALYTICS=false
VITE_ENABLE_DEBUG=true
EOF
        print_success "Created web .env file"
    fi
    
    cd ..
    print_success "Web application setup completed"
}

# Setup mobile (preserved for future)
setup_mobile() {
    print_status "Setting up mobile application (preserved for future development)..."
    
    # Create mobile directory structure
    mkdir -p mobile
    
    # Copy existing mobile apps
    if [ -d "apps/open-policy-main" ]; then
        cp -r apps/open-policy-main mobile/
    fi
    
    if [ -d "apps/open-policy-app" ]; then
        cp -r apps/open-policy-app mobile/
    fi
    
    print_success "Mobile application setup completed"
}

# Create startup scripts
create_startup_scripts() {
    print_status "Creating startup scripts..."
    
    # Backend startup
    cat > start-backend.sh << 'EOF'
#!/bin/bash
echo "Starting Open Policy Backend..."
cd backend
source venv/bin/activate
cd api
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
EOF
    chmod +x start-backend.sh
    
    # Web startup
    cat > start-web.sh << 'EOF'
#!/bin/bash
echo "Starting Open Policy Web Application..."
cd web
npm run dev
EOF
    chmod +x start-web.sh
    
    # All services startup
    cat > start-all.sh << 'EOF'
#!/bin/bash
echo "Starting all Open Policy services..."
echo "This will start backend and web application"

# Start backend in background
./start-backend.sh &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 5

# Start web application in background
./start-web.sh &
WEB_PID=$!

echo "All services started!"
echo "Backend PID: $BACKEND_PID"
echo "Web PID: $WEB_PID"
echo ""
echo "To stop all services, run: kill $BACKEND_PID $WEB_PID"
echo ""
echo "Access the applications:"
echo "  - Backend API: http://localhost:8000"
echo "  - API Docs: http://localhost:8000/docs"
echo "  - Web Interface: http://localhost:5173"
echo "  - Admin Interface: http://localhost:5173/admin"

# Wait for user to stop
wait
EOF
    chmod +x start-all.sh
    
    print_success "Startup scripts created"
}

# Display next steps
show_next_steps() {
    echo ""
    echo "🎉 Unified setup completed successfully!"
    echo "================================"
    echo ""
    echo "Next steps:"
    echo ""
    echo "1. Configure environment variables:"
    echo "   - Edit backend/.env"
    echo "   - Edit web/.env"
    echo ""
    echo "2. Start the services:"
    echo "   - Backend: ./start-backend.sh"
    echo "   - Web Interface: ./start-web.sh"
    echo "   - All Services: ./start-all.sh"
    echo ""
    echo "3. Access the applications:"
    echo "   - Backend API: http://localhost:8000"
    echo "   - API Documentation: http://localhost:8000/docs"
    echo "   - Web Interface: http://localhost:5173"
    echo "   - Admin Interface: http://localhost:5173/admin"
    echo ""
    echo "4. Default admin credentials:"
    echo "   - Username: admin"
    echo "   - Password: admin"
    echo ""
    echo "5. Documentation:"
    echo "   - Reorganization Plan: REORGANIZATION_PLAN.md"
    echo "   - API Documentation: http://localhost:8000/docs"
    echo ""
    echo "Happy coding! 🚀"
}

# Main execution
main() {
    echo "Starting Open Policy Platform unified setup..."
    echo ""
    
    check_prerequisites
    setup_database
    setup_backend
    setup_web
    setup_mobile
    create_startup_scripts
    show_next_steps
}

# Run main function
main "$@"
