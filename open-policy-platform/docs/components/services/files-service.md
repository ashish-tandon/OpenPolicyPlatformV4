# 📁 Files Service - Open Policy Platform

## 📅 **Last Updated**: 2025-08-17
## 🔍 **Status**: ✅ **IMPLEMENTED AND COMPLIANT**
## 🚨 **Priority**: 🟡 **MEDIUM** - Business Service
## 📋 **Port**: 8015 (per documented architecture)

---

## 🎯 **SERVICE OVERVIEW**

The **Files Service** is a core business service that handles all file-related functionality in the Open Policy Platform. It provides comprehensive file management including upload, download, storage, versioning, metadata management, and access control.

### **Purpose**
- **Primary**: Manage file uploads, downloads, and storage
- **Secondary**: Provide file metadata and versioning
- **Tertiary**: Support file sharing and collaboration

### **Business Value**
- **Document Management**: Centralized file storage and organization
- **Policy Attachments**: Support for policy document attachments
- **File Sharing**: Secure file sharing with permission controls
- **Version Control**: Track file changes and maintain history
- **Metadata Management**: Rich file categorization and search

---

## 🏗️ **ARCHITECTURE AND DESIGN**

### **Service Architecture**
```
┌─────────────────────────────────────────────────────────────┐
│                    API GATEWAY                              │
│                    Port 8000                                │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                   FILES SERVICE                             │
│                    Port 8015                                │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │   Health    │ │   Metrics   │ │   Ready     │          │
│  │   Checks    │ │  Endpoints  │ │   Checks    │          │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                PERSISTENT STORAGE                           │
│              (Kubernetes PVC - 10Gi)                       │
└─────────────────────────────────────────────────────────────┘
```

### **Design Principles**
1. **Single Responsibility**: Focus solely on file management
2. **Data Validation**: Comprehensive input validation and sanitization
3. **Security First**: Access control and permission management
4. **Scalability**: Support for large files and high throughput
5. **Extensibility**: Clear extension points for future features

### **Technology Stack**
- **Framework**: FastAPI (Python 3.11)
- **Validation**: Marshmallow (Pydantic alternative for Python 3.13 compatibility)
- **File Handling**: Python multipart for file uploads
- **Storage**: Kubernetes Persistent Volume Claims
- **Monitoring**: Prometheus metrics
- **Logging**: Structured logging with service identification

---

## 🔧 **SERVICE FUNCTIONALITY**

### **Core Features**

#### **1. File CRUD Operations**
- **Create**: Upload new files with validation
- **Read**: Download files with access control
- **Update**: Modify file metadata and permissions
- **Delete**: Soft delete files (status change)

#### **2. File Upload/Download**
- **Upload**: Multi-part file upload with size limits
- **Download**: Secure file download with permission checks
- **Validation**: File type, size, and content validation
- **Checksums**: SHA-256 checksum calculation for integrity

#### **3. Metadata Management**
- **File Information**: Name, size, type, upload date
- **Custom Metadata**: Title, description, category, tags
- **User Information**: Uploader, permissions, access history
- **Version Tracking**: File version history and changes

#### **4. Access Control**
- **Permission System**: Read, write, delete permissions
- **User Management**: User-specific file access
- **Role-based Access**: Admin and user role support
- **Security Validation**: Authentication and authorization checks

#### **5. File Organization**
- **Categorization**: File categories and tags
- **Search Capabilities**: Full-text search across metadata
- **Filtering**: Filter by status, category, user
- **Pagination**: Support for large file collections

### **API Endpoints**

#### **Health and Monitoring**
- `GET /healthz` - Health check endpoint
- `GET /readyz` - Readiness check endpoint
- `GET /metrics` - Prometheus metrics endpoint

#### **File Management**
- `GET /files` - List all files with filtering
- `GET /files/{id}` - Get specific file information
- `POST /files` - Upload new file
- `PUT /files/{id}` - Update file metadata
- `DELETE /files/{id}` - Delete file (soft delete)

