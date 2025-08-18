# 🚀 Complete Open Policy Platform Deployment with Centralized Logging

## 🎯 **OVERVIEW**

This guide covers the **complete deployment** of the Open Policy Platform with **centralized logging infrastructure**. The platform now includes:

- **23 Microservices** (all business logic services)
- **ELK Stack** (Elasticsearch, Logstash, Kibana) for log management
- **Prometheus + Grafana** for metrics and monitoring
- **Fluentd** for log aggregation from all containers
- **Automatic log collection and stashing** to local logs folder

## 🏗️ **ARCHITECTURE OVERVIEW**

### **Logging Flow**
```
[All 23 Services] → [Fluentd] → [Elasticsearch] + [Local Log Files]
                           ↓
                    [Kibana] + [Prometheus] + [Grafana]
```

### **Service Categories**

#### **1. Infrastructure Services**
- **PostgreSQL** (Port 5432) - Database
- **Redis** (Port 6379) - Caching
- **Elasticsearch** (Port 9200) - Log storage and search
- **Logstash** (Ports 5044, 5000, 9600) - Log processing
- **Kibana** (Port 5601) - Log visualization
- **Prometheus** (Port 9090) - Metrics collection
- **Grafana** (Port 3001) - Metrics visualization
- **Fluentd** (Port 24224) - Log aggregation

#### **2. Core Microservices (23 Services)**
- **API Gateway** (Port 9000) - Central routing
- **Config Service** (Port 9001) - Configuration management
- **Auth Service** (Port 9002) - Authentication
- **Policy Service** (Port 9003) - Policy management
- **Notification Service** (Port 9004) - Notifications
- **Analytics Service** (Port 9005) - Analytics
- **Monitoring Service** (Port 9006) - System monitoring
- **ETL Service** (Port 9007) - Data transformation
- **Scraper Service** (Port 9008) - Web scraping
- **Search Service** (Port 9009) - Search functionality
- **Dashboard Service** (Port 9010) - Dashboards
- **Files Service** (Port 9011) - File management
- **Reporting Service** (Port 9012) - Report generation
- **Workflow Service** (Port 9013) - Workflow management
- **Integration Service** (Port 9014) - External integrations
- **Data Management Service** (Port 9015) - Data operations
- **Representatives Service** (Port 9016) - Representative data
- **Plotly Service** (Port 9017) - Data visualization
- **Mobile API** (Port 9018) - Mobile endpoints
- **Legacy Django** (Port 9019) - Legacy system support

#### **3. Frontend Services**
- **Web Frontend** (Port 3000) - React application

## 📁 **LOG STRUCTURE**

### **Automatic Log Collection**
All services automatically log to the following structure:

```
logs/
├── 📁 services/                    # Individual service logs
│   ├── api-gateway.log            # API Gateway logs
│   ├── config-service.log         # Config service logs
│   ├── auth-service.log           # Auth service logs
│   ├── policy-service.log         # Policy service logs
│   ├── notification-service.log   # Notification service logs
│   ├── analytics-service.log      # Analytics service logs
│   ├── monitoring-service.log     # Monitoring service logs
│   ├── etl-service.log            # ETL service logs
│   ├── scraper-service.log        # Scraper service logs
│   ├── search-service.log         # Search service logs
│   ├── dashboard-service.log      # Dashboard service logs
│   ├── files-service.log          # Files service logs
│   ├── reporting-service.log      # Reporting service logs
│   ├── workflow-service.log       # Workflow service logs
│   ├── integration-service.log    # Integration service logs
│   ├── data-management-service.log # Data management logs
│   ├── representatives-service.log # Representatives logs
│   ├── plotly-service.log         # Plotly service logs
│   ├── mobile-api.log             # Mobile API logs
│   ├── legacy-django.log          # Legacy Django logs
│   └── web-frontend.log           # Web frontend logs
├── 📁 infrastructure/              # Infrastructure logs
│   ├── postgres.log               # Database logs
│   ├── redis.log                  # Cache logs
│   ├── elasticsearch.log          # Elasticsearch logs
│   ├── logstash.log               # Logstash logs
│   ├── kibana.log                 # Kibana logs
│   ├── prometheus.log             # Prometheus logs
│   └── grafana.log                # Grafana logs
├── 📁 errors/                      # Error logs
│   └── application-errors.log     # All application errors
├── 📁 performance/                 # Performance logs
│   └── response-times.log         # Response time metrics
└── 📁 run/                         # Runtime logs
    └── health.log                 # Health check logs
```

