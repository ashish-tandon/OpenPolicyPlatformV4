"""
Comprehensive Audit Logging Service for OpenPolicy Platform
Tracks all user actions, system events, and security activities
"""

import os
import json
import time
import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from enum import Enum
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Request, Query, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, validator
from motor.motor_asyncio import AsyncIOMotorClient
import redis.asyncio as redis
from elasticsearch import AsyncElasticsearch
from kafka import KafkaProducer, KafkaConsumer
import structlog
from prometheus_client import Counter, Histogram, generate_latest

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Configuration
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
MONGODB_DB = os.getenv("MONGODB_DB", "audit_logs")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/4")
ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
KAFKA_BROKERS = os.getenv("KAFKA_BROKERS", "localhost:9092").split(",")
SERVICE_PORT = int(os.getenv("SERVICE_PORT", 9028))
LOG_RETENTION_DAYS = int(os.getenv("LOG_RETENTION_DAYS", 365))
ENABLE_ENCRYPTION = os.getenv("ENABLE_ENCRYPTION", "true").lower() == "true"
ENCRYPTION_KEY = os.getenv("AUDIT_ENCRYPTION_KEY", "default-key-change-me")

# Prometheus metrics
audit_logs_created = Counter('audit_logs_created_total', 'Total audit logs created', ['event_type', 'service'])
audit_logs_queried = Counter('audit_logs_queried_total', 'Total audit log queries')
audit_log_latency = Histogram('audit_log_processing_seconds', 'Audit log processing latency')
audit_log_size = Histogram('audit_log_size_bytes', 'Size of audit logs in bytes')

# Security
security = HTTPBearer()

class EventType(str, Enum):
    """Types of audit events"""
    # Authentication events
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    USER_REGISTER = "user.register"
    PASSWORD_CHANGE = "user.password_change"
    PASSWORD_RESET = "user.password_reset"
    TWO_FACTOR_ENABLED = "user.2fa_enabled"
    TWO_FACTOR_DISABLED = "user.2fa_disabled"
    
    # Authorization events
    PERMISSION_GRANTED = "auth.permission_granted"
    PERMISSION_DENIED = "auth.permission_denied"
    ROLE_ASSIGNED = "auth.role_assigned"
    ROLE_REMOVED = "auth.role_removed"
    
    # Data events
    DATA_CREATE = "data.create"
    DATA_READ = "data.read"
    DATA_UPDATE = "data.update"
    DATA_DELETE = "data.delete"
    DATA_EXPORT = "data.export"
    DATA_IMPORT = "data.import"
    
    # API events
    API_CALL = "api.call"
    API_ERROR = "api.error"
    API_RATE_LIMITED = "api.rate_limited"
    
    # System events
    SERVICE_START = "system.service_start"
    SERVICE_STOP = "system.service_stop"
    CONFIG_CHANGE = "system.config_change"
    BACKUP_CREATED = "system.backup_created"
    MAINTENANCE_MODE = "system.maintenance_mode"
    
    # Security events
    SECURITY_ALERT = "security.alert"
    BREACH_DETECTED = "security.breach_detected"
    SUSPICIOUS_ACTIVITY = "security.suspicious_activity"
    FAILED_LOGIN = "security.failed_login"
    ACCOUNT_LOCKED = "security.account_locked"
    
    # Compliance events
    CONSENT_GRANTED = "compliance.consent_granted"
    CONSENT_REVOKED = "compliance.consent_revoked"
    DATA_REQUEST = "compliance.data_request"
    DATA_DELETION = "compliance.data_deletion"
    POLICY_ACCEPTED = "compliance.policy_accepted"

class Severity(str, Enum):
    """Severity levels for audit events"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class AuditLog(BaseModel):
    """Audit log entry model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    event_type: EventType
    severity: Severity = Severity.INFO
    service: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    action: str
    result: str = "success"
    details: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    duration_ms: Optional[int] = None
    request_id: Optional[str] = None
    correlation_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('details', 'metadata')
    def remove_sensitive_data(cls, v):
        """Remove sensitive data from logs"""
        if v and isinstance(v, dict):
            sensitive_keys = ['password', 'token', 'secret', 'key', 'credential']
            for key in list(v.keys()):
                if any(sensitive in key.lower() for sensitive in sensitive_keys):
                    v[key] = "[REDACTED]"
        return v

