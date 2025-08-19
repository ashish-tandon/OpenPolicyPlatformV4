#!/bin/bash

# OpenPolicyPlatform V4 - LOCAL DEPLOYMENT
# Deploy the entire platform locally using Docker Compose

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

echo -e "${BLUE}🚀 OpenPolicyPlatform V4 - LOCAL DEPLOYMENT${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Function to check Docker
check_docker() {
    echo -e "\n${YELLOW}🐳 Checking Docker...${NC}"
    
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}✗ Docker is not installed${NC}"
        echo -e "${YELLOW}Please install Docker first: https://docs.docker.com/get-docker/${NC}"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        echo -e "${RED}✗ Docker daemon is not running${NC}"
        echo -e "${YELLOW}Please start Docker Desktop or Docker daemon${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Docker is running${NC}"
    
    # Check docker-compose
    if command -v docker-compose &> /dev/null; then
        echo -e "${GREEN}✓ docker-compose is available${NC}"
    else
        echo -e "${YELLOW}Using 'docker compose' (v2) instead of 'docker-compose'${NC}"
    fi
}

# Function to create environment files
create_env_files() {
    echo -e "\n${YELLOW}📋 Creating environment files...${NC}"
    
    # Infrastructure layer
    cat > migration-repos/openpolicy-infrastructure/.env << 'EOF'
# Database
DB_PASSWORD=SecureLocalPassword123!
DATABASE_URL=postgresql://openpolicy:SecureLocalPassword123!@postgres:5432/openpolicy

# Redis
REDIS_URL=redis://redis:6379/0

# Security
SECRET_KEY=local-dev-secret-key-change-in-production
JWT_SECRET=local-dev-jwt-secret-change-in-production

# Monitoring
GRAFANA_PASSWORD=admin

# Services
AUTH_SERVICE_URL=http://auth-service:9001
CONFIG_SERVICE_URL=http://config-service:9005
MONITORING_SERVICE_URL=http://monitoring-service:9006
EOF
    
    # Data layer
    cat > migration-repos/openpolicy-data/.env << 'EOF'
DATABASE_URL=postgresql://openpolicy:SecureLocalPassword123!@localhost:5432/openpolicy
REDIS_URL=redis://localhost:6379/0
ELASTICSEARCH_URL=http://localhost:9200
SCRAPERS_DATA_DIR=/app/scrapers-data
EOF
    
    # Business layer
    cat > migration-repos/openpolicy-business/.env << 'EOF'
DATABASE_URL=postgresql://openpolicy:SecureLocalPassword123!@localhost:5432/openpolicy
REDIS_URL=redis://localhost:6379/0
API_GATEWAY_URL=http://localhost:9000
EOF
    
    # Frontend layer
    cat > migration-repos/openpolicy-frontend/.env << 'EOF'
VITE_API_URL=http://localhost:8000
REACT_APP_API_URL=http://localhost:9000
DATABASE_URL=postgresql://openpolicy:SecureLocalPassword123!@localhost:5432/openpolicy
REDIS_URL=redis://localhost:6379/0
EOF
    
    echo -e "${GREEN}✓ Environment files created${NC}"
}

# Function to start infrastructure layer
start_infrastructure() {
    echo -e "\n${YELLOW}🔧 Starting Infrastructure Layer...${NC}"
    
    cd migration-repos/openpolicy-infrastructure
    
    # Use docker compose v2 if available, otherwise docker-compose
    if command -v docker-compose &> /dev/null; then
        docker-compose up -d
    else
        docker compose up -d
    fi
    
    echo -e "${GREEN}✓ Infrastructure layer started${NC}"
    
    # Wait for services to be ready
    echo -e "${YELLOW}⏳ Waiting for services to initialize (30 seconds)...${NC}"
    sleep 30
    
    # Check health
    echo -e "${BLUE}Checking service health...${NC}"
    docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "(postgres|redis|auth-service|api-gateway)"
    
    cd ../..
}

# Function to start data layer
start_data_layer() {
    echo -e "\n${YELLOW}📊 Starting Data Layer...${NC}"
    
    cd migration-repos/openpolicy-data
    
    # For now, we'll note that this needs the services to be built
    echo -e "${BLUE}Data layer services:${NC}"
    echo "  - ETL Service"
    echo "  - Scraper Service" 
    echo "  - Policy Service"
    echo "  - Search Service"
    echo "  - Data Management Service"
    echo "  - Files Service"
    
    echo -e "${YELLOW}Note: Build these services individually as needed${NC}"
    
    cd ../..
}

