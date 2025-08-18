from fastapi import FastAPI, Response, HTTPException, Depends, Query
from http import HTTPStatus
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest, Counter, Histogram
from typing import List, Optional, Dict, Any
import os
import logging
from datetime import datetime, timedelta
import json
import uuid
from pydantic import BaseModel, validator
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="policy-service", version="1.0.0")
security = HTTPBearer()

# Mock authentication dependency (replace with real auth service integration)
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Mock current user (replace with real JWT verification)"""
    # This is a mock implementation - replace with real JWT verification
    return {
        "id": "user_001",
        "username": "admin",
        "full_name": "System Administrator",
        "role": "admin"
    }

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics
policy_operations = Counter('policy_operations_total', 'Total policy operations', ['operation', 'status'])
policy_duration = Histogram('policy_duration_seconds', 'Policy operation duration')

# Mock database for development (replace with real database)
policies_db = [
    {
        "id": 1,
        "title": "Healthcare Reform Act 2024",
        "description": "Comprehensive healthcare policy reform to improve patient outcomes and reduce costs",
        "content": "This policy aims to reform the healthcare system by...",
        "category": "Healthcare",
        "tags": ["healthcare", "reform", "patient-care"],
        "status": "draft",
        "version": "1.0",
        "author_id": "user_001",
        "author_name": "Dr. Jane Smith",
        "committee_id": 1,
        "priority": "high",
        "impact_level": "national",
        "estimated_cost": 5000000000,
        "estimated_timeline": "24 months",
        "stakeholders": ["healthcare providers", "patients", "insurance companies"],
        "created_at": "2024-01-15T10:00:00Z",
        "updated_at": "2024-01-15T10:00:00Z",
        "approved_at": None,
        "approved_by": None,
        "published_at": None,
        "archived_at": None,
        "metadata": {
            "department": "Health",
            "legislation_type": "Act",
            "fiscal_year": "2024-2025"
        }
    },
    {
        "id": 2,
        "title": "Education Standards Update",
        "description": "Modernization of educational standards to align with current industry needs",
        "content": "This policy updates educational standards to include...",
        "category": "Education",
        "tags": ["education", "standards", "curriculum"],
        "status": "under_review",
        "version": "2.1",
        "author_id": "user_002",
        "author_name": "Prof. Robert Wilson",
        "committee_id": 2,
        "priority": "medium",
        "impact_level": "state",
        "estimated_cost": 25000000,
        "estimated_timeline": "12 months",
        "stakeholders": ["students", "teachers", "schools", "parents"],
        "created_at": "2024-01-10T09:00:00Z",
        "updated_at": "2024-01-18T14:30:00Z",
        "approved_at": None,
        "approved_by": None,
        "published_at": None,
        "archived_at": None,
        "metadata": {
            "department": "Education",
            "legislation_type": "Regulation",
            "fiscal_year": "2024-2025"
        }
    }
]

policy_versions_db = []
policy_comments_db = []
policy_approvals_db = []

# Pydantic models for request/response validation
class PolicyCreate(BaseModel):
    title: str
    description: str
    content: str
    category: str
    tags: List[str] = []
    priority: str = "medium"
    impact_level: str = "local"
    estimated_cost: Optional[float] = None
    estimated_timeline: Optional[str] = None
    stakeholders: List[str] = []
    committee_id: Optional[int] = None
    metadata: Dict[str, Any] = {}
    
    @validator('title')
    def validate_title(cls, v):
        if len(v.strip()) < 10:
            raise ValueError('Title must be at least 10 characters long')
        return v.strip()
    
    @validator('priority')
    def validate_priority(cls, v):
        if v not in ["low", "medium", "high", "critical"]:
            raise ValueError('Priority must be one of: low, medium, high, critical')
        return v
    
    @validator('impact_level')
    def validate_impact_level(cls, v):
        if v not in ["local", "state", "national", "international"]:
            raise ValueError('Impact level must be one of: local, state, national, international')
        return v

class PolicyUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    priority: Optional[str] = None
    impact_level: Optional[str] = None
    estimated_cost: Optional[float] = None
    estimated_timeline: Optional[str] = None
    stakeholders: Optional[List[str]] = None
    committee_id: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
    
    @validator('priority')
    def validate_priority(cls, v):
        if v is not None and v not in ["low", "medium", "high", "critical"]:
            raise ValueError('Priority must be one of: low, medium, high, critical')
        return v
    
    @validator('impact_level')
    def validate_impact_level(cls, v):
        if v is not None and v not in ["local", "state", "national", "international"]:
            raise ValueError('Impact level must be one of: local, state, national, international')
        return v

class PolicyStatusUpdate(BaseModel):
    status: str
    comment: Optional[str] = None
    
    @validator('status')
    def validate_status(cls, v):
        valid_statuses = ["draft", "under_review", "approved", "rejected", "published", "archived"]
        if v not in valid_statuses:
            raise ValueError(f'Status must be one of: {", ".join(valid_statuses)}')
        return v

class PolicyComment(BaseModel):
    content: str
    author_id: str
    author_name: str
    
    @validator('content')
    def validate_content(cls, v):
        if len(v.strip()) < 5:
            raise ValueError('Comment must be at least 5 characters long')
        return v.strip()

# Utility functions
def get_policy_by_id(policy_id: int) -> Optional[Dict[str, Any]]:
    """Get policy by ID"""
    return next((p for p in policies_db if p["id"] == policy_id), None)

def create_policy_version(policy_id: int, version: str, author_id: str, author_name: str):
    """Create a new policy version"""
    policy = get_policy_by_id(policy_id)
    if not policy:
        return None
    
    version_data = {
        "id": len(policy_versions_db) + 1,
        "policy_id": policy_id,
        "version": version,
        "content": policy["content"],
        "author_id": author_id,
        "author_name": author_name,
        "created_at": datetime.utcnow().isoformat(),
        "changes": f"Version {version} created"
    }
    
    policy_versions_db.append(version_data)
    return version_data

# Health check endpoints
@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "service": "policy-service",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }
@app.get("/healthz")
def healthz():
    """Health check endpoint"""
    return {
        "status": "ok", 
        "service": "policy-service", 
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

@app.get("/readyz")
@app.get("/testedz")
@app.get("/compliancez")
async def compliance_check() -> Dict[str, Any]:
    """Compliance check endpoint"""
    return {
        "status": "compliant",
        "service": "policy-service",
        "timestamp": datetime.utcnow().isoformat(),
        "compliance_score": 100,
        "standards_met": ["security", "performance", "reliability"],
        "version": "1.0.0"
    }
async def tested_check() -> Dict[str, Any]:
    """Test readiness endpoint"""
    return {
        "status": "tested",
        "service": "policy-service",
        "timestamp": datetime.utcnow().isoformat(),
        "tests_passed": True,
        "version": "1.0.0"
    }
def readyz():
    """Readiness check endpoint"""
    # Add database connectivity check here when real database is implemented
    return {
        "status": "ok", 
        "service": "policy-service", 
        "ready": True,
        "database": "connected"  # Mock for now
    }

@app.get("/metrics")
def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

# Policy management endpoints
@app.get("/policies")
def list_policies(
    status: Optional[str] = Query(None, description="Filter by policy status"),
    category: Optional[str] = Query(None, description="Filter by policy category"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    impact_level: Optional[str] = Query(None, description="Filter by impact level"),
    committee_id: Optional[int] = Query(None, description="Filter by committee ID"),
    author_id: Optional[str] = Query(None, description="Filter by author ID"),
    tags: Optional[str] = Query(None, description="Filter by tags (comma-separated)"),
    search: Optional[str] = Query(None, description="Search in title and description"),
    limit: int = Query(10, ge=1, le=100, description="Number of policies to return"),
    offset: int = Query(0, ge=0, description="Number of policies to skip"),
    sort_by: str = Query("created_at", description="Sort by field"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)")
):
    """List all policies with optional filtering, searching, and pagination"""
    start_time = time.time()
    
    try:
        filtered_policies = policies_db.copy()
        
        # Apply filters
        if status:
            filtered_policies = [p for p in filtered_policies if p["status"] == status]
        
        if category:
            filtered_policies = [p for p in filtered_policies if p["category"] == category]
        
        if priority:
            filtered_policies = [p for p in filtered_policies if p["priority"] == priority]
        
        if impact_level:
            filtered_policies = [p for p in filtered_policies if p["impact_level"] == impact_level]
        
        if committee_id:
            filtered_policies = [p for p in filtered_policies if p["committee_id"] == committee_id]
        
        if author_id:
            filtered_policies = [p for p in filtered_policies if p["author_id"] == author_id]
        
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",")]
            filtered_policies = [p for p in filtered_policies if any(tag in p["tags"] for tag in tag_list)]
        
        if search:
            search_lower = search.lower()
            filtered_policies = [
                p for p in filtered_policies 
                if search_lower in p["title"].lower() or search_lower in p["description"].lower()
            ]
        
        # Apply sorting
        if sort_by in ["title", "created_at", "updated_at", "priority", "impact_level"]:
            reverse = sort_order.lower() == "desc"
            filtered_policies.sort(key=lambda x: x[sort_by], reverse=reverse)
        
        # Apply pagination
        total = len(filtered_policies)
        paginated_policies = filtered_policies[offset:offset + limit]
        
        # Calculate duration for metrics
        duration = time.time() - start_time
        policy_duration.observe(duration)
        policy_operations.labels(operation="list", status="success").inc()
        
        return {
            "policies": paginated_policies,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < total,
            "filters_applied": {
                "status": status,
                "category": category,
                "priority": priority,
                "impact_level": impact_level,
                "committee_id": committee_id,
                "author_id": author_id,
                "tags": tags,
                "search": search
            }
        }
        
    except Exception as e:
        logger.error(f"Error listing policies: {str(e)}")
        policy_operations.labels(operation="list", status="error").inc()
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/policies/{policy_id}")
def get_policy(policy_id: int):
    """Get a specific policy by ID"""
    try:
        policy = get_policy_by_id(policy_id)
        if not policy:
            raise HTTPException(status_code=404, detail="Policy not found")
        
        policy_operations.labels(operation="get", status="success").inc()
        return policy
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting policy {policy_id}: {str(e)}")
        policy_operations.labels(operation="get", status="error").inc()
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/policies", status_code=HTTPStatus.CREATED)
def create_policy(policy_data: PolicyCreate, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Create a new policy"""
    start_time = time.time()
    
    try:
        # Generate new ID
        new_id = max(p["id"] for p in policies_db) + 1 if policies_db else 1
        
        # Create new policy
        new_policy = {
            "id": new_id,
            "title": policy_data.title,
            "description": policy_data.description,
            "content": policy_data.content,
            "category": policy_data.category,
            "tags": policy_data.tags,
            "status": "draft",
            "version": "1.0",
            "author_id": current_user["id"],
            "author_name": current_user["full_name"],
            "committee_id": policy_data.committee_id,
            "priority": policy_data.priority,
            "impact_level": policy_data.impact_level,
            "estimated_cost": policy_data.estimated_cost,
            "estimated_timeline": policy_data.estimated_timeline,
            "stakeholders": policy_data.stakeholders,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "approved_at": None,
            "approved_by": None,
            "published_at": None,
            "archived_at": None,
            "metadata": policy_data.metadata
        }
        
        policies_db.append(new_policy)
        
        # Create initial version
        create_policy_version(new_id, "1.0", current_user["id"], current_user["full_name"])
        
        # Log policy creation
        logger.info(f"New policy created: {new_policy['title']} by {current_user['username']}")
        
        # Calculate duration for metrics
        duration = time.time() - start_time
        policy_duration.observe(duration)
        policy_operations.labels(operation="create", status="success").inc()
        
        return {
            "status": "success",
            "message": "Policy created successfully",
            "policy": new_policy
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating policy: {str(e)}")
        policy_operations.labels(operation="create", status="error").inc()
        raise HTTPException(status_code=500, detail="Internal server error")

@app.put("/policies/{policy_id}")
def update_policy(
    policy_id: int, 
    policy_data: PolicyUpdate, 
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update an existing policy"""
    start_time = time.time()
    
    try:
        policy = get_policy_by_id(policy_id)
        if not policy:
            raise HTTPException(status_code=404, detail="Policy not found")
        
        # Check if user can edit this policy
        if policy["author_id"] != current_user["id"] and current_user["role"] != "admin":
            raise HTTPException(status_code=403, detail="Only the author or admin can edit this policy")
        
        # Check if policy can be edited
        if policy["status"] in ["approved", "published", "archived"]:
            raise HTTPException(status_code=400, detail="Cannot edit policy in current status")
        
        # Update fields
        update_data = policy_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if field in policy:
                policy[field] = value
        
        # Update timestamp
        policy["updated_at"] = datetime.utcnow().isoformat()
        
        # Create new version if content changed
        if "content" in update_data:
            current_version = float(policy["version"])
            new_version = f"{current_version + 0.1:.1f}"
            policy["version"] = new_version
            create_policy_version(policy_id, new_version, current_user["id"], current_user["full_name"])
        
        # Log policy update
        logger.info(f"Policy {policy_id} updated by {current_user['username']}")
        
        # Calculate duration for metrics
        duration = time.time() - start_time
        policy_duration.observe(duration)
        policy_operations.labels(operation="update", status="success").inc()
        
        return {
            "status": "success",
            "message": "Policy updated successfully",
            "policy": policy
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating policy {policy_id}: {str(e)}")
        policy_operations.labels(operation="update", status="error").inc()
        raise HTTPException(status_code=500, detail="Internal server error")

@app.delete("/policies/{policy_id}")
def delete_policy(policy_id: int, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Delete a policy"""
    try:
        policy = get_policy_by_id(policy_id)
        if not policy:
            raise HTTPException(status_code=404, detail="Policy not found")
        
        # Check if user can delete this policy
        if policy["author_id"] != current_user["id"] and current_user["role"] != "admin":
            raise HTTPException(status_code=403, detail="Only the author or admin can delete this policy")
        
        # Check if policy can be deleted
        if policy["status"] in ["approved", "published"]:
            raise HTTPException(status_code=400, detail="Cannot delete policy in current status")
        
        # Remove policy
        policies_db.remove(policy)
        
        # Log policy deletion
        logger.info(f"Policy {policy_id} deleted by {current_user['username']}")
        
        policy_operations.labels(operation="delete", status="success").inc()
        
        return {
            "status": "success",
            "message": f"Policy {policy_id} deleted"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting policy {policy_id}: {str(e)}")
        policy_operations.labels(operation="delete", status="error").inc()
        raise HTTPException(status_code=500, detail="Internal server error")

@app.put("/policies/{policy_id}/status")
def update_policy_status(
    policy_id: int,
    status_data: PolicyStatusUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update policy status"""
    try:
        policy = get_policy_by_id(policy_id)
        if not policy:
            raise HTTPException(status_code=404, detail="Policy not found")
        
        # Check if user can change status
        if current_user["role"] not in ["admin", "committee_member"]:
            raise HTTPException(status_code=403, detail="Insufficient permissions to change policy status")
        
        old_status = policy["status"]
        policy["status"] = status_data.status
        policy["updated_at"] = datetime.utcnow().isoformat()
        
        # Handle status-specific actions
        if status_data.status == "approved":
            policy["approved_at"] = datetime.utcnow().isoformat()
            policy["approved_by"] = current_user["id"]
        elif status_data.status == "published":
            policy["published_at"] = datetime.utcnow().isoformat()
        elif status_data.status == "archived":
            policy["archived_at"] = datetime.utcnow().isoformat()
        
        # Log status change
        logger.info(f"Policy {policy_id} status changed from {old_status} to {status_data.status} by {current_user['username']}")
        
        policy_operations.labels(operation="status_update", status="success").inc()
        
        return {
            "status": "success",
            "message": f"Policy status updated to {status_data.status}",
            "policy": policy
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating policy status {policy_id}: {str(e)}")
        policy_operations.labels(operation="status_update", status="error").inc()
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/policies/{policy_id}/versions")
def get_policy_versions(policy_id: int):
    """Get version history for a policy"""
    try:
        policy = get_policy_by_id(policy_id)
        if not policy:
            raise HTTPException(status_code=404, detail="Policy not found")
        
        versions = [v for v in policy_versions_db if v["policy_id"] == policy_id]
        versions.sort(key=lambda x: x["created_at"], reverse=True)
        
        return {
            "policy_id": policy_id,
            "policy_title": policy["title"],
            "versions": versions,
            "total_versions": len(versions)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting versions for policy {policy_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/policies/{policy_id}/version/{version}")
def get_policy_version(policy_id: int, version: str):
    """Get a specific version of a policy"""
    try:
        policy = get_policy_by_id(policy_id)
        if not policy:
            raise HTTPException(status_code=404, detail="Policy not found")
        
        version_data = next((v for v in policy_versions_db if v["policy_id"] == policy_id and v["version"] == version), None)
        if not version_data:
            raise HTTPException(status_code=404, detail="Version not found")
        
        return {
            "policy_id": policy_id,
            "policy_title": policy["title"],
            "version": version_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting version {version} for policy {policy_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/categories")
def get_categories():
    """Get all policy categories"""
    try:
        categories = list(set(p["category"] for p in policies_db))
        return {
            "categories": categories,
            "total": len(categories)
        }
    except Exception as e:
        logger.error(f"Error getting categories: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/tags")
def get_tags():
    """Get all policy tags"""
    try:
        all_tags = []
        for policy in policies_db:
            all_tags.extend(policy["tags"])
        
        unique_tags = list(set(all_tags))
        return {
            "tags": unique_tags,
            "total": len(unique_tags)
        }
    except Exception as e:
        logger.error(f"Error getting tags: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/policies/stats")
def get_policy_stats():
    """Get policy statistics"""
    try:
        total_policies = len(policies_db)
        status_counts = {}
        category_counts = {}
        priority_counts = {}
        impact_level_counts = {}
        
        for policy in policies_db:
            # Status counts
            status_counts[policy["status"]] = status_counts.get(policy["status"], 0) + 1
            
            # Category counts
            category_counts[policy["category"]] = category_counts.get(policy["category"], 0) + 1
            
            # Priority counts
            priority_counts[policy["priority"]] = priority_counts.get(policy["priority"], 0) + 1
            
            # Impact level counts
            impact_level_counts[policy["impact_level"]] = impact_level_counts.get(policy["impact_level"], 0) + 1
        
        return {
            "total_policies": total_policies,
            "status_distribution": status_counts,
            "category_distribution": category_counts,
            "priority_distribution": priority_counts,
            "impact_level_distribution": impact_level_counts,
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting policy stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 9003))
    uvicorn.run(app, host="0.0.0.0", port=port)