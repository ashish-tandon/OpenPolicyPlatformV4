# Docker Configurations for OpenPolicyPlatform Microservices

## 1. Local Development Docker Compose

Create this file in orchestration repository as `docker-compose.local.yml`

```yaml
version: '3.8'

networks:
  openpolicy-network:
    driver: bridge

volumes:
  postgres_data:
  redis_data:
  elasticsearch_data:

services:
  # Database Services
  postgres:
    image: postgres:15-alpine
    restart: unless-stopped
    environment:
      POSTGRES_DB: openpolicy
      POSTGRES_USER: openpolicy
      POSTGRES_PASSWORD: dev_password_change_in_prod
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-db:/docker-entrypoint-initdb.d
    ports:
      - "5432:5432"
    networks:
      - openpolicy-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U openpolicy"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    networks:
      - openpolicy-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    restart: unless-stopped
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
    ports:
      - "9200:9200"
    networks:
      - openpolicy-network
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:9200/_cluster/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Core Microservices
  api-gateway:
    build:
      context: ../api-gateway
      dockerfile: Dockerfile
    restart: unless-stopped
    environment:
      - NODE_ENV=development
      - PORT=3000
      - POLICY_PROCESSOR_URL=http://policy-processor:3001
      - DOCUMENT_SERVICE_URL=http://document-service:3002
      - NOTIFICATION_SERVICE_URL=http://notification-service:3003
      - AUTH_SERVICE_URL=http://auth-service:3004
      - ANALYTICS_SERVICE_URL=http://analytics-service:3005
      - DATABASE_URL=postgresql://openpolicy:dev_password_change_in_prod@postgres:5432/openpolicy
      - REDIS_URL=redis://redis:6379
    ports:
      - "3000:3000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - openpolicy-network
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:3000/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3

  policy-processor:
    build:
      context: ../policy-processor
      dockerfile: Dockerfile
    restart: unless-stopped
    environment:
      - PYTHON_ENV=development
      - DATABASE_URL=postgresql://openpolicy:dev_password_change_in_prod@postgres:5432/openpolicy
      - REDIS_URL=redis://redis:6379
      - ELASTICSEARCH_URL=http://elasticsearch:9200
      - DOCUMENT_SERVICE_URL=http://document-service:3002
    ports:
      - "3001:3001"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      elasticsearch:
        condition: service_healthy
    networks:
      - openpolicy-network
    volumes:
      - ./data/policies:/app/data
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:3001/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3

  document-service:
    build:
      context: ../document-service
      dockerfile: Dockerfile
    restart: unless-stopped
    environment:
      - NODE_ENV=development
      - PORT=3002
      - DATABASE_URL=postgresql://openpolicy:dev_password_change_in_prod@postgres:5432/openpolicy
      - ELASTICSEARCH_URL=http://elasticsearch:9200
      - FILE_STORAGE_PATH=/app/storage
    ports:
      - "3002:3002"
    depends_on:
      postgres:
        condition: service_healthy
      elasticsearch:
        condition: service_healthy
    networks:
      - openpolicy-network
    volumes:
      - ./storage/documents:/app/storage
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:3002/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3

  notification-service:
    build:
      context: ../notification-service
      dockerfile: Dockerfile
    restart: unless-stopped
    environment:
      - NODE_ENV=development
      - PORT=3003
      - DATABASE_URL=postgresql://openpolicy:dev_password_change_in_prod@postgres:5432/openpolicy
      - REDIS_URL=redis://redis:6379
      - SMTP_HOST=mailhog
      - SMTP_PORT=1025
      - SMTP_USER=
      - SMTP_PASS=
    ports:
      - "3003:3003"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - openpolicy-network
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:3003/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3

  auth-service:
    build:
      context: ../auth-service
      dockerfile: Dockerfile
    restart: unless-stopped
    environment:
      - NODE_ENV=development
      - PORT=3004
      - DATABASE_URL=postgresql://openpolicy:dev_password_change_in_prod@postgres:5432/openpolicy
      - REDIS_URL=redis://redis:6379
      - JWT_SECRET=dev_secret_change_in_prod
      - JWT_EXPIRATION=24h
    ports:
      - "3004:3004"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - openpolicy-network
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:3004/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3

  analytics-service:
    build:
      context: ../analytics-service
      dockerfile: Dockerfile
    restart: unless-stopped
    environment:
      - PYTHON_ENV=development
      - DATABASE_URL=postgresql://openpolicy:dev_password_change_in_prod@postgres:5432/openpolicy
      - REDIS_URL=redis://redis:6379
      - ELASTICSEARCH_URL=http://elasticsearch:9200
    ports:
      - "3005:3005"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      elasticsearch:
        condition: service_healthy
    networks:
      - openpolicy-network
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:3005/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend-web:
    build:
      context: ../frontend-web
      dockerfile: Dockerfile
      args:
        - REACT_APP_API_URL=http://localhost:3000
    restart: unless-stopped
    environment:
      - NODE_ENV=development
    ports:
      - "3006:80"
    depends_on:
      api-gateway:
        condition: service_healthy
    networks:
      - openpolicy-network
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:80/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Development Tools
  mailhog:
    image: mailhog/mailhog:latest
    restart: unless-stopped
    ports:
      - "1025:1025"  # SMTP
      - "8025:8025"  # Web UI
    networks:
      - openpolicy-network

  nginx:
    image: nginx:alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
    depends_on:
      - frontend-web
      - api-gateway
    networks:
      - openpolicy-network
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## 2. QNAP Container Station Docker Compose

Create this file for QNAP deployment as `docker-compose.qnap.yml`

```yaml
version: '3.8'

