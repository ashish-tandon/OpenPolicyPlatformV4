# 🚀 Azure Service Deployment Plan - OpenPolicyPlatform V4
**Generated:** January 27, 2025  
**Objective:** Deploy all services to Azure and migrate to native Azure Redis

## 🎯 Executive Summary

This plan outlines the systematic deployment of all OpenPolicyPlatform V4 services to Azure and the migration from local Redis to Azure Cache for Redis. The approach ensures zero-downtime deployment with proper testing and rollback capabilities.

## 📊 Current Azure Infrastructure Status

### **✅ Infrastructure Services - OPERATIONAL**
| Service | Name | Status | Health | Notes |
|---------|------|--------|---------|-------|
| **Container Registry** | `openpolicyacr` | ✅ **Running** | Healthy | Ready for container images |
| **PostgreSQL Database** | `openpolicy-postgresql` | ✅ **Running** | Healthy | Flexible Server v15, 32GB storage |
| **Redis Cache** | `openpolicy-redis` | ✅ **Running** | Healthy | Basic SKU, Redis 6.0 |
| **Storage Account** | `openpolicystorage` | ✅ **Running** | Healthy | Standard LRS, Blob/File/Queue/Table |
| **Application Insights** | `openpolicy-appinsights` | ✅ **Running** | Healthy | 90-day retention, monitoring ready |
| **Key Vault** | `openpolicy-keyvault` | ✅ **Running** | Healthy | RBAC enabled, secrets management |

### **❌ Application Services - NEED DEPLOYMENT**
| Service | Status | Priority | Dependencies |
|---------|--------|----------|--------------|
| **API Gateway** | ❌ Not Deployed | 🔴 **HIGH** | Container Registry, PostgreSQL, Redis |
| **Backend API** | ❌ Not Deployed | 🔴 **HIGH** | PostgreSQL, Redis, Key Vault |
| **Web Frontend** | ❌ Not Deployed | 🟡 **MEDIUM** | API Gateway, Storage |
| **Nginx Gateway** | ❌ Not Deployed | 🟡 **MEDIUM** | API, Web services |

## 🔄 Redis Migration Strategy

### **Phase 1: Preparation & Testing**
- **Duration:** 1-2 days
- **Objective:** Validate Azure Redis connectivity and performance
- **Activities:**
  1. Test Azure Redis connection from local environment
  2. Validate Redis operations (SET, GET, DEL, etc.)
  3. Performance benchmarking (response times, throughput)
  4. Security testing (TLS, authentication)

### **Phase 2: Dual-Write Migration**
- **Duration:** 2-3 days
- **Objective:** Implement dual-write to both local and Azure Redis
- **Activities:**
  1. Modify application code for dual Redis connections
  2. Implement write-through caching strategy
  3. Add Redis connection pooling and failover
  4. Monitor data consistency between environments

### **Phase 3: Read Migration**
- **Duration:** 1-2 days
- **Objective:** Gradually shift read operations to Azure Redis
- **Activities:**
  1. Implement read-from-Azure strategy
  2. Add health checks and fallback to local Redis
  3. Monitor performance and error rates
  4. Validate data integrity

### **Phase 4: Full Migration**
- **Duration:** 1 day
- **Objective:** Complete migration to Azure Redis
- **Activities:**
  1. Remove local Redis dependencies
  2. Update configuration files
  3. Remove local Redis containers
  4. Update monitoring and health checks

### **Phase 5: Validation & Cleanup**
- **Duration:** 1 day
- **Objective:** Ensure system stability and cleanup
- **Activities:**
  1. Comprehensive testing of all Redis operations
  2. Performance validation
  3. Remove dual-write code
  4. Update documentation

## 🚀 Azure Service Deployment Plan

### **Step 1: Container Image Preparation**
```bash
# Build and push all container images to Azure Container Registry
docker build -t openpolicyacr.azurecr.io/openpolicy-api:latest ./backend
docker build -t openpolicyacr.azurecr.io/openpolicy-web:latest ./web
docker build -t openpolicyacr.azurecr.io/openpolicy-gateway:latest ./infrastructure/gateway

# Push to Azure Container Registry
az acr login --name openpolicyacr
docker push openpolicyacr.azurecr.io/openpolicy-api:latest
docker push openpolicyacr.azurecr.io/openpolicy-web:latest
docker push openpolicyacr.azurecr.io/openpolicy-gateway:latest
```

