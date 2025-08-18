# 🚀 Open Policy Platform V4 - Azure Deployment Instructions

## 📋 Prerequisites
1. Azure subscription (ID: 5602b849-384e-4da7-8b75-fd5eb70ea355)
2. Azure CLI installed and configured
3. Docker installed locally
4. PostgreSQL client tools (for database import)

## 🔐 Azure Authentication
```bash
# Login to Azure
az login

# Set subscription
az account set --subscription 5602b849-384e-4da7-8b75-fd5eb70ea355
```

## 🏗️ Azure Resource Creation

### 1. Create Resource Group
```bash
az group create --name openpolicy-platform-rg --location canadacentral
```

### 2. Create Azure Container Registry (ACR)
```bash
az acr create --resource-group openpolicy-platform-rg   --name openpolicyacr --sku Basic

# Login to ACR
az acr login --name openpolicyacr
```

### 3. Create Azure Database for PostgreSQL
```bash
az postgres flexible-server create   --resource-group openpolicy-platform-rg   --name openpolicy-postgres   --location canadacentral   --admin-user openpolicy   --admin-password "your_secure_password"   --sku-name Standard_B1ms   --version 14   --storage-size 32

# Create database
az postgres flexible-server db create   --resource-group openpolicy-platform-rg   --server-name openpolicy-postgres   --database-name openpolicy
```

### 4. Create Azure Cache for Redis
```bash
az redis create   --resource-group openpolicy-platform-rg   --name openpolicy-redis   --location canadacentral   --sku Basic --vm-size c0
```

### 5. Create App Service Plan
```bash
az appservice plan create   --resource-group openpolicy-platform-rg   --name openpolicy-asp   --location canadacentral   --sku B1 --is-linux
```

## 🐳 Docker Image Building & Pushing

### 1. Build Images
```bash
# Build API image
docker build -t openpolicyacr.azurecr.io/openpolicy-api:latest ./backend

# Build Web image
docker build -t openpolicyacr.azurecr.io/openpolicy-web:latest ./web
```

### 2. Push to ACR
```bash
# Push API image
docker push openpolicyacr.azurecr.io/openpolicy-api:latest

# Push Web image
docker push openpolicyacr.azurecr.io/openpolicy-web:latest
```

## 🚀 Platform Deployment

### 1. Update Environment Variables
Update `.env.azure` with your actual Azure resource details:
- Database connection string
- Redis connection string
- Azure resource names

### 2. Deploy with Docker Compose
```bash
docker-compose -f docker-compose.azure.yml up -d
```

### 3. Import Database
```bash
# Get database connection details
az postgres flexible-server show   --resource-group openpolicy-platform-rg   --name openpolicy-postgres

# Import database
./scripts/import-database-azure.sh   database-exports/full_database_*.sql   your-server.postgres.database.azure.com   your_password
```

## 🌐 Access URLs
- **Web Interface**: https://your-azure-domain.com
- **API**: https://your-azure-domain.com:8000
- **Grafana**: https://your-azure-domain.com:3001
- **Prometheus**: https://your-azure-domain.com:9090

## 🔍 Verification
```bash
# Check service status
docker-compose -f docker-compose.azure.yml ps

# Check logs
docker-compose -f docker-compose.azure.yml logs -f

# Test database connection
az postgres flexible-server execute   --resource-group openpolicy-platform-rg   --name openpolicy-postgres   --database-name openpolicy   --querytext "SELECT version();"
```

## 🆘 Troubleshooting
- Check Azure resource status in Azure Portal
- Verify firewall rules allow your IP
- Check ACR authentication
- Monitor resource usage and limits
- Review Azure Monitor logs

## 💰 Cost Optimization
- Use Basic SKUs for development
- Consider reserved instances for production
- Monitor and set up spending limits
- Use Azure Advisor for recommendations
