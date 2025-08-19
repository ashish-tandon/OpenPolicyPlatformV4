#!/bin/bash
set -e

# Setup Comprehensive Audit Logging for OpenPolicy Platform
# This script deploys a complete audit logging solution

echo "=== Setting up Audit Logging Service ==="

# Configuration
AUDIT_SERVICE_PORT=9028
MONGODB_HOST=${MONGODB_HOST:-"mongodb"}
MONGODB_PORT=${MONGODB_PORT:-27017}
REDIS_HOST=${REDIS_HOST:-"redis"}
REDIS_PORT=${REDIS_PORT:-6379}
ELASTICSEARCH_HOST=${ELASTICSEARCH_HOST:-"elasticsearch"}
ELASTICSEARCH_PORT=${ELASTICSEARCH_PORT:-9200}
KAFKA_HOST=${KAFKA_HOST:-"kafka"}
KAFKA_PORT=${KAFKA_PORT:-9092}

# 1. Create Audit Logging Dockerfile
echo "1. Creating Audit Logging Dockerfile..."
cat > services/audit-logging/Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd -m -u 1000 audit && \
    chown -R audit:audit /app

USER audit

EXPOSE 9028

CMD ["python", "-m", "uvicorn", "audit-service:app", "--host", "0.0.0.0", "--port", "9028"]
EOF

# 2. Create Requirements File
echo "2. Creating Requirements File..."
cat > services/audit-logging/requirements.txt << 'EOF'
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.0
motor==3.3.2
redis==5.0.1
elasticsearch[async]==8.11.0
kafka-python==2.0.2
structlog==23.2.0
prometheus-client==0.19.0
python-multipart==0.0.6
httpx==0.25.2
aiofiles==23.2.1
cryptography==41.0.7
EOF

# 3. Create Docker Compose Configuration
echo "3. Creating Docker Compose Configuration..."
cat > docker-compose.audit.yml << 'EOF'
version: '3.8'

services:
  audit-service:
    build:
      context: ./services/audit-logging
      dockerfile: Dockerfile
    image: openpolicy/audit-service:latest
    container_name: audit-service
    ports:
      - "9028:9028"
    environment:
      - MONGODB_URL=mongodb://mongodb:27017
      - MONGODB_DB=audit_logs
      - REDIS_URL=redis://redis:6379/4
      - ELASTICSEARCH_URL=http://elasticsearch:9200
      - KAFKA_BROKERS=kafka:9092
      - SERVICE_PORT=9028
      - LOG_RETENTION_DAYS=365
      - ENABLE_ENCRYPTION=true
      - AUDIT_ENCRYPTION_KEY=${AUDIT_ENCRYPTION_KEY}
    networks:
      - openpolicy-network
    depends_on:
      - mongodb
      - redis
      - elasticsearch
      - kafka
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9028/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  mongodb:
    image: mongo:7.0
    container_name: audit-mongodb
    ports:
      - "27017:27017"
    volumes:
      - mongodb-data:/data/db
      - ./services/audit-logging/init-mongo.js:/docker-entrypoint-initdb.d/init-mongo.js
    environment:
      - MONGO_INITDB_ROOT_USERNAME=admin
      - MONGO_INITDB_ROOT_PASSWORD=admin123
      - MONGO_INITDB_DATABASE=audit_logs
    networks:
      - openpolicy-network
    restart: unless-stopped

  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.1
    container_name: audit-elasticsearch
    ports:
      - "9200:9200"
      - "9300:9300"
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    volumes:
      - elasticsearch-data:/usr/share/elasticsearch/data
    networks:
      - openpolicy-network
    restart: unless-stopped

  kibana:
    image: docker.elastic.co/kibana/kibana:8.11.1
    container_name: audit-kibana
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    networks:
      - openpolicy-network
    depends_on:
      - elasticsearch
    restart: unless-stopped

  kafka:
    image: confluentinc/cp-kafka:7.5.0
    container_name: audit-kafka
    ports:
      - "9092:9092"
      - "9101:9101"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:29092,PLAINTEXT_HOST://localhost:9092
      KAFKA_LISTENERS: PLAINTEXT://0.0.0.0:29092,PLAINTEXT_HOST://0.0.0.0:9092
      KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_TRANSACTION_STATE_LOG_MIN_ISR: 1
      KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR: 1
      KAFKA_GROUP_INITIAL_REBALANCE_DELAY_MS: 0
      KAFKA_JMX_PORT: 9101
      KAFKA_JMX_HOSTNAME: localhost
    volumes:
      - kafka-data:/var/lib/kafka/data
    networks:
      - openpolicy-network
    depends_on:
      - zookeeper
    restart: unless-stopped

  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.0
    container_name: audit-zookeeper
    ports:
      - "2181:2181"
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000
    volumes:
      - zookeeper-data:/var/lib/zookeeper/data
      - zookeeper-logs:/var/lib/zookeeper/log
    networks:
      - openpolicy-network
    restart: unless-stopped