### **Step 2: Azure Container Apps Environment**
```bash
# Create Container Apps Environment
az containerapp env create \
  --name openpolicy-env \
  --resource-group openpolicy-platform-rg \
  --location canadacentral \
  --logs-workspace-id <log-analytics-workspace-id>
```

### **Step 3: Deploy Core Services**
```bash
# Deploy API Gateway
az containerapp create \
  --name openpolicy-api-gateway \
  --resource-group openpolicy-platform-rg \
  --environment openpolicy-env \
  --image openpolicyacr.azurecr.io/openpolicy-gateway:latest \
  --target-port 80 \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 3

# Deploy Backend API
az containerapp create \
  --name openpolicy-api \
  --resource-group openpolicy-platform-rg \
  --environment openpolicy-env \
  --image openpolicyacr.azurecr.io/openpolicy-api:latest \
  --target-port 8000 \
  --ingress internal \
  --min-replicas 2 \
  --max-replicas 5

# Deploy Web Frontend
az containerapp create \
  --name openpolicy-web \
  --resource-group openpolicy-platform-rg \
  --environment openpolicy-env \
  --image openpolicyacr.azurecr.io/openpolicy-web:latest \
  --target-port 3000 \
  --ingress internal \
  --min-replicas 2 \
  --max-replicas 3
```

### **Step 4: Configure Environment Variables**
```bash
# Set environment variables for each service
az containerapp update \
  --name openpolicy-api \
  --resource-group openpolicy-platform-rg \
  --set-env-vars \
    DATABASE_URL="postgresql://openpolicy:<password>@openpolicy-postgresql.postgres.database.azure.com:5432/openpolicy" \
    REDIS_URL="openpolicy-redis.redis.cache.windows.net:6379,password=<redis-key>,ssl=True" \
    ENVIRONMENT="production" \
    LOG_LEVEL="info"
```

## 🔧 Redis Migration Implementation

### **1. Update Redis Configuration**
```python
# config/redis_config.py
import redis
import os
from typing import Optional

class RedisManager:
    def __init__(self):
        self.local_redis = None
        self.azure_redis = None
        self.migration_mode = os.getenv('REDIS_MIGRATION_MODE', 'local')
        
        # Initialize local Redis (fallback)
        if os.getenv('LOCAL_REDIS_URL'):
            self.local_redis = redis.Redis.from_url(
                os.getenv('LOCAL_REDIS_URL'),
                decode_responses=True
            )
        
        # Initialize Azure Redis
        if os.getenv('AZURE_REDIS_URL'):
            self.azure_redis = redis.Redis.from_url(
                os.getenv('AZURE_REDIS_URL'),
                decode_responses=True,
                ssl=True,
                ssl_cert_reqs=None
            )
    
    def get(self, key: str) -> Optional[str]:
        """Get value with fallback strategy"""
        try:
            if self.migration_mode in ['azure', 'dual'] and self.azure_redis:
                value = self.azure_redis.get(key)
                if value:
                    return value
            
            # Fallback to local Redis
            if self.local_redis:
                return self.local_redis.get(key)
        except Exception as e:
            print(f"Redis get error: {e}")
            if self.local_redis:
                return self.local_redis.get(key)
        return None
    
    def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        """Set value with dual-write strategy"""
        success = True
        
        # Write to Azure Redis
        if self.migration_mode in ['azure', 'dual'] and self.azure_redis:
            try:
                self.azure_redis.set(key, value, ex=ex)
            except Exception as e:
                print(f"Azure Redis set error: {e}")
                success = False
        
        # Write to local Redis (fallback or dual-write)
        if self.local_redis:
            try:
                self.local_redis.set(key, value, ex=ex)
            except Exception as e:
                print(f"Local Redis set error: {e}")
                success = False
        
        return success
```

### **2. Environment Configuration**
```bash
# .env.azure
# Redis Migration Configuration
REDIS_MIGRATION_MODE=dual  # local, dual, azure
LOCAL_REDIS_URL=redis://localhost:6379/0
AZURE_REDIS_URL=rediss://:<password>@openpolicy-redis.redis.cache.windows.net:6380

# Azure Service Configuration
AZURE_POSTGRES_URL=postgresql://openpolicy:<password>@openpolicy-postgresql.postgres.database.azure.com:5432/openpolicy
AZURE_STORAGE_CONNECTION_STRING=<storage-connection-string>
AZURE_APPINSIGHTS_KEY=<appinsights-key>
```

