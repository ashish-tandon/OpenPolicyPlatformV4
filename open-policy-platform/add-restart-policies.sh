#!/bin/bash

# ========================================
# ADD RESTART POLICIES TO ALL SERVICES
# ========================================
# This script adds restart: unless-stopped to all services
# to prevent Docker crashes from stopping the platform
# ========================================

echo "🔄 ADDING RESTART POLICIES TO ALL SERVICES..."

# Add restart policies to all microservices
echo "🔧 Adding restart policies to microservices..."

# Find all service sections and add restart policy
sed -i '' '/^  [a-zA-Z0-9-]*:$/{
  /^  [a-zA-Z0-9-]*:$/!b
  :a
  N
  /image:/{
    s/image:/restart: unless-stopped\n    image:/
    b
  }
  ba
}' docker-compose.complete.yml

echo "✅ Restart policies added to all services!"
echo "🔧 All services now have: restart: unless-stopped"
echo "🚀 Services will auto-restart on Docker crashes!"