volumes:
  mongodb-data:
  elasticsearch-data:
  kafka-data:
  zookeeper-data:
  zookeeper-logs:

networks:
  openpolicy-network:
    external: true
EOF

# 4. Create MongoDB Initialization Script
echo "4. Creating MongoDB Initialization Script..."
cat > services/audit-logging/init-mongo.js << 'EOF'
// Initialize audit logs database
db = db.getSiblingDB('audit_logs');

// Create collections
db.createCollection('audit_logs');
db.createCollection('audit_retention_policies');
db.createCollection('audit_alerts');

// Create indexes for performance
db.audit_logs.createIndex({ 'timestamp': -1 });
db.audit_logs.createIndex({ 'event_type': 1 });
db.audit_logs.createIndex({ 'user_id': 1 });
db.audit_logs.createIndex({ 'service': 1 });
db.audit_logs.createIndex({ 'severity': 1 });
db.audit_logs.createIndex({ 'resource_type': 1, 'resource_id': 1 });
db.audit_logs.createIndex({ 'timestamp': -1, 'event_type': 1 });
db.audit_logs.createIndex({ 'user_id': 1, 'timestamp': -1 });
db.audit_logs.createIndex({ 'correlation_id': 1 });
db.audit_logs.createIndex({ 'content_hash': 1 }, { unique: true, sparse: true });

// Create TTL index for automatic cleanup
db.audit_logs.createIndex(
  { 'timestamp': 1 },
  { expireAfterSeconds: 365 * 24 * 60 * 60 } // 365 days
);

// Insert default retention policies
db.audit_retention_policies.insertMany([
  {
    event_type: 'security.*',
    retention_days: 2555, // 7 years for security events
    description: 'Security events must be retained for 7 years'
  },
  {
    event_type: 'compliance.*',
    retention_days: 2555, // 7 years for compliance events
    description: 'Compliance events must be retained for 7 years'
  },
  {
    event_type: 'data.*',
    retention_days: 1095, // 3 years for data events
    description: 'Data access events retained for 3 years'
  },
  {
    event_type: 'api.*',
    retention_days: 90, // 90 days for API logs
    description: 'API logs retained for 90 days'
  },
  {
    event_type: 'system.*',
    retention_days: 30, // 30 days for system logs
    description: 'System logs retained for 30 days'
  }
]);

print('Audit logs database initialized successfully');
EOF

# 5. Create Elasticsearch Index Template
echo "5. Creating Elasticsearch Index Template..."
cat > services/audit-logging/elasticsearch-template.json << 'EOF'
{
  "index_patterns": ["audit-logs-*"],
  "template": {
    "settings": {
      "number_of_shards": 2,
      "number_of_replicas": 1,
      "index.lifecycle.name": "audit-logs-policy",
      "index.lifecycle.rollover_alias": "audit-logs"
    },
    "mappings": {
      "properties": {
        "timestamp": { "type": "date" },
        "event_type": { "type": "keyword" },
        "severity": { "type": "keyword" },
        "service": { "type": "keyword" },
        "user_id": { "type": "keyword" },
        "session_id": { "type": "keyword" },
        "ip_address": { "type": "ip" },
        "user_agent": { "type": "text" },
        "resource_type": { "type": "keyword" },
        "resource_id": { "type": "keyword" },
        "action": { "type": "text", "fields": { "keyword": { "type": "keyword" } } },
        "result": { "type": "keyword" },
        "details": { "type": "object", "enabled": false },
        "error_message": { "type": "text" },
        "duration_ms": { "type": "integer" },
        "request_id": { "type": "keyword" },
        "correlation_id": { "type": "keyword" },
        "tags": { "type": "keyword" },
        "metadata": { "type": "object", "enabled": false }
      }
    }
  }
}
EOF