### **3. Health Check Implementation**
```python
# health/redis_health.py
import redis
import os
from typing import Dict, Any

def check_redis_health() -> Dict[str, Any]:
    """Comprehensive Redis health check"""
    health_status = {
        'local_redis': {'status': 'unknown', 'response_time': None, 'error': None},
        'azure_redis': {'status': 'unknown', 'response_time': None, 'error': None},
        'overall_status': 'unknown'
    }
    
    # Check local Redis
    if os.getenv('LOCAL_REDIS_URL'):
        try:
            local_redis = redis.Redis.from_url(os.getenv('LOCAL_REDIS_URL'))
            start_time = time.time()
            local_redis.ping()
            response_time = (time.time() - start_time) * 1000
            
            health_status['local_redis'] = {
                'status': 'healthy',
                'response_time': f"{response_time:.2f}ms",
                'error': None
            }
        except Exception as e:
            health_status['local_redis'] = {
                'status': 'unhealthy',
                'response_time': None,
                'error': str(e)
            }
    
    # Check Azure Redis
    if os.getenv('AZURE_REDIS_URL'):
        try:
            azure_redis = redis.Redis.from_url(
                os.getenv('AZURE_REDIS_URL'),
                ssl=True,
                ssl_cert_reqs=None
            )
            start_time = time.time()
            azure_redis.ping()
            response_time = (time.time() - start_time) * 1000
            
            health_status['azure_redis'] = {
                'status': 'healthy',
                'response_time': f"{response_time:.2f}ms",
                'error': None
            }
        except Exception as e:
            health_status['azure_redis'] = {
                'status': 'unhealthy',
                'response_time': None,
                'error': str(e)
            }
    
    # Determine overall status
    if (health_status['local_redis']['status'] == 'healthy' or 
        health_status['azure_redis']['status'] == 'healthy'):
        health_status['overall_status'] = 'healthy'
    else:
        health_status['overall_status'] = 'unhealthy'
    
    return health_status
```

## 📋 Deployment Checklist

### **Pre-Deployment**
- [ ] Validate Azure Redis connectivity
- [ ] Test Redis operations and performance
- [ ] Build and push container images
- [ ] Create Container Apps Environment
- [ ] Configure environment variables
- [ ] Set up monitoring and alerting

### **Deployment**
- [ ] Deploy API Gateway
- [ ] Deploy Backend API
- [ ] Deploy Web Frontend
- [ ] Configure service dependencies
- [ ] Test service communication
- [ ] Validate health checks

### **Post-Deployment**
- [ ] Monitor service performance
- [ ] Validate Redis migration
- [ ] Test failover scenarios
- [ ] Update monitoring dashboards
- [ ] Document deployment
- [ ] Plan production rollout

## 🚨 Rollback Plan

### **Immediate Rollback (5 minutes)**
- Revert environment variables to local Redis
- Restart affected services
- Validate system functionality

### **Service Rollback (15 minutes)**
- Redeploy previous container versions
- Restore local Redis configuration
- Validate all services operational

### **Full Rollback (30 minutes)**
- Stop Azure Container Apps
- Restore local Docker Compose setup
- Validate complete system functionality

## 📊 Success Metrics

### **Performance Targets**
- **Redis Response Time:** < 10ms (Azure), < 5ms (local)
- **API Response Time:** < 100ms
- **Service Uptime:** > 99.9%
- **Migration Success Rate:** > 99%

### **Monitoring KPIs**
- Redis operation success rate
- Service response times
- Error rates and types
- Resource utilization
- Cost optimization

## 🎯 Next Steps

1. **Immediate (Today):**
   - Test Azure Redis connectivity
   - Validate Redis performance
   - Prepare container images

2. **This Week:**
   - Deploy core services to Azure
   - Implement Redis migration code
   - Begin dual-write testing

3. **Next Week:**
   - Complete Redis migration
   - Validate all services
   - Plan production rollout

## 🔍 Risk Mitigation

### **High-Risk Scenarios**
- **Azure Redis connectivity issues**
  - Mitigation: Maintain local Redis fallback
  - Rollback: Immediate switch to local Redis

- **Service deployment failures**
  - Mitigation: Staged deployment with health checks
  - Rollback: Previous version redeployment

- **Performance degradation**
  - Mitigation: Performance monitoring and alerts
  - Rollback: Scale up resources or revert

This comprehensive plan ensures a smooth transition to Azure with minimal risk and maximum reliability. Each phase includes validation steps and rollback procedures to maintain system stability throughout the migration process.
