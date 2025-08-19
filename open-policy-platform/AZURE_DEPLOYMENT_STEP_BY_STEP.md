# 🚀 Open Policy Platform V4 - Azure Deployment Step by Step

## 📋 Prerequisites Check

Before starting, ensure you have the following installed:

1. **Azure CLI** - Install from: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli
2. **Docker** - Install from: https://docs.docker.com/get-docker/
3. **Docker Compose** - Usually comes with Docker Desktop
4. **jq** (JSON processor) - Install with: `brew install jq` (macOS) or `apt-get install jq` (Ubuntu)

## 🔐 Step 1: Azure Authentication

```bash
# Login to Azure
az login

# Set your subscription (use the ID from azure-config.json)
az account set --subscription 5602b849-384e-4da7-8b75-fd5eb70ea355

# Verify current subscription
az account show
```

## 🏗️ Step 2: Create Azure Resources

### Option A: Use the Fixed Script (Recommended)
```bash
# Navigate to the platform directory
cd open-policy-platform

# Run the fixed deployment script
./deploy-azure-fixed.sh
```

### Option B: Manual Step-by-Step Creation

#### 2.1 Create Resource Group
```bash
az group create \
  --name openpolicy-platform-rg \
  --location canadacentral
```

#### 2.2 Create Azure Container Registry (ACR)
```bash
az acr create \
  --resource-group openpolicy-platform-rg \
  --name openpolicyacr \
  --sku Basic \
  --admin-enabled true

# Login to ACR
az acr login --name openpolicyacr
```

#### 2.3 Create Azure Database for PostgreSQL (FIXED COMMAND)
```bash
# Create the PostgreSQL server
az postgres flexible-server create \
  --resource-group openpolicy-platform-rg \
  --name openpolicy-postgresql \
  --location canadacentral \
  --admin-user openpolicy \
  --admin-password "YourSecurePassword123!" \
  --sku-name Standard_B1ms \
  --tier Burstable \
  --storage-size 32 \
  --version 15 \
  --yes

# Create the main database
az postgres flexible-server db create \
  --resource-group openpolicy-platform-rg \
  --server-name openpolicy-postgresql \
  --database-name openpolicy

# Create the test database
az postgres flexible-server db create \
  --resource-group openpolicy-platform-rg \
  --server-name openpolicy-postgresql \
  --database-name openpolicy_test

# Configure firewall rules (allow all Azure services)
az postgres flexible-server firewall-rule create \
  --resource-group openpolicy-platform-rg \
  --name openpolicy-postgresql \
  --rule-name "AllowAllAzureServices" \
  --start-ip-address "0.0.0.0" \
  --end-ip-address "255.255.255.255"
```

#### 2.4 Create Azure Cache for Redis
```bash
az redis create \
  --resource-group openpolicy-platform-rg \
  --name openpolicy-redis \
  --location canadacentral \
  --sku Basic \
  --vm-size C0 \
  --enable-non-ssl-port
```

#### 2.5 Create Azure Storage Account
```bash
az storage account create \
  --resource-group openpolicy-platform-rg \
  --name openpolicystorage \
  --location canadacentral \
  --sku Standard_LRS \
  --encryption-services blob
```

#### 2.6 Create Application Insights
```bash
az monitor app-insights component create \
  --app openpolicy-appinsights \
  --location canadacentral \
  --resource-group openpolicy-platform-rg \
  --kind web
```

#### 2.7 Create Azure Key Vault
```bash
az keyvault create \
  --resource-group openpolicy-platform-rg \
  --name openpolicy-keyvault \
  --location canadacentral \
  --sku standard
```

## 🐳 Step 3: Build and Push Docker Images

```bash
# Login to ACR (if not already logged in)
az acr login --name openpolicyacr

# Build and push backend image
docker build -t openpolicyacr.azurecr.io/openpolicy-api:latest ./backend
docker push openpolicyacr.azurecr.io/openpolicy-api:latest

# Build and push web image
docker build -t openpolicyacr.azurecr.io/openpolicy-web:latest ./web
docker push openpolicyacr.azurecr.io/openpolicy-web:latest
```

## ⚙️ Step 4: Create Environment Configuration

Create a `.env.azure` file with your Azure resource details:

