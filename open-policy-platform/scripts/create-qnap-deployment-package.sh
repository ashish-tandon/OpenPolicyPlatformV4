#!/bin/bash

# Create QNAP Deployment Package for OpenPolicyPlatform V4
# This script creates a complete deployment package for QNAP Container Station

set -e

echo "🚀 Creating QNAP Deployment Package for OpenPolicyPlatform V4"
echo "=========================================================="

# Configuration
PACKAGE_NAME="openpolicy-qnap-deployment"
PACKAGE_VERSION="1.0.0"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
PACKAGE_DIR="${PACKAGE_NAME}-${TIMESTAMP}"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Create package directory structure
log "Creating package directory structure..."
mkdir -p ${PACKAGE_DIR}/{helm,docker,scripts,docs,config}

# Copy Helm charts
log "Copying Helm charts..."
cp -r charts/open-policy-platform ${PACKAGE_DIR}/helm/

# Create QNAP-specific values file
log "Creating QNAP-specific Helm values..."
cat > ${PACKAGE_DIR}/helm/values-qnap.yaml << 'EOF'
# QNAP-specific values for OpenPolicyPlatform
# Override default values for QNAP Container Station deployment

# Enable QNAP optimizations
qnap:
  enabled: true
  nfs:
    server: "YOUR_QNAP_IP"  # Replace with your QNAP IP
    path: "/share/Container/open-policy-platform"
  containerStation:
    optimizations: true
    resourceLimits: true

# Use local storage class for QNAP
global:
  storageClass: "local-path"
  domain: "openpolicy.qnap.local"
  adminDomain: "openpolicyadmin.qnap.local"

# Adjust resource limits for QNAP
postgres:
  resources:
    requests:
      memory: "256Mi"
      cpu: "250m"
    limits:
      memory: "512Mi"
      cpu: "500m"

redis:
  resources:
    requests:
      memory: "128Mi"
      cpu: "100m"
    limits:
      memory: "256Mi"
      cpu: "250m"

# Reduce replicas for QNAP
apiGateway:
  replicas: 1
  autoscaling:
    enabled: false

services:
  authService:
    replicas: 1
  policyService:
    replicas: 1
  searchService:
    replicas: 1

web:
  replicas: 1

# Use NodePort for external access on QNAP
nginx:
  service:
    type: NodePort
    nodePort: 30080
    httpsNodePort: 30443

# Disable resource quotas for QNAP
resourceQuota:
  enabled: false
EOF

# Create Docker Compose file for QNAP Container Station
log "Creating Docker Compose configuration for QNAP..."
cat > ${PACKAGE_DIR}/docker/docker-compose-qnap.yml << 'EOF'
version: '3.8'

services:
  # PostgreSQL Main Database
  postgres:
    image: postgres:15
    container_name: openpolicy-postgres
    environment:
      POSTGRES_DB: openpolicy
      POSTGRES_USER: openpolicy
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-openpolicy123}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U openpolicy"]
      interval: 30s
      timeout: 10s
      retries: 5

  # Redis Cache
  redis:
    image: redis:7-alpine
    container_name: openpolicy-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped
    command: redis-server --appendonly yes

  # API Gateway
  api-gateway:
    image: openpolicy/api-gateway:latest
    container_name: openpolicy-api-gateway
    ports:
      - "9000:9000"
    environment:
      - PORT=9000
      - DATABASE_URL=postgresql://openpolicy:${POSTGRES_PASSWORD:-openpolicy123}@postgres:5432/openpolicy
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

  # Web Frontend
  web:
    image: openpolicy/web:latest
    container_name: openpolicy-web
    ports:
      - "3000:3000"
    environment:
      - API_URL=http://api-gateway:9000
    depends_on:
      - api-gateway
    restart: unless-stopped

  # Admin Dashboard
  admin-dashboard:
    image: openpolicy/admin-dashboard:latest
    container_name: openpolicy-admin
    ports:
      - "3001:3001"
    environment:
      - API_URL=http://api-gateway:9000
    depends_on:
      - api-gateway
    restart: unless-stopped

  # Nginx Reverse Proxy
  nginx:
    image: nginx:alpine
    container_name: openpolicy-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./config/nginx:/etc/nginx/conf.d:ro
      - ./config/nginx/html:/usr/share/nginx/html:ro
    depends_on:
      - web
      - admin-dashboard
      - api-gateway
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
EOF

