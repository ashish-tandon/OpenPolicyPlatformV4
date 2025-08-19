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
