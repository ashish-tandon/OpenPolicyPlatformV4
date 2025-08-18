# Open Policy Platform V4 - Complete Services Inventory

## 🚨 **Current Status: 37+ Services Running**

**Last Updated**: 2025-08-18  
**Total Services**: 37+  
**Total Containers**: 37+  
**Resource Usage**: High (Docker overloaded)

---

## 📊 **Service Categories & Architecture**

### 🏗️ **1. CORE INFRASTRUCTURE SERVICES**

#### **Database Layer**
| Service | Port | Status | Purpose | Resource Usage |
|---------|------|--------|---------|----------------|
| `postgres` | 5432 | ✅ Healthy | Main production database | Low |
| `postgres-test` | 5433 | ✅ Healthy | Test/validation database | Low |
| `redis` | 6379 | ✅ Running | Cache & message broker | Low |

#### **Logging & Monitoring Infrastructure (ELK Stack)**
| Service | Port | Status | Purpose | Resource Usage |
|---------|------|--------|---------|----------------|
| `elasticsearch` | 9200 | ✅ Running | Log storage & indexing | **HIGH** |
| `logstash` | 5044, 9600, 5001 | ✅ Running | Log processing pipeline | Medium |
| `kibana` | 5601 | ✅ Running | Log visualization & search | Medium |
| `fluentd` | 24224 | ✅ Running | Log aggregation | Low |

#### **Monitoring & Observability**
| Service | Port | Status | Purpose | Resource Usage |
|---------|------|--------|---------|----------------|
| `prometheus` | 9090 | ✅ Running | Metrics collection | Medium |
| `grafana` | 3001 | ✅ Running | Monitoring dashboards | Medium |
| `docker-monitor` | 9020 | ✅ Running | Container monitoring | Low |

---

### 🌐 **2. API & GATEWAY SERVICES**

#### **API Management**
| Service | Port | Status | Purpose | Resource Usage |
|---------|------|--------|---------|----------------|
| `api-gateway` | 9000 | ✅ Running | Central API gateway | Medium |
| `gateway` | 80 | ✅ Running | Nginx reverse proxy | Low |
| `main-api` | 8000 | ✅ Healthy | Core backend API | Medium |

#### **Core Business Services**
| Service | Port | Status | Purpose | Resource Usage |
|---------|------|--------|---------|----------------|
| `auth-service` | 9002 | ✅ Running | Authentication & authorization | Medium |
| `config-service` | 9001 | ✅ Running | Configuration management | Low |
| `policy-service` | 9003 | ✅ Running | Policy management engine | Medium |
| `notification-service` | 9004 | ✅ Running | User notifications | Low |

---

### 📊 **3. DATA & ANALYTICS SERVICES**

#### **Data Processing**
| Service | Port | Status | Purpose | Resource Usage |
|---------|------|--------|---------|----------------|
| `etl-service` | 9007 | ✅ Running | Data pipeline processing | **HIGH** |
| `analytics-service` | 9005 | ✅ Running | Data analytics engine | **HIGH** |
| `data-management-service` | 9015 | ✅ Running | Data governance | Medium |
| `search-service` | 9009 | ✅ Running | Full-text search | Medium |

#### **Reporting & Visualization**
| Service | Port | Status | Purpose | Resource Usage |
|---------|------|--------|---------|----------------|
| `reporting-service` | 9012 | ✅ Running | Report generation | Medium |
| `plotly-service` | 9017 | ✅ Running | Data visualization | Medium |
| `dashboard-service` | 9010 | ✅ Running | User dashboards | Medium |

---

### 🔄 **4. BACKGROUND PROCESSING SERVICES**

#### **Task Queue & Scheduling**
| Service | Port | Status | Purpose | Resource Usage |
|---------|------|--------|---------|----------------|
| `celery-worker` | - | ⚠️ Unhealthy | Background task processing | **HIGH** |
| `celery-beat` | - | ⚠️ Unhealthy | Scheduled task scheduler | Medium |
| `flower` | 5555 | ✅ Running | Celery monitoring UI | Low |

#### **Data Collection & Processing**
| Service | Port | Status | Purpose | Resource Usage |
|---------|------|--------|---------|----------------|
| `scraper-service` | 9008 | ✅ Running | Data collection service | Medium |
| `scraper-runner` | - | ⚠️ Unhealthy | Background scraper execution | **HIGH** |

---

### 🌟 **5. USER EXPERIENCE SERVICES**

#### **Frontend & Web**
| Service | Port | Status | Purpose | Resource Usage |
|---------|------|--------|---------|----------------|
| `web` | 3000 | ✅ Running | React web application | Medium |
| `mobile-api` | 9018 | ✅ Running | Mobile app backend | Medium |
| `legacy-django` | 9019 | ✅ Running | Legacy Django application | Medium |

#### **Business Process Services**
| Service | Port | Status | Purpose | Resource Usage |
|---------|------|--------|---------|----------------|
| `workflow-service` | 9013 | ✅ Running | Business process automation | Medium |
| `integration-service` | 9014 | ✅ Running | Third-party integrations | Medium |
| `representatives-service` | 9016 | ✅ Running | User management | Low |
| `files-service` | 9011 | ✅ Running | File management | Low |
| `monitoring-service` | 9006 | ✅ Running | System monitoring | Medium |

---

## 🚨 **Resource Usage Analysis**

### **High Resource Consumption Services**
1. **`elasticsearch`** - Log storage (199.4MiB RAM, 113.90% CPU)
2. **`etl-service`** - Data processing pipeline
3. **`analytics-service`** - Analytics engine
4. **`celery-worker`** - Background processing
5. **`scraper-runner`** - Data collection

### **Medium Resource Consumption Services**
- Most business logic services (9000-9019 ports)
- Monitoring and logging services
- Database and cache services

### **Low Resource Consumption Services**
- Configuration services
- File management
- User management
- Gateway services

---

## 📈 **Current Platform Metrics**

### **Port Ranges**
- **Core Services**: 8000, 9000-9019
- **Monitoring**: 3001, 9090, 9020
- **Logging**: 5601, 9200, 24224
- **Web**: 3000, 80
- **Background**: 5555

### **Health Status**
- **Healthy**: 3 services
- **Running**: 30+ services
- **Unhealthy**: 3 services (celery services + scraper-runner)

### **Resource Allocation**
- **Total Memory**: ~2-3GB across all services
- **Total CPU**: Variable, some services spiking to 100%+
- **Network I/O**: High activity across services
- **Disk I/O**: Significant activity, especially for data services

---

## 🔧 **Immediate Actions Required**

### **1. Resource Optimization**
- Monitor high-CPU services (elasticsearch, etl-service)
- Consider resource limits for heavy services
- Implement health check improvements

### **2. Service Health**
- Fix unhealthy celery services
- Resolve scraper-runner issues
- Implement proper health endpoints

### **3. Monitoring & Alerting**
- Set up resource usage alerts
- Monitor service dependencies
- Implement circuit breakers

---

## 📋 **Next Steps & Recommendations**

### **Phase 1: Stabilization (Immediate)**
- [ ] Fix unhealthy services
- [ ] Implement resource limits
- [ ] Set up proper monitoring

### **Phase 2: Optimization (Short-term)**
- [ ] Resource usage optimization
- [ ] Service dependency mapping
- [ ] Performance tuning

### **Phase 3: Scaling (Long-term)**
- [ ] Kubernetes migration planning
- [ ] Service mesh implementation
- [ ] Auto-scaling configuration

---

**Note**: This platform is now running at enterprise scale. Consider implementing proper resource management and monitoring to prevent Docker overload.
