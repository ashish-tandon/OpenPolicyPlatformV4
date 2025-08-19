# 🔧 OpenPolicyPlatform Services

Business logic microservices for OpenPolicyPlatform V5.

## Services
- **Auth Service**: Authentication and authorization
- **Policy Service**: Policy management and analysis
- **Analytics Service**: Data analytics and insights
- **Monitoring Service**: Service monitoring and health
- **ETL Service**: Data extraction, transformation, loading
- **Scraper Service**: Web scraping and data collection

## Quick Start
```bash
# Start all services
docker-compose up -d

# Start specific service
docker-compose up -d auth-service policy-service
```

## Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest

# Run service locally
uvicorn main:app --reload
```
