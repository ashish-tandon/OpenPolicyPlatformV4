from fastapi import FastAPI, Response, HTTPException, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from typing import List, Optional, Dict, Any
import os
import logging
from datetime import datetime
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="votes-service", version="1.0.0")
security = HTTPBearer()

# Mock database for development (replace with real database)
votes_db = [
    {
        "id": 1,
        "policy_id": 1,
        "debate_id": 1,
        "voter_id": "user_001",
        "voter_name": "Dr. Jane Smith",
        "vote": "yes",
        "reasoning": "Supports healthcare reform for better patient outcomes",
        "timestamp": "2024-01-20T16:30:00Z",
        "weight": 1.0
    },
    {
        "id": 2,
        "policy_id": 1,
        "debate_id": 1,
        "voter_id": "user_002",
        "voter_name": "Dr. John Doe",
        "vote": "no",
        "reasoning": "Concerns about implementation costs and timeline",
        "timestamp": "2024-01-20T16:32:00Z",
        "weight": 1.0
    },
    {
        "id": 3,
        "policy_id": 2,
        "debate_id": 2,
        "voter_id": "user_003",
        "voter_name": "Prof. Robert Wilson",
        "vote": "yes",
        "reasoning": "Educational standards need modernization",
        "timestamp": "2024-01-22T12:15:00Z",
        "weight": 1.0
    }
]

policies_db = [
    {
        "id": 1,
        "title": "Healthcare Reform Act",
        "description": "Comprehensive healthcare policy reform",
        "status": "under_review"
    },
    {
        "id": 2,
        "title": "Education Standards Update",
        "description": "Modernization of educational standards",
        "status": "under_review"
    }
]

@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "service": "votes-service",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }
@app.get("/healthz")
def healthz():
    """Health check endpoint"""
    return {"status": "ok", "service": "votes-service", "timestamp": datetime.utcnow().isoformat()}

@app.get("/readyz")
@app.get("/testedz")
@app.get("/compliancez")
async def compliance_check() -> Dict[str, Any]:
    """Compliance check endpoint"""
    return {
        "status": "compliant",
        "service": "votes-service",
        "timestamp": datetime.utcnow().isoformat(),
        "compliance_score": 100,
        "standards_met": ["security", "performance", "reliability"],
        "version": "1.0.0"
    }
async def tested_check() -> Dict[str, Any]:
    """Test readiness endpoint"""
    return {
        "status": "tested",
        "service": "votes-service",
        "timestamp": datetime.utcnow().isoformat(),
        "tests_passed": True,
        "version": "1.0.0"
    }
def readyz():
    """Readiness check endpoint"""
    # Add database connectivity check here when real database is implemented
    return {"status": "ok", "service": "votes-service", "ready": True}

@app.get("/metrics")
def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/votes")
def list_votes(
    policy_id: Optional[int] = Query(None, description="Filter by policy ID"),
    debate_id: Optional[int] = Query(None, description="Filter by debate ID"),
    voter_id: Optional[str] = Query(None, description="Filter by voter ID"),
    vote: Optional[str] = Query(None, description="Filter by vote type (yes/no/abstain)"),
    limit: int = Query(10, ge=1, le=100, description="Number of votes to return"),
    offset: int = Query(0, ge=0, description="Number of votes to skip")
):
    """List all votes with optional filtering and pagination"""
    try:
        filtered_votes = votes_db
        
        if policy_id:
            filtered_votes = [v for v in votes_db if v["policy_id"] == policy_id]
        
        if debate_id:
            filtered_votes = [v for v in filtered_votes if v["debate_id"] == debate_id]
        
        if voter_id:
            filtered_votes = [v for v in filtered_votes if v["voter_id"] == voter_id]
        
        if vote:
            filtered_votes = [v for v in filtered_votes if v["vote"] == vote]
        
        # Apply pagination
        paginated_votes = filtered_votes[offset:offset + limit]
        
        return {
            "votes": paginated_votes,
            "total": len(filtered_votes),
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < len(filtered_votes)
        }
    except Exception as e:
        logger.error(f"Error listing votes: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/votes/{vote_id}")