#### **File Operations**
- `GET /files/{id}/versions` - Get file version history
- `GET /files/search?q={query}` - Search files
- `GET /files/category/{category}` - Files by category
- `GET /files/user/{user_id}` - Files by user

---

## 🔗 **SERVICE DEPENDENCIES**

### **Required Dependencies**
| Service | Purpose | Port | Status |
|---------|---------|------|--------|
| **API Gateway** | Routing and load balancing | 8000 | ✅ **Active** |
| **Auth Service** | Authentication and authorization | 8001 | ✅ **Active** |

### **Optional Dependencies**
| Service | Purpose | Port | Status |
|---------|---------|------|--------|
| **Database** | File metadata storage | N/A | 🔄 **Planned** |
| **Cache Service** | Performance optimization | N/A | 🔄 **Planned** |

### **External Dependencies**
| Dependency | Purpose | Status |
|------------|---------|--------|
| **Python 3.11** | Runtime environment | ✅ **Active** |
| **FastAPI** | Web framework | ✅ **Active** |
| **Marshmallow** | Data validation | ✅ **Active** |
| **Python Multipart** | File upload handling | ✅ **Active** |
| **Kubernetes PVC** | Persistent storage | ✅ **Active** |

---

## ⚙️ **SERVICE CONFIGURATION**

### **Environment Variables**
```bash
# Service Configuration
PORT=8015                           # Service port (default: 8015)
ENVIRONMENT=production              # Environment (dev/staging/prod)
LOG_LEVEL=INFO                     # Logging level

# Storage Configuration
STORAGE_PATH=/app/files            # File storage path
MAX_FILE_SIZE=104857600            # Maximum file size (100MB)

# Database Configuration (Future)
DATABASE_URL=postgresql://...      # Database connection string
REDIS_URL=redis://...              # Redis connection string

# External Service URLs
AUTH_SERVICE_URL=http://auth-service:8001  # Authentication service
```

### **Configuration Files**
- **requirements.txt**: Python dependencies
- **Dockerfile**: Container configuration
- **kubernetes.yaml**: Kubernetes deployment with PVC

### **Storage Configuration**
- **Persistent Volume**: 10Gi Kubernetes PVC
- **Access Mode**: ReadWriteMany (shared access)
- **Storage Class**: Standard storage class
- **Mount Path**: `/app/files` in container

