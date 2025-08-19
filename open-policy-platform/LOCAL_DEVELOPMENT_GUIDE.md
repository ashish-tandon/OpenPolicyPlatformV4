# 🚀 **OPEN POLICY PLATFORM V4 - LOCAL DEVELOPMENT GUIDE**

## 📅 **Guide Created**: 2025-08-19 00:35 UTC
## 🎯 **Purpose**: Set up complete local development environment on your laptop

---

## 🏗️ **LOCAL DEVELOPMENT ARCHITECTURE**

### **Services Running Locally**
1. **PostgreSQL Database** - Local database for development
2. **Redis Cache** - Local caching service
3. **API Service** - FastAPI backend with hot-reload
4. **Web Frontend** - React/Vite frontend with hot-reload
5. **Scraper Service** - Data collection service
6. **Prometheus** - Local metrics collection
7. **Grafana** - Local monitoring dashboards

### **Port Mapping**
- **PostgreSQL**: 5432
- **Redis**: 6379
- **API**: 8000
- **Web Frontend**: 3000
- **Scraper**: 9008
- **Prometheus**: 9090
- **Grafana**: 3001

---

## 🚀 **QUICK START - AUTOMATED SETUP**

### **1. Run the Setup Script**
```bash
# Make sure you're in the open-policy-platform directory
cd open-policy-platform

# Run the automated setup script
./setup-local-development.sh
```

### **2. What the Script Does**
- ✅ Checks Docker status
- ✅ Verifies port availability
- ✅ Creates necessary directories
- ✅ Builds and starts all services
- ✅ Waits for services to be healthy
- ✅ Initializes database with sample data
- ✅ Displays final status and access points

---

## 🔧 **MANUAL SETUP (Alternative)**

### **1. Prerequisites**
```bash
# Ensure Docker Desktop is running
docker --version
docker compose version

# Check if ports are available
lsof -i :5432 -i :6379 -i :8000 -i :3000 -i :9008 -i :9090 -i :3001
```

### **2. Create Local Environment**
```bash
# Create data directories
mkdir -p data/{postgres,redis,prometheus,grafana,scraper/{reports,logs}}

# Start services
docker compose -f docker-compose.local.yml up -d --build
```

### **3. Wait for Services**
```bash
# Check service status
docker compose -f docker-compose.local.yml ps

# Monitor logs
docker compose -f docker-compose.local.yml logs -f
```

---

## 📊 **VERIFYING YOUR SETUP**

### **Health Checks**
```bash
# API Service
curl http://localhost:8000/health

# Scraper Service
curl http://localhost:9008/health

# Web Frontend
curl http://localhost:3000

# Database
docker exec openpolicy-local-postgres pg_isready -U openpolicy -d openpolicy

# Redis
docker exec openpolicy-local-redis redis-cli ping
```

### **Expected Responses**
- **API Health**: `{"status":"healthy","timestamp":"...","version":"1.0.0"}`
- **Scraper Health**: `{"status":"healthy","service":"scraper-service"}`
- **Web Frontend**: HTML response (200 OK)
- **Database**: `openpolicy:5432 - accepting connections`
- **Redis**: `PONG`

---

## 🛠️ **DEVELOPMENT WORKFLOW**

### **1. Making API Changes**
```bash
# The API service has hot-reload enabled
# Edit files in ./backend/ directory
# Changes are automatically detected and reloaded

# View API logs
docker compose -f docker-compose.local.yml logs -f api

# Restart API service if needed
docker compose -f docker-compose.local.yml restart api
```

### **2. Making Frontend Changes**
```bash
# The web service has hot-reload enabled
# Edit files in ./web/ directory
# Changes are automatically detected and reloaded

# View web logs
docker compose -f docker-compose.local.yml logs -f web

# Restart web service if needed
docker compose -f docker-compose.local.yml restart web
```

### **3. Making Scraper Changes**
```bash
# Edit files in ./services/scraper-service/ directory
# Restart the service to apply changes

docker compose -f docker-compose.local.yml restart scraper
```

---

## 📚 **DEVELOPMENT ENDPOINTS**

### **API Endpoints**
- **Health**: `GET http://localhost:8000/health`
- **Comprehensive Health**: `GET http://localhost:8000/api/v1/health/comprehensive`
- **Policies**: `GET http://localhost:8000/api/v1/policies/`
- **Categories**: `GET http://localhost:8000/api/v1/policies/list/categories`
- **Jurisdictions**: `GET http://localhost:8000/api/v1/policies/list/jurisdictions`
- **Stats**: `GET http://localhost:8000/api/v1/policies/summary/stats`

### **Scraper Endpoints**
- **Health**: `GET http://localhost:9008/health`
- **Stats**: `GET http://localhost:9008/stats`
- **Jobs**: `GET http://localhost:9008/jobs`
- **Data**: `GET http://localhost:9008/data`

### **Monitoring Endpoints**
- **Prometheus**: `http://localhost:9090`
- **Grafana**: `http://localhost:3001` (admin/admin)

---

## 🔍 **DEBUGGING & TROUBLESHOOTING**

### **Common Issues & Solutions**

#### **1. Port Already in Use**
```bash
# Check what's using the port
lsof -i :8000

# Kill the process or change the port in docker-compose.local.yml
```

#### **2. Service Not Starting**
```bash
# Check service logs
docker compose -f docker-compose.local.yml logs [service-name]

# Check service status
docker compose -f docker-compose.local.yml ps

# Restart specific service
docker compose -f docker-compose.local.yml restart [service-name]
```