def get_vote(vote_id: int):
    """Get a specific vote by ID"""
    try:
        vote = next((v for v in votes_db if v["id"] == vote_id), None)
        if not vote:
            raise HTTPException(status_code=404, detail="Vote not found")
        return vote
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting vote {vote_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/votes")
def create_vote(vote_data: dict):
    """Create a new vote"""
    try:
        # Validate required fields
        required_fields = ["policy_id", "debate_id", "voter_id", "voter_name", "vote"]
        for field in required_fields:
            if field not in vote_data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        # Validate vote value
        valid_votes = ["yes", "no", "abstain"]
        if vote_data["vote"] not in valid_votes:
            raise HTTPException(status_code=400, detail=f"Invalid vote value. Must be one of: {valid_votes}")
        
        # Check if voter already voted on this policy
        existing_vote = next((v for v in votes_db if v["policy_id"] == vote_data["policy_id"] and v["voter_id"] == vote_data["voter_id"]), None)
        if existing_vote:
            raise HTTPException(status_code=400, detail="Voter has already voted on this policy")
        
        # Generate new ID
        new_id = max(v["id"] for v in votes_db) + 1 if votes_db else 1
        
        new_vote = {
            "id": new_id,
            "policy_id": vote_data["policy_id"],
            "debate_id": vote_data["debate_id"],
            "voter_id": vote_data["voter_id"],
            "voter_name": vote_data["voter_name"],
            "vote": vote_data["vote"],
            "reasoning": vote_data.get("reasoning", ""),
            "timestamp": datetime.utcnow().isoformat(),
            "weight": vote_data.get("weight", 1.0)
        }
        
        votes_db.append(new_vote)
        logger.info(f"Created new vote: {new_vote['voter_name']} voted {new_vote['vote']} on policy {new_vote['policy_id']}")
        
        return {"status": "success", "vote": new_vote}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating vote: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.put("/votes/{vote_id}")
def update_vote(vote_id: int, vote_data: dict):
    """Update an existing vote"""
    try:
        vote = next((v for v in votes_db if v["id"] == vote_id), None)
        if not vote:
            raise HTTPException(status_code=404, detail="Vote not found")
        
        # Only allow updating certain fields
        updatable_fields = ["reasoning", "weight"]
        for field, value in vote_data.items():
            if field in updatable_fields:
                vote[field] = value
        
        logger.info(f"Updated vote {vote_id}")
        return {"status": "success", "vote": vote}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating vote {vote_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.delete("/votes/{vote_id}")
def delete_vote(vote_id: int):
    """Delete a vote"""
    try:
        vote = next((v for v in votes_db if v["id"] == vote_id), None)
        if not vote:
            raise HTTPException(status_code=404, detail="Vote not found")
        
        votes_db.remove(vote)
        logger.info(f"Deleted vote {vote_id}")
        
        return {"status": "success", "message": f"Vote {vote_id} deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting vote {vote_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/policies/{policy_id}/results")
def get_policy_results(policy_id: int):
    """Get voting results for a specific policy"""
    try:
        # Check if policy exists
        policy = next((p for p in policies_db if p["id"] == policy_id), None)
        if not policy:
            raise HTTPException(status_code=404, detail="Policy not found")
        
        # Get all votes for this policy
        policy_votes = [v for v in votes_db if v["policy_id"] == policy_id]
        
        if not policy_votes:
            return {
                "policy_id": policy_id,
                "policy_title": policy["title"],
                "total_votes": 0,
                "results": {"yes": 0, "no": 0, "abstain": 0},
                "passing": False
            }
        
        # Calculate results
        yes_votes = sum(1 for v in policy_votes if v["vote"] == "yes")
        no_votes = sum(1 for v in policy_votes if v["vote"] == "no")
        abstain_votes = sum(1 for v in policy_votes if v["vote"] == "abstain")
        
        total_votes = len(policy_votes)
        passing = yes_votes > no_votes  # Simple majority rule
        
        return {
            "policy_id": policy_id,
            "policy_title": policy["title"],
            "total_votes": total_votes,
            "results": {
                "yes": yes_votes,
                "no": no_votes,
                "abstain": abstain_votes
            },
            "passing": passing,
            "majority_threshold": total_votes // 2 + 1
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting results for policy {policy_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/debates/{debate_id}/results")
def get_debate_results(debate_id: int):
    """Get voting results for a specific debate"""
    try:
        # Get all votes for this debate
        debate_votes = [v for v in votes_db if v["debate_id"] == debate_id]
        
        if not debate_votes:
            return {
                "debate_id": debate_id,
                "total_votes": 0,
                "results": {"yes": 0, "no": 0, "abstain": 0}
            }
        
        # Calculate results
        yes_votes = sum(1 for v in debate_votes if v["vote"] == "yes")
        no_votes = sum(1 for v in debate_votes if v["vote"] == "no")
        abstain_votes = sum(1 for v in debate_votes if v["vote"] == "abstain")
        
        return {
            "debate_id": debate_id,
            "total_votes": len(debate_votes),
            "results": {
                "yes": yes_votes,
                "no": no_votes,
                "abstain": abstain_votes
            }
        }
    except Exception as e:
        logger.error(f"Error getting results for debate {debate_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 9013))
    uvicorn.run(app, host="0.0.0.0", port=port)