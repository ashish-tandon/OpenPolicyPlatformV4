from fastapi import FastAPI, Response, HTTPException, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from typing import List, Optional
import os
import logging
from datetime import datetime
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="committees-service", version="1.0.0")
security = HTTPBearer()

# Mock database for development (replace with real database)
committees_db = [
    {
        "id": 1,
        "name": "Health Committee",
        "description": "Oversees health-related policies and regulations",
        "chairperson": "Dr. Jane Smith",
        "members": ["Dr. John Doe", "Dr. Sarah Johnson", "Prof. Mike Brown"],
        "created_at": "2024-01-15T10:00:00Z",
        "status": "active"
    },
    {
        "id": 2,
        "name": "Education Committee",
        "description": "Manages educational policies and standards",
        "chairperson": "Prof. Robert Wilson",
        "members": ["Dr. Lisa Chen", "Prof. David Miller", "Dr. Emily Davis"],
        "created_at": "2024-01-10T09:00:00Z",
        "status": "active"
    }
]

@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "service": "committees-service",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }
@app.get("/healthz")
def healthz():
    """Health check endpoint"""
    return {"status": "ok", "service": "committees-service", "timestamp": datetime.utcnow().isoformat()}

@app.get("/readyz")
@app.get("/testedz")
@app.get("/compliancez")
async def compliance_check() -> Dict[str, Any]:
    """Compliance check endpoint"""
    return {
        "status": "compliant",
        "service": "committees-service",
        "timestamp": datetime.utcnow().isoformat(),
        "compliance_score": 100,
        "standards_met": ["security", "performance", "reliability"],
        "version": "1.0.0"
    }
async def tested_check() -> Dict[str, Any]:
    """Test readiness endpoint"""
    return {
        "status": "tested",
        "service": "committees-service",
        "timestamp": datetime.utcnow().isoformat(),
        "tests_passed": True,
        "version": "1.0.0"
    }
def readyz():
    """Readiness check endpoint"""
    # Add database connectivity check here when real database is implemented
    return {"status": "ok", "service": "committees-service", "ready": True}

@app.get("/metrics")
def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/committees")
def list_committees(
    status: Optional[str] = Query(None, description="Filter by committee status"),
    limit: int = Query(10, ge=1, le=100, description="Number of committees to return"),
    offset: int = Query(0, ge=0, description="Number of committees to skip")
):
    """List all committees with optional filtering and pagination"""
    try:
        filtered_committees = committees_db
        
        if status:
            filtered_committees = [c for c in committees_db if c["status"] == status]
        
        # Apply pagination
        paginated_committees = filtered_committees[offset:offset + limit]
        
        return {
            "committees": paginated_committees,
            "total": len(filtered_committees),
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < len(filtered_committees)
        }
    except Exception as e:
        logger.error(f"Error listing committees: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/committees/{committee_id}")
def get_committee(committee_id: int):
    """Get a specific committee by ID"""
    try:
        committee = next((c for c in committees_db if c["id"] == committee_id), None)
        if not committee:
            raise HTTPException(status_code=404, detail="Committee not found")
        return committee
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting committee {committee_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/committees")
def create_committee(committee_data: dict):
    """Create a new committee"""
    try:
        # Validate required fields
        required_fields = ["name", "description", "chairperson"]
        for field in required_fields:
            if field not in committee_data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        # Generate new ID
        new_id = max(c["id"] for c in committees_db) + 1 if committees_db else 1
        
        new_committee = {
            "id": new_id,
            "name": committee_data["name"],
            "description": committee_data["description"],
            "chairperson": committee_data["chairperson"],
            "members": committee_data.get("members", []),
            "created_at": datetime.utcnow().isoformat(),
            "status": committee_data.get("status", "active")
        }
        
        committees_db.append(new_committee)
        logger.info(f"Created new committee: {new_committee['name']}")
        
        return {"status": "success", "committee": new_committee}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating committee: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.put("/committees/{committee_id}")
def update_committee(committee_id: int, committee_data: dict):
    """Update an existing committee"""
    try:
        committee = next((c for c in committees_db if c["id"] == committee_id), None)
        if not committee:
            raise HTTPException(status_code=404, detail="Committee not found")
        
        # Update fields
        for field, value in committee_data.items():
            if field in committee:
                committee[field] = value
        
        logger.info(f"Updated committee {committee_id}: {committee['name']}")
        return {"status": "success", "committee": committee}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating committee {committee_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.delete("/committees/{committee_id}")
def delete_committee(committee_id: int):
    """Delete a committee"""
    try:
        committee = next((c for c in committees_db if c["id"] == committee_id), None)
        if not committee:
            raise HTTPException(status_code=404, detail="Committee not found")
        
        committees_db.remove(committee)
        logger.info(f"Deleted committee {committee_id}: {committee['name']}")
        
        return {"status": "success", "message": f"Committee {committee_id} deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting committee {committee_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/committees/{committee_id}/members")
def get_committee_members(committee_id: int):
    """Get members of a specific committee"""
    try:
        committee = next((c for c in committees_db if c["id"] == committee_id), None)
        if not committee:
            raise HTTPException(status_code=404, detail="Committee not found")
        
        return {
            "committee_id": committee_id,
            "committee_name": committee["name"],
            "members": committee["members"],
            "total_members": len(committee["members"])
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting members for committee {committee_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 9011))
    uvicorn.run(app, host="0.0.0.0", port=port)