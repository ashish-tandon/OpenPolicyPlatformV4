# 🚀 Open Policy Platform - Full Deployment Guide

## 📋 **OVERVIEW**

This guide provides comprehensive instructions for deploying the complete Open Policy Platform with all 23 microservices on your local machine.

### **What You'll Get:**
- ✅ **23 Microservices** running simultaneously
- ✅ **API Gateway** routing all requests
- ✅ **Centralized Monitoring** with Prometheus & Grafana
- ✅ **Background Workers** for data processing
- ✅ **Complete Frontend** with modern UI
- ✅ **Database & Caching** infrastructure

---

## 🎯 **PREREQUISITES**

### **Required Software:**
- **Docker** (version 20.10+)
- **Docker Compose** (version 2.0+)
- **Git** (for cloning the repository)
- **curl** (for health checks)

### **System Requirements:**
- **RAM**: Minimum 8GB, Recommended 16GB+
- **Storage**: Minimum 20GB free space
- **CPU**: 4+ cores recommended
- **OS**: macOS, Linux, or Windows with Docker Desktop

### **Verify Installation:**
```bash
# Check Docker
docker --version
docker-compose --version

# Check Docker daemon
docker info

# Check available resources
docker system df
```

---

## 🚀 **QUICK START**

### **1. Clone and Navigate:**
```bash
git clone <your-repo-url>
cd open-policy-platform
```

### **2. Run Full Deployment:**
```bash
# Make script executable (if not already)
chmod +x deploy-full.sh

# Run the full deployment
./deploy-full.sh
```

### **3. Wait for Completion:**
The script will:
- ✅ Check prerequisites
- ✅ Validate configuration
- ✅ Build all services
- ✅ Start infrastructure
- ✅ Deploy microservices
- ✅ Run health checks
- ✅ Display status

**Expected Time**: 10-20 minutes depending on your system

---

## 🔧 **MANUAL DEPLOYMENT**

If you prefer manual control or need to troubleshoot:

### **1. Start Infrastructure:**
```bash
docker-compose -f docker-compose.full.yml up -d postgres redis
```

### **2. Wait for Database:**
```bash
# Check PostgreSQL health
docker-compose -f docker-compose.full.yml exec postgres pg_isready -U openpolicy -d openpolicy
```

### **3. Start Core Services:**
```bash
docker-compose -f docker-compose.full.yml up -d --build \
  auth-service policy-service search-service notification-service \
  config-service monitoring-service etl-service scraper-service
```

### **4. Start Specialized Services:**
```bash
docker-compose -f docker-compose.full.yml up -d --build \
  mobile-api legacy-django committees-service debates-service votes-service
```

### **5. Start Business Services:**
```bash
docker-compose -f docker-compose.full.yml up -d --build \
  representatives-service files-service dashboard-service \
  data-management-service analytics-service reporting-service \
  workflow-service integration-service
```

### **6. Start Utility Services:**
```bash
docker-compose -f docker-compose.full.yml up -d --build \
  plotly-service mcp-service
```

### **7. Start API Gateway:**
```bash
docker-compose -f docker-compose.full.yml up -d --build api-gateway
```

### **8. Start Remaining Services:**
```bash
docker-compose -f docker-compose.full.yml up -d \
  api web prometheus grafana celery-worker celery-beat flower scraper-runner
```

---

## 🌐 **SERVICE ENDPOINTS**

### **Main Access Points:**
| Service | URL | Port | Purpose |
|----------|-----|------|---------|
| **API Gateway** | http://localhost:9000 | 9000 | Main entry point for all APIs |
| **Frontend** | http://localhost:5173 | 5173 | Web application interface |
| **Legacy API** | http://localhost:8000 | 8000 | Backward compatibility |

### **Individual Microservices:**
| Service | Port | Health Check |
|---------|------|--------------|
| Auth Service | 9001 | `/healthz` |
| Policy Service | 9002 | `/healthz` |
| Search Service | 9003 | `/healthz` |
| Notification Service | 9004 | `/healthz` |
| Config Service | 9005 | `/healthz` |
| Monitoring Service | 9006 | `/healthz` |
| ETL Service | 9007 | `/healthz` |
| Scraper Service | 9008 | `/healthz` |
| Mobile API | 8009 | `/healthz` |
| Legacy Django | 8010 | `/healthz` |
| Committees Service | 9011 | `/healthz` |
| Debates Service | 9012 | `/healthz` |
| Votes Service | 9013 | `/healthz` |
| Representatives Service | 8014 | `/healthz` |
| Files Service | 8015 | `/healthz` |
| Dashboard Service | 8016 | `/healthz` |
| Data Management Service | 8017 | `/healthz` |
| Analytics Service | 8018 | `/healthz` |
| Reporting Service | 8019 | `/healthz` |
| Workflow Service | 8020 | `/healthz` |
| Integration Service | 8021 | `/healthz` |
| Plotly Service | 9019 | `/healthz` |
| MCP Service | 9020 | `/healthz` |

### **Infrastructure Services:**
| Service | Port | Purpose |
|---------|------|---------|
| PostgreSQL | 5432 | Primary database |
| Redis | 6379 | Caching & message broker |
| Prometheus | 9090 | Metrics collection |
| Grafana | 3000 | Monitoring dashboards |
| Flower | 5555 | Celery task monitoring |

