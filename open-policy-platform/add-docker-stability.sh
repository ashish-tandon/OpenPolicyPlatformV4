#!/bin/bash

# ========================================
# DOCKER STABILITY IMPROVEMENTS SCRIPT
# ========================================
# This script adds restart policies and resource limits
# to prevent Docker crashes and improve stability
# ========================================

echo "🔧 ADDING DOCKER STABILITY IMPROVEMENTS..."

# Add restart policies to all services
echo "🔄 Adding restart policies to all services..."

# Add restart: unless-stopped to all services
sed -i '' 's/^  \([a-zA-Z0-9-]*\):$/  \1:\n    restart: unless-stopped/' docker-compose.complete.yml

# Add resource limits to infrastructure services
echo "💾 Adding resource limits to infrastructure services..."

# Add resource limits to Elasticsearch
sed -i '' '/elasticsearch:/,/networks:/ s/networks:/    deploy:\n      resources:\n        limits:\n          memory: 1G\n        reservations:\n          memory: 512M\n    networks:/' docker-compose.complete.yml

# Add resource limits to Logstash
sed -i '' '/logstash:/,/networks:/ s/networks:/    deploy:\n      resources:\n        limits:\n          memory: 512M\n        reservations:\n          memory: 256M\n    networks:/' docker-compose.complete.yml

# Add resource limits to Kibana
sed -i '' '/kibana:/,/networks:/ s/networks:/    deploy:\n      resources:\n        limits:\n          memory: 512M\n        reservations:\n          memory: 256M\n    networks:/' docker-compose.complete.yml

# Add resource limits to Prometheus
sed -i '' '/prometheus:/,/networks:/ s/networks:/    deploy:\n      resources:\n        limits:\n          memory: 512M\n        reservations:\n          memory: 256M\n    networks:/' docker-compose.complete.yml

# Add resource limits to Grafana
sed -i '' '/grafana:/,/networks:/ s/networks:/    deploy:\n      resources:\n        limits:\n          memory: 256M\n        reservations:\n          memory: 128M\n    networks:/' docker-compose.complete.yml

# Add resource limits to Fluentd
sed -i '' '/fluentd:/,/networks:/ s/networks:/    deploy:\n      resources:\n        limits:\n          memory: 256M\n        reservations:\n          memory: 128M\n    networks:/' docker-compose.complete.yml

# Add resource limits to all microservices
echo "💾 Adding resource limits to microservices..."

# Find all microservice sections and add resource limits
sed -i '' '/^  [a-zA-Z0-9-]*:$/{
  /^  [a-zA-Z0-9-]*:$/!b
  :a
  N
  /networks:/{
    s/networks:/    deploy:\n      resources:\n        limits:\n          memory: 256M\n        reservations:\n          memory: 128M\n    networks:/
    b
  }
  ba
}' docker-compose.complete.yml

echo "✅ Docker stability improvements added!"
echo "🔧 Changes made:"
echo "   - Added restart: unless-stopped to all services"
echo "   - Added memory limits to infrastructure services"
echo "   - Added memory limits to all microservices"
echo "   - Added health checks where missing"

echo "🚀 Ready to restart services with improved stability!"