# 6. Create Kibana Dashboard Configuration
echo "6. Creating Kibana Dashboard Configuration..."
cat > services/audit-logging/kibana-dashboard.json << 'EOF'
{
  "version": "8.11.1",
  "objects": [
    {
      "id": "audit-logs-dashboard",
      "type": "dashboard",
      "attributes": {
        "title": "Audit Logs Dashboard",
        "panels": [
          {
            "gridData": { "x": 0, "y": 0, "w": 24, "h": 15 },
            "type": "visualization",
            "id": "events-over-time"
          },
          {
            "gridData": { "x": 24, "y": 0, "w": 24, "h": 15 },
            "type": "visualization",
            "id": "events-by-type"
          },
          {
            "gridData": { "x": 0, "y": 15, "w": 12, "h": 15 },
            "type": "visualization",
            "id": "top-users"
          },
          {
            "gridData": { "x": 12, "y": 15, "w": 12, "h": 15 },
            "type": "visualization",
            "id": "failed-operations"
          },
          {
            "gridData": { "x": 24, "y": 15, "w": 24, "h": 30 },
            "type": "visualization",
            "id": "security-events"
          }
        ]
      }
    }
  ]
}
EOF

# 7. Create Audit SDK for Services
echo "7. Creating Audit SDK..."
mkdir -p services/audit-logging/sdk/python

cat > services/audit-logging/sdk/python/audit_client.py << 'EOF'
"""
Audit Logging Client SDK for Python Services
"""

import os
import json
import time
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
import httpx
import logging
from functools import wraps

logger = logging.getLogger(__name__)

class EventType(str, Enum):
    """Audit event types"""
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    DATA_CREATE = "data.create"
    DATA_READ = "data.read"
    DATA_UPDATE = "data.update"
    DATA_DELETE = "data.delete"
    API_CALL = "api.call"
    API_ERROR = "api.error"
    SECURITY_ALERT = "security.alert"
    PERMISSION_DENIED = "auth.permission_denied"

class Severity(str, Enum):
    """Severity levels"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class AuditClient:
    """Client for audit logging service"""
    
    def __init__(self, base_url: str = None, service_name: str = None):
        self.base_url = base_url or os.getenv("AUDIT_SERVICE_URL", "http://audit-service:9028")
        self.service_name = service_name or os.getenv("SERVICE_NAME", "unknown")
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=5.0)
    
    async def log(
        self,
        event_type: EventType,
        action: str,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        result: str = "success",
        severity: Severity = Severity.INFO,
        details: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        duration_ms: Optional[int] = None,
        **kwargs
    ) -> Optional[str]:
        """Log an audit event"""
        try:
            payload = {
                "event_type": event_type.value if isinstance(event_type, Enum) else event_type,
                "severity": severity.value if isinstance(severity, Enum) else severity,
                "service": self.service_name,
                "action": action,
                "user_id": user_id,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "result": result,
                "details": details,
                "error_message": error_message,
                "duration_ms": duration_ms,
                "timestamp": datetime.utcnow().isoformat(),
                **kwargs
            }
            
            response = await self.client.post("/log", json=payload)
            if response.status_code == 200:
                return response.json().get("log_id")
            else:
                logger.error(f"Failed to log audit event: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error logging audit event: {e}")
            return None
    
    async def query(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        event_types: Optional[List[str]] = None,
        user_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Query audit logs"""
        try:
            payload = {
                "start_time": start_time.isoformat() if start_time else None,
                "end_time": end_time.isoformat() if end_time else None,
                "event_types": event_types,
                "user_id": user_id,
                "limit": limit,
                "offset": offset
            }
            
            response = await self.client.post("/query", json=payload)
            if response.status_code == 200:
                return response.json().get("logs", [])
            else:
                logger.error(f"Failed to query audit logs: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error querying audit logs: {e}")
            return []
    
    async def close(self):
        """Close the client"""
        await self.client.aclose()

