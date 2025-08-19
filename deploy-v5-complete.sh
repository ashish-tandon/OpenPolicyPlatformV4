#!/bin/bash

# 🚀 OpenPolicyPlatform V5 - Complete Deployment Script

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
echo -e "${BLUE}🚀 OpenPolicyPlatform V5 - Complete Deployment${NC}"
echo -e "${BLUE}==================================================${NC}"
echo

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker and try again.${NC}"
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ docker-compose not found. Installing...${NC}"
    # Try to install docker-compose
    if command -v brew &> /dev/null; then
        brew install docker-compose
    else
        echo -e "${RED}❌ Please install docker-compose manually${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✅ Docker environment ready${NC}"
echo

# Create V5 environment file
echo -e "${CYAN}🔧 Creating V5 environment configuration...${NC}"
cat > .env.v5 << 'EOF'
# OpenPolicyPlatform V5 - Environment Configuration

# ========================================
# CORE SERVICES
# ========================================
POSTGRES_DB=openpolicy_v5
POSTGRES_USER=openpolicy_user
POSTGRES_PASSWORD=secure_password_v5
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=secure_redis_v5

# ========================================
# API SERVICES
# ========================================
API_GATEWAY_PORT=8000
API_SERVICE_PORT=8001
WEB_SERVICE_PORT=8002
MOBILE_API_PORT=8003

# ========================================
# MONITORING
# ========================================
ELASTICSEARCH_PORT=9200
LOGSTASH_PORT=5044
KIBANA_PORT=5601
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
FLUENTD_PORT=24224

# ========================================
# BACKGROUND PROCESSING
# ========================================
CELERY_BROKER_URL=redis://:secure_redis_v5@redis:6379/0
CELERY_RESULT_BACKEND=redis://:secure_redis_v5@redis:6379/0

# ========================================
# SECURITY
# ========================================
JWT_SECRET_KEY=your_jwt_secret_key_here_v5
AUTH0_DOMAIN=your_auth0_domain
AUTH0_CLIENT_ID=your_auth0_client_id
AUTH0_CLIENT_SECRET=your_auth0_client_secret

# ========================================
# EXTERNAL SERVICES
# ========================================
AZURE_STORAGE_CONNECTION_STRING=your_azure_storage_connection_string
QNAP_NAS_HOST=your_qnap_nas_host
QNAP_NAS_USERNAME=your_qnap_username
QNAP_NAS_PASSWORD=your_qnap_password

# ========================================
# LOGGING
# ========================================
LOG_LEVEL=INFO
LOG_FORMAT=json
FLUENTD_TAG=docker.openpolicy_v5

# ========================================
# PERFORMANCE
# ========================================
WORKER_PROCESSES=4
MAX_CONNECTIONS=1000
TIMEOUT=30
EOF

echo -e "${GREEN}✅ V5 environment file created${NC}"
echo

# Create V5 docker-compose file
echo -e "${CYAN}🐳 Creating V5 Docker Compose configuration...${NC}"
cat > docker-compose.v5.yml << 'EOF'
version: '3.8'

