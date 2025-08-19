#!/bin/bash

# 🚀 OpenPolicyPlatform V5 - Clean Deployment Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}==================================================${NC}"
echo -e "${BLUE}🚀 OpenPolicyPlatform V5 - Clean Deployment${NC}"
echo -e "${BLUE}==================================================${NC}"
echo

# Check if we're in the right directory
if [ ! -d "open-policy-platform" ]; then
    echo -e "${RED}❌ Error: open-policy-platform directory not found${NC}"
    echo -e "${YELLOW}Please run this script from the root of the V5 repository${NC}"
    exit 1
fi

echo -e "${CYAN}Step 1: Setting up V5 environment...${NC}"

# Create clean environment file
cat > open-policy-platform/.env.v5 <<EOF
# OpenPolicyPlatform V5 - Environment Configuration
# Copy this to .env.local and update with your values

# ========================================
# DATABASE CONFIGURATION
# ========================================
DATABASE_URL=postgresql://openpolicy:openpolicy123@postgres:5432/openpolicy
DATABASE_URL_TEST=postgresql://openpolicy:openpolicy123@postgres-test:5432/openpolicy_test
POSTGRES_DB=openpolicy
POSTGRES_USER=openpolicy
POSTGRES_PASSWORD=openpolicy123

# ========================================
# REDIS CONFIGURATION
# ========================================
REDIS_URL=redis://redis:6379/0
REDIS_HOST=redis
REDIS_PORT=6379

# ========================================
# SERVICE CONFIGURATION
# ========================================
SERVICE_NAME=openpolicy-v5
ENVIRONMENT=development
SECRET_KEY=your-secret-key-here-change-this
DEBUG=True

# ========================================
# AUTH0 CONFIGURATION (OAuth)
# ========================================
AUTH0_DOMAIN=dev-openpolicy.ca.auth0.com
AUTH0_CLIENT_ID=your-client-id-here
AUTH0_CLIENT_SECRET=your-client-secret-here
AUTH0_AUDIENCE=https://api.openpolicy.com

# ========================================
# API CONFIGURATION
# ========================================
API_BASE_URL=http://api-gateway:9000
FRONTEND_URL=http://web:3000

# ========================================
# LOGGING CONFIGURATION
# ========================================
LOG_LEVEL=INFO
ELASTICSEARCH_HOST=elasticsearch:9200
FLUENTD_HOST=fluentd
FLUENTD_PORT=24224

# ========================================
# MONITORING CONFIGURATION
# ========================================
PROMETHEUS_URL=http://prometheus:9090
GRAFANA_URL=http://grafana:3000

# ========================================
# CELERY CONFIGURATION
# ========================================
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# ========================================
# AZURE CONFIGURATION (Optional)
# ========================================
# AZURE_KEY_VAULT_URL=https://your-keyvault.vault.azure.net/
# AZURE_SEARCH_SERVICE=your-search-service
# AZURE_CLIENT_ID=your-azure-client-id
# AZURE_TENANT_ID=your-azure-tenant-id
# AZURE_CLIENT_SECRET=your-azure-client-secret
# AZURE_SUBSCRIPTION_ID=your-subscription-id
EOF

echo -e "${GREEN}✅ Created .env.v5 template${NC}"

# Create clean docker-compose for V5
cat > open-policy-platform/docker-compose.v5.yml <<EOF
version: '3.8'