```bash
# Get PostgreSQL connection details
POSTGRES_HOST=$(az postgres flexible-server show \
  --resource-group openpolicy-platform-rg \
  --name openpolicy-postgresql \
  --query fullyQualifiedDomainName -o tsv)

# Get Redis connection details
REDIS_HOST=$(az redis show \
  --resource-group openpolicy-platform-rg \
  --name openpolicy-redis \
  --query hostName -o tsv)

# Get Redis password
REDIS_PASSWORD=$(az redis list-keys \
  --resource-group openpolicy-platform-rg \
  --name openpolicy-redis \
  --query primaryKey -o tsv)

# Get ACR credentials
ACR_USERNAME=$(az acr credential show \
  --name openpolicyacr \
  --query username -o tsv)

ACR_PASSWORD=$(az acr credential show \
  --name openpolicyacr \
  --query passwords[0].value -o tsv)

# Create .env.azure file
cat > .env.azure << EOF
# Azure Configuration
AZURE_SUBSCRIPTION_ID=$(az account show --query id -o tsv)
AZURE_RESOURCE_GROUP=openpolicy-platform-rg
AZURE_LOCATION=canadacentral

# Azure Container Registry
AZURE_ACR_NAME=openpolicyacr
AZURE_ACR_USERNAME=$ACR_USERNAME
AZURE_ACR_PASSWORD=$ACR_PASSWORD

# Database Configuration
AZURE_POSTGRES_USER=openpolicy
AZURE_POSTGRES_PASSWORD=YourSecurePassword123!
AZURE_POSTGRES_SERVER=$POSTGRES_HOST
AZURE_POSTGRES_DATABASE=openpolicy
AZURE_POSTGRES_TEST_DATABASE=openpolicy_test

# Redis Configuration
AZURE_REDIS_PASSWORD=$REDIS_PASSWORD
AZURE_REDIS_NAME=$REDIS_HOST
AZURE_REDIS_PORT=6379

# Storage Configuration
AZURE_STORAGE_ACCOUNT=openpolicystorage
AZURE_STORAGE_KEY=$(az storage account keys list \
  --resource-group openpolicy-platform-rg \
  --account-name openpolicystorage \
  --query '[0].value' -o tsv)

# Application Configuration
NODE_ENV=production
DATABASE_URL=postgresql://openpolicy:YourSecurePassword123!@$POSTGRES_HOST:5432/openpolicy
REDIS_URL=redis://:$REDIS_PASSWORD@$REDIS_HOST:6379
EOF
```

## 🚀 Step 5: Deploy the Platform

```bash
# Deploy with Docker Compose
docker-compose -f docker-compose.azure.yml --env-file .env.azure up -d

# Check service status
docker-compose -f docker-compose.azure.yml ps

# View logs
docker-compose -f docker-compose.azure.yml logs -f
```

## 🔍 Step 6: Verify Deployment

### Check PostgreSQL Connection
```bash
# Test database connection
az postgres flexible-server execute \
  --resource-group openpolicy-platform-rg \
  --name openpolicy-postgresql \
  --database-name openpolicy \
  --querytext "SELECT version();"
```

### Check Redis Connection
```bash
# Test Redis connection
az redis list-keys \
  --resource-group openpolicy-platform-rg \
  --name openpolicy-redis
```

### Check Service Status
```bash
# Check all services
docker-compose -f docker-compose.azure.yml ps

# Check specific service logs
docker-compose -f docker-compose.azure.yml logs api
docker-compose -f docker-compose.azure.yml logs web
```

## 🗄️ Step 7: Import Database Data (Optional)

If you have existing database data to import:

```bash
# Get connection string
POSTGRES_HOST=$(az postgres flexible-server show \
  --resource-group openpolicy-platform-rg \
  --name openpolicy-postgresql \
  --query fullyQualifiedDomainName -o tsv)

# Import data (replace path with your actual SQL file)
psql "host=$POSTGRES_HOST port=5432 dbname=openpolicy user=openpolicy password=YourSecurePassword123! sslmode=require" < your_database_export.sql
```

## 🌐 Step 8: Access Your Platform

- **Web Interface**: Check the Docker Compose logs for the web service URL
- **API**: Check the Docker Compose logs for the API service URL
- **Database**: Access via Azure Portal or Azure CLI

## 🆘 Troubleshooting Common Issues

### Issue 1: PostgreSQL Creation Fails
**Problem**: `az postgres flexible-server create` command fails
**Solution**: Use the corrected command with `--yes` flag and proper parameters

### Issue 2: Firewall Rules
**Problem**: Can't connect to PostgreSQL
**Solution**: Ensure firewall rules are configured to allow connections

### Issue 3: ACR Authentication
**Problem**: Docker push fails
**Solution**: Run `az acr login --name your-acr-name`

### Issue 4: Resource Group Not Found
**Problem**: Resources can't be created
**Solution**: Ensure you're in the correct subscription and region

### Issue 5: Docker Compose Fails
**Problem**: Services won't start
**Solution**: Check the `.env.azure` file and ensure all variables are set correctly

## 📊 Monitoring and Maintenance

### Check Resource Usage
```bash
# Monitor resource usage
az monitor metrics list \
  --resource-group openpolicy-platform-rg \
  --resource-type Microsoft.DBforPostgreSQL/flexibleServers \
  --resource-name openpolicy-postgresql \
  --metric "cpu_percent,memory_percent"
```

### Backup Database
```bash
# Create backup
az postgres flexible-server execute \
  --resource-group openpolicy-platform-rg \
  --name openpolicy-postgresql \
  --database-name openpolicy \
  --querytext "SELECT pg_backup_start('backup_$(date +%Y%m%d_%H%M%S)');"
```

## 💰 Cost Optimization

- Use Basic SKUs for development
- Consider reserved instances for production
- Monitor spending with Azure Cost Management
- Use Azure Advisor for recommendations

## 🎯 Next Steps

1. **Customize Configuration**: Update environment variables for your specific needs
2. **Set Up Monitoring**: Configure Azure Monitor and Application Insights
3. **Implement CI/CD**: Set up GitHub Actions or Azure DevOps for automated deployments
4. **Security Hardening**: Configure network security groups and access policies
5. **Backup Strategy**: Implement automated backup and disaster recovery

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review Azure Portal logs and metrics
3. Check Docker Compose logs
4. Verify all prerequisites are installed
5. Ensure you have proper Azure permissions

---

**Note**: This guide assumes you're using the `canadacentral` region. Adjust the location parameter if you prefer a different region.
