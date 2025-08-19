# 🚀 **OPEN POLICY PLATFORM V4 - LOCAL DEVELOPMENT SUMMARY**

## 📅 **Document Created**: 2025-08-19 00:40 UTC
## 🎯 **Purpose**: Complete local development setup replacing Azure cloud services

---

## 🔄 **AZURE TO LOCAL SERVICE MAPPING**

### **Cloud Services → Local Alternatives**

| **Azure Service** | **Local Alternative** | **Purpose** | **Access** |
|-------------------|----------------------|-------------|------------|
| **Azure PostgreSQL** | **Local PostgreSQL** | Database | `localhost:5432` |
| **Azure Redis Cache** | **Local Redis** | Caching | `localhost:6379` |
| **Azure Storage** | **MinIO (S3-compatible)** | File Storage | `localhost:9000` |
| **Azure Key Vault** | **HashiCorp Vault** | Secrets Management | `localhost:8200` |
| **Azure Search** | **Elasticsearch** | Full-text Search | `localhost:9200` |
| **Azure App Insights** | **Prometheus + Grafana** | Monitoring | `localhost:9090,3001` |

---

## 🏗️ **COMPLETE LOCAL SERVICE STACK**

### **Core Services**
1. **PostgreSQL Database** - `localhost:5432`
   - Database: `openpolicy`
   - User: `openpolicy`
   - Password: `openpolicy123`

2. **Redis Cache** - `localhost:6379`
   - No authentication required locally

3. **MinIO Storage** - `localhost:9000`
   - Console: `localhost:9001`
   - Access Key: `minioadmin`
   - Secret Key: `minio123`

4. **Vault Secrets** - `localhost:8200`
   - Token: `vault123`
   - Development mode (no persistence)

5. **Elasticsearch** - `localhost:9200`
   - Single node setup
   - Security disabled for development

### **Application Services**
6. **API Service** - `localhost:8000`
   - FastAPI backend with hot-reload
   - All endpoints functional

7. **Web Frontend** - `localhost:3000`
   - React/Vite with hot-reload
   - Connected to local API

8. **Scraper Service** - `localhost:9008`
   - Data collection service
   - Connected to local database

9. **Auth Service** - `localhost:8001`
   - Authentication and authorization
   - JWT token management

10. **Policy Service** - `localhost:8002`
    - Policy management
    - Connected to local API

11. **Data Management** - `localhost:8003`
    - Data processing and management
    - File operations via MinIO

12. **Search Service** - `localhost:8004`
    - Full-text search capabilities
    - Connected to Elasticsearch

### **Monitoring Services**
13. **Prometheus** - `localhost:9090`
    - Metrics collection
    - Service monitoring

14. **Grafana** - `localhost:3001`
    - Dashboards: `admin/admin`
    - Visualization of metrics

---

## 🚀 **QUICK START COMMANDS**

### **1. Full Setup (First Time)**
```bash
# Run the complete setup script
./setup-local-development.sh
```

### **2. Quick Start (Subsequent Times)**
```bash
# Start all services quickly
./start-local-dev.sh
```

### **3. Manual Control**
```bash
# Start services
docker compose -f docker-compose.local.yml up -d

# Stop services
docker compose -f docker-compose.local.yml down

# View status
docker compose -f docker-compose.local.yml ps

# View logs
docker compose -f docker-compose.local.yml logs -f [service]
```

---

## 🔐 **LOCAL SERVICE CREDENTIALS**

### **Database Access**
```bash
# Connect to PostgreSQL
docker exec -it openpolicy-local-postgres psql -U openpolicy -d openpolicy

# Or from host
psql -h localhost -U openpolicy -d openpolicy
# Password: openpolicy123
```

### **Storage Access**
```bash
# MinIO Console
# URL: http://localhost:9001
# Username: minioadmin
# Password: minio123

# Create bucket
docker exec openpolicy-local-minio mkdir -p /data/openpolicy-bucket
```

### **Secrets Access**
```bash
# Vault Console
# URL: http://localhost:8200
# Token: vault123

# Check status
curl http://localhost:8200/v1/sys/health
```

### **Search Access**
```bash
# Elasticsearch
# URL: http://localhost:9200

# Check cluster health
curl http://localhost:9200/_cluster/health
```

---

## 📁 **DEVELOPMENT WORKFLOW**

### **Making Changes**
1. **API Changes** - Edit files in `./backend/` (hot-reload)
2. **Frontend Changes** - Edit files in `./web/` (hot-reload)
3. **Service Changes** - Edit files in `./services/[service-name]/`
4. **Database Changes** - Use PostgreSQL directly or migrations
5. **Storage Changes** - Use MinIO console or API
6. **Search Changes** - Use Elasticsearch API

### **Hot Reload Services**
- **API Service**: ✅ Automatic reload
- **Web Frontend**: ✅ Automatic reload
- **Other Services**: Restart required

### **Data Persistence**
- **PostgreSQL**: ✅ Persistent (data/postgres/)
- **Redis**: ✅ Persistent (data/redis/)
- **MinIO**: ✅ Persistent (data/minio/)
- **Elasticsearch**: ✅ Persistent (data/elasticsearch/)
- **Vault**: ❌ Not persistent (dev mode)

