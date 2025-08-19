# 🏗️ OpenPolicyPlatform Core

Core infrastructure and foundational services for OpenPolicyPlatform V5.

## Services
- **API Gateway**: Go-based API routing and management
- **PostgreSQL**: Primary database service
- **Redis**: Cache and message broker
- **Nginx**: Reverse proxy and load balancer

## Quick Start
```bash
docker-compose up -d
```

## Development
```bash
# Build services
docker-compose build

# Run tests
docker-compose run --rm api-gateway go test ./...

# Development mode
docker-compose -f docker-compose.dev.yml up
```
