#!/bin/bash

# Open Policy Platform V4 - QNAP Deployment Script
# This script deploys the platform to QNAP NAS

set -e

echo "🚀 Starting Open Policy Platform V4 deployment to QNAP NAS..."

# Configuration
COMPOSE_FILE="docker-compose.qnap.yml"
ENV_FILE=".env.qnap"
CONFIG_FILE="qnap-config.json"
SSH_KEY="$HOME/.ssh/openpolicy_qnap_key"
BACKUP_DIR="/share/Container/OpenPolicyPlatform/backups"
LOG_DIR="/share/Container/OpenPolicyPlatform/logs"

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

# Check if running on QNAP
check_qnap() {
    if [ ! -f "/etc/config/qpkg.conf" ]; then
        print_warning "This script is designed for QNAP NAS. Some features may not work on other systems."
    else
        print_success "QNAP NAS detected"
    fi
}

# Setup SSH key for QNAP access
setup_ssh_key() {
    print_status "Setting up SSH key for QNAP access..."
    
    if [ ! -f "$SSH_KEY" ]; then
        print_error "SSH key not found at $SSH_KEY"
        print_status "Generating new SSH key..."
        ssh-keygen -t rsa -b 4096 -f "$SSH_KEY" -N "" -C "ashish.tandon@openpolicy.me"
        print_success "SSH key generated successfully"
    fi
    
    # Display public key for manual addition to QNAP
    print_status "SSH Public Key (add this to QNAP SSH settings):"
    echo "=========================================="
    cat "${SSH_KEY}.pub"
    echo "=========================================="
    print_warning "Please add this SSH key to your QNAP SSH settings manually"
    print_status "You can copy the key above and add it in QNAP Control Panel > Network & File Services > SSH"
}

# Check Container Station availability
check_container_station() {
    print_status "Checking Container Station availability..."
    
    if [ -d "/share/Container" ]; then
        print_success "Container Station detected at /share/Container"
    else
        print_warning "Container Station not found at /share/Container"
        print_status "Checking alternative Container Station locations..."
        
        # Check common Container Station paths
        for path in "/share/ContainerStation" "/share/Container" "/share/ContainerStation/Compose"; do
            if [ -d "$path" ]; then
                print_success "Container Station found at: $path"
                CONTAINER_PATH="$path"
                break
            fi
        done
        
        if [ -z "$CONTAINER_PATH" ]; then
            print_error "Container Station not found. Please install Container Station from QNAP App Center"
            exit 1
        fi
    fi
}

# Create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    
    mkdir -p "$BACKUP_DIR"
    mkdir -p "$LOG_DIR"
    mkdir -p "./nginx/ssl"
    mkdir -p "./monitoring/prometheus"
    mkdir -p "./monitoring/grafana/provisioning/datasources"
    mkdir -p "./monitoring/grafana/provisioning/dashboards"
    mkdir -p "./monitoring/grafana/dashboards"
    mkdir -p "./monitoring/alertmanager"
    
    print_success "Directories created successfully"
}

# Test QNAP connectivity
test_qnap_connectivity() {
    print_status "Testing QNAP connectivity..."
    
    # Test HTTP access
    if curl -s -f "http://192.168.2.152:8080" > /dev/null; then
        print_success "QNAP HTTP access successful"
    else
        print_error "Cannot access QNAP HTTP interface at http://192.168.2.152:8080"
        print_warning "Please check QNAP IP address and port"
    fi
    
    # Test SSH access
    if ssh -o ConnectTimeout=10 -o BatchMode=yes -i "$SSH_KEY" ashish101@192.168.2.152 "echo 'SSH connection successful'" 2>/dev/null; then
        print_success "QNAP SSH access successful"
        SSH_ACCESS=true
    else
        print_warning "SSH access not yet configured. Please add the SSH key to QNAP first."
        print_status "You can test SSH access manually with:"
        echo "ssh -i $SSH_KEY ashish101@192.168.2.152"
        SSH_ACCESS=false
    fi
}

# Create environment file
create_env_file() {
    print_status "Creating environment configuration file..."
    
    if [ ! -f "$ENV_FILE" ]; then
        cat > "$ENV_FILE" << EOF
# Open Policy Platform V4 - QNAP Environment Configuration

# Database Configuration
POSTGRES_PASSWORD=openpolicy123
POSTGRES_USER=openpolicy
POSTGRES_DB=openpolicy

# JWT Configuration
JWT_SECRET=your_jwt_secret_key_here_change_in_production

# Grafana Configuration
GRAFANA_PASSWORD=admin123

# Platform Configuration
ENVIRONMENT=production
LOG_LEVEL=INFO

# Network Configuration
PLATFORM_DOMAIN=your-qnap-domain.com
PLATFORM_PORT=8000
WEB_PORT=3000
GATEWAY_PORT=80
GATEWAY_SSL_PORT=443

# Monitoring Configuration
PROMETHEUS_PORT=9090
GRAFANA_PORT=3001
ALERTMANAGER_PORT=9093

# Backup Configuration
BACKUP_RETENTION_DAYS=30
BACKUP_SCHEDULE=0 2 * * *
EOF
        print_success "Environment file created: $ENV_FILE"
    else
        print_warning "Environment file already exists: $ENV_FILE"
    fi
}