networks:
  openpolicy-network:
    external: true

volumes:
  postgres_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /share/Container/openpolicy/data/postgres
  redis_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /share/Container/openpolicy/data/redis

services:
  # Database Services - Blue Environment
  postgres-blue:
    image: postgres:15-alpine
    restart: unless-stopped
    container_name: openpolicy-postgres-blue
    environment:
      POSTGRES_DB: openpolicy
      POSTGRES_USER: openpolicy
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - openpolicy-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U openpolicy"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis-blue:
    image: redis:7-alpine
    restart: unless-stopped
    container_name: openpolicy-redis-blue
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    networks:
      - openpolicy-network
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD}", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Blue Environment Services
  api-gateway-blue:
    image: ghcr.io/ashish-tandon/openpolicy-api-gateway:latest
    restart: unless-stopped
    container_name: openpolicy-api-gateway-blue
    environment:
      - NODE_ENV=production
      - PORT=3000
      - DATABASE_URL=postgresql://openpolicy:${POSTGRES_PASSWORD}@postgres-blue:5432/openpolicy
      - REDIS_URL=redis://redis-blue:6379
      - REDIS_PASSWORD=${REDIS_PASSWORD}
      - POLICY_PROCESSOR_URL=http://policy-processor-blue:3001
      - DOCUMENT_SERVICE_URL=http://document-service-blue:3002
      - NOTIFICATION_SERVICE_URL=http://notification-service-blue:3003
      - AUTH_SERVICE_URL=http://auth-service-blue:3004
      - ANALYTICS_SERVICE_URL=http://analytics-service-blue:3005
    depends_on:
      postgres-blue:
        condition: service_healthy
      redis-blue:
        condition: service_healthy
    networks:
      - openpolicy-network
    labels:
      - "environment=blue"
      - "service=api-gateway"
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:3000/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Green Environment Services (for Blue-Green Deployment)
  api-gateway-green:
    image: ghcr.io/ashish-tandon/openpolicy-api-gateway:latest
    restart: "no"  # Only start when needed for deployment
    container_name: openpolicy-api-gateway-green
    environment:
      - NODE_ENV=production
      - PORT=3000
      - DATABASE_URL=postgresql://openpolicy:${POSTGRES_PASSWORD}@postgres-blue:5432/openpolicy
      - REDIS_URL=redis://redis-blue:6379
      - REDIS_PASSWORD=${REDIS_PASSWORD}
    depends_on:
      postgres-blue:
        condition: service_healthy
      redis-blue:
        condition: service_healthy
    networks:
      - openpolicy-network
    labels:
      - "environment=green"
      - "service=api-gateway"
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:3000/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Load Balancer / Reverse Proxy
  nginx:
    image: nginx:alpine
    restart: unless-stopped
    container_name: openpolicy-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /share/Container/openpolicy/nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - /share/Container/openpolicy/nginx/ssl:/etc/nginx/ssl:ro
      - /share/Container/openpolicy/nginx/logs:/var/log/nginx
    depends_on:
      - api-gateway-blue
    networks:
      - openpolicy-network
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## 3. Service-Specific Dockerfile Templates