# Copy nginx configuration
log "Copying nginx configuration..."
mkdir -p ${PACKAGE_DIR}/config/nginx
cp nginx/custom-domains.conf ${PACKAGE_DIR}/config/nginx/default.conf
cp nginx/proxy_params ${PACKAGE_DIR}/config/nginx/
cp -r nginx/html ${PACKAGE_DIR}/config/nginx/

# Create deployment scripts
log "Creating deployment scripts..."

# QNAP deployment script
cat > ${PACKAGE_DIR}/scripts/deploy-to-qnap.sh << 'EOF'
#!/bin/bash

echo "🚀 Deploying OpenPolicyPlatform to QNAP Container Station"
echo "========================================================"

# Check if running on QNAP
if [ ! -f /etc/platform.conf ]; then
    echo "Warning: This doesn't appear to be a QNAP system"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Load environment variables
if [ -f .env ]; then
    source .env
fi

# Create necessary directories
echo "Creating directories..."
mkdir -p /share/Container/open-policy-platform/{data,logs,config}

# Copy configuration files
echo "Copying configuration files..."
cp -r config/* /share/Container/open-policy-platform/config/

# Deploy using Docker Compose
echo "Deploying services..."
cd docker
docker-compose -f docker-compose-qnap.yml up -d

# Wait for services to start
echo "Waiting for services to start..."
sleep 30

# Check service health
echo "Checking service health..."
docker ps --format "table {{.Names}}\t{{.Status}}"

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Access the platform at:"
echo "  Main site: http://YOUR_QNAP_IP"
echo "  Admin dashboard: http://YOUR_QNAP_IP:3001"
echo "  API Gateway: http://YOUR_QNAP_IP:9000"
echo ""
echo "Default admin credentials:"
echo "  Username: admin"
echo "  Password: AdminSecure123!"
echo ""
echo "⚠️  Remember to change the default passwords!"
EOF

chmod +x ${PACKAGE_DIR}/scripts/deploy-to-qnap.sh

# Create health check script
cat > ${PACKAGE_DIR}/scripts/health-check.sh << 'EOF'
#!/bin/bash

echo "🏥 OpenPolicyPlatform Health Check"
echo "================================="

# Function to check service health
check_service() {
    local service=$1
    local url=$2
    
    echo -n "Checking $service... "
    
    if curl -fs "$url" > /dev/null; then
        echo "✅ OK"
        return 0
    else
        echo "❌ FAILED"
        return 1
    fi
}

# Check all services
check_service "API Gateway" "http://localhost:9000/health"
check_service "Web Frontend" "http://localhost:3000"
check_service "Admin Dashboard" "http://localhost:3001"
check_service "PostgreSQL" "localhost:5432" || echo "(Use: docker exec openpolicy-postgres pg_isready)"
check_service "Redis" "localhost:6379" || echo "(Use: docker exec openpolicy-redis redis-cli ping)"

echo ""
echo "Container Status:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
EOF

chmod +x ${PACKAGE_DIR}/scripts/health-check.sh

# Create update script
cat > ${PACKAGE_DIR}/scripts/update-platform.sh << 'EOF'
#!/bin/bash

echo "🔄 Updating OpenPolicyPlatform"
echo "============================="

# Pull latest images
echo "Pulling latest images..."
docker-compose -f docker/docker-compose-qnap.yml pull

# Restart services with zero downtime
echo "Restarting services..."
docker-compose -f docker/docker-compose-qnap.yml up -d --no-deps --build

# Run database migrations
echo "Running database migrations..."
docker exec openpolicy-api-gateway npm run migrate

echo "✅ Update complete!"
EOF

chmod +x ${PACKAGE_DIR}/scripts/update-platform.sh

# Create documentation
log "Creating documentation..."

cat > ${PACKAGE_DIR}/docs/QNAP_DEPLOYMENT_GUIDE.md << 'EOF'
# OpenPolicyPlatform QNAP Deployment Guide

## Prerequisites

1. QNAP NAS with Container Station installed
2. At least 8GB RAM available
3. 50GB free storage space
4. Static IP or domain name for your QNAP

## Quick Start

1. **Upload Package**
   - Upload this package to your QNAP
   - Extract to `/share/Container/open-policy-platform`

2. **Configure Environment**
   ```bash
   cd /share/Container/open-policy-platform
   cp .env.example .env
   # Edit .env with your settings
   ```

3. **Deploy Platform**
   ```bash
   ./scripts/deploy-to-qnap.sh
   ```

4. **Verify Deployment**
   ```bash
   ./scripts/health-check.sh
   ```

## Accessing the Platform

- **Main Website**: http://YOUR_QNAP_IP
- **Admin Dashboard**: http://YOUR_QNAP_IP:3001
- **API Documentation**: http://YOUR_QNAP_IP:9000/docs

## Configuration

### Custom Domain Setup
1. Edit `/etc/hosts` on your local machine:
   ```
   YOUR_QNAP_IP openpolicy.local
   YOUR_QNAP_IP openpolicyadmin.local
   ```

2. Or configure your DNS server to point these domains to your QNAP

### SSL/TLS Configuration
For production use, configure SSL certificates:
1. Place certificates in `/share/Container/open-policy-platform/config/ssl/`
2. Update nginx configuration
3. Restart nginx container

## Maintenance

### Backup
```bash
./scripts/backup.sh
```

### Update
```bash
./scripts/update-platform.sh
```

### Monitoring
- Access Grafana: http://YOUR_QNAP_IP:3001
- Access Kibana: http://YOUR_QNAP_IP:5601

## Troubleshooting

### Check Logs
```bash
docker logs openpolicy-api-gateway
docker logs openpolicy-web
```

### Restart Services
```bash
docker-compose -f docker/docker-compose-qnap.yml restart
```

### Reset Database
```bash
docker exec openpolicy-postgres psql -U openpolicy -c "DROP DATABASE openpolicy;"
docker exec openpolicy-postgres psql -U openpolicy -c "CREATE DATABASE openpolicy;"
```

## Support

For issues and support:
- GitHub: https://github.com/your-org/open-policy-platform
- Documentation: https://docs.openpolicyplatform.com
EOF

# Create environment template
cat > ${PACKAGE_DIR}/.env.example << 'EOF'
# OpenPolicyPlatform Environment Configuration

# Database
POSTGRES_PASSWORD=change_me_in_production
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=openpolicy
POSTGRES_USER=openpolicy

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# Security
JWT_SECRET=change_me_to_random_string
ADMIN_PASSWORD=change_me_immediately

# QNAP Settings
QNAP_IP=192.168.1.100
QNAP_DOMAIN=openpolicy.local

# Email Configuration (optional)
SMTP_HOST=
SMTP_PORT=
SMTP_USER=
SMTP_PASS=

# Monitoring (optional)
GRAFANA_ADMIN_PASSWORD=admin
KIBANA_ADMIN_PASSWORD=admin
EOF

# Create README
cat > ${PACKAGE_DIR}/README.md << 'EOF'
# OpenPolicyPlatform QNAP Deployment Package

This package contains everything needed to deploy OpenPolicyPlatform on a QNAP NAS using Container Station.

## 📦 Package Contents

- `/helm` - Kubernetes Helm charts (for advanced users)
- `/docker` - Docker Compose configuration
- `/scripts` - Deployment and maintenance scripts
- `/config` - Configuration files
- `/docs` - Documentation

## 🚀 Quick Start

1. Extract this package to your QNAP
2. Run `./scripts/deploy-to-qnap.sh`
3. Access the platform at http://YOUR_QNAP_IP

## 📖 Documentation

See `/docs/QNAP_DEPLOYMENT_GUIDE.md` for detailed instructions.

## 🔧 Support

- Issues: https://github.com/your-org/open-policy-platform/issues
- Documentation: https://docs.openpolicyplatform.com

## 📝 License

Copyright © 2024 OpenPolicyPlatform Team
EOF

# Create the package archive
log "Creating deployment package archive..."
tar -czf ${PACKAGE_NAME}-${PACKAGE_VERSION}-${TIMESTAMP}.tar.gz ${PACKAGE_DIR}/

# Create checksum
log "Creating checksum..."
sha256sum ${PACKAGE_NAME}-${PACKAGE_VERSION}-${TIMESTAMP}.tar.gz > ${PACKAGE_NAME}-${PACKAGE_VERSION}-${TIMESTAMP}.sha256

# Cleanup
rm -rf ${PACKAGE_DIR}

echo ""
echo "✅ QNAP Deployment Package Created Successfully!"
echo ""
echo "📦 Package: ${PACKAGE_NAME}-${PACKAGE_VERSION}-${TIMESTAMP}.tar.gz"
echo "🔒 Checksum: ${PACKAGE_NAME}-${PACKAGE_VERSION}-${TIMESTAMP}.sha256"
echo ""
echo "📋 Next Steps:"
echo "1. Upload the package to your QNAP NAS"
echo "2. Extract the package"
echo "3. Follow the deployment guide in the docs folder"
echo ""
echo "🎉 Happy deploying!"