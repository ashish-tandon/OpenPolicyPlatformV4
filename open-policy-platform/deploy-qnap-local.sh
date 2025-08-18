#!/bin/bash

# Open Policy Platform V4 - Local QNAP Deployment Preparation
# This script prepares the platform for deployment to QNAP NAS

set -e

echo "🚀 Open Policy Platform V4 - QNAP Deployment Preparation"
echo "========================================================"

# Configuration
COMPOSE_FILE="docker-compose.qnap.yml"
ENV_FILE=".env.qnap"
CONFIG_FILE="qnap-config.json"
SSH_KEY="$HOME/.ssh/openpolicy_qnap_key"

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

# Check SSH key
check_ssh_key() {
    print_status "Checking SSH key for QNAP access..."
    
    if [ ! -f "$SSH_KEY" ]; then
        print_error "SSH key not found at $SSH_KEY"
        print_status "Generating new SSH key..."
        ssh-keygen -t rsa -b 4096 -f "$SSH_KEY" -N "" -C "ashish.tandon@openpolicy.me"
        print_success "SSH key generated successfully"
    else
        print_success "SSH key found"
    fi
    
    # Display public key
    print_status "SSH Public Key (add this to QNAP SSH settings):"
    echo "=========================================="
    cat "${SSH_KEY}.pub"
    echo "=========================================="
    print_warning "Please add this SSH key to your QNAP SSH settings manually"
    print_status "You can copy the key above and add it in QNAP Control Panel > Network & File Services > SSH"
}

# Create QNAP environment file
create_qnap_env() {
    print_status "Creating QNAP environment file..."
    
    cat > "$ENV_FILE" << EOF
# Open Policy Platform V4 - QNAP Environment Configuration
# Copy this file to your QNAP NAS and update values as needed

# Database Configuration
DATABASE_URL=postgresql://openpolicy:openpolicy123@postgres:5432/openpolicy
REDIS_URL=redis://redis:6379/0

# Security Configuration
JWT_SECRET=openpolicy_production_jwt_secret_2024_secure_32_chars
JWT_EXPIRY_MINUTES=30
JWT_REFRESH_EXPIRY_DAYS=7
SECRET_KEY=openpolicy_production_secret_key_2024_secure_32_chars

# Auth0 Configuration
AUTH0_DOMAIN=dev-openpolicy.ca.auth0.com
AUTH0_CLIENT_ID=zR9zxYpZnRjaMHUfIOTUx9BSMfOekrnG
AUTH0_CLIENT_SECRET=tVfKcn-qUhC9d3v0ihtICtWxgAhMlLeMCwWZBIS2jXTrph72nf4m7kZ1Q4VqO5yo
AUTH0_AUDIENCE=https://api.openpolicy.com

# System Configuration
SYSTEM_ADMIN_EMAIL=ashish.tandon@openpolicy.me
LOG_LEVEL=INFO
ENVIRONMENT=production

# CORS Configuration
ALLOWED_HOSTS=["192.168.2.152","localhost","127.0.0.1"]
ALLOWED_ORIGINS=["http://192.168.2.152:3000","http://localhost:3000"]

# Umami Analytics Configuration
UMAMI_WEBSITE_ID=your_umami_website_id
UMAMI_API_URL=https://your-umami-instance.com/api
UMAMI_USERNAME=ashish.tandon@openpolicy.me
UMAMI_PASSWORD=nrt2rfv!mwc1NUH8fra
EOF

    print_success "QNAP environment file created: $ENV_FILE"
}

# Create deployment instructions
create_deployment_instructions() {
    print_status "Creating deployment instructions..."
    
    cat > "QNAP_DEPLOYMENT_INSTRUCTIONS.md" << EOF
# 🚀 Open Policy Platform V4 - QNAP Deployment Instructions

## 📋 Prerequisites
1. QNAP NAS with Container Station installed
2. SSH access enabled on QNAP
3. SSH key added to QNAP (see key above)

## 🔑 SSH Key Setup
Add this SSH key to your QNAP:
\`\`\`
$(cat "${SSH_KEY}.pub")
\`\`\`

**Steps:**
1. Go to QNAP Control Panel > Network & File Services > SSH
2. Enable SSH service
3. Add the public key above to authorized keys

## 📁 Files to Copy to QNAP
Copy these files to your QNAP NAS:
- \`docker-compose.qnap.yml\`
- \`.env.qnap\`
- \`qnap-config.json\`
- \`scripts/import-database-qnap.sh\`
- \`database-exports/full_database_*.sql\`

## 🐳 Deployment Steps

### 1. Connect to QNAP
\`\`\`bash
ssh admin@192.168.2.152
\`\`\`

### 2. Create Platform Directory
\`\`\`bash
mkdir -p /share/Container/OpenPolicyPlatform
cd /share/Container/OpenPolicyPlatform
\`\`\`

### 3. Copy Files
Copy all deployment files to this directory

### 4. Start Platform
\`\`\`bash
docker-compose -f docker-compose.qnap.yml up -d
\`\`\`

### 5. Import Database
\`\`\`bash
chmod +x scripts/import-database-qnap.sh
./scripts/import-database-qnap.sh database-exports/full_database_*.sql
\`\`\`

## 🌐 Access URLs
- **Web Interface**: http://192.168.2.152:3000
- **API**: http://192.168.2.152:8000
- **Grafana**: http://192.168.2.152:3001
- **Prometheus**: http://192.168.2.152:9090

## 🔍 Verification
\`\`\`bash
# Check service status
docker-compose -f docker-compose.qnap.yml ps

# Check logs
docker-compose -f docker-compose.qnap.yml logs -f
\`\`\`

## 🆘 Troubleshooting
- Check Container Station is running
- Verify SSH key is properly added
- Check firewall settings
- Monitor system resources
EOF

    print_success "Deployment instructions created: QNAP_DEPLOYMENT_INSTRUCTIONS.md"
}

# Main execution
main() {
    echo ""
    print_status "Starting QNAP deployment preparation..."
    
    check_ssh_key
    create_qnap_env
    create_deployment_instructions
    
    echo ""
    print_success "QNAP deployment preparation completed!"
    echo ""
    print_status "Next steps:"
    echo "1. Add the SSH key above to your QNAP NAS"
    echo "2. Copy the deployment files to QNAP"
    echo "3. Follow the instructions in QNAP_DEPLOYMENT_INSTRUCTIONS.md"
    echo ""
    print_warning "IMPORTANT: The SSH key above must be added to QNAP before deployment"
}

# Run main function
main "$@"
