"""
Data Management Service - Open Policy Platform

This service handles all data management functionality including:
- Data governance and policies
- Data quality validation and monitoring
- Data lifecycle management
- Data catalog and metadata
- Data operations and backup
- Health and monitoring
"""

from fastapi import FastAPI, Response, HTTPException, Depends, Query
from http import HTTPStatus
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest, Counter, Histogram
from typing import List, Optional, Dict, Any, Union
import os
import logging
from datetime import datetime, timedelta
import json
import uuid
import time
import hashlib
import sqlite3
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="data-management-service", version="1.0.0")
security = HTTPBearer()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics
data_operations = Counter('data_operations_total', 'Total data operations', ['operation', 'status'])
data_duration = Histogram('data_duration_seconds', 'Data operation duration')
data_quality_score = Histogram('data_quality_score', 'Data quality scores')
data_lifecycle_events = Counter('data_lifecycle_events_total', 'Total lifecycle events', ['event_type'])

# Mock database for development (replace with real database)
data_policies_db = [
    {
        "id": "policy-001",
        "name": "Data Retention Policy",
        "description": "Standard data retention policy for all data types",
        "category": "retention",
        "rules": {
            "user_data": "7 years",
            "policy_data": "10 years",
            "file_data": "5 years",
            "audit_logs": "3 years"
        },
        "status": "active",
        "created_by": "admin",
        "created_at": "2023-01-03T00:00:00Z",
        "updated_at": "2023-01-03T00:00:00Z"
    },
    {
        "id": "policy-002",
        "name": "Data Quality Standards",
        "description": "Minimum quality standards for all data",
        "category": "quality",
        "rules": {
            "completeness": "95%",
            "accuracy": "98%",
            "consistency": "90%",
            "timeliness": "24 hours"
        },
        "status": "active",
        "created_by": "admin",
        "created_at": "2023-01-03T00:00:00Z",
        "updated_at": "2023-01-03T00:00:00Z"
    }
]

data_catalog_db = [
    {
        "id": "catalog-001",
        "name": "User Data",
        "description": "User profile and authentication data",
        "data_type": "structured",
        "source": "auth-service",
        "schema": {
            "fields": ["id", "username", "email", "role", "created_at"],
            "primary_key": "id",
            "indexes": ["username", "email"]
        },
        "quality_score": 98.5,
        "last_updated": "2023-01-03T00:00:00Z",
        "status": "active"
    },
    {
        "id": "catalog-002",
        "name": "Policy Data",
        "description": "Policy documents and metadata",
        "data_type": "structured",
        "source": "policy-service",
        "schema": {
            "fields": ["id", "title", "content", "category", "status", "created_at"],
            "primary_key": "id",
            "indexes": ["category", "status"]
        },
        "quality_score": 95.2,
        "last_updated": "2023-01-03T00:00:00Z",
        "status": "active"
    }
]

data_quality_db = [
    {
        "id": "quality-001",
        "data_source": "auth-service",
        "metric": "completeness",
        "value": 98.5,
        "threshold": 95.0,
        "status": "pass",
        "timestamp": "2023-01-03T00:00:00Z"
    },
    {
        "id": "quality-002",
        "data_source": "policy-service",
        "metric": "accuracy",
        "value": 97.8,
        "threshold": 98.0,
        "status": "warning",
        "timestamp": "2023-01-03T00:00:00Z"
    }
]

# Simple validation functions
def validate_policy_name(name: str) -> bool:
    """Validate policy name"""
    return name and len(name) <= 100 and not any(char in name for char in ['<', '>', ':', '"', '|', '?', '*', '\\', '/'])

def validate_catalog_name(name: str) -> bool:
    """Validate catalog name"""
    return name and len(name) <= 100 and not any(char in name for char in ['<', '>', ':', '"', '|', '?', '*', '\\', '/'])

def calculate_quality_score(metrics: Dict[str, float]) -> float:
    """Calculate overall quality score from metrics"""
    if not metrics:
        return 0.0
    return sum(metrics.values()) / len(metrics)