services:
  # ========================================
  # INFRASTRUCTURE SERVICES
  # ========================================
  postgres:
    image: postgres:15-alpine
    container_name: openpolicy_v5_postgres
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database/init:/docker-entrypoint-initdb.d
    ports:
      - "${POSTGRES_PORT}:5432"
    networks:
      - openpolicy_v5_network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7-alpine
    container_name: openpolicy_v5_redis
    command: redis-server --requirepass ${REDIS_PASSWORD}
    ports:
      - "${REDIS_PORT}:6379"
    volumes:
      - redis_data:/data
    networks:
      - openpolicy_v5_network
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  # ========================================
  # MONITORING STACK
  # ========================================
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    container_name: openpolicy_v5_elasticsearch
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
    ports:
      - "${ELASTICSEARCH_PORT}:9200"
    networks:
      - openpolicy_v5_network
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:9200/_cluster/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3

  logstash:
    image: docker.elastic.co/logstash/logstash:8.11.0
    container_name: openpolicy_v5_logstash
    volumes:
      - ./monitoring/logstash/pipeline:/usr/share/logstash/pipeline
      - ./monitoring/logstash/config/logstash.yml:/usr/share/logstash/config/logstash.yml
    ports:
      - "${LOGSTASH_PORT}:5044"
    networks:
      - openpolicy_v5_network
    depends_on:
      - elasticsearch
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:9600 || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3

  kibana:
    image: docker.elastic.co/kibana/kibana:8.11.0
    container_name: openpolicy_v5_kibana
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    ports:
      - "${KIBANA_PORT}:5601"
    networks:
      - openpolicy_v5_network
    depends_on:
      - elasticsearch
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:5601/api/status || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3

  fluentd:
    image: fluent/fluentd:v1.16-1
    container_name: openpolicy_v5_fluentd
    volumes:
      - ./monitoring/fluentd/conf:/fluentd/etc
      - ./monitoring/fluentd/log:/fluentd/log
    ports:
      - "${FLUENTD_PORT}:24224"
    networks:
      - openpolicy_v5_network
    healthcheck:
      test: ["CMD-SHELL", "pgrep fluentd || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3

  prometheus:
    image: prom/prometheus:latest
    container_name: openpolicy_v5_prometheus
    volumes:
      - ./monitoring/prometheus:/etc/prometheus
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=200h'
      - '--web.enable-lifecycle'
    ports:
      - "${PROMETHEUS_PORT}:9090"
    networks:
      - openpolicy_v5_network
    healthcheck:
      test: ["CMD-SHELL", "wget --no-verbose --tries=1 --spider http://localhost:9090/-/healthy || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3

  grafana:
    image: grafana/grafana:latest
    container_name: openpolicy_v5_grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin_v5
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/provisioning:/etc/grafana/provisioning
    ports:
      - "${GRAFANA_PORT}:3000"
    networks:
      - openpolicy_v5_network
    depends_on:
      - prometheus
    healthcheck:
      test: ["CMD-SHELL", "wget --no-verbose --tries=1 --spider http://localhost:3000/api/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3

  # ========================================
  # API GATEWAY
  # ========================================
  nginx:
    image: nginx:alpine
    container_name: openpolicy_v5_nginx
    volumes:
      - ./nginx/nginx.v5.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
    ports:
      - "80:80"
      - "443:443"
    networks:
      - openpolicy_v5_network
    depends_on:
      - api-gateway
    healthcheck:
      test: ["CMD-SHELL", "wget --no-verbose --tries=1 --spider http://localhost/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3

  api-gateway:
    image: openpolicyplatform/v5-api-gateway:latest
    container_name: openpolicy_v5_api_gateway
    environment:
      - GATEWAY_PORT=${API_GATEWAY_PORT}
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:${REDIS_PORT}
    ports:
      - "${API_GATEWAY_PORT}:${API_GATEWAY_PORT}"
    networks:
      - openpolicy_v5_network
    depends_on:
      - redis
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:${API_GATEWAY_PORT}/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3

  # ========================================
  # BACKGROUND PROCESSING
  # ========================================
  celery-worker:
    image: openpolicyplatform/v5-celery-worker:latest
    container_name: openpolicy_v5_celery_worker
    environment:
      - CELERY_BROKER_URL=${CELERY_BROKER_URL}
      - CELERY_RESULT_BACKEND=${CELERY_RESULT_BACKEND}
      - POSTGRES_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:${POSTGRES_PORT}/${POSTGRES_DB}
    volumes:
      - ./logs:/app/logs
    networks:
      - openpolicy_v5_network
    depends_on:
      - redis
      - postgres
    healthcheck:
      test: ["CMD-SHELL", "celery -A app.celery inspect ping || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3

  celery-beat:
    image: openpolicyplatform/v5-celery-beat:latest
    container_name: openpolicy_v5_celery_beat
    environment:
      - CELERY_BROKER_URL=${CELERY_BROKER_URL}
      - CELERY_RESULT_BACKEND=${CELERY_RESULT_BACKEND}
      - POSTGRES_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:${POSTGRES_PORT}/${POSTGRES_DB}
    volumes:
      - ./logs:/app/logs
    networks:
      - openpolicy_v5_network
    depends_on:
      - redis
      - postgres
    healthcheck:
      test: ["CMD-SHELL", "ps aux | grep celery | grep beat || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3

  flower:
    image: openpolicyplatform/v5-flower:latest
    container_name: openpolicy_v5_flower
    environment:
      - CELERY_BROKER_URL=${CELERY_BROKER_URL}
      - FLOWER_PORT=5555
    ports:
      - "5555:5555"
    networks:
      - openpolicy_v5_network
    depends_on:
      - redis
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:5555/ || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3

  # ========================================
  # WEB FRONTEND
  # ========================================
  web-frontend:
    image: openpolicyplatform/v5-web-frontend:latest
    container_name: openpolicy_v5_web_frontend
    environment:
      - REACT_APP_API_URL=http://api-gateway:${API_GATEWAY_PORT}
      - REACT_APP_AUTH0_DOMAIN=${AUTH0_DOMAIN}
      - REACT_APP_AUTH0_CLIENT_ID=${AUTH0_CLIENT_ID}
    ports:
      - "${WEB_SERVICE_PORT}:3000"
    networks:
      - openpolicy_v5_network
    depends_on:
      - api-gateway
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:3000/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  postgres_data:
  redis_data:
  elasticsearch_data:
  prometheus_data:
  grafana_data:

networks:
  openpolicy_v5_network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
EOF

echo -e "${GREEN}✅ V5 Docker Compose file created${NC}"
echo

# Create monitoring configuration files
echo -e "${CYAN}📊 Creating monitoring configuration...${NC}"
mkdir -p monitoring/{prometheus,grafana,logstash,fluentd}

# Prometheus configuration
cat > monitoring/prometheus/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "rules/*.yml"

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'openpolicy-v5-services'
    static_configs:
      - targets:
        - 'api-gateway:8000'
        - 'web-frontend:3000'
        - 'celery-worker:8000'
        - 'celery-beat:8000'
        - 'flower:5555'
        - 'postgres:5432'
        - 'redis:6379'
        - 'elasticsearch:9200'
        - 'logstash:5044'
        - 'kibana:5601'
        - 'fluentd:24224'

  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx:80']
    metrics_path: /metrics
EOF

# Logstash configuration
cat > monitoring/logstash/config/logstash.yml << 'EOF'
http.host: "0.0.0.0"
xpack.monitoring.elasticsearch.hosts: [ "http://elasticsearch:9200" ]
EOF

cat > monitoring/logstash/pipeline/logstash.conf << 'EOF'
input {
  beats {
    port => 5044
  }
}

filter {
  if [fields][service] == "openpolicy_v5" {
    grok {
      match => { "message" => "%{TIMESTAMP_ISO8601:timestamp} %{LOGLEVEL:level} %{GREEDYDATA:message}" }
    }
    date {
      match => [ "timestamp", "ISO8601" ]
    }
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "openpolicy-v5-logs-%{+YYYY.MM.dd}"
  }
}
EOF

# Fluentd configuration
cat > monitoring/fluentd/conf/fluent.conf << 'EOF'
<source>
  @type forward
  port 24224
  bind 0.0.0.0
</source>

<filter docker.openpolicy_v5>
  @type record_transformer
  <record>
    service openpolicy_v5
    environment production
    version v5
  </record>
</filter>

<match docker.openpolicy_v5>
  @type elasticsearch
  host elasticsearch
  port 9200
  logstash_format true
  logstash_prefix openpolicy-v5-logs
  <buffer>
    @type file
    path /fluentd/log
    flush_interval 5s
  </buffer>
</match>
EOF

echo -e "${GREEN}✅ Monitoring configuration created${NC}"
echo

# Create Nginx configuration
echo -e "${CYAN}🌐 Creating Nginx configuration...${NC}"
mkdir -p nginx/ssl

cat > nginx/nginx.v5.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream api_gateway {
        server api-gateway:8000;
    }

    upstream web_frontend {
        server web-frontend:3000;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=web:10m rate=20r/s;

    # Logging
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    server {
        listen 80;
        server_name localhost;
        
        # Health check
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }

        # API Gateway
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://api_gateway;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_connect_timeout 30s;
            proxy_send_timeout 30s;
            proxy_read_timeout 30s;
        }

        # Web Frontend
        location / {
            limit_req zone=web burst=30 nodelay;
            proxy_pass http://web_frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_connect_timeout 30s;
            proxy_send_timeout 30s;
            proxy_read_timeout 30s;
        }
    }
}
EOF

echo -e "${GREEN}✅ Nginx configuration created${NC}"
echo

# Create deployment script
echo -e "${CYAN}📦 Creating deployment script...${NC}"
cat > deploy-v5.sh << 'EOF'
#!/bin/bash

echo "🚀 Deploying OpenPolicyPlatform V5..."
echo "=================================================="

# Load environment variables
source .env.v5

# Create necessary directories
mkdir -p logs database/init monitoring/{prometheus,grafana,logstash,fluentd}/data nginx/ssl

# Deploy services
echo "🐳 Starting V5 services..."
docker-compose -f docker-compose.v5.yml up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 30

# Check service status
echo "📊 Checking service status..."
docker-compose -f docker-compose.v5.yml ps

echo "✅ V5 deployment complete!"
echo "🌐 Access points:"
echo "  - Web Frontend: http://localhost:8002"
echo "  - API Gateway: http://localhost:8000"
echo "  - Kibana: http://localhost:5601"
echo "  - Grafana: http://localhost:3000"
echo "  - Prometheus: http://localhost:9090"
echo "  - Flower: http://localhost:5555"
EOF

chmod +x deploy-v5.sh

echo -e "${GREEN}✅ Deployment script created${NC}"
echo

# Create health check script
echo -e "${CYAN}🏥 Creating health check script...${NC}"
cat > v5-health-check.sh << 'EOF'
#!/bin/bash

echo "🏥 OpenPolicyPlatform V5 - Health Check"
echo "=================================================="

# Check Docker services
echo "🐳 Checking Docker services..."
docker-compose -f docker-compose.v5.yml ps

echo
echo "🔍 Checking service health..."

# Check API Gateway
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ API Gateway: Healthy"
else
    echo "❌ API Gateway: Unhealthy"
fi

# Check Web Frontend
if curl -f http://localhost:8002/health > /dev/null 2>&1; then
    echo "✅ Web Frontend: Healthy"
else
    echo "❌ Web Frontend: Unhealthy"
fi

# Check PostgreSQL
if docker exec openpolicy_v5_postgres pg_isready -U openpolicy_user -d openpolicy_v5 > /dev/null 2>&1; then
    echo "✅ PostgreSQL: Healthy"
else
    echo "❌ PostgreSQL: Unhealthy"
fi

# Check Redis
if docker exec openpolicy_v5_redis redis-cli --raw incr ping > /dev/null 2>&1; then
    echo "✅ Redis: Healthy"
else
    echo "❌ Redis: Unhealthy"
fi

# Check Elasticsearch
if curl -f http://localhost:9200/_cluster/health > /dev/null 2>&1; then
    echo "✅ Elasticsearch: Healthy"
else
    echo "❌ Elasticsearch: Unhealthy"
fi

# Check Kibana
if curl -f http://localhost:5601/api/status > /dev/null 2>&1; then
    echo "✅ Kibana: Healthy"
else
    echo "❌ Kibana: Unhealthy"
fi

# Check Prometheus
if curl -f http://localhost:9090/-/healthy > /dev/null 2>&1; then
    echo "✅ Prometheus: Healthy"
else
    echo "❌ Prometheus: Unhealthy"
fi

# Check Grafana
if curl -f http://localhost:3000/api/health > /dev/null 2>&1; then
    echo "✅ Grafana: Healthy"
else
    echo "❌ Grafana: Unhealthy"
fi

echo
echo "=================================================="
echo "🏥 Health check complete!"
EOF

chmod +x v5-health-check.sh

echo -e "${GREEN}✅ Health check script created${NC}"
echo

echo -e "${GREEN}==================================================${NC}"
echo -e "${GREEN}✅ V5 COMPLETE SETUP READY!${NC}"
echo -e "${GREEN}==================================================${NC}"
echo
echo -e "${YELLOW}📋 What was created:${NC}"
echo -e "  ✅ .env.v5 - Environment configuration"
echo -e "  ✅ docker-compose.v5.yml - Complete service orchestration"
echo -e "  ✅ monitoring/ - Full monitoring stack config"
echo -e "  ✅ nginx/nginx.v5.conf - Reverse proxy configuration"
echo -e "  ✅ deploy-v5.sh - Deployment script"
echo -e "  ✅ v5-health-check.sh - Health monitoring script"
echo
echo -e "${CYAN}🚀 To deploy V5:${NC}"
echo -e "  1. Review and customize .env.v5"
echo -e "  2. Run: ./deploy-v5.sh"
echo -e "  3. Monitor with: ./v5-health-check.sh"
echo
echo -e "${PURPLE}🎉 Your V5 platform is ready for deployment!${NC}"