---

## 🔍 **MONITORING & HEALTH CHECKS**

### **Service Health Dashboard:**
```bash
# Check all service status
docker-compose -f docker-compose.full.yml ps

# Check specific service logs
docker-compose -f docker-compose.full.yml logs -f [service-name]

# Check service health
curl http://localhost:9000/status
```

### **Grafana Dashboards:**
- **URL**: http://localhost:3000
- **Username**: `admin`
- **Password**: `admin`
- **Features**: Service metrics, performance monitoring, alerting

### **Prometheus Metrics:**
- **URL**: http://localhost:9090
- **Features**: Raw metrics, query interface, alerting rules

---

## 🛠️ **TROUBLESHOOTING**

### **Common Issues:**

#### **1. Port Conflicts:**
```bash
# Check what's using a port
lsof -i :9000

# Stop conflicting service
docker-compose -f docker-compose.full.yml down
```

#### **2. Service Won't Start:**
```bash
# Check service logs
docker-compose -f docker-compose.full.yml logs [service-name]

# Check service configuration
docker-compose -f docker-compose.full.yml config
```

#### **3. Database Connection Issues:**
```bash
# Check PostgreSQL health
docker-compose -f docker-compose.full.yml exec postgres pg_isready -U openpolicy -d openpolicy

# Check database logs
docker-compose -f docker-compose.full.yml logs postgres
```

#### **4. Memory Issues:**
```bash
# Check Docker resource usage
docker system df
docker stats

# Increase Docker memory limit in Docker Desktop settings
```

### **Reset Everything:**
```bash
# Stop all services
docker-compose -f docker-compose.full.yml down

# Remove all containers and networks
docker-compose -f docker-compose.full.yml down --remove-orphans

# Remove volumes (WARNING: This will delete all data)
docker-compose -f docker-compose.full.yml down -v

# Clean up Docker system
docker system prune -a --volumes

# Start fresh
./deploy-full.sh
```

---

## 📊 **PERFORMANCE OPTIMIZATION**

### **Resource Allocation:**
- **PostgreSQL**: 2-4GB RAM
- **Redis**: 1-2GB RAM
- **Microservices**: 512MB-1GB RAM each
- **Total**: 16-24GB RAM recommended

### **Docker Optimizations:**
```bash
# Enable BuildKit for faster builds
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# Use multi-stage builds in Dockerfiles
# Enable layer caching
# Use .dockerignore files
```

### **Service Scaling:**
```bash
# Scale specific services
docker-compose -f docker-compose.full.yml up -d --scale auth-service=2

# Check resource usage
docker stats
```

---

## 🔒 **SECURITY CONSIDERATIONS**

### **Development Environment:**
- ✅ Default passwords (change in production)
- ✅ Exposed ports (restrict in production)
- ✅ No SSL/TLS (add in production)

### **Production Hardening:**
- 🔒 Change default passwords
- 🔒 Use environment variables for secrets
- 🔒 Restrict network access
- 🔒 Enable SSL/TLS
- 🔒 Use secrets management
- 🔒 Implement proper authentication

---

## 📚 **ADDITIONAL RESOURCES**

### **Documentation:**
- [Architecture Overview](../architecture/README.md)
- [API Documentation](../api/README.md)
- [Service Development Guide](../development/README.md)

### **Useful Commands:**
```bash
# View all running containers
docker ps

# View service logs
docker-compose -f docker-compose.full.yml logs -f

# Execute commands in containers
docker-compose -f docker-compose.full.yml exec [service-name] [command]

# Update services
docker-compose -f docker-compose.full.yml pull
docker-compose -f docker-compose.full.yml up -d

# Backup data
docker-compose -f docker-compose.full.yml exec postgres pg_dump -U openpolicy openpolicy_app > backup.sql
```

---

## 🎉 **SUCCESS INDICATORS**

### **When Everything is Working:**
- ✅ All 23 services show "Up" status
- ✅ API Gateway responds at http://localhost:9000
- ✅ Frontend loads at http://localhost:5173
- ✅ Grafana dashboard accessible at http://localhost:3000
- ✅ Health checks pass for all services
- ✅ No error messages in logs

### **Next Steps:**
1. **Explore the API**: Use the API Gateway at port 9000
2. **Test the Frontend**: Navigate to port 5173
3. **Monitor Performance**: Check Grafana dashboards
4. **Develop**: Start building new features
5. **Scale**: Add more instances of services as needed

---

## 🆘 **GETTING HELP**

### **If You're Stuck:**
1. **Check logs**: `docker-compose -f docker-compose.full.yml logs -f`
2. **Verify ports**: Ensure no conflicts with existing services
3. **Check resources**: Ensure sufficient RAM and disk space
4. **Review configuration**: Validate docker-compose.full.yml syntax

### **Support Resources:**
- **GitHub Issues**: Report bugs and request features
- **Documentation**: Check this guide and related docs
- **Community**: Join discussions and ask questions

---

**🚀 Happy Deploying! Your Open Policy Platform is ready to transform policy management! 🚀**