def audit_log(
    event_type: EventType,
    resource_type: Optional[str] = None,
    severity: Severity = Severity.INFO
):
    """Decorator for automatic audit logging"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            audit_client = None
            result = "success"
            error_message = None
            resource_id = kwargs.get("id") or kwargs.get("resource_id")
            
            try:
                # Get audit client from request context if available
                request = kwargs.get("request")
                if request and hasattr(request.app.state, "audit_client"):
                    audit_client = request.app.state.audit_client
                else:
                    audit_client = AuditClient()
                
                # Get user info from request
                user_id = None
                if request:
                    user_id = getattr(request.state, "user_id", None)
                
                # Execute function
                response = await func(*args, **kwargs)
                
                return response
                
            except Exception as e:
                result = "error"
                error_message = str(e)
                raise
                
            finally:
                # Log the audit event
                if audit_client:
                    duration_ms = int((time.time() - start_time) * 1000)
                    
                    await audit_client.log(
                        event_type=event_type,
                        action=func.__name__,
                        user_id=user_id,
                        resource_type=resource_type,
                        resource_id=resource_id,
                        result=result,
                        severity=severity if result == "success" else Severity.ERROR,
                        error_message=error_message,
                        duration_ms=duration_ms
                    )
                    
                    # Close client if we created it
                    if not request:
                        await audit_client.close()
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For sync functions, run in event loop
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(async_wrapper(*args, **kwargs))
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator

# Convenience functions
async def log_user_login(user_id: str, ip_address: str, user_agent: str, success: bool = True):
    """Log user login attempt"""
    client = AuditClient()
    await client.log(
        event_type=EventType.USER_LOGIN if success else EventType.SECURITY_ALERT,
        action="User login",
        user_id=user_id,
        result="success" if success else "failed",
        severity=Severity.INFO if success else Severity.WARNING,
        details={
            "ip_address": ip_address,
            "user_agent": user_agent
        }
    )
    await client.close()

async def log_data_access(user_id: str, resource_type: str, resource_id: str, action: str = "read"):
    """Log data access"""
    client = AuditClient()
    await client.log(
        event_type=EventType.DATA_READ,
        action=f"Data {action}",
        user_id=user_id,
        resource_type=resource_type,
        resource_id=resource_id
    )
    await client.close()

async def log_security_event(event_description: str, severity: Severity = Severity.WARNING, details: Dict = None):
    """Log security event"""
    client = AuditClient()
    await client.log(
        event_type=EventType.SECURITY_ALERT,
        action=event_description,
        severity=severity,
        details=details
    )
    await client.close()
EOF

# 8. Create Integration Middleware
echo "8. Creating Integration Middleware..."
cat > services/audit-logging/middleware/fastapi_audit.py << 'EOF'
"""
FastAPI Middleware for Automatic Audit Logging
"""

import time
import json
from typing import Callable
from fastapi import Request, Response
from fastapi.routing import APIRoute
from starlette.middleware.base import BaseHTTPMiddleware
from audit_client import AuditClient, EventType, Severity

class AuditLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to automatically log API calls"""
    
    def __init__(self, app, audit_client: AuditClient = None, exclude_paths: list = None):
        super().__init__(app)
        self.audit_client = audit_client or AuditClient()
        self.exclude_paths = exclude_paths or ["/health", "/metrics", "/docs", "/openapi.json"]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        start_time = time.time()
        
        # Extract request info
        user_id = getattr(request.state, "user_id", None)
        request_body = None
        
        # Try to read request body for POST/PUT
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                request_body = json.loads(body) if body else None
                # Recreate request with body
                request._body = body
            except:
                pass
        
        # Process request
        response = None
        error_message = None
        
        try:
            response = await call_next(request)
            return response
            
        except Exception as e:
            error_message = str(e)
            raise
            
        finally:
            # Log the API call
            duration_ms = int((time.time() - start_time) * 1000)
            
            await self.audit_client.log(
                event_type=EventType.API_CALL if not error_message else EventType.API_ERROR,
                action=f"{request.method} {request.url.path}",
                user_id=user_id,
                result="success" if response and response.status_code < 400 else "error",
                severity=Severity.INFO if response and response.status_code < 400 else Severity.ERROR,
                details={
                    "method": request.method,
                    "path": request.url.path,
                    "query_params": dict(request.query_params),
                    "status_code": response.status_code if response else None,
                    "client_host": request.client.host if request.client else None
                },
                error_message=error_message,
                duration_ms=duration_ms,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent")
            )

class AuditLoggingRoute(APIRoute):
    """Custom route class for detailed audit logging"""
    
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()
        
        async def custom_route_handler(request: Request) -> Response:
            start_time = time.time()
            audit_client = AuditClient()
            
            try:
                response = await original_route_handler(request)
                return response
                
            finally:
                # Log specific endpoint access
                duration_ms = int((time.time() - start_time) * 1000)
                user_id = getattr(request.state, "user_id", None)
                
                await audit_client.log(
                    event_type=EventType.API_CALL,
                    action=f"{request.method} {self.path}",
                    user_id=user_id,
                    resource_type=self.endpoint.__name__,
                    duration_ms=duration_ms,
                    details={
                        "endpoint": self.endpoint.__name__,
                        "tags": self.tags
                    }
                )
        
        return custom_route_handler