---

## 🔍 **TROUBLESHOOTING LOCAL SERVICES**

### **Common Issues**

#### **1. Port Conflicts**
```bash
# Check what's using a port
lsof -i :8000

# Kill the process or change port in docker-compose.local.yml
```

#### **2. Service Not Starting**
```bash
# Check logs
docker compose -f docker-compose.local.yml logs [service]

# Check status
docker compose -f docker-compose.local.yml ps

# Restart service
docker compose -f docker-compose.local.yml restart [service]
```

#### **3. Database Connection Issues**
```bash
# Check if database is running
docker compose -f docker-compose.local.yml ps postgres

# Test connection
docker exec openpolicy-local-postgres pg_isready -U openpolicy -d openpolicy
```

#### **4. Storage Issues**
```bash
# Check MinIO status
curl http://localhost:9000/minio/health/live

# Check MinIO logs
docker compose -f docker-compose.local.yml logs minio
```

---

## 📊 **PERFORMANCE & RESOURCES**

### **Resource Requirements**
- **Memory**: Minimum 8GB RAM recommended
- **CPU**: 4+ cores recommended
- **Storage**: 10GB+ free space
- **Docker**: Latest version with 4GB+ memory allocation

### **Optimization Tips**
1. **Elasticsearch**: Limited to 512MB RAM for development
2. **PostgreSQL**: Uses default settings (adjustable)
3. **Redis**: Uses default settings (adjustable)
4. **MinIO**: Uses default settings (adjustable)

### **Monitoring Resources**
```bash
# Check container resource usage
docker stats

# Check disk usage
docker system df

# Clean up unused resources
docker system prune -a
```

---

## 🔄 **SYNCING WITH AZURE DEPLOYMENT**

### **Code Compatibility**
- **API Endpoints**: ✅ Identical
- **Database Schema**: ✅ Identical
- **Service Logic**: ✅ Identical
- **Configuration**: ⚠️ Different (local vs Azure)

### **Environment Variables**
- **Local**: Uses `docker-compose.local.yml`
- **Azure**: Uses `docker-compose.azure-simple.yml`
- **Shared**: Core application code

### **Data Migration**
- **Local → Azure**: Export from local, import to Azure
- **Azure → Local**: Export from Azure, import to local
- **Schema**: Identical between environments

---

## 🎯 **DEVELOPMENT BENEFITS**

### **Advantages of Local Development**
1. **No Internet Dependency** - Works offline
2. **Fast Iteration** - Hot-reload enabled
3. **Full Control** - All services local
4. **Cost Effective** - No cloud charges
5. **Privacy** - All data stays local
6. **Customization** - Easy to modify services

### **Local vs Azure Trade-offs**
| **Aspect** | **Local** | **Azure** |
|------------|-----------|-----------|
| **Setup Time** | ⚠️ Longer initial setup | ✅ Quick deployment |
| **Cost** | ✅ Free | ❌ Pay-per-use |
| **Performance** | ⚠️ Limited by hardware | ✅ Scalable |
| **Reliability** | ⚠️ Depends on local machine | ✅ High availability |
| **Security** | ⚠️ Basic (dev mode) | ✅ Enterprise-grade |
| **Scalability** | ❌ Limited | ✅ Auto-scaling |

---

## 🚀 **NEXT STEPS**

### **Immediate Actions**
1. **Run Setup**: `./setup-local-development.sh`
2. **Verify Services**: Check all health endpoints
3. **Explore APIs**: Test all service endpoints
4. **Start Development**: Begin coding features

### **Development Goals**
1. **Feature Development** - Build new capabilities
2. **Service Integration** - Connect local services
3. **Testing** - Add comprehensive tests
4. **Documentation** - Update API docs
5. **Performance** - Optimize local services

---

## 🎊 **CONCLUSION**

**Your local development environment now provides:**
- ✅ **Complete service stack** running locally
- ✅ **Azure service alternatives** for all functionality
- ✅ **Hot-reload development** for rapid iteration
- ✅ **Persistent data storage** across restarts
- ✅ **Comprehensive monitoring** and debugging
- ✅ **Full development control** without cloud dependencies

**🚀 Start developing with confidence - all key services are now executable locally!**

---

## 📞 **SUPPORT & RESOURCES**

### **If You Need Help**
1. **Check Service Status**: `docker compose -f docker-compose.local.yml ps`
2. **View Service Logs**: `docker compose -f docker-compose.local.yml logs -f [service]`
3. **Test Health Endpoints**: Use the health check URLs provided
4. **Restart Services**: `docker compose -f docker-compose.local.yml restart`

### **Useful Resources**
- **Docker Compose**: https://docs.docker.com/compose/
- **MinIO**: https://min.io/docs/
- **Vault**: https://www.vaultproject.io/docs
- **Elasticsearch**: https://www.elastic.co/guide/
- **PostgreSQL**: https://www.postgresql.org/docs/

**Happy Local Development! 🎉**