class AuditLogQuery(BaseModel):
    """Query parameters for searching audit logs"""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    event_types: Optional[List[EventType]] = None
    severity_levels: Optional[List[Severity]] = None
    user_id: Optional[str] = None
    service: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    ip_address: Optional[str] = None
    search_text: Optional[str] = None
    limit: int = Field(default=100, le=1000)
    offset: int = Field(default=0, ge=0)
    sort_by: str = Field(default="timestamp", regex="^(timestamp|event_type|severity|user_id)$")
    sort_order: str = Field(default="desc", regex="^(asc|desc)$")

class AuditLogStats(BaseModel):
    """Statistics about audit logs"""
    total_logs: int
    logs_by_type: Dict[str, int]
    logs_by_severity: Dict[str, int]
    logs_by_service: Dict[str, int]
    time_range: Dict[str, Any]
    top_users: List[Dict[str, Any]]
    error_rate: float

# Global instances
mongo_client: Optional[AsyncIOMotorClient] = None
redis_client: Optional[redis.Redis] = None
es_client: Optional[AsyncElasticsearch] = None
kafka_producer: Optional[KafkaProducer] = None

class AuditLogger:
    """Centralized audit logging handler"""
    
    def __init__(self, mongo_db, redis_client, es_client, kafka_producer):
        self.mongo_db = mongo_db
        self.redis = redis_client
        self.es = es_client
        self.kafka = kafka_producer
        self.collection = mongo_db.audit_logs
        
    async def log(self, audit_log: AuditLog) -> str:
        """Log an audit event"""
        start_time = time.time()
        
        try:
            # Convert to dict
            log_dict = audit_log.dict()
            
            # Add server-side timestamp
            log_dict['server_timestamp'] = datetime.utcnow()
            
            # Calculate hash for deduplication
            content_hash = self._calculate_hash(log_dict)
            log_dict['content_hash'] = content_hash
            
            # Check for duplicate
            if await self._is_duplicate(content_hash):
                logger.debug("Duplicate audit log detected", hash=content_hash)
                return audit_log.id
            
            # Encrypt sensitive fields if enabled
            if ENABLE_ENCRYPTION:
                log_dict = self._encrypt_sensitive_fields(log_dict)
            
            # Store in MongoDB (primary storage)
            await self.collection.insert_one(log_dict)
            
            # Index in Elasticsearch for searching
            await self._index_in_elasticsearch(log_dict)
            
            # Send to Kafka for real-time processing
            self._send_to_kafka(log_dict)
            
            # Cache recent logs in Redis
            await self._cache_in_redis(log_dict)
            
            # Update metrics
            audit_logs_created.labels(
                event_type=audit_log.event_type,
                service=audit_log.service
            ).inc()
            
            audit_log_size.observe(len(json.dumps(log_dict)))
            
            # Log processing time
            processing_time = time.time() - start_time
            audit_log_latency.observe(processing_time)
            
            logger.info(
                "Audit log created",
                log_id=audit_log.id,
                event_type=audit_log.event_type,
                processing_time=processing_time
            )
            
            return audit_log.id
            
        except Exception as e:
            logger.error("Failed to create audit log", error=str(e), log_id=audit_log.id)
            raise
    
    async def query(self, query: AuditLogQuery) -> List[Dict[str, Any]]:
        """Query audit logs"""
        try:
            # Build MongoDB query
            mongo_query = {}
            
            if query.start_time:
                mongo_query['timestamp'] = {'$gte': query.start_time}
            if query.end_time:
                if 'timestamp' in mongo_query:
                    mongo_query['timestamp']['$lte'] = query.end_time
                else:
                    mongo_query['timestamp'] = {'$lte': query.end_time}
            
            if query.event_types:
                mongo_query['event_type'] = {'$in': [et.value for et in query.event_types]}
            if query.severity_levels:
                mongo_query['severity'] = {'$in': [s.value for s in query.severity_levels]}
            if query.user_id:
                mongo_query['user_id'] = query.user_id
            if query.service:
                mongo_query['service'] = query.service
            if query.resource_type:
                mongo_query['resource_type'] = query.resource_type
            if query.resource_id:
                mongo_query['resource_id'] = query.resource_id
            if query.ip_address:
                mongo_query['ip_address'] = query.ip_address
            
            # Use Elasticsearch for text search if available
            if query.search_text and self.es:
                return await self._search_in_elasticsearch(query)
            
            # Sort order
            sort_direction = 1 if query.sort_order == "asc" else -1
            
            # Execute query
            cursor = self.collection.find(mongo_query).sort(
                query.sort_by, sort_direction
            ).skip(query.offset).limit(query.limit)
            
            logs = []
            async for log in cursor:
                # Decrypt if needed
                if ENABLE_ENCRYPTION:
                    log = self._decrypt_sensitive_fields(log)
                
                # Remove MongoDB _id
                log.pop('_id', None)
                logs.append(log)
            
            # Update query counter
            audit_logs_queried.inc()
            
            return logs
            
        except Exception as e:
            logger.error("Failed to query audit logs", error=str(e))
            raise
    
    async def get_stats(self, time_range: Optional[int] = 24) -> AuditLogStats:
        """Get audit log statistics"""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=time_range)
            
            # Aggregation pipeline
            pipeline = [
                {
                    '$match': {
                        'timestamp': {'$gte': start_time, '$lte': end_time}
                    }
                },
                {
                    '$facet': {
                        'total': [{'$count': 'count'}],
                        'by_type': [
                            {'$group': {'_id': '$event_type', 'count': {'$sum': 1}}},
                            {'$sort': {'count': -1}}
                        ],
                        'by_severity': [
                            {'$group': {'_id': '$severity', 'count': {'$sum': 1}}}
                        ],
                        'by_service': [
                            {'$group': {'_id': '$service', 'count': {'$sum': 1}}},
                            {'$sort': {'count': -1}}
                        ],
                        'top_users': [
                            {'$match': {'user_id': {'$ne': None}}},
                            {'$group': {'_id': '$user_id', 'count': {'$sum': 1}}},
                            {'$sort': {'count': -1}},
                            {'$limit': 10}
                        ],
                        'errors': [
                            {'$match': {'result': 'error'}},
                            {'$count': 'count'}
                        ]
                    }
                }
            ]
            
            result = await self.collection.aggregate(pipeline).to_list(1)
            
            if not result:
                return AuditLogStats(
                    total_logs=0,
                    logs_by_type={},
                    logs_by_severity={},
                    logs_by_service={},
                    time_range={'start': start_time, 'end': end_time, 'hours': time_range},
                    top_users=[],
                    error_rate=0.0
                )
            
            data = result[0]
            total = data['total'][0]['count'] if data['total'] else 0
            errors = data['errors'][0]['count'] if data['errors'] else 0
            
            return AuditLogStats(
                total_logs=total,
                logs_by_type={item['_id']: item['count'] for item in data['by_type']},
                logs_by_severity={item['_id']: item['count'] for item in data['by_severity']},
                logs_by_service={item['_id']: item['count'] for item in data['by_service']},
                time_range={'start': start_time, 'end': end_time, 'hours': time_range},
                top_users=[{'user_id': item['_id'], 'count': item['count']} for item in data['top_users']],
                error_rate=(errors / total * 100) if total > 0 else 0.0
            )
            
        except Exception as e:
            logger.error("Failed to get audit stats", error=str(e))
            raise
    
    async def cleanup_old_logs(self, retention_days: Optional[int] = None) -> int:
        """Clean up old audit logs"""
        try:
            retention = retention_days or LOG_RETENTION_DAYS
            cutoff_date = datetime.utcnow() - timedelta(days=retention)
            
            # Archive before deletion (optional)
            # await self._archive_old_logs(cutoff_date)
            
            # Delete from MongoDB
            result = await self.collection.delete_many({
                'timestamp': {'$lt': cutoff_date}
            })
            
            # Delete from Elasticsearch
            if self.es:
                await self.es.delete_by_query(
                    index='audit-logs',
                    body={
                        'query': {
                            'range': {
                                'timestamp': {'lt': cutoff_date.isoformat()}
                            }
                        }
                    }
                )
            
            logger.info(
                "Cleaned up old audit logs",
                deleted_count=result.deleted_count,
                cutoff_date=cutoff_date
            )
            
            return result.deleted_count
            
        except Exception as e:
            logger.error("Failed to cleanup old logs", error=str(e))
            raise
    
    def _calculate_hash(self, log_dict: Dict) -> str:
        """Calculate hash for deduplication"""
        # Use key fields for hash
        key_fields = ['event_type', 'user_id', 'resource_id', 'action', 'timestamp']
        hash_input = ''.join(str(log_dict.get(f, '')) for f in key_fields)
        return hashlib.sha256(hash_input.encode()).hexdigest()
    
    async def _is_duplicate(self, content_hash: str) -> bool:
        """Check if log is duplicate using Redis"""
        if not self.redis:
            return False
        
        key = f"audit:hash:{content_hash}"
        exists = await self.redis.exists(key)
        if not exists:
            await self.redis.setex(key, 300, "1")  # 5 minute TTL
        return exists
    
    def _encrypt_sensitive_fields(self, log_dict: Dict) -> Dict:
        """Encrypt sensitive fields"""
        # TODO: Implement encryption for sensitive fields
        return log_dict
    
    def _decrypt_sensitive_fields(self, log_dict: Dict) -> Dict:
        """Decrypt sensitive fields"""
        # TODO: Implement decryption for sensitive fields
        return log_dict
    
    async def _index_in_elasticsearch(self, log_dict: Dict):
        """Index log in Elasticsearch for searching"""
        if not self.es:
            return
        
        try:
            await self.es.index(
                index='audit-logs',
                id=log_dict['id'],
                document=log_dict
            )
        except Exception as e:
            logger.warning("Failed to index in Elasticsearch", error=str(e))
    
    def _send_to_kafka(self, log_dict: Dict):
        """Send log to Kafka for real-time processing"""
        if not self.kafka:
            return
        
        try:
            self.kafka.send(
                'audit-logs',
                key=log_dict['id'].encode(),
                value=json.dumps(log_dict, default=str).encode()
            )
        except Exception as e:
            logger.warning("Failed to send to Kafka", error=str(e))
    
    async def _cache_in_redis(self, log_dict: Dict):
        """Cache recent logs in Redis"""
        if not self.redis:
            return
        
        try:
            # Add to sorted set by timestamp
            score = log_dict['timestamp'].timestamp()
            await self.redis.zadd(
                'audit:recent',
                {json.dumps(log_dict, default=str): score}
            )
            
            # Keep only last 1000 logs
            await self.redis.zremrangebyrank('audit:recent', 0, -1001)
        except Exception as e:
            logger.warning("Failed to cache in Redis", error=str(e))
    
    async def _search_in_elasticsearch(self, query: AuditLogQuery) -> List[Dict]:
        """Search logs using Elasticsearch"""
        if not self.es:
            return []
        
        try:
            body = {
                'query': {
                    'bool': {
                        'must': [
                            {
                                'multi_match': {
                                    'query': query.search_text,
                                    'fields': ['action', 'details.*', 'error_message']
                                }
                            }
                        ],
                        'filter': []
                    }
                },
                'from': query.offset,
                'size': query.limit,
                'sort': [{query.sort_by: {'order': query.sort_order}}]
            }
            
            # Add filters
            if query.start_time:
                body['query']['bool']['filter'].append({
                    'range': {'timestamp': {'gte': query.start_time.isoformat()}}
                })
            
            result = await self.es.search(index='audit-logs', body=body)
            
            return [hit['_source'] for hit in result['hits']['hits']]
            
        except Exception as e:
            logger.error("Elasticsearch search failed", error=str(e))
            return []