### **Validation Rules**
- **File Size**: Maximum 100MB per file
- **File Types**: Restricted to safe MIME types
- **Filename**: No invalid characters (<, >, :, ", |, ?, *, \, /)
- **Required Fields**: filename, mime_type, uploaded_by
- **Unique Constraints**: Filenames must be unique

---

## 🧪 **TESTING AND VALIDATION**

### **Testing Strategy**
1. **Unit Tests**: Individual function testing
2. **Integration Tests**: Service communication testing
3. **API Tests**: Endpoint functionality testing
4. **File Operations**: Upload/download testing
5. **Security Tests**: Permission and access control testing

### **Test Coverage Requirements**
- **Minimum Coverage**: 80% code coverage
- **Critical Paths**: 100% coverage for core functionality
- **File Operations**: All file handling scenarios tested
- **Security**: All permission checks tested
- **Validation**: All validation rules tested

### **Testing Tools**
- **pytest**: Python testing framework
- **httpx**: HTTP client for testing
- **pytest-asyncio**: Async testing support
- **pytest-cov**: Coverage reporting
- **tempfile**: Temporary file creation for testing

### **Test Data**
- **Mock Files**: Sample files for testing
- **Edge Cases**: Large files, invalid types, boundary conditions
- **Error Scenarios**: Permission denied, file not found
- **Performance Data**: Multiple concurrent uploads

---

## 🚀 **DEPLOYMENT AND OPERATIONS**

### **Deployment Prerequisites**
1. **Kubernetes Cluster**: Running Kubernetes environment
2. **Docker Registry**: Access to container registry
3. **Storage Class**: Available storage class for PVC
4. **Monitoring**: Prometheus and Grafana setup

### **Deployment Steps**
1. **Build Image**: `docker build -t files-service .`
2. **Push Image**: `docker push files-service:latest`
3. **Deploy to K8s**: `kubectl apply -f k8s/files-service.yaml`
4. **Verify PVC**: Check persistent volume claim creation
5. **Verify Deployment**: Check service health and metrics

### **Rollback Procedures**
1. **Identify Issue**: Monitor health checks and metrics
2. **Stop Traffic**: Update API Gateway routing
3. **Revert Image**: Deploy previous version
4. **Verify Rollback**: Confirm service functionality
5. **Check Storage**: Verify file data integrity

### **Scaling Configuration**
- **Horizontal Scaling**: 2+ replicas for high availability
- **Resource Limits**: CPU 500m, Memory 512Mi
- **Resource Requests**: CPU 250m, Memory 256Mi
- **Storage Scaling**: PVC can be expanded as needed
- **Auto-scaling**: HPA configuration (future)

---

## 📊 **MONITORING AND OBSERVABILITY**

### **Health Checks**
- **Liveness Probe**: `/healthz` endpoint
- **Readiness Probe**: `/readyz` endpoint
- **Probe Configuration**: 30s initial delay, 10s period

### **Metrics Collection**
- **Operation Counters**: Total operations by type and status
- **Duration Histograms**: Operation timing metrics
- **File Counters**: Total files by status
- **File Size Histograms**: File size distribution
- **Custom Metrics**: Business-specific measurements

### **Logging Standards**
- **Log Format**: Structured JSON logging
- **Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Service Identification**: Service name and version in all logs
- **Request Tracing**: Unique request IDs for tracking
- **File Operations**: Log all file operations for audit

### **Alerting Rules**
- **Service Down**: Health check failures
- **High Error Rate**: Error percentage thresholds
- **Performance Issues**: Response time thresholds
- **Storage Issues**: Disk space and I/O problems
- **Security Alerts**: Unauthorized access attempts

---

## 🔒 **SECURITY AND COMPLIANCE**

### **Authentication**
- **Bearer Token**: JWT-based authentication
- **User Roles**: Role-based access control
- **API Keys**: Service-to-service authentication (future)

### **Authorization**
- **Endpoint Access**: Role-based endpoint access
- **File Access**: User-specific file permissions
- **Admin Functions**: Administrative-only operations
- **Permission Inheritance**: Role-based permission inheritance

### **Data Protection**
- **Input Validation**: Comprehensive input sanitization
- **File Validation**: File type and content validation
- **Access Control**: Strict permission checking
- **Audit Logging**: Complete operation audit trail
- **Data Encryption**: At-rest and in-transit encryption (future)

### **Compliance Requirements**
- **GDPR**: Data privacy and protection
- **Access Logging**: Audit trail for all operations
- **Data Retention**: Configurable data retention policies
- **Right to Deletion**: File deletion capabilities
- **Data Portability**: File export capabilities

---

## 🚨 **TROUBLESHOOTING AND SUPPORT**

### **Common Issues**

#### **1. File Upload Failures**
- **Symptoms**: 400 Bad Request on file upload
- **Causes**: File too large, invalid type, missing metadata
- **Solutions**: Check file size, validate type, include metadata

#### **2. Permission Denied**
- **Symptoms**: 403 Forbidden responses
- **Causes**: Insufficient permissions, expired tokens
- **Solutions**: Check user permissions, refresh authentication

#### **3. Storage Issues**
- **Symptoms**: 500 Internal Server Error
- **Causes**: PVC full, storage class issues, mount problems
- **Solutions**: Check storage capacity, verify PVC status

#### **4. Performance Problems**
- **Symptoms**: Slow file operations
- **Causes**: Large files, high load, resource constraints
- **Solutions**: Optimize file handling, scale resources

### **Debugging Commands**
```bash
# Check service status
kubectl get pods -n openpolicy -l app=files-service

# View service logs
kubectl logs -n openpolicy -l app=files-service

# Check storage status
kubectl get pvc -n openpolicy
kubectl describe pvc files-storage-pvc -n openpolicy

# Check service health
curl http://localhost:8015/healthz

# View metrics
curl http://localhost:8015/metrics

# Test file upload
curl -X POST -H "Authorization: Bearer <token>" \
  -F "file=@test.txt" \
  -F "metadata={\"title\":\"Test File\"}" \
  http://localhost:8015/files
```

### **Support Resources**
- **Documentation**: This service documentation
- **Logs**: Service logs and error messages
- **Metrics**: Performance and health metrics
- **Kubernetes**: PVC and deployment status
- **Team**: Development and operations team

---

## 🔄 **FUTURE ENHANCEMENTS**

### **Phase 1: Core Improvements**
- **Database Integration**: Replace mock data with real database
- **Caching Layer**: Redis-based caching for performance
- **Advanced Search**: Full-text search with Elasticsearch
- **Bulk Operations**: Batch file operations

### **Phase 2: Advanced Features**
- **Multiple Storage Backends**: S3, Azure Blob, Google Cloud Storage
- **Advanced Versioning**: Git-like version control
- **File Compression**: Automatic compression for large files
- **CDN Integration**: Content delivery network support

### **Phase 3: Enterprise Features**
- **Multi-tenancy**: Support for multiple organizations
- **Advanced Security**: Enhanced encryption and security
- **Compliance Tools**: Automated compliance checking
- **Analytics**: File usage analytics and insights

---

## 📚 **REFERENCES AND RESOURCES**

### **Related Documentation**
- [Service Documentation Template](../SERVICE_DOCUMENTATION_TEMPLATE.md)
- [Architecture Overview](../../architecture/README.md)
- [Microservices Architecture](../../components/microservices/README.md)
- [Development Process](../../processes/development/README.md)
- [Representatives Service](./representatives-service.md)

### **External Resources**
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Marshmallow Documentation](https://marshmallow.readthedocs.io/)
- [Kubernetes PVC Documentation](https://kubernetes.io/docs/concepts/storage/persistent-volumes/)
- [Python Multipart Documentation](https://python-multipart.readthedocs.io/)

### **Code Repository**
- **Service Location**: `services/files-service/`
- **Main File**: `src/main.py`
- **Configuration**: `Dockerfile`, `requirements.txt`
- **Deployment**: `infrastructure/k8s/files-service.yaml`

---

## 📋 **IMPLEMENTATION CHECKLIST**

### **Development Complete** ✅
- [x] Service implementation with core functionality
- [x] File upload/download operations
- [x] Metadata management and validation
- [x] Access control and permissions
- [x] Health check and monitoring endpoints
- [x] Error handling and logging

### **Architecture Compliance** ✅
- [x] Microservices architecture compliance
- [x] Port configuration (8015)
- [x] Health check endpoints
- [x] Centralized logging
- [x] Monitoring integration
- [x] API Gateway integration
- [x] Persistent storage configuration

### **Testing and Validation** ✅
- [x] Architecture compliance check (100%)
- [x] Deployment process validation
- [x] Dependency installation
- [x] Docker image building
- [x] Service health validation

### **Documentation** ✅
- [x] Service documentation
- [x] API endpoint documentation
- [x] Configuration documentation
- [x] Deployment procedures
- [x] Troubleshooting guide

---

**Status**: ✅ **IMPLEMENTED AND COMPLIANT**
**Next Action**: Continue with Phase 4 implementation
**Owner**: Development Team
**Last Review**: 2025-08-17
**Architecture Compliance**: 100% ✅