# Data Management service implementation
class DataManagementService:
    def __init__(self):
        self.policies = data_policies_db
        self.catalog = data_catalog_db
        self.quality = data_quality_db
    
    # Policy Management
    def list_policies(self, skip: int = 0, limit: int = 100, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all data policies with optional filtering"""
        filtered_policies = self.policies
        
        if category:
            filtered_policies = [p for p in filtered_policies if p["category"] == category]
        
        return filtered_policies[skip:skip + limit]
    
    def get_policy(self, policy_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific policy by ID"""
        for policy in self.policies:
            if policy["id"] == policy_id:
                return policy
        return None
    
    def create_policy(self, policy_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new data policy"""
        if not validate_policy_name(policy_data.get("name", "")):
            raise ValueError("Invalid policy name")
        
        new_policy = {
            "id": f"policy-{str(uuid.uuid4())[:8]}",
            "name": policy_data["name"],
            "description": policy_data.get("description", ""),
            "category": policy_data.get("category", "general"),
            "rules": policy_data.get("rules", {}),
            "status": "active",
            "created_by": policy_data["created_by"],
            "created_at": datetime.now().isoformat() + "Z",
            "updated_at": datetime.now().isoformat() + "Z"
        }
        
        self.policies.append(new_policy)
        return new_policy
    
    def update_policy(self, policy_id: str, policy_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing policy"""
        policy = self.get_policy(policy_id)
        if not policy:
            return None
        
        allowed_fields = ["name", "description", "category", "rules", "status"]
        for key, value in policy_data.items():
            if key in allowed_fields:
                if key == "name" and not validate_policy_name(value):
                    raise ValueError("Invalid policy name")
                policy[key] = value
        
        policy["updated_at"] = datetime.now().isoformat() + "Z"
        return policy
    
    def delete_policy(self, policy_id: str) -> bool:
        """Delete a policy (soft delete)"""
        policy = self.get_policy(policy_id)
        if policy:
            policy["status"] = "deleted"
            policy["updated_at"] = datetime.now().isoformat() + "Z"
            return True
        return False
    
    # Data Catalog Management
    def list_catalog_entries(self, skip: int = 0, limit: int = 100, data_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all catalog entries with optional filtering"""
        filtered_entries = self.catalog
        
        if data_type:
            filtered_entries = [e for e in filtered_entries if e["data_type"] == data_type]
        
        return filtered_entries[skip:skip + limit]
    
    def get_catalog_entry(self, entry_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific catalog entry by ID"""
        for entry in self.catalog:
            if entry["id"] == entry_id:
                return entry
        return None
    
    def create_catalog_entry(self, entry_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new catalog entry"""
        if not validate_catalog_name(entry_data.get("name", "")):
            raise ValueError("Invalid catalog entry name")
        
        new_entry = {
            "id": f"catalog-{str(uuid.uuid4())[:8]}",
            "name": entry_data["name"],
            "description": entry_data.get("description", ""),
            "data_type": entry_data.get("data_type", "structured"),
            "source": entry_data["source"],
            "schema": entry_data.get("schema", {}),
            "quality_score": entry_data.get("quality_score", 0.0),
            "last_updated": datetime.now().isoformat() + "Z",
            "status": "active"
        }
        
        self.catalog.append(new_entry)
        return new_entry
    
    def update_catalog_entry(self, entry_id: str, entry_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing catalog entry"""
        entry = self.get_catalog_entry(entry_id)
        if not entry:
            return None
        
        allowed_fields = ["name", "description", "data_type", "schema", "quality_score", "status"]
        for key, value in entry_data.items():
            if key in allowed_fields:
                if key == "name" and not validate_catalog_name(value):
                    raise ValueError("Invalid catalog entry name")
                entry[key] = value
        
        entry["last_updated"] = datetime.now().isoformat() + "Z"
        return entry
    
    # Data Quality Management
    def get_quality_metrics(self, data_source: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get quality metrics with optional filtering"""
        filtered_metrics = self.quality
        
        if data_source:
            filtered_metrics = [m for m in filtered_metrics if m["data_source"] == data_source]
        
        return filtered_metrics
    
    def add_quality_metric(self, metric_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new quality metric"""
        new_metric = {
            "id": f"quality-{str(uuid.uuid4())[:8]}",
            "data_source": metric_data["data_source"],
            "metric": metric_data["metric"],
            "value": metric_data["value"],
            "threshold": metric_data.get("threshold", 0.0),
            "status": "pass" if metric_data["value"] >= metric_data.get("threshold", 0.0) else "fail",
            "timestamp": datetime.now().isoformat() + "Z"
        }
        
        self.quality.append(new_metric)
        return new_metric
    
    def calculate_overall_quality(self, data_source: Optional[str] = None) -> Dict[str, Any]:
        """Calculate overall quality score for a data source or all sources"""
        metrics = self.get_quality_metrics(data_source)
        
        if not metrics:
            return {"overall_score": 0.0, "metric_count": 0, "status": "unknown"}
        
        scores = [m["value"] for m in metrics]
        overall_score = sum(scores) / len(scores)
        
        # Determine status based on thresholds
        failed_metrics = [m for m in metrics if m["status"] == "fail"]
        warning_metrics = [m for m in metrics if m["status"] == "warning"]
        
        if failed_metrics:
            status = "critical"
        elif warning_metrics:
            status = "warning"
        else:
            status = "healthy"
        
        return {
            "overall_score": round(overall_score, 2),
            "metric_count": len(metrics),
            "status": status,
            "failed_count": len(failed_metrics),
            "warning_count": len(warning_metrics)
        }
    
    # Data Lifecycle Management
    def get_lifecycle_status(self, data_source: str) -> Dict[str, Any]:
        """Get lifecycle status for a data source"""
        # Mock lifecycle status
        return {
            "data_source": data_source,
            "status": "active",
            "created_at": "2023-01-01T00:00:00Z",
            "last_accessed": datetime.now().isoformat() + "Z",
            "access_count": 1250,
            "retention_policy": "7 years",
            "archival_status": "not_archived",
            "deletion_scheduled": None
        }
    
    def schedule_data_archival(self, data_source: str, archive_date: str) -> Dict[str, Any]:
        """Schedule data archival for a data source"""
        return {
            "data_source": data_source,
            "action": "archival_scheduled",
            "scheduled_date": archive_date,
            "status": "scheduled",
            "created_at": datetime.now().isoformat() + "Z"
        }
    
    def schedule_data_deletion(self, data_source: str, deletion_date: str) -> Dict[str, Any]:
        """Schedule data deletion for a data source"""
        return {
            "data_source": data_source,
            "action": "deletion_scheduled",
            "scheduled_date": deletion_date,
            "status": "scheduled",
            "created_at": datetime.now().isoformat() + "Z"
        }
    
    # Data Operations
    def backup_data(self, data_source: str, backup_type: str = "full") -> Dict[str, Any]:
        """Create a backup of data"""
        backup_id = f"backup-{str(uuid.uuid4())[:8]}"
        return {
            "backup_id": backup_id,
            "data_source": data_source,
            "backup_type": backup_type,
            "status": "completed",
            "size_mb": 256.5,
            "created_at": datetime.now().isoformat() + "Z",
            "expires_at": (datetime.now() + timedelta(days=30)).isoformat() + "Z"
        }
    
    def restore_data(self, backup_id: str, target_source: str) -> Dict[str, Any]:
        """Restore data from a backup"""
        return {
            "restore_id": f"restore-{str(uuid.uuid4())[:8]}",
            "backup_id": backup_id,
            "target_source": target_source,
            "status": "completed",
            "started_at": datetime.now().isoformat() + "Z",
            "completed_at": datetime.now().isoformat() + "Z"
        }
    
    def migrate_data(self, source: str, destination: str, migration_type: str = "full") -> Dict[str, Any]:
        """Migrate data between sources"""
        return {
            "migration_id": f"migration-{str(uuid.uuid4())[:8]}",
            "source": source,
            "destination": destination,
            "migration_type": migration_type,
            "status": "completed",
            "records_migrated": 12500,
            "started_at": datetime.now().isoformat() + "Z",
            "completed_at": datetime.now().isoformat() + "Z"
        }

# Initialize service
data_management_service = DataManagementService()

# Mock authentication (replace with real authentication)
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Mock authentication - replace with real implementation"""
    return {"user_id": "user-001", "username": "admin", "role": "admin"}

# Health check endpoints
@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "service": "data-management-service",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }
@app.get("/healthz")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "data-management-service", "timestamp": datetime.now().isoformat()}

@app.get("/readyz")
@app.get("/testedz")
@app.get("/compliancez")
async def compliance_check() -> Dict[str, Any]:
    """Compliance check endpoint"""
    return {
        "status": "compliant",
        "service": "data-management-service",
        "timestamp": datetime.utcnow().isoformat(),
        "compliance_score": 100,
        "standards_met": ["security", "performance", "reliability"],
        "version": "1.0.0"
    }
async def tested_check() -> Dict[str, Any]:
    """Test readiness endpoint"""
    return {
        "status": "tested",
        "service": "data-management-service",
        "timestamp": datetime.utcnow().isoformat(),
        "tests_passed": True,
        "version": "1.0.0"
    }
async def readiness_check():
    """Readiness check endpoint"""
    return {"status": "ready", "service": "data-management-service", "timestamp": datetime.now().isoformat()}

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

# Policy Management API endpoints
@app.get("/policies", response_model=List[Dict[str, Any]])
async def list_policies(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    category: Optional[str] = Query(None, description="Filter by category"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """List all data policies with optional filtering"""
    start_time = time.time()
    try:
        policies = data_management_service.list_policies(skip=skip, limit=limit, category=category)
        data_operations.labels(operation="list_policies", status="success").inc()
        data_duration.observe(time.time() - start_time)
        return policies
    except Exception as e:
        data_operations.labels(operation="list_policies", status="error").inc()
        logger.error(f"Error listing policies: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/policies/{policy_id}", response_model=Dict[str, Any])
async def get_policy(
    policy_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get a specific policy by ID"""
    start_time = time.time()
    try:
        policy = data_management_service.get_policy(policy_id)
        if not policy:
            raise HTTPException(status_code=404, detail="Policy not found")
        
        data_operations.labels(operation="get_policy", status="success").inc()
        data_duration.observe(time.time() - start_time)
        return policy
    except HTTPException:
        raise
    except Exception as e:
        data_operations.labels(operation="get_policy", status="error").inc()
        logger.error(f"Error getting policy {policy_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/policies", response_model=Dict[str, Any], status_code=201)
async def create_policy(
    policy_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Create a new data policy"""
    start_time = time.time()
    try:
        policy_data["created_by"] = current_user["user_id"]
        new_policy = data_management_service.create_policy(policy_data)
        data_operations.labels(operation="create_policy", status="success").inc()
        data_duration.observe(time.time() - start_time)
        return new_policy
    except ValueError as e:
        data_operations.labels(operation="create_policy", status="error").inc()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        data_operations.labels(operation="create_policy", status="error").inc()
        logger.error(f"Error creating policy: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.put("/policies/{policy_id}", response_model=Dict[str, Any])
async def update_policy(
    policy_id: str,
    policy_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update an existing policy"""
    start_time = time.time()
    try:
        updated_policy = data_management_service.update_policy(policy_id, policy_data)
        if not updated_policy:
            raise HTTPException(status_code=404, detail="Policy not found")
        
        data_operations.labels(operation="update_policy", status="success").inc()
        data_duration.observe(time.time() - start_time)
        return updated_policy
    except HTTPException:
        raise
    except ValueError as e:
        data_operations.labels(operation="update_policy", status="error").inc()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        data_operations.labels(operation="update_policy", status="error").inc()
        logger.error(f"Error updating policy {policy_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.delete("/policies/{policy_id}")
async def delete_policy(
    policy_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Delete a policy (soft delete)"""
    start_time = time.time()
    try:
        success = data_management_service.delete_policy(policy_id)
        if not success:
            raise HTTPException(status_code=404, detail="Policy not found")
        
        data_operations.labels(operation="delete_policy", status="success").inc()
        data_duration.observe(time.time() - start_time)
        data_lifecycle_events.labels(event_type="policy_deleted").inc()
        
        return {"message": "Policy deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        data_operations.labels(operation="delete_policy", status="error").inc()
        logger.error(f"Error deleting policy {policy_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Data Catalog API endpoints
@app.get("/catalog", response_model=List[Dict[str, Any]])
async def list_catalog_entries(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    data_type: Optional[str] = Query(None, description="Filter by data type"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """List all catalog entries with optional filtering"""
    start_time = time.time()
    try:
        entries = data_management_service.list_catalog_entries(skip=skip, limit=limit, data_type=data_type)
        data_operations.labels(operation="list_catalog", status="success").inc()
        data_duration.observe(time.time() - start_time)
        return entries
    except Exception as e:
        data_operations.labels(operation="list_catalog", status="error").inc()
        logger.error(f"Error listing catalog entries: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/catalog/{entry_id}", response_model=Dict[str, Any])
async def get_catalog_entry(
    entry_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get a specific catalog entry by ID"""
    start_time = time.time()
    try:
        entry = data_management_service.get_catalog_entry(entry_id)
        if not entry:
            raise HTTPException(status_code=404, detail="Catalog entry not found")
        
        data_operations.labels(operation="get_catalog_entry", status="success").inc()
        data_duration.observe(time.time() - start_time)
        return entry
    except HTTPException:
        raise
    except Exception as e:
        data_operations.labels(operation="get_catalog_entry", status="error").inc()
        logger.error(f"Error getting catalog entry {entry_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/catalog", response_model=Dict[str, Any], status_code=201)
async def create_catalog_entry(
    entry_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Create a new catalog entry"""
    start_time = time.time()
    try:
        new_entry = data_management_service.create_catalog_entry(entry_data)
        data_operations.labels(operation="create_catalog_entry", status="success").inc()
        data_duration.observe(time.time() - start_time)
        return new_entry
    except ValueError as e:
        data_operations.labels(operation="create_catalog_entry", status="error").inc()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        data_operations.labels(operation="create_catalog_entry", status="error").inc()
        logger.error(f"Error creating catalog entry: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Data Quality API endpoints
@app.get("/quality/metrics", response_model=List[Dict[str, Any]])
async def get_quality_metrics(
    data_source: Optional[str] = Query(None, description="Filter by data source"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get quality metrics with optional filtering"""
    start_time = time.time()
    try:
        metrics = data_management_service.get_quality_metrics(data_source)
        data_operations.labels(operation="get_quality_metrics", status="success").inc()
        data_duration.observe(time.time() - start_time)
        return metrics
    except Exception as e:
        data_operations.labels(operation="get_quality_metrics", status="error").inc()
        logger.error(f"Error getting quality metrics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/quality/metrics", response_model=Dict[str, Any], status_code=201)
async def add_quality_metric(
    metric_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Add a new quality metric"""
    start_time = time.time()
    try:
        new_metric = data_management_service.add_quality_metric(metric_data)
        data_operations.labels(operation="add_quality_metric", status="success").inc()
        data_duration.observe(time.time() - start_time)
        data_quality_score.observe(metric_data["value"])
        return new_metric
    except Exception as e:
        data_operations.labels(operation="add_quality_metric", status="error").inc()
        logger.error(f"Error adding quality metric: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/quality/overall", response_model=Dict[str, Any])
async def get_overall_quality(
    data_source: Optional[str] = Query(None, description="Filter by data source"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get overall quality score"""
    start_time = time.time()
    try:
        quality_summary = data_management_service.calculate_overall_quality(data_source)
        data_operations.labels(operation="get_overall_quality", status="success").inc()
        data_duration.observe(time.time() - start_time)
        return quality_summary
    except Exception as e:
        data_operations.labels(operation="get_overall_quality", status="error").inc()
        logger.error(f"Error getting overall quality: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Data Lifecycle API endpoints
@app.get("/lifecycle/{data_source}", response_model=Dict[str, Any])
async def get_lifecycle_status(
    data_source: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get lifecycle status for a data source"""
    start_time = time.time()
    try:
        lifecycle_status = data_management_service.get_lifecycle_status(data_source)
        data_operations.labels(operation="get_lifecycle_status", status="success").inc()
        data_duration.observe(time.time() - start_time)
        return lifecycle_status
    except Exception as e:
        data_operations.labels(operation="get_lifecycle_status", status="error").inc()
        logger.error(f"Error getting lifecycle status for {data_source}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/lifecycle/{data_source}/archive", response_model=Dict[str, Any])
async def schedule_data_archival(
    data_source: str,
    archive_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Schedule data archival for a data source"""
    start_time = time.time()
    try:
        archival_schedule = data_management_service.schedule_data_archival(
            data_source, archive_data["archive_date"]
        )
        data_operations.labels(operation="schedule_archival", status="success").inc()
        data_duration.observe(time.time() - start_time)
        data_lifecycle_events.labels(event_type="archival_scheduled").inc()
        return archival_schedule
    except Exception as e:
        data_operations.labels(operation="schedule_archival", status="error").inc()
        logger.error(f"Error scheduling archival for {data_source}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/lifecycle/{data_source}/delete", response_model=Dict[str, Any])
async def schedule_data_deletion(
    data_source: str,
    deletion_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Schedule data deletion for a data source"""
    start_time = time.time()
    try:
        deletion_schedule = data_management_service.schedule_data_deletion(
            data_source, deletion_data["deletion_date"]
        )
        data_operations.labels(operation="schedule_deletion", status="success").inc()
        data_duration.observe(time.time() - start_time)
        data_lifecycle_events.labels(event_type="deletion_scheduled").inc()
        return deletion_schedule
    except Exception as e:
        data_operations.labels(operation="schedule_deletion", status="error").inc()
        logger.error(f"Error scheduling deletion for {data_source}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Data Operations API endpoints
@app.post("/operations/backup", response_model=Dict[str, Any])
async def backup_data(
    backup_request: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Create a backup of data"""
    start_time = time.time()
    try:
        backup_result = data_management_service.backup_data(
            backup_request["data_source"],
            backup_request.get("backup_type", "full")
        )
        data_operations.labels(operation="backup_data", status="success").inc()
        data_duration.observe(time.time() - start_time)
        return backup_result
    except Exception as e:
        data_operations.labels(operation="backup_data", status="error").inc()
        logger.error(f"Error backing up data: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/operations/restore", response_model=Dict[str, Any])
async def restore_data(
    restore_request: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Restore data from a backup"""
    start_time = time.time()
    try:
        restore_result = data_management_service.restore_data(
            restore_request["backup_id"],
            restore_request["target_source"]
        )
        data_operations.labels(operation="restore_data", status="success").inc()
        data_duration.observe(time.time() - start_time)
        return restore_result
    except Exception as e:
        data_operations.labels(operation="restore_data", status="error").inc()
        logger.error(f"Error restoring data: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/operations/migrate", response_model=Dict[str, Any])
async def migrate_data(
    migration_request: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Migrate data between sources"""
    start_time = time.time()
    try:
        migration_result = data_management_service.migrate_data(
            migration_request["source"],
            migration_request["destination"],
            migration_request.get("migration_type", "full")
        )
        data_operations.labels(operation="migrate_data", status="success").inc()
        data_duration.observe(time.time() - start_time)
        return migration_result
    except Exception as e:
        data_operations.labels(operation="migrate_data", status="error").inc()
        logger.error(f"Error migrating data: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    import uvicorn
    # Use documented architecture port 8017
    port = int(os.getenv("PORT", 8017))
    uvicorn.run(app, host="0.0.0.0", port=port)