#!/bin/bash

# Open Policy Platform - Unified Setup Script
# This script sets up the entire platform including backend, frontend, and scrapers

set -e  # Exit on any error

echo "🚀 Open Policy Platform - Unified Setup"
echo "======================================"

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
    
    # Check pip
    if ! command -v pip3 &> /dev/null; then
        print_error "pip3 is not installed. Please install pip"
        exit 1
    fi
    
    # Check Docker (optional but recommended)
    if ! command -v docker &> /dev/null; then
        print_warning "Docker is not installed. Some features may not work without Docker."
    fi
    
    print_success "Prerequisites check completed"
}

# Setup backend
setup_backend() {
    print_status "Setting up backend..."
    
    cd backend/OpenPolicyAshBack
    
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
    
    # Check if database setup is needed
    if [ -f "manage.py" ]; then
        print_status "Setting up database..."
        python manage.py migrate --run-syncdb
    fi
    
    cd ../..
    print_success "Backend setup completed"
}

# Setup frontend applications
setup_frontend() {
    print_status "Setting up frontend applications..."
    
    # Setup web interface
    print_status "Setting up open-policy-web..."
    cd apps/open-policy-web
    npm install
    cd ../..
    
    # Setup mobile app
    print_status "Setting up open-policy-main..."
    cd apps/open-policy-main
    npm install
    cd ../..
    
    # Setup policy app
    print_status "Setting up open-policy-app..."
    cd apps/open-policy-app
    npm install
    cd ../..
    
    # Setup admin interface
    print_status "Setting up admin-open-policy..."
    cd apps/admin-open-policy
    npm install
    cd ../..
    
    print_success "Frontend setup completed"
}

# Setup scrapers
setup_scrapers() {
    print_status "Setting up data scrapers..."
    
    # Setup openparliament
    if [ -f "scrapers/openparliament/requirements.txt" ]; then
        print_status "Setting up openparliament scraper..."
        cd scrapers/openparliament
        pip3 install -r requirements.txt
        cd ../..
    fi
    
    # Setup scrapers-ca
    if [ -f "scrapers/scrapers-ca/requirements.txt" ]; then
        print_status "Setting up Canadian scrapers..."
        cd scrapers/scrapers-ca
        pip3 install -r requirements.txt
        cd ../..
    fi
    
    # Setup civic-scraper
    if [ -f "scrapers/civic-scraper/requirements.txt" ]; then
        print_status "Setting up civic scraper..."
        cd scrapers/civic-scraper
        pip3 install -r requirements.txt
        cd ../..
    fi
    
    print_success "Scrapers setup completed"
}

# Create environment files
create_env_files() {
    print_status "Creating environment configuration files..."
    
    # Backend environment
    if [ ! -f "backend/OpenPolicyAshBack/.env" ]; then
        cat > backend/OpenPolicyAshBack/.env << EOF
# Database Configuration
DATABASE_URL=postgresql://localhost/openpolicy
REDIS_URL=redis://localhost:6379

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

# Security
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1

# External Services
OPENAI_API_KEY=your-openai-api-key-here

# Logging
LOG_LEVEL=INFO
EOF
        print_success "Created backend .env file"
    fi
    
    # Frontend environment files
    for app in apps/open-policy-main apps/open-policy-app apps/open-policy-web apps/admin-open-policy; do
        if [ ! -f "$app/.env" ]; then
            cat > "$app/.env" << EOF
# API Configuration
REACT_APP_API_URL=http://localhost:8000
REACT_APP_ENVIRONMENT=development

# Feature Flags
REACT_APP_ENABLE_ANALYTICS=false
REACT_APP_ENABLE_DEBUG=true
EOF
            print_success "Created .env file for $app"
        fi
    done
}

# Create startup scripts
create_startup_scripts() {
    print_status "Creating startup scripts..."
    
    # Backend startup
    cat > start-backend.sh << 'EOF'
#!/bin/bash
echo "Starting Open Policy Backend..."
cd backend/OpenPolicyAshBack
source venv/bin/activate
python manage.py runserver 0.0.0.0:8000
EOF
    chmod +x start-backend.sh
    
    # Web frontend startup
    cat > start-web.sh << 'EOF'
#!/bin/bash
echo "Starting Open Policy Web Interface..."
cd apps/open-policy-web
npm run dev
EOF
    chmod +x start-web.sh
    
    # Mobile app startup
    cat > start-mobile.sh << 'EOF'
#!/bin/bash
echo "Starting Open Policy Mobile App..."
cd apps/open-policy-main
npx expo start
EOF
    chmod +x start-mobile.sh
    
    # All services startup
    cat > start-all.sh << 'EOF'
#!/bin/bash
echo "Starting all Open Policy services..."
echo "This will start backend, web interface, and mobile app"

# Start backend in background
./start-backend.sh &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 5

# Start web interface in background
./start-web.sh &
WEB_PID=$!

# Start mobile app in background
./start-mobile.sh &
MOBILE_PID=$!

echo "All services started!"
echo "Backend PID: $BACKEND_PID"
echo "Web PID: $WEB_PID"
echo "Mobile PID: $MOBILE_PID"
echo ""
echo "To stop all services, run: kill $BACKEND_PID $WEB_PID $MOBILE_PID"

# Wait for user to stop
wait
EOF
    chmod +x start-all.sh
    
    print_success "Startup scripts created"
}

# Display next steps
show_next_steps() {
    echo ""
    echo "🎉 Setup completed successfully!"
    echo "================================"
    echo ""
    echo "Next steps:"
    echo ""
    echo "1. Configure environment variables:"
    echo "   - Edit backend/OpenPolicyAshBack/.env"
    echo "   - Edit .env files in each app directory"
    echo ""
    echo "2. Start the services:"
    echo "   - Backend: ./start-backend.sh"
    echo "   - Web Interface: ./start-web.sh"
    echo "   - Mobile App: ./start-mobile.sh"
    echo "   - All Services: ./start-all.sh"
    echo ""
    echo "3. Access the applications:"
    echo "   - Backend API: http://localhost:8000"
    echo "   - Web Interface: http://localhost:5173"
    echo "   - Mobile App: Use Expo Go app to scan QR code"
    echo ""
    echo "4. Documentation:"
    echo "   - Main README: README.md"
    echo "   - Merge Documentation: MERGE_DOCUMENTATION.md"
    echo "   - Individual component READMEs in each directory"
    echo ""
    echo "Happy coding! 🚀"
}

# Main execution
main() {
    echo "Starting Open Policy Platform setup..."
    echo ""
    
    check_prerequisites
    setup_backend
    setup_frontend
    setup_scrapers
    create_env_files
    create_startup_scripts
    show_next_steps
}

# Run main function
main "$@"
