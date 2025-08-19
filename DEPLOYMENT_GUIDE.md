# 🚀 OpenPolicyPlatform V4 - DEPLOYMENT GUIDE

## 📋 Deployment Options

I've created **TWO deployment scripts** for you:

### 1. **DEPLOY_NOW.sh** - Full Cloud Deployment (Recommended)
- Deploys to GitHub and Azure
- Creates all cloud resources
- Sets up CI/CD pipelines
- Fully automated deployment

### 2. **DEPLOY_LOCAL.sh** - Local Development
- Runs everything on your machine
- Uses Docker Compose
- No cloud accounts needed
- Perfect for testing

## 🚀 Option 1: Full Cloud Deployment

### Prerequisites
1. **GitHub CLI** installed and authenticated:
   ```bash
   # Install GitHub CLI
   brew install gh  # macOS
   # or
   winget install --id GitHub.cli  # Windows
   
   # Authenticate
   gh auth login
   ```

2. **Azure CLI** installed and authenticated:
   ```bash
   # Install Azure CLI
   brew install azure-cli  # macOS
   # or
   curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash  # Linux
   
   # Authenticate
   az login
   ```

3. **Docker** installed and running

### Run Full Deployment
```bash
# From the workspace directory
./DEPLOY_NOW.sh
```

This will:
1. ✅ Create 6 GitHub repositories
2. ✅ Push all code to GitHub
3. ✅ Create Azure resources (PostgreSQL, Redis, Container Registry, etc.)
4. ✅ Configure GitHub secrets for CI/CD
5. ✅ Trigger automatic deployments
6. ✅ Monitor deployment progress

### What Gets Created

**GitHub Repositories:**
- https://github.com/ashish-tandon/openpolicy-infrastructure
- https://github.com/ashish-tandon/openpolicy-data
- https://github.com/ashish-tandon/openpolicy-business
- https://github.com/ashish-tandon/openpolicy-frontend
- https://github.com/ashish-tandon/openpolicy-legacy
- https://github.com/ashish-tandon/openpolicy-orchestration

**Azure Resources:**
- Resource Group: `openpolicy-platform-rg`
- Container Registry: `openpolicyacr`
- PostgreSQL Server: `openpolicy-postgresql`
- Redis Cache: `openpolicy-redis`
- Storage Account: `openpolicystorage`
- Application Insights: `openpolicy-appinsights`
- Container Apps Environment: `openpolicy-env`

## 🖥️ Option 2: Local Deployment

### Prerequisites
1. **Docker Desktop** installed and running
2. At least 8GB RAM available
3. 20GB disk space

### Run Local Deployment
```bash
# From the workspace directory
./DEPLOY_LOCAL.sh
```

This will:
1. ✅ Create local environment files
2. ✅ Start PostgreSQL, Redis, Elasticsearch
3. ✅ Start monitoring stack (Prometheus, Grafana)
4. ✅ Set up networking between services
5. ✅ Display access URLs

### Access Local Services
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379
- **Elasticsearch**: http://localhost:9200
- **Kibana**: http://localhost:5601
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001 (admin/admin)

## 📊 Post-Deployment Steps

### For Cloud Deployment
1. **Monitor CI/CD Progress**:
   ```bash
   # Check GitHub Actions
   gh run list --repo ashish-tandon/openpolicy-infrastructure
   
   # Check Azure deployments
   az containerapp list -g openpolicy-platform-rg -o table
   ```

2. **Get Application URLs**:
   ```bash
   # List all Container Apps
   az containerapp list -g openpolicy-platform-rg --query "[].{Name:name, URL:properties.configuration.ingress.fqdn}" -o table
   ```

3. **View Logs**:
   ```bash
   # GitHub Actions logs
   gh run view --repo ashish-tandon/openpolicy-infrastructure
   
   # Azure Container Apps logs
   az containerapp logs show -n <app-name> -g openpolicy-platform-rg
   ```

### For Local Deployment
1. **Check Service Health**:
   ```bash
   docker ps
   docker-compose -f migration-repos/docker-compose.unified.yml ps
   ```

2. **View Logs**:
   ```bash
   # All services
   docker-compose -f migration-repos/docker-compose.unified.yml logs -f
   
   # Specific service
   docker-compose -f migration-repos/docker-compose.unified.yml logs -f postgres
   ```

3. **Stop Services**:
   ```bash
   cd migration-repos
   docker-compose -f docker-compose.unified.yml down
   ```

## 🔧 Troubleshooting

### GitHub Authentication Failed
```bash
gh auth status  # Check status
gh auth login   # Re-authenticate
```

### Azure Authentication Failed
```bash
az account show  # Check status
az login         # Re-authenticate
```

### Port Already in Use (Local)
```bash
# Find process using port
lsof -i :5432  # Example for PostgreSQL
# Kill process or change port in docker-compose
```

### Docker Not Running
- Start Docker Desktop
- Or start Docker daemon: `sudo systemctl start docker`

### Deployment Failed
1. Check logs in GitHub Actions
2. Check Azure Portal for resource status
3. Review error messages in deployment output

## 🎯 Next Steps After Deployment

1. **Set Up Domain Names** (Optional)
   - Configure custom domains in Azure Container Apps
   - Update DNS records

2. **Configure SSL/TLS**
   - Azure Container Apps provides automatic HTTPS
   - Configure custom certificates if needed

3. **Set Up Monitoring Alerts**
   - Configure Application Insights alerts
   - Set up Grafana dashboards

4. **Deploy Sample Data**
   - Run database migrations
   - Import sample data
   - Test scrapers

5. **Configure Backup**
   - Set up PostgreSQL backups
   - Configure storage account backups

## 📞 Support

If you encounter issues:

1. **Check the logs** first
2. **Review error messages** carefully
3. **Verify prerequisites** are met
4. **Check service health** endpoints

### Health Check URLs
- Infrastructure: `http://<service-url>/healthz`
- API Gateway: `http://<gateway-url>/health`
- Individual services: `http://<service-url>:port/healthz`

## ✅ Success Indicators

Your deployment is successful when:

1. **All GitHub Actions show green checkmarks** ✅
2. **Azure Container Apps show "Running" status** ✅
3. **Health endpoints return 200 OK** ✅
4. **Grafana shows healthy metrics** ✅
5. **No error logs in past 5 minutes** ✅

## 🎉 Congratulations!

Once deployed, you'll have a fully functional, scalable OpenPolicy Platform V4 with:
- 6 independent repositories
- Automated CI/CD pipelines
- Cloud-native infrastructure
- Comprehensive monitoring
- Ready for production use

**Choose your deployment method and run the appropriate script!** 🚀