### Node.js Services Dockerfile (API Gateway, Document Service, etc.)
```dockerfile
# Node.js Services Dockerfile
FROM node:18-alpine as builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production && npm cache clean --force

# Copy source code
COPY . .

# Build the application (if applicable)
RUN npm run build || true

# Production stage
FROM node:18-alpine as production

# Create app user
RUN addgroup -g 1001 -S nodejs && adduser -S nextjs -u 1001

WORKDIR /app

# Copy built application
COPY --from=builder --chown=nextjs:nodejs /app/dist ./dist
COPY --from=builder --chown=nextjs:nodejs /app/node_modules ./node_modules
COPY --from=builder --chown=nextjs:nodejs /app/package.json ./package.json

# Health check
COPY --chown=nextjs:nodejs healthcheck.js ./

USER nextjs

EXPOSE 3000

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3     CMD node healthcheck.js

CMD ["npm", "start"]
```

### Python Services Dockerfile (Policy Processor, Analytics Service)
```dockerfile
# Python Services Dockerfile
FROM python:3.11-slim as builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y     build-essential     curl     && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --user --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim as production

# Create app user
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /home/appuser/.local

# Copy application code
COPY --chown=appuser:appuser . .

# Make sure scripts are executable
RUN chmod +x ./scripts/*.sh

USER appuser

# Update PATH
ENV PATH=/home/appuser/.local/bin:$PATH

EXPOSE 3001

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3     CMD curl -f http://localhost:3001/health || exit 1

CMD ["python", "app.py"]
```

### React Frontend Dockerfile
```dockerfile
# React Frontend Dockerfile
FROM node:18-alpine as builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build the application
ARG REACT_APP_API_URL
ENV REACT_APP_API_URL=$REACT_APP_API_URL

RUN npm run build

# Production stage with nginx
FROM nginx:alpine as production

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built application
COPY --from=builder /app/build /usr/share/nginx/html

# Add health check script
COPY healthcheck.sh /healthcheck.sh
RUN chmod +x /healthcheck.sh

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3     CMD /healthcheck.sh

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

## 4. Nginx Configuration for QNAP Blue-Green Deployment

Create this file as `nginx/nginx.conf`

```nginx
upstream api_blue {
    server api-gateway-blue:3000;
}

upstream api_green {
    server api-gateway-green:3000;
}

# Current active upstream (change for blue-green deployment)
upstream api_current {
    server api-gateway-blue:3000;
}

server {
    listen 80;
    server_name openpolicy.local;

    # Health check endpoint
    location /nginx-health {
        access_log off;
        return 200 "healthy
";
        add_header Content-Type text/plain;
    }

    # API routes
    location /api/ {
        proxy_pass http://api_current;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Health check for load balancer
        proxy_next_upstream error timeout invalid_header http_500 http_502 http_503 http_504;
    }

    # Frontend routes
    location / {
        proxy_pass http://frontend-web-blue;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 5. Environment Configuration

Create `.env` files for different environments:

### Local Development (.env.local)
```bash
POSTGRES_PASSWORD=dev_password_change_in_prod
REDIS_PASSWORD=dev_redis_password
JWT_SECRET=dev_jwt_secret_change_in_prod
GRAFANA_PASSWORD=admin

# Service URLs
API_GATEWAY_URL=http://localhost:3000
FRONTEND_URL=http://localhost:3006

# External APIs
GOVERNMENT_API_URL=https://api.parl.gc.ca
NOTIFICATION_EMAIL_FROM=noreply@openpolicy.local
```

### QNAP Environment (.env.qnap)
```bash
POSTGRES_PASSWORD=secure_qnap_postgres_password
REDIS_PASSWORD=secure_qnap_redis_password
JWT_SECRET=secure_qnap_jwt_secret
GRAFANA_PASSWORD=secure_qnap_grafana_password

# Service URLs
API_GATEWAY_URL=https://openpolicy-test.local
FRONTEND_URL=https://openpolicy-test.local

# External APIs
GOVERNMENT_API_URL=https://api.parl.gc.ca
NOTIFICATION_EMAIL_FROM=noreply@openpolicy-test.local
```

## 6. Health Check Scripts

### Node.js Health Check (healthcheck.js)
```javascript
const http = require('http');

const options = {
  host: 'localhost',
  port: process.env.PORT || 3000,
  path: '/health',
  timeout: 2000
};

const request = http.request(options, (res) => {
  if (res.statusCode === 200) {
    process.exit(0);
  } else {
    process.exit(1);
  }
});

request.on('error', () => {
  process.exit(1);
});

request.end();
```

### React Health Check (healthcheck.sh)
```bash
#!/bin/sh
curl -f http://localhost:80/health || exit 1
```

This comprehensive Docker configuration provides:
1. Complete local development environment
2. QNAP production-ready setup with blue-green deployment
3. Service-specific Dockerfiles optimized for production
4. Nginx load balancing and reverse proxy
5. Health checks for all services
6. Environment-specific configurations

The setup enables smooth blue-green deployments on QNAP while maintaining development productivity locally.