services:
  # ========================================
  # INFRASTRUCTURE SERVICES
  # ========================================
  
  # PostgreSQL Database
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: openpolicy
      POSTGRES_USER: openpolicy
      POSTGRES_PASSWORD: openpolicy123
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U openpolicy"]
      interval: 30s
      timeout: 10s
      retries: 5
    networks:
      - openpolicy-v5-network

  # Redis Cache
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 5
    networks:
      - openpolicy-v5-network

  # ========================================
  # MONITORING STACK
  # ========================================
  
  # Prometheus
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=200h'
      - '--web.enable-lifecycle'
    networks:
      - openpolicy-v5-network

  # Grafana
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
    depends_on:
      - prometheus
    networks:
      - openpolicy-v5-network

  # ========================================
  # CORE SERVICES
  # ========================================
  
  # API Gateway
  api-gateway:
    build:
      context: ./services/api-gateway
      dockerfile: Dockerfile
    ports:
      - "9000:9000"
    environment:
      - DATABASE_URL=postgresql://openpolicy:openpolicy123@postgres:5432/openpolicy
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    networks:
      - openpolicy-v5-network

  # Web Frontend
  web:
    build:
      context: ./apps/web
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - VITE_API_URL=http://localhost:9000
      - NODE_ENV=development
    depends_on:
      - api-gateway
    networks:
      - openpolicy-v5-network

  # ========================================
  # BACKGROUND PROCESSING
  # ========================================
  
  # Celery Worker
  celery-worker:
    build:
      context: ./services/scraper-service
      dockerfile: Dockerfile
    command: celery -A celery_tasks worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql://openpolicy:openpolicy123@postgres:5432/openpolicy
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    networks:
      - openpolicy-v5-network

  # Celery Beat
  celery-beat:
    build:
      context: ./services/scraper-service
      dockerfile: Dockerfile
    command: celery -A celery_tasks beat --loglevel=info
    environment:
      - DATABASE_URL=postgresql://openpolicy:openpolicy123@postgres:5432/openpolicy
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    networks:
      - openpolicy-v5-network

  # Flower (Celery Monitoring)
  flower:
    build:
      context: ./services/scraper-service
      dockerfile: Dockerfile
    command: celery -A celery_tasks flower --port=5555
    ports:
      - "5555:5555"
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    depends_on:
      - redis
      - celery-worker
      - celery-beat
    networks:
      - openpolicy-v5-network

  # ========================================
  # GATEWAY
  # ========================================
  
  # Nginx Gateway
  gateway:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx/nginx.v5.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - api-gateway
      - web
    networks:
      - openpolicy-v5-network

volumes:
  postgres_data:
  redis_data:
  prometheus_data:
  grafana_data:

networks:
  openpolicy-v5-network:
    driver: bridge
EOF

echo -e "${GREEN}✅ Created docker-compose.v5.yml${NC}"

# Create Nginx configuration for V5
mkdir -p open-policy-platform/nginx

cat > open-policy-platform/nginx/nginx.v5.conf <<EOF
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format main '\$remote_addr - \$remote_user [\$time_local] "\$request" '
                    '\$status \$body_bytes_sent "\$http_referer" '
                    '"\$http_user_agent" "\$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;

    # Rate limiting
    limit_req_zone \$binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone \$binary_remote_addr zone=web:10m rate=30r/s;

    # Upstream definitions
    upstream api_backend {
        server api-gateway:9000;
    }

    upstream web_backend {
        server web:3000;
    }

    # Default server
    server {
        listen 80 default_server;
        listen [::]:80 default_server;
        server_name _;

        # API routes
        location /api {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://api_backend;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }

        # Web routes
        location / {
            limit_req zone=web burst=50 nodelay;
            proxy_pass http://web_backend;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }

        # Health check
        location /health {
            access_log off;
            return 200 "healthy\\n";
            add_header Content-Type text/plain;
        }
    }
}
EOF

echo -e "${GREEN}✅ Created Nginx configuration${NC}"

# Create Prometheus configuration
mkdir -p open-policy-platform/monitoring

cat > open-policy-platform/monitoring/prometheus.yml <<EOF
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "prometheus-alerts.yml"

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'api-gateway'
    static_configs:
      - targets: ['api-gateway:9000']
    metrics_path: /metrics

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:5432']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']
EOF

echo -e "${GREEN}✅ Created Prometheus configuration${NC}"

# Create V5 deployment script
cat > open-policy-platform/deploy-v5.sh <<'EOF'
#!/bin/bash