# Function to create unified docker-compose
create_unified_compose() {
    echo -e "\n${YELLOW}🔗 Creating unified Docker Compose...${NC}"
    
    cat > migration-repos/docker-compose.unified.yml << 'EOF'
version: '3.8'

networks:
  openpolicy-network:
    driver: bridge

volumes:
  postgres_data:
  redis_data:
  elasticsearch_data:
  prometheus_data:
  grafana_data:

services:
  # Infrastructure Layer
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: openpolicy
      POSTGRES_USER: openpolicy
      POSTGRES_PASSWORD: SecureLocalPassword123!
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - openpolicy-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U openpolicy"]
      interval: 30s
      timeout: 10s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - openpolicy-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 5

  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    ports:
      - "9200:9200"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
    networks:
      - openpolicy-network

  kibana:
    image: docker.elastic.co/kibana/kibana:8.11.0
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    networks:
      - openpolicy-network
    depends_on:
      - elasticsearch

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - prometheus_data:/prometheus
    networks:
      - openpolicy-network

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
    networks:
      - openpolicy-network

  # You can add more services here as they're built
EOF
    
    echo -e "${GREEN}✓ Unified Docker Compose created${NC}"
}

# Function to display access information
display_access_info() {
    echo -e "\n${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}✅ LOCAL DEPLOYMENT RUNNING!${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    echo -e "\n${BLUE}🌐 Access Points:${NC}"
    echo -e "   PostgreSQL:     localhost:5432"
    echo -e "   Redis:          localhost:6379"
    echo -e "   Elasticsearch:  http://localhost:9200"
    echo -e "   Kibana:         http://localhost:5601"
    echo -e "   Prometheus:     http://localhost:9090"
    echo -e "   Grafana:        http://localhost:3001 (admin/admin)"
    
    echo -e "\n${BLUE}📊 Service Status:${NC}"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    
    echo -e "\n${BLUE}🔧 Useful Commands:${NC}"
    echo -e "   View logs:      docker-compose logs -f [service-name]"
    echo -e "   Stop services:  docker-compose down"
    echo -e "   Restart:        docker-compose restart [service-name]"
    echo -e "   View stats:     docker stats"
    
    echo -e "\n${BLUE}📋 Next Steps:${NC}"
    echo -e "   1. Build individual services as needed"
    echo -e "   2. Access Grafana at http://localhost:3001"
    echo -e "   3. Import dashboards for monitoring"
    echo -e "   4. Start developing your services!"
}

# Function to check port availability
check_ports() {
    echo -e "\n${YELLOW}🔍 Checking port availability...${NC}"
    
    local ports=("5432" "6379" "9200" "5601" "9090" "3001" "9000" "8000")
    local all_clear=true
    
    for port in "${ports[@]}"; do
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            echo -e "${RED}✗ Port $port is already in use${NC}"
            all_clear=false
        else
            echo -e "${GREEN}✓ Port $port is available${NC}"
        fi
    done
    
    if [ "$all_clear" = false ]; then
        echo -e "\n${YELLOW}Some ports are in use. Do you want to continue anyway? (y/n)${NC}"
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            echo -e "${RED}Deployment cancelled${NC}"
            exit 1
        fi
    fi
}

# Main execution
main() {
    echo -e "${PURPLE}Starting local deployment...${NC}"
    
    # Check prerequisites
    check_docker
    
    # Check if migration-repos exists
    if [ ! -d "migration-repos" ]; then
        echo -e "${RED}Error: migration-repos directory not found${NC}"
        echo -e "${YELLOW}Please run the migration script first${NC}"
        exit 1
    fi
    
    # Check ports
    check_ports
    
    # Create environment files
    create_env_files
    
    # Create unified compose file
    create_unified_compose
    
    # Start services
    echo -e "\n${YELLOW}🚀 Starting services...${NC}"
    cd migration-repos
    
    if command -v docker-compose &> /dev/null; then
        docker-compose -f docker-compose.unified.yml up -d
    else
        docker compose -f docker-compose.unified.yml up -d
    fi
    
    cd ..
    
    # Wait for services to initialize
    echo -e "\n${YELLOW}⏳ Waiting for services to initialize (30 seconds)...${NC}"
    sleep 30
    
    # Display access information
    display_access_info
    
    echo -e "\n${GREEN}🎉 Local deployment complete!${NC}"
    echo -e "${YELLOW}To stop all services, run: cd migration-repos && docker-compose -f docker-compose.unified.yml down${NC}"
}

# Run main function
main "$@"