## 🚀 **DEPLOYMENT PROCESS**

### **Prerequisites**
- Docker and Docker Compose installed
- At least 8GB RAM available
- At least 20GB disk space

### **Quick Start**
```bash
# 1. Navigate to project directory
cd open-policy-platform

# 2. Deploy everything with logging
./deploy-complete-with-logging.sh

# 3. Check status
./deploy-complete-with-logging.sh status

# 4. View logs
./deploy-complete-with-logging.sh logs [service-name]
```

### **Deployment Phases**

#### **Phase 1: Infrastructure (5 minutes)**
- PostgreSQL, Redis, Elasticsearch, Logstash, Kibana, Prometheus, Grafana, Fluentd
- All logging infrastructure starts first

#### **Phase 2: Microservices (10 minutes)**
- All 23 microservices start in parallel
- Each service automatically logs to Fluentd
- Fluentd forwards logs to Elasticsearch and local files

#### **Phase 3: Frontend (2 minutes)**
- React web application starts
- Connects to API Gateway and logging infrastructure

#### **Phase 4: Verification (5 minutes)**
- Health checks for all services
- Logging infrastructure verification
- Error collection and fixing (if any)

## 🔧 **MANAGEMENT COMMANDS**

### **Deployment Script Commands**
```bash
# Deploy everything (default)
./deploy-complete-with-logging.sh

# Show comprehensive status
./deploy-complete-with-logging.sh status

# View logs for all services
./deploy-complete-with-logging.sh logs

# View logs for specific service
./deploy-complete-with-logging.sh logs api-gateway

# Restart specific service
./deploy-complete-with-logging.sh restart config-service

# Check deployment errors
./deploy-complete-with-logging.sh errors

# Stop all services
./deploy-complete-with-logging.sh stop

# Show help
./deploy-complete-with-logging.sh help
```

### **Docker Compose Commands**
```bash
# View all running services
docker-compose -f docker-compose.complete.yml ps

# View logs for specific service
docker-compose -f docker-compose.complete.yml logs -f api-gateway

# Restart specific service
docker-compose -f docker-compose.complete.yml restart config-service

# Stop all services
docker-compose -f docker-compose.complete.yml down

# Rebuild and start specific service
docker-compose -f docker-compose.complete.yml up -d --build api-gateway
```

## 🌐 **ACCESS POINTS**

### **Application Access**
- **Web Frontend**: http://localhost:3000
- **API Gateway**: http://localhost:9000
- **Database**: localhost:5432
- **Redis**: localhost:6379

### **Logging & Monitoring Access**
- **Kibana (Logs)**: http://localhost:5601
- **Grafana (Metrics)**: http://localhost:3001
- **Prometheus (Metrics)**: http://localhost:9090
- **Elasticsearch (Log Storage)**: http://localhost:9200

## 📊 **MONITORING & OBSERVABILITY**

### **Automatic Metrics Collection**
- **Prometheus** collects metrics from all services every 15 seconds
- **Grafana** provides pre-configured dashboards
- **Service health** monitored via `/health` and `/healthz` endpoints

### **Log Analysis**
- **Kibana** provides powerful log search and analysis
- **Structured logging** with JSON format for easy parsing
- **Service identification** in all log entries
- **Error tracking** with automatic categorization