# Deploy OpenPolicyPlatform V5

echo "🚀 Starting OpenPolicyPlatform V5 deployment..."

# Copy environment file
if [ ! -f ".env.local" ]; then
    echo "📝 Creating .env.local from template..."
    cp .env.v5 .env.local
    echo "⚠️  Please edit .env.local with your actual values before continuing"
    echo "Press Enter when ready to continue..."
    read
fi

# Deploy services
echo "🐳 Deploying services..."
docker-compose -f docker-compose.v5.yml up -d

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 60

# Check service health
echo "🔍 Checking service health..."
docker-compose -f docker-compose.v5.yml ps

echo "
✅ OpenPolicyPlatform V5 deployment complete!

Access Points:
- Main Application: http://localhost
- API Gateway: http://localhost:9000
- Web Frontend: http://localhost:3000
- Grafana: http://localhost:3001
- Prometheus: http://localhost:9090
- Flower: http://localhost:5555

Default Credentials:
- Grafana: admin/admin

To stop services:
docker-compose -f docker-compose.v5.yml down

To view logs:
docker-compose -f docker-compose.v5.yml logs -f [service-name]
"
EOF

chmod +x open-policy-platform/deploy-v5.sh

echo -e "${GREEN}✅ Created V5 deployment script${NC}"

# Create V5 status script
cat > open-policy-platform/v5-status.sh <<'EOF'
#!/bin/bash

# Check OpenPolicyPlatform V5 status

echo "🔍 OpenPolicyPlatform V5 Status Check"
echo "======================================"

# Check if services are running
echo "📊 Service Status:"
docker-compose -f docker-compose.v5.yml ps

echo ""
echo "🌐 Service Health:"
echo "------------------"

# Check gateway
if curl -s http://localhost/health > /dev/null; then
    echo "✅ Gateway: Healthy"
else
    echo "❌ Gateway: Unhealthy"
fi

# Check API
if curl -s http://localhost:9000/health > /dev/null; then
    echo "✅ API Gateway: Healthy"
else
    echo "❌ API Gateway: Unhealthy"
fi

# Check web frontend
if curl -s http://localhost:3000 > /dev/null; then
    echo "✅ Web Frontend: Healthy"
else
    echo "❌ Web Frontend: Unhealthy"
fi

# Check Prometheus
if curl -s http://localhost:9090/-/healthy > /dev/null; then
    echo "✅ Prometheus: Healthy"
else
    echo "❌ Prometheus: Unhealthy"
fi

# Check Grafana
if curl -s http://localhost:3001/api/health > /dev/null; then
    echo "✅ Grafana: Healthy"
else
    echo "❌ Grafana: Unhealthy"
fi

echo ""
echo "📈 Resource Usage:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"
EOF

chmod +x open-policy-platform/v5-status.sh

echo -e "${GREEN}✅ Created V5 status script${NC}"

echo
echo -e "${GREEN}==================================================${NC}"
echo -e "${GREEN}✅ V5 SETUP COMPLETE!${NC}"
echo -e "${GREEN}==================================================${NC}"
echo
echo -e "${YELLOW}📋 What was created:${NC}"
echo -e "  - .env.v5 template (copy to .env.local and update)"
echo -e "  - docker-compose.v5.yml (clean V5 services)"
echo -e "  - nginx/nginx.v5.conf (gateway configuration)"
echo -e "  - monitoring/prometheus.yml (monitoring config)"
echo -e "  - deploy-v5.sh (deployment script)"
echo -e "  - v5-status.sh (status checking script)"
echo
echo -e "${CYAN}🚀 To deploy V5:${NC}"
echo -e "  1. cd open-policy-platform"
echo -e "  2. cp .env.v5 .env.local"
echo -e "  3. Edit .env.local with your values"
echo -e "  4. ./deploy-v5.sh"
echo
echo -e "${PURPLE}🎉 Your clean OpenPolicyPlatform V5 is ready!${NC}"