#### **3. Database Connection Issues**
```bash
# Check if database is running
docker compose -f docker-compose.local.yml ps postgres

# Check database logs
docker compose -f docker-compose.local.yml logs postgres

# Test database connection
docker exec openpolicy-local-postgres psql -U openpolicy -d openpolicy -c "SELECT 1;"
```

#### **4. Hot Reload Not Working**
```bash
# Check if volumes are mounted correctly
docker compose -f docker-compose.local.yml exec api ls -la /app

# Restart the service
docker compose -f docker-compose.local.yml restart api
```

---

## 📁 **PROJECT STRUCTURE FOR DEVELOPMENT**

```
open-policy-platform/
├── backend/                    # API service source code
│   ├── api/
│   │   ├── main.py           # FastAPI application
│   │   ├── config.py         # Configuration
│   │   └── routers/          # API routes
│   └── Dockerfile
├── web/                       # Frontend source code
│   ├── src/                  # React components
│   ├── public/               # Static assets
│   └── Dockerfile
├── services/
│   └── scraper-service/      # Scraper service
│       ├── src/              # Python source
│       └── Dockerfile
├── docker-compose.local.yml   # Local development setup
├── setup-local-development.sh # Automated setup script
└── LOCAL_DEVELOPMENT_GUIDE.md # This guide
```

---

## 🚀 **DEVELOPMENT COMMANDS REFERENCE**

### **Service Management**
```bash
# Start all services
docker compose -f docker-compose.local.yml up -d

# Stop all services
docker compose -f docker-compose.local.yml down

# Restart specific service
docker compose -f docker-compose.local.yml restart [service]

# View service status
docker compose -f docker-compose.local.yml ps

# View service logs
docker compose -f docker-compose.local.yml logs -f [service]
```

### **Database Operations**
```bash
# Connect to database
docker exec -it openpolicy-local-postgres psql -U openpolicy -d openpolicy

# Run SQL file
docker exec -i openpolicy-local-postgres psql -U openpolicy -d openpolicy < script.sql

# Backup database
docker exec openpolicy-local-postgres pg_dump -U openpolicy openpolicy > backup.sql
```

### **Development Tools**
```bash
# Run tests (if available)
docker compose -f docker-compose.local.yml exec api python -m pytest

# Install new Python packages
docker compose -f docker-compose.local.yml exec api pip install package-name

# Install new Node packages
docker compose -f docker-compose.local.yml exec web npm install package-name
```

---

## 🔄 **SYNCING WITH AZURE DEPLOYMENT**

### **Local vs Azure Differences**
- **Database**: Local PostgreSQL vs Azure PostgreSQL
- **Cache**: Local Redis vs Azure Redis
- **Storage**: Local volumes vs Azure Storage
- **Authentication**: Local mock vs Azure Key Vault
- **Monitoring**: Local Prometheus/Grafana vs Azure Insights

### **Environment Variables**
- **Local**: Uses `docker-compose.local.yml` with local values
- **Azure**: Uses `docker-compose.azure-simple.yml` with Azure values
- **Shared**: Core application logic and API endpoints

---

## 📈 **PERFORMANCE & OPTIMIZATION**

### **Local Development Tips**
1. **Use Volume Mounts**: Source code changes are reflected immediately
2. **Monitor Resource Usage**: Use `docker stats` to track container performance
3. **Database Indexing**: Add indexes for frequently queried fields
4. **Caching**: Utilize Redis for frequently accessed data
5. **Logging**: Set `LOG_LEVEL=DEBUG` for detailed debugging

### **Resource Monitoring**
```bash
# Monitor container resources
docker stats

# Monitor specific service
docker stats openpolicy-local-api

# Check disk usage
docker system df
```

---

## 🎯 **NEXT STEPS**

### **Immediate Actions**
1. **Run Setup Script**: `./setup-local-development.sh`
2. **Verify Services**: Check all health endpoints
3. **Explore API**: Test API endpoints with tools like Postman or curl
4. **Start Development**: Begin making changes to the codebase

### **Development Goals**
1. **Feature Development**: Implement new API endpoints
2. **Frontend Enhancement**: Improve user interface
3. **Data Processing**: Enhance scraper functionality
4. **Testing**: Add comprehensive test coverage
5. **Documentation**: Update API documentation

---

## 🎊 **CONCLUSION**

**Your local development environment is now ready with:**
- ✅ **Complete service stack** running locally
- ✅ **Hot-reload enabled** for rapid development
- ✅ **Local database** with sample data
- ✅ **Monitoring tools** for debugging
- ✅ **Comprehensive documentation** for reference

**🚀 Start developing and building amazing features for Open Policy Platform V4!**

---

## 📞 **SUPPORT & RESOURCES**

### **If You Need Help**
1. **Check Logs**: `docker compose -f docker-compose.local.yml logs -f [service]`
2. **Verify Health**: Test health endpoints
3. **Check Status**: `docker compose -f docker-compose.local.yml ps`
4. **Restart Services**: `docker compose -f docker-compose.local.yml restart`

### **Useful Resources**
- **Docker Compose**: https://docs.docker.com/compose/
- **FastAPI**: https://fastapi.tiangolo.com/
- **React**: https://reactjs.org/
- **PostgreSQL**: https://www.postgresql.org/docs/
- **Redis**: https://redis.io/documentation

**Happy Coding! 🎉**