# Generate SSL certificates (self-signed for testing)
generate_ssl_certificates() {
    print_status "Generating SSL certificates..."
    
    if [ ! -f "./nginx/ssl/nginx.crt" ] || [ ! -f "./nginx/ssl/nginx.key" ]; then
        mkdir -p "./nginx/ssl"
        
        # Generate self-signed certificate
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout ./nginx/ssl/nginx.key \
            -out ./nginx/ssl/nginx.crt \
            -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
        
        print_success "SSL certificates generated successfully"
    else
        print_warning "SSL certificates already exist"
    fi
}

# Create Nginx configuration
create_nginx_config() {
    print_status "Creating Nginx configuration..."
    
    mkdir -p "./nginx"
    
    cat > "./nginx/nginx.qnap.conf" << 'EOF'
events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;
    
    # Logging
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';
    
    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log warn;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=web:10m rate=30r/s;
    
    # Upstream definitions
    upstream api_backend {
        server api:8000;
    }
    
    upstream web_backend {
        server web:3000;
    }
    
    # Health check endpoint
    server {
        listen 80;
        server_name _;
        
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }
    }
    
    # Main server configuration
    server {
        listen 80;
        listen 443 ssl http2;
        server_name _;
        
        # SSL configuration
        ssl_certificate /etc/nginx/ssl/nginx.crt;
        ssl_certificate_key /etc/nginx/ssl/nginx.key;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;
        
        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
        
        # API endpoints
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://api_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_connect_timeout 30s;
            proxy_send_timeout 30s;
            proxy_read_timeout 30s;
        }
        
        # Web application
        location / {
            limit_req zone=web burst=50 nodelay;
            proxy_pass http://web_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_connect_timeout 30s;
            proxy_send_timeout 30s;
            proxy_read_timeout 30s;
        }
        
        # Monitoring endpoints
        location /monitoring/ {
            proxy_pass http://api_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
EOF
    
    print_success "Nginx configuration created successfully"
}

# Check Docker and Docker Compose
check_dependencies() {
    print_status "Checking dependencies..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    print_success "Dependencies check passed"
}

# Stop existing containers
stop_existing_containers() {
    print_status "Stopping existing containers..."
    
    if docker-compose -f "$COMPOSE_FILE" down 2>/dev/null; then
        print_success "Existing containers stopped"
    else
        print_warning "No existing containers to stop"
    fi
}

# Deploy the platform
deploy_platform() {
    print_status "Deploying Open Policy Platform V4..."
    
    # Build and start services
    docker-compose -f "$COMPOSE_FILE" up -d --build
    
    print_success "Platform deployment initiated"
}

# Wait for services to be ready
wait_for_services() {
    print_status "Waiting for services to be ready..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        print_status "Checking service health (attempt $attempt/$max_attempts)..."
        
        if curl -f http://localhost:8000/api/v1/health >/dev/null 2>&1; then
            print_success "API service is ready"
            break
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            print_error "Services failed to become ready after $max_attempts attempts"
            exit 1
        fi
        
        attempt=$((attempt + 1))
        sleep 10
    done
    
    print_success "All services are ready"
}

# Display deployment information
show_deployment_info() {
    print_success "Open Policy Platform V4 deployed successfully to QNAP NAS!"
    
    echo ""
    echo "🌐 Platform Access Information:"
    echo "   API: http://localhost:8000"
    echo "   Web: http://localhost:3000"
    echo "   Gateway: http://localhost"
    echo "   Gateway (SSL): https://localhost"
    echo ""
    echo "📊 Monitoring:"
    echo "   Prometheus: http://localhost:9090"
    echo "   Grafana: http://localhost:3001 (admin/admin123)"
    echo "   AlertManager: http://localhost:9093"
    echo ""
    echo "🔐 Default Credentials:"
    echo "   Admin: admin@openpolicy.com / admin123"
    echo "   Moderator: moderator@openpolicy.com / mod123"
    echo "   MP Office: mp_office@openpolicy.com / mp123"
    echo ""
    echo "📁 Data Locations:"
    echo "   Backups: $BACKUP_DIR"
    echo "   Logs: $LOG_DIR"
    echo ""
    echo "🛠️  Management Commands:"
    echo "   View logs: docker-compose -f $COMPOSE_FILE logs -f"
    echo "   Stop services: docker-compose -f $COMPOSE_FILE down"
    echo "   Restart services: docker-compose -f $COMPOSE_FILE restart"
    echo "   Update platform: docker-compose -f $COMPOSE_FILE up -d --build"
}

# Main deployment process
main() {
    echo "=========================================="
    echo "Open Policy Platform V4 - QNAP Deployment"
    echo "=========================================="
    echo ""
    
    check_qnap
    setup_ssh_key
    check_container_station
    test_qnap_connectivity
    create_directories
    create_env_file
    generate_ssl_certificates
    create_nginx_config
    check_docker_dependencies
    stop_existing_containers
    deploy_platform
    wait_for_services
    show_deployment_info
    
    if [ "$SSH_ACCESS" = true ]; then
        print_success "QNAP deployment completed successfully with SSH access! 🎉"
    else
        print_warning "QNAP deployment completed, but SSH access needs to be configured manually"
        print_status "Please add the SSH key to QNAP and test SSH connectivity"
        print_success "Deployment completed successfully! 🎉"
    fi
}

# Run main function
main "$@"