# Dependency
audit_logger: Optional[AuditLogger] = None

async def get_audit_logger() -> AuditLogger:
    """Get audit logger instance"""
    if not audit_logger:
        raise HTTPException(status_code=503, detail="Audit logger not initialized")
    return audit_logger

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify authentication token"""
    # TODO: Implement proper token verification
    return {"user_id": "system", "role": "admin"}

# Lifespan manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    global mongo_client, redis_client, es_client, kafka_producer, audit_logger
    
    # Startup
    logger.info("Starting Audit Logging Service...")
    
    # Connect to MongoDB
    mongo_client = AsyncIOMotorClient(MONGODB_URL)
    mongo_db = mongo_client[MONGODB_DB]
    
    # Create indexes
    await mongo_db.audit_logs.create_index("timestamp")
    await mongo_db.audit_logs.create_index("event_type")
    await mongo_db.audit_logs.create_index("user_id")
    await mongo_db.audit_logs.create_index("service")
    await mongo_db.audit_logs.create_index([("timestamp", -1), ("event_type", 1)])
    
    # Connect to Redis
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    await redis_client.ping()
    
    # Connect to Elasticsearch (optional)
    try:
        es_client = AsyncElasticsearch([ELASTICSEARCH_URL])
        await es_client.info()
    except:
        logger.warning("Elasticsearch not available, search functionality limited")
        es_client = None
    
    # Connect to Kafka (optional)
    try:
        kafka_producer = KafkaProducer(
            bootstrap_servers=KAFKA_BROKERS,
            value_serializer=lambda v: json.dumps(v, default=str).encode()
        )
    except:
        logger.warning("Kafka not available, real-time streaming disabled")
        kafka_producer = None
    
    # Initialize audit logger
    audit_logger = AuditLogger(mongo_db, redis_client, es_client, kafka_producer)
    
    # Log service start
    await audit_logger.log(AuditLog(
        event_type=EventType.SERVICE_START,
        service="audit-logging",
        action="Service started",
        details={"version": "1.0.0", "port": SERVICE_PORT}
    ))
    
    logger.info("Audit Logging Service started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Audit Logging Service...")
    
    # Log service stop
    await audit_logger.log(AuditLog(
        event_type=EventType.SERVICE_STOP,
        service="audit-logging",
        action="Service stopped"
    ))
    
    # Close connections
    if mongo_client:
        mongo_client.close()
    if redis_client:
        await redis_client.close()
    if es_client:
        await es_client.close()
    if kafka_producer:
        kafka_producer.close()

# Create FastAPI app
app = FastAPI(
    title="Audit Logging Service",
    description="Comprehensive audit logging for OpenPolicy Platform",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "audit-logging",
        "backends": {
            "mongodb": mongo_client is not None,
            "redis": redis_client is not None,
            "elasticsearch": es_client is not None,
            "kafka": kafka_producer is not None
        }
    }

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(generate_latest())

@app.post("/log")
async def create_audit_log(
    audit_log: AuditLog,
    request: Request,
    background_tasks: BackgroundTasks,
    logger: AuditLogger = Depends(get_audit_logger),
    auth: Dict = Depends(verify_token)
):
    """Create a new audit log entry"""
    try:
        # Enrich with request information
        audit_log.ip_address = audit_log.ip_address or request.client.host
        audit_log.user_agent = audit_log.user_agent or request.headers.get("user-agent")
        audit_log.request_id = request.headers.get("x-request-id")
        
        # Log asynchronously
        log_id = await logger.log(audit_log)
        
        return {"log_id": log_id, "status": "created"}
        
    except Exception as e:
        logger.error("Failed to create audit log", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create audit log")

@app.post("/query")
async def query_audit_logs(
    query: AuditLogQuery,
    logger: AuditLogger = Depends(get_audit_logger),
    auth: Dict = Depends(verify_token)
):
    """Query audit logs"""
    try:
        logs = await logger.query(query)
        return {
            "logs": logs,
            "count": len(logs),
            "offset": query.offset,
            "limit": query.limit
        }
    except Exception as e:
        logger.error("Failed to query audit logs", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to query audit logs")

@app.get("/stats")
async def get_audit_stats(
    time_range: int = Query(default=24, description="Time range in hours"),
    logger: AuditLogger = Depends(get_audit_logger),
    auth: Dict = Depends(verify_token)
):
    """Get audit log statistics"""
    try:
        stats = await logger.get_stats(time_range)
        return stats
    except Exception as e:
        logger.error("Failed to get audit stats", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get statistics")

@app.post("/cleanup")
async def cleanup_old_logs(
    retention_days: Optional[int] = None,
    logger: AuditLogger = Depends(get_audit_logger),
    auth: Dict = Depends(verify_token)
):
    """Clean up old audit logs"""
    try:
        # Verify admin role
        if auth.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        deleted_count = await logger.cleanup_old_logs(retention_days)
        
        # Log the cleanup action
        await logger.log(AuditLog(
            event_type=EventType.DATA_DELETE,
            service="audit-logging",
            user_id=auth["user_id"],
            action="Cleaned up old audit logs",
            details={"deleted_count": deleted_count, "retention_days": retention_days}
        ))
        
        return {"deleted_count": deleted_count, "status": "completed"}
        
    except Exception as e:
        logger.error("Failed to cleanup logs", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to cleanup logs")

@app.get("/export")
async def export_audit_logs(
    format: str = Query(default="json", regex="^(json|csv)$"),
    query: AuditLogQuery = Depends(),
    logger: AuditLogger = Depends(get_audit_logger),
    auth: Dict = Depends(verify_token)
):
    """Export audit logs in various formats"""
    try:
        logs = await logger.query(query)
        
        if format == "csv":
            # Convert to CSV
            import csv
            import io
            
            output = io.StringIO()
            if logs:
                writer = csv.DictWriter(output, fieldnames=logs[0].keys())
                writer.writeheader()
                writer.writerows(logs)
            
            from fastapi.responses import Response
            return Response(
                content=output.getvalue(),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=audit-logs.csv"}
            )
        else:
            # Return JSON
            return {
                "logs": logs,
                "export_date": datetime.utcnow().isoformat(),
                "query": query.dict()
            }
            
    except Exception as e:
        logger.error("Failed to export logs", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to export logs")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=SERVICE_PORT)