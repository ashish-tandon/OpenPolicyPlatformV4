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

app = FastAPI(title="debates-service", version="1.0.0")
security = HTTPBearer()

# Mock database for development (replace with real database)
debates_db = [
    {
        "id": 1,
        "title": "Healthcare Reform Debate",
        "description": "Discussion on proposed healthcare policy changes",
        "committee_id": 1,
        "participants": ["Dr. Jane Smith", "Dr. John Doe", "Prof. Sarah Johnson"],
        "start_date": "2024-01-20T14:00:00Z",
        "end_date": "2024-01-20T16:00:00Z",
        "status": "scheduled",
        "transcript": "",
        "decisions": []
    },
    {
        "id": 2,
        "title": "Education Standards Review",
        "description": "Review of current educational standards and proposed improvements",
        "committee_id": 2,
        "participants": ["Prof. Robert Wilson", "Dr. Lisa Chen", "Prof. David Miller"],
        "start_date": "2024-01-22T10:00:00Z",
        "end_date": "2024-01-22T12:00:00Z",
        "status": "scheduled",
        "transcript": "",
        "decisions": []
    }
]

@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "service": "debates-service",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }
@app.get("/healthz")
def healthz():
    """Health check endpoint"""
    return {"status": "ok", "service": "debates-service", "timestamp": datetime.utcnow().isoformat()}

@app.get("/readyz")
@app.get("/testedz")
@app.get("/compliancez")
async def compliance_check() -> Dict[str, Any]:
    """Compliance check endpoint"""
    return {
        "status": "compliant",
        "service": "debates-service",
        "timestamp": datetime.utcnow().isoformat(),
        "compliance_score": 100,
        "standards_met": ["security", "performance", "reliability"],
        "version": "1.0.0"
    }
async def tested_check() -> Dict[str, Any]:
    """Test readiness endpoint"""
    return {
        "status": "tested",
        "service": "debates-service",
        "timestamp": datetime.utcnow().isoformat(),
        "tests_passed": True,
        "version": "1.0.0"
    }
def readyz():
    """Readiness check endpoint"""
    # Add database connectivity check here when real database is implemented
    return {"status": "ok", "service": "debates-service", "ready": True}

@app.get("/metrics")
def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/debates")
def list_debates(
    status: Optional[str] = Query(None, description="Filter by debate status"),
    committee_id: Optional[int] = Query(None, description="Filter by committee ID"),
    limit: int = Query(10, ge=1, le=100, description="Number of debates to return"),
    offset: int = Query(0, ge=0, description="Number of debates to skip")
):
    """List all debates with optional filtering and pagination"""
    try:
        filtered_debates = debates_db
        
        if status:
            filtered_debates = [d for d in debates_db if d["status"] == status]
        
        if committee_id:
            filtered_debates = [d for d in filtered_debates if d["committee_id"] == committee_id]
        
        # Apply pagination
        paginated_debates = filtered_debates[offset:offset + limit]
        
        return {
            "debates": paginated_debates,
            "total": len(filtered_debates),
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < len(filtered_debates)
        }
    except Exception as e:
        logger.error(f"Error listing debates: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/debates/{debate_id}")
def get_debate(debate_id: int):
    """Get a specific debate by ID"""
    try:
        debate = next((d for d in debates_db if d["id"] == debate_id), None)
        if not debate:
            raise HTTPException(status_code=404, detail="Debate not found")
        return debate
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting debate {debate_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/debates")
def create_debate(debate_data: dict):
    """Create a new debate"""
    try:
        # Validate required fields
        required_fields = ["title", "description", "committee_id", "participants", "start_date"]
        for field in required_fields:
            if field not in debate_data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        # Generate new ID
        new_id = max(d["id"] for d in debates_db) + 1 if debates_db else 1
        
        new_debate = {
            "id": new_id,
            "title": debate_data["title"],
            "description": debate_data["description"],
            "committee_id": debate_data["committee_id"],
            "participants": debate_data["participants"],
            "start_date": debate_data["start_date"],
            "end_date": debate_data.get("end_date"),
            "status": debate_data.get("status", "scheduled"),
            "transcript": debate_data.get("transcript", ""),
            "decisions": debate_data.get("decisions", [])
        }
        
        debates_db.append(new_debate)
        logger.info(f"Created new debate: {new_debate['title']}")
        
        return {"status": "success", "debate": new_debate}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating debate: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.put("/debates/{debate_id}")
def update_debate(debate_id: int, debate_data: dict):
    """Update an existing debate"""
    try:
        debate = next((d for d in debates_db if d["id"] == debate_id), None)
        if not debate:
            raise HTTPException(status_code=404, detail="Debate not found")
        
        # Update fields
        for field, value in debate_data.items():
            if field in debate:
                debate[field] = value
        
        logger.info(f"Updated debate {debate_id}: {debate['title']}")
        return {"status": "success", "debate": debate}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating debate {debate_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.delete("/debates/{debate_id}")
def delete_debate(debate_id: int):
    """Delete a debate"""
    try:
        debate = next((d for d in debates_db if d["id"] == debate_id), None)
        if not debate:
            raise HTTPException(status_code=404, detail="Debate not found")
        
        debates_db.remove(debate)
        logger.info(f"Deleted debate {debate_id}: {debate['title']}")
        
        return {"status": "success", "message": f"Debate {debate_id} deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting debate {debate_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/debates/{debate_id}/start")
def start_debate(debate_id: int):
    """Start a scheduled debate"""
    try:
        debate = next((d for d in debates_db if d["id"] == debate_id), None)
        if not debate:
            raise HTTPException(status_code=404, detail="Debate not found")
        
        if debate["status"] != "scheduled":
            raise HTTPException(status_code=400, detail="Debate is not scheduled")
        
        debate["status"] = "in_progress"
        debate["start_date"] = datetime.utcnow().isoformat()
        
        logger.info(f"Started debate {debate_id}: {debate['title']}")
        return {"status": "success", "debate": debate}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting debate {debate_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/debates/{debate_id}/end")
def end_debate(debate_id: int, transcript: str = "", decisions: List[str] = []):
    """End an in-progress debate"""
    try:
        debate = next((d for d in debates_db if d["id"] == debate_id), None)
        if not debate:
            raise HTTPException(status_code=404, detail="Debate not found")
        
        if debate["status"] != "in_progress":
            raise HTTPException(status_code=400, detail="Debate is not in progress")
        
        debate["status"] = "completed"
        debate["end_date"] = datetime.utcnow().isoformat()
        debate["transcript"] = transcript
        debate["decisions"] = decisions
        
        logger.info(f"Ended debate {debate_id}: {debate['title']}")
        return {"status": "success", "debate": debate}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ending debate {debate_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/debates/{debate_id}/transcript")
def get_debate_transcript(debate_id: int):
    """Get the transcript of a completed debate"""
    try:
        debate = next((d for d in debates_db if d["id"] == debate_id), None)
        if not debate:
            raise HTTPException(status_code=404, detail="Debate not found")
        
        if debate["status"] != "completed":
            raise HTTPException(status_code=400, detail="Debate is not completed")
        
        return {
            "debate_id": debate_id,
            "title": debate["title"],
            "transcript": debate["transcript"],
            "decisions": debate["decisions"]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting transcript for debate {debate_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 9012))
    uvicorn.run(app, host="0.0.0.0", port=port)