### **Performance Monitoring**
- **Response times** automatically logged
- **Resource usage** tracked per service
- **Database performance** monitored
- **Cache hit rates** tracked

## 🚨 **TROUBLESHOOTING**

### **Common Issues**

#### **1. Service Not Starting**
```bash
# Check service logs
./deploy-complete-with-logging.sh logs [service-name]

# Check Docker container status
docker-compose -f docker-compose.complete.yml ps

# Restart specific service
./deploy-complete-with-logging.sh restart [service-name]
```

#### **2. Logging Not Working**
```bash
# Check Fluentd status
docker-compose -f docker-compose.complete.yml logs fluentd

# Check Elasticsearch
curl http://localhost:9200/_cluster/health

# Check if log files are being created
ls -la logs/services/
```

#### **3. High Resource Usage**
```bash
# Check resource usage
docker stats

# Check specific service resources
docker stats [service-name]

# Restart resource-heavy services
./deploy-complete-with-logging.sh restart [service-name]
```

### **Error Recovery**
The deployment script automatically:
1. **Collects all errors** during deployment
2. **Fixes all issues together** rather than one by one
3. **Restarts failed services** automatically
4. **Verifies recovery** after fixing

## 📈 **SCALING & OPTIMIZATION**

### **Resource Optimization**
- **Elasticsearch**: Configured with 512MB RAM (adjustable)
- **Logstash**: Configured with 256MB RAM (adjustable)
- **Prometheus**: 200-hour retention for metrics
- **Fluentd**: Async logging with buffer management

### **Performance Tuning**
- **Log rotation**: Automatic log file rotation
- **Buffer management**: Memory-efficient buffering
- **Async processing**: Non-blocking log forwarding
- **Health checks**: Comprehensive service monitoring

## 🔒 **SECURITY CONSIDERATIONS**

### **Current Configuration**
- **Development mode**: Security features disabled for local development
- **No authentication**: Services accessible without credentials
- **Local access only**: Services bound to localhost

### **Production Hardening**
- **Enable X-Pack security** for Elasticsearch
- **Add authentication** to all services
- **Configure TLS/SSL** for all endpoints
- **Implement access controls** for logs and metrics

## 📝 **LOGGING STANDARDS**

### **Mandatory Log Fields**
All services automatically include:
```json
{
  "timestamp": "ISO8601",
  "level": "LOG_LEVEL",
  "service": "SERVICE_NAME",
  "component": "COMPONENT_NAME",
  "operation": "OPERATION_NAME",
  "message": "Human readable message",
  "context": {
    "additional": "context data"
  }
}
```

### **Log Levels**
- **DEBUG**: Detailed debugging information
- **INFO**: General operational information
- **WARNING**: Warning conditions
- **ERROR**: Error conditions
- **CRITICAL**: Critical system failures

## 🎯 **NEXT STEPS**

### **Immediate Actions**
1. **Deploy the platform** using the script
2. **Verify all services** are running
3. **Check logging infrastructure** is working
4. **Access Kibana** to view logs
5. **Access Grafana** to view metrics

### **Future Enhancements**
1. **Custom dashboards** in Grafana
2. **Alert rules** in Prometheus
3. **Log retention policies** in Elasticsearch
4. **Performance optimization** based on metrics
5. **Security hardening** for production

## 📞 **SUPPORT**

### **Documentation**
- **Architecture**: `docs/architecture/`
- **Deployment**: `docs/deployment/`
- **Service Documentation**: `services/*/README.md`

### **Troubleshooting**
- **Error Log**: Check `./deploy-complete-with-logging.sh errors`
- **Service Logs**: Use `./deploy-complete-with-logging.sh logs [service]`
- **Status Check**: Use `./deploy-complete-with-logging.sh status`

---

**🎉 You now have a complete Open Policy Platform with centralized logging, automatic log collection, and comprehensive monitoring!**