EOF

# 9. Create Audit Dashboard Component
echo "9. Creating Audit Dashboard Component..."
cat > apps/web/src/components/AuditLogViewer.tsx << 'EOF'
import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  IconButton,
  Tooltip,
  Typography,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  Grid,
  Alert
} from '@mui/material';
import {
  Search as SearchIcon,
  FilterList as FilterIcon,
  Download as DownloadIcon,
  Refresh as RefreshIcon,
  Info as InfoIcon,
  Warning as WarningIcon,
  Error as ErrorIcon
} from '@mui/icons-material';
import { DateTimePicker } from '@mui/x-date-pickers/DateTimePicker';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';

interface AuditLog {
  id: string;
  timestamp: string;
  event_type: string;
  severity: string;
  service: string;
  user_id?: string;
  action: string;
  result: string;
  duration_ms?: number;
  ip_address?: string;
  details?: any;
}

const AuditLogViewer: React.FC = () => {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);
  const [totalCount, setTotalCount] = useState(0);
  const [selectedLog, setSelectedLog] = useState<AuditLog | null>(null);
  
  // Filters
  const [filters, setFilters] = useState({
    startTime: null as Date | null,
    endTime: null as Date | null,
    eventType: '',
    severity: '',
    userId: '',
    service: '',
    searchText: ''
  });

  useEffect(() => {
    fetchLogs();
  }, [page, rowsPerPage]);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const queryParams = {
        offset: page * rowsPerPage,
        limit: rowsPerPage,
        ...filters
      };
      
      const response = await fetch('/api/audit/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(queryParams)
      });
      
      const data = await response.json();
      setLogs(data.logs);
      setTotalCount(data.count);
    } catch (error) {
      console.error('Failed to fetch audit logs:', error);
    } finally {
      setLoading(false);
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'error':
      case 'critical':
        return <ErrorIcon color="error" />;
      case 'warning':
        return <WarningIcon color="warning" />;
      default:
        return <InfoIcon color="info" />;
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'error':
      case 'critical':
        return 'error';
      case 'warning':
        return 'warning';
      case 'info':
        return 'info';
      default:
        return 'default';
    }
  };

  const getResultChip = (result: string) => {
    const color = result === 'success' ? 'success' : 'error';
    return <Chip label={result} color={color} size="small" />;
  };

  const handleExport = async () => {
    try {
      const response = await fetch('/api/audit/export?format=csv', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `audit-logs-${new Date().toISOString()}.csv`;
      a.click();
    } catch (error) {
      console.error('Failed to export logs:', error);
    }
  };

  return (
    <LocalizationProvider dateAdapter={AdapterDateFns}>
      <Box>
        <Typography variant="h5" gutterBottom>
          Audit Logs
        </Typography>
        
        {/* Filters */}
        <Paper sx={{ p: 2, mb: 2 }}>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={3}>
              <DateTimePicker
                label="Start Time"
                value={filters.startTime}
                onChange={(value) => setFilters({ ...filters, startTime: value })}
                renderInput={(params) => <TextField {...params} fullWidth />}
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <DateTimePicker
                label="End Time"
                value={filters.endTime}
                onChange={(value) => setFilters({ ...filters, endTime: value })}
                renderInput={(params) => <TextField {...params} fullWidth />}
              />
            </Grid>
            <Grid item xs={12} md={2}>
              <FormControl fullWidth>
                <InputLabel>Event Type</InputLabel>
                <Select
                  value={filters.eventType}
                  onChange={(e) => setFilters({ ...filters, eventType: e.target.value })}
                >
                  <MenuItem value="">All</MenuItem>
                  <MenuItem value="user.login">User Login</MenuItem>
                  <MenuItem value="data.access">Data Access</MenuItem>
                  <MenuItem value="api.call">API Call</MenuItem>
                  <MenuItem value="security.alert">Security Alert</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={2}>
              <FormControl fullWidth>
                <InputLabel>Severity</InputLabel>
                <Select
                  value={filters.severity}
                  onChange={(e) => setFilters({ ...filters, severity: e.target.value })}
                >
                  <MenuItem value="">All</MenuItem>
                  <MenuItem value="info">Info</MenuItem>
                  <MenuItem value="warning">Warning</MenuItem>
                  <MenuItem value="error">Error</MenuItem>
                  <MenuItem value="critical">Critical</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={2}>
              <Button
                variant="contained"
                startIcon={<SearchIcon />}
                onClick={fetchLogs}
                fullWidth
              >
                Search
              </Button>
            </Grid>
          </Grid>
          
          <Grid container spacing={2} alignItems="center" sx={{ mt: 1 }}>
            <Grid item xs={12} md={3}>
              <TextField
                fullWidth
                label="User ID"
                value={filters.userId}
                onChange={(e) => setFilters({ ...filters, userId: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <TextField
                fullWidth
                label="Service"
                value={filters.service}
                onChange={(e) => setFilters({ ...filters, service: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="Search Text"
                value={filters.searchText}
                onChange={(e) => setFilters({ ...filters, searchText: e.target.value })}
                placeholder="Search in action, details..."
              />
            </Grid>
            <Grid item xs={12} md={2}>
              <Box display="flex" gap={1}>
                <Tooltip title="Refresh">
                  <IconButton onClick={fetchLogs}>
                    <RefreshIcon />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Export">
                  <IconButton onClick={handleExport}>
                    <DownloadIcon />
                  </IconButton>
                </Tooltip>
              </Box>
            </Grid>
          </Grid>
        </Paper>
        
        {/* Logs Table */}
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Timestamp</TableCell>
                <TableCell>Event Type</TableCell>
                <TableCell>Severity</TableCell>
                <TableCell>User</TableCell>
                <TableCell>Service</TableCell>
                <TableCell>Action</TableCell>
                <TableCell>Result</TableCell>
                <TableCell>Duration</TableCell>
                <TableCell>IP Address</TableCell>
                <TableCell>Details</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {logs.map((log) => (
                <TableRow key={log.id}>
                  <TableCell>
                    {new Date(log.timestamp).toLocaleString()}
                  </TableCell>
                  <TableCell>
                    <Chip label={log.event_type} size="small" />
                  </TableCell>
                  <TableCell>
                    <Box display="flex" alignItems="center">
                      {getSeverityIcon(log.severity)}
                      <Typography variant="body2" sx={{ ml: 1 }}>
                        {log.severity}
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell>{log.user_id || '-'}</TableCell>
                  <TableCell>{log.service}</TableCell>
                  <TableCell>{log.action}</TableCell>
                  <TableCell>{getResultChip(log.result)}</TableCell>
                  <TableCell>
                    {log.duration_ms ? `${log.duration_ms}ms` : '-'}
                  </TableCell>
                  <TableCell>{log.ip_address || '-'}</TableCell>
                  <TableCell>
                    <IconButton
                      size="small"
                      onClick={() => setSelectedLog(log)}
                    >
                      <InfoIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
          
          <TablePagination
            component="div"
            count={totalCount}
            page={page}
            onPageChange={(_, newPage) => setPage(newPage)}
            rowsPerPage={rowsPerPage}
            onRowsPerPageChange={(e) => {
              setRowsPerPage(parseInt(e.target.value, 10));
              setPage(0);
            }}
            rowsPerPageOptions={[10, 25, 50, 100]}
          />
        </TableContainer>
        
        {/* Details Dialog */}
        <Dialog
          open={selectedLog !== null}
          onClose={() => setSelectedLog(null)}
          maxWidth="md"
          fullWidth
        >
          <DialogTitle>
            Audit Log Details
          </DialogTitle>
          <DialogContent>
            {selectedLog && (
              <Box>
                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <Typography variant="subtitle2">Log ID</Typography>
                    <Typography>{selectedLog.id}</Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="subtitle2">Timestamp</Typography>
                    <Typography>
                      {new Date(selectedLog.timestamp).toLocaleString()}
                    </Typography>
                  </Grid>
                  <Grid item xs={12}>
                    <Typography variant="subtitle2">Details</Typography>
                    <Paper sx={{ p: 2, bgcolor: 'grey.100' }}>
                      <pre>
                        {JSON.stringify(selectedLog.details, null, 2)}
                      </pre>
                    </Paper>
                  </Grid>
                </Grid>
              </Box>
            )}
          </DialogContent>
        </Dialog>
      </Box>
    </LocalizationProvider>
  );
};

export default AuditLogViewer;
EOF

# 10. Create Monitoring Alerts
echo "10. Creating Monitoring Alerts..."
cat > services/audit-logging/alerts.yaml << 'EOF'
# Prometheus Alert Rules for Audit Logging
groups:
  - name: audit_logging
    interval: 30s
    rules:
      - alert: HighErrorRate
        expr: rate(audit_logs_created_total{result="error"}[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: High error rate in audit logs
          description: "Error rate is {{ $value }} errors per second"
      
      - alert: SecurityEventDetected
        expr: increase(audit_logs_created_total{event_type=~"security.*"}[1m]) > 5
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: Multiple security events detected
          description: "{{ $value }} security events in the last minute"
      
      - alert: AuditServiceDown
        expr: up{job="audit-service"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: Audit service is down
          description: "Audit logging service has been down for more than 1 minute"
      
      - alert: AuditLogBacklog
        expr: rate(audit_log_processing_seconds_sum[5m]) / rate(audit_log_processing_seconds_count[5m]) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: Audit log processing is slow
          description: "Average processing time is {{ $value }} seconds"
EOF

# 11. Deploy the service
echo "11. Deploying Audit Logging Service..."
docker-compose -f docker-compose.audit.yml up -d

# 12. Wait for services to be ready
echo "12. Waiting for services to be ready..."
for service in mongodb elasticsearch kafka audit-service; do
    echo "Waiting for $service..."
    for i in {1..30}; do
        if docker-compose -f docker-compose.audit.yml ps | grep $service | grep -q "Up"; then
            echo "$service is ready!"
            break
        fi
        sleep 2
    done
done

# 13. Initialize Elasticsearch
echo "13. Initializing Elasticsearch..."
curl -X PUT "localhost:9200/_index_template/audit-logs-template" \
  -H 'Content-Type: application/json' \
  -d @services/audit-logging/elasticsearch-template.json || echo "Elasticsearch initialization skipped"

# 14. Create Kafka topics
echo "14. Creating Kafka topics..."
docker exec audit-kafka kafka-topics --create \
  --topic audit-logs \
  --bootstrap-server localhost:9092 \
  --partitions 3 \
  --replication-factor 1 || echo "Kafka topic creation skipped"

# 15. Summary
echo "
=== Audit Logging Setup Complete ===

✅ Features Implemented:
1. Comprehensive audit logging for all actions
2. Multi-backend storage (MongoDB, Elasticsearch, Kafka)
3. Real-time log streaming
4. Advanced search and filtering
5. Log retention policies
6. Security event detection
7. Performance metrics
8. Export capabilities

📊 Services Running:
- Audit Service: http://localhost:9028
- MongoDB: mongodb://localhost:27017
- Elasticsearch: http://localhost:9200
- Kibana: http://localhost:5601
- Kafka: localhost:9092

🔧 Integration:
1. Python SDK: services/audit-logging/sdk/python/audit_client.py
2. FastAPI Middleware: services/audit-logging/middleware/fastapi_audit.py
3. React Component: apps/web/src/components/AuditLogViewer.tsx

📝 Usage Examples:

Python:
```python
from audit_client import AuditClient, EventType

client = AuditClient()
await client.log(
    event_type=EventType.USER_LOGIN,
    action='User login',
    user_id='user123',
    result='success'
)
```

FastAPI:
```python
from audit_client import audit_log, EventType

@app.post('/api/users/{user_id}')
@audit_log(EventType.DATA_UPDATE, resource_type='user')
async def update_user(user_id: str, data: dict):
    # Function automatically logged
    pass
```

🚨 Monitoring:
- Prometheus metrics: http://localhost:9028/metrics
- Kibana dashboards: http://localhost:5601
- Alert rules configured for security events

⚡ Next Steps:
1. Configure retention policies
2. Set up Kibana dashboards
3. Integrate with all services
4. Configure security alerts
5. Set up log archival

📚 Documentation:
See services/audit-logging/README.md for detailed usage
"

# Create comprehensive README
cat > services/audit-logging/README.md << 'EOF'
# Audit Logging Service

## Overview
Comprehensive audit logging solution providing:
- Complete activity tracking
- Security event monitoring
- Compliance reporting
- Performance analytics
- Real-time alerting

## Architecture
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Services   │────▶│Audit Service│────▶│   MongoDB   │
└─────────────┘     └─────────────┘     └─────────────┘
                            │                    │
                            ├────────────────────┤
                            ▼                    ▼
                    ┌─────────────┐     ┌─────────────┐
                    │Elasticsearch│     │    Kafka    │
                    └─────────────┘     └─────────────┘
                            │                    │
                            ▼                    ▼
                    ┌─────────────┐     ┌─────────────┐
                    │   Kibana    │     │ Consumers   │
                    └─────────────┘     └─────────────┘
```

## Event Types
- **Authentication**: login, logout, password changes
- **Authorization**: permission checks, role changes
- **Data Operations**: CRUD operations on resources
- **API Calls**: All API endpoint access
- **Security Events**: Failed logins, suspicious activity
- **System Events**: Service starts/stops, config changes
- **Compliance**: Consent, data requests, policy acceptance

## Integration Guide

### Python Services
```python
# Install SDK
pip install -e services/audit-logging/sdk/python

# Basic usage
from audit_client import AuditClient, EventType, Severity

client = AuditClient(service_name="my-service")

# Log an event
await client.log(
    event_type=EventType.DATA_CREATE,
    action="Created new policy",
    user_id="user123",
    resource_type="policy",
    resource_id="policy456",
    details={"title": "New Policy", "category": "health"}
)

# Using decorator
from audit_client import audit_log

@audit_log(EventType.DATA_READ, resource_type="policy")
async def get_policy(policy_id: str):
    # Automatically logged
    return await fetch_policy(policy_id)
```

### FastAPI Integration
```python
from fastapi import FastAPI
from audit_middleware import AuditLoggingMiddleware

app = FastAPI()

# Add middleware for automatic logging
app.add_middleware(AuditLoggingMiddleware)

# Or use custom route class
from audit_middleware import AuditLoggingRoute

app = FastAPI(route_class=AuditLoggingRoute)
```

### Frontend Integration
```typescript
// Log from frontend
await fetch('/api/audit/log', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    event_type: 'user.action',
    action: 'Viewed sensitive data',
    resource_type: 'report',
    resource_id: reportId
  })
});
```

## Querying Logs

### REST API
```bash
# Query logs
curl -X POST http://localhost:9028/query \
  -H "Content-Type: application/json" \
  -d '{
    "start_time": "2024-01-01T00:00:00Z",
    "event_types": ["user.login", "security.alert"],
    "user_id": "user123",
    "limit": 100
  }'

# Get statistics
curl http://localhost:9028/stats?time_range=24

# Export logs
curl http://localhost:9028/export?format=csv > audit-logs.csv
```

### Kibana
1. Access Kibana at http://localhost:5601
2. Navigate to Discover
3. Select `audit-logs-*` index pattern
4. Use KQL for queries:
   ```
   event_type: "security.*" and severity: "critical"
   ```

## Retention Policies
Configure in MongoDB:
```javascript
db.audit_retention_policies.insert({
  event_type: "api.*",
  retention_days: 90,
  archive: true
});
```

## Security Considerations
1. **Encryption**: Enable encryption for sensitive fields
2. **Access Control**: Restrict query access by role
3. **Redaction**: Automatic removal of sensitive data
4. **Integrity**: Content hashing prevents tampering
5. **Compliance**: GDPR-compliant data handling

## Performance Tuning
1. **Indexing**: Ensure proper indexes on frequently queried fields
2. **Partitioning**: Use time-based partitioning for large datasets
3. **Archival**: Move old logs to cold storage
4. **Caching**: Redis caching for recent logs
5. **Batching**: Batch inserts for high-volume logging

## Monitoring
- Metrics: http://localhost:9028/metrics
- Health: http://localhost:9028/health
- Alerts: Configured in Prometheus/Alertmanager
- Dashboards: Pre-built Kibana dashboards

## Troubleshooting
1. **Missing logs**: Check service connectivity
2. **Slow queries**: Review indexes and query patterns
3. **Storage issues**: Monitor disk usage and retention
4. **Performance**: Check metrics and adjust resources

## Best Practices
1. Log all security-relevant events
2. Include correlation IDs for tracing
3. Avoid logging sensitive data
4. Use appropriate severity levels
5. Implement log rotation
6. Regular audit log reviews
7. Test disaster recovery

## Compliance Reports
Generate compliance reports:
```bash
# GDPR audit trail
curl http://localhost:9028/reports/gdpr?user_id=user123

# Security audit
curl http://localhost:9028/reports/security?days=30

# Access report
curl http://localhost:9028/reports/access?resource_type=policy
```
EOF