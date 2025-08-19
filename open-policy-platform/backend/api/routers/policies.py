"""
Enhanced Policies Router
Provides comprehensive policy management, search, and analysis functionality
"""

from fastapi import APIRouter, Depends, Query, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import subprocess
import json
import os
from datetime import datetime, timedelta
from pydantic import BaseModel

from ..dependencies import get_db
from ..config import settings

router = APIRouter()

# Data models
class PolicyCreate(BaseModel):
    title: str
    content: str
    category: str
    jurisdiction: str
    status: str = "draft"
    tags: Optional[List[str]] = None

class PolicyUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    jurisdiction: Optional[str] = None
    status: Optional[str] = None
    tags: Optional[List[str]] = None

class PolicyAnalysis(BaseModel):
    policy_id: int
    analysis_type: str
    results: Dict[str, Any]
    timestamp: str

# STATIC ROUTES - Must come before dynamic routes to avoid conflicts

@router.get("/")
async def get_policies(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    category: Optional[str] = None,
    jurisdiction: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get policies with advanced filtering and pagination"""
    try:
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            raise HTTPException(status_code=500, detail="Database URL not configured")
        
        base_query = "SELECT * FROM bills_bill WHERE 1=1"
        
        if search:
            base_query += f" AND (title ILIKE '%{search}%' OR classification ILIKE '%{search}%')"
        if category:
            base_query += f" AND classification = '{category}'"
        if status:
            base_query += f" AND status = '{status}'"
        
        offset = (page - 1) * limit
        query = f"{base_query} ORDER BY id DESC LIMIT {limit} OFFSET {offset}"
        
        result = subprocess.run([
            "psql", database_url,
            "-c", query,
            "-t", "-A"
        ], capture_output=True, text=True, timeout=30)
        
        policies = []
        if result.returncode == 0 and result.stdout.strip():
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if line.strip():
                    fields = line.split('|')
                    policies.append({
                        "id": fields[0] if len(fields) > 0 else None,
                        "title": fields[1] if len(fields) > 1 else None,
                        "classification": fields[2] if len(fields) > 2 else None,
                        "session": fields[3] if len(fields) > 3 else None
                    })
        
        count_result = subprocess.run([
            "psql", database_url,
            "-c", "SELECT COUNT(*) FROM bills_bill",
            "-t", "-A"
        ], capture_output=True, text=True, timeout=10)
        
        total = 0
        if count_result.returncode == 0 and count_result.stdout.strip():
            total = int(count_result.stdout.strip())
        
        return {
            "policies": policies,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit,
            "filters": {
                "search": search,
                "category": category,
                "jurisdiction": jurisdiction,
                "status": status
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving policies: {str(e)}")

@router.get("/search")
async def search_policies(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Simple policy search"""
    return await search_policies_advanced(q=q, limit=limit, db=db)

@router.get("/search/advanced")
async def search_policies_advanced(
    q: str = Query(..., min_length=1),
    category: Optional[str] = None,
    jurisdiction: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """Advanced policy search with multiple criteria"""
    try:
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            raise HTTPException(status_code=500, detail="Database URL not configured")
        
        query = f"""
        SELECT * FROM bills_bill 
        WHERE (title ILIKE '%{q}%' OR classification ILIKE '%{q}%')
        """
        
        if category:
            query += f" AND classification = '{category}'"
        if jurisdiction:
            query += f" AND session = '{jurisdiction}'"
        
        query += f" ORDER BY id DESC LIMIT {limit}"
        
        result = subprocess.run([
            "psql", database_url,
            "-c", query,
            "-t", "-A"
        ], capture_output=True, text=True, timeout=30)
        
        policies = []
        if result.returncode == 0 and result.stdout.strip():
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if line.strip():
                    fields = line.split('|')
                    policies.append({
                        "id": fields[0] if len(fields) > 0 else None,
                        "title": fields[1] if len(fields) > 1 else None,
                        "classification": fields[2] if len(fields) > 2 else None,
                        "session": fields[3] if len(fields) > 3 else None
                    })
        
        return {
            "query": q,
            "policies": policies,
            "total": len(policies),
            "filters": {
                "category": category,
                "jurisdiction": jurisdiction
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching policies: {str(e)}")

@router.get("/list/categories")
async def get_policy_categories(db: Session = Depends(get_db)):
    """Get all available policy categories"""
    try:
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            raise HTTPException(status_code=500, detail="Database URL not configured")
        
        result = subprocess.run([
            "psql", database_url,
            "-c", "SELECT DISTINCT classification FROM bills_bill WHERE classification IS NOT NULL",
            "-t", "-A"
        ], capture_output=True, text=True, timeout=10)
        
        categories = []
        if result.returncode == 0 and result.stdout.strip():
            categories = [line.strip() for line in result.stdout.split('\n') if line.strip()]
        
        return {"categories": categories}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving categories: {str(e)}")

@router.get("/list/jurisdictions")
async def get_policy_jurisdictions(db: Session = Depends(get_db)):
    """Get all available policy jurisdictions"""
    try:
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            raise HTTPException(status_code=500, detail="Database URL not configured")
        
        result = subprocess.run([
            "psql", database_url,
            "-c", "SELECT DISTINCT session FROM bills_bill WHERE session IS NOT NULL",
            "-t", "-A"
        ], capture_output=True, text=True, timeout=10)
        
        jurisdictions = []
        if result.returncode == 0 and result.stdout.strip():
            jurisdictions = [line.strip() for line in result.stdout.split('\n') if line.strip()]
        
        return {"jurisdictions": jurisdictions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving jurisdictions: {str(e)}")

@router.get("/summary/stats")
async def get_policy_stats(db: Session = Depends(get_db)):
    """Get policy statistics"""
    try:
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            raise HTTPException(status_code=500, detail="Database URL not configured")
        
        count_result = subprocess.run([
            "psql", database_url,
            "-c", "SELECT COUNT(*) FROM bills_bill",
            "-t", "-A"
        ], capture_output=True, text=True, timeout=10)
        
        total = 0
        if count_result.returncode == 0 and count_result.stdout.strip():
            total = int(count_result.stdout.strip())
        
        cat_result = subprocess.run([
            "psql", database_url,
            "-c", "SELECT classification, COUNT(*) FROM bills_bill GROUP BY classification",
            "-t", "-A"
        ], capture_output=True, text=True, timeout=10)
        
        categories = {}
        if cat_result.returncode == 0 and cat_result.stdout.strip():
            for line in cat_result.stdout.strip().split('\n'):
                if line.strip():
                    fields = line.split('|')
                    if len(fields) >= 2:
                        categories[fields[0]] = int(fields[1])
        
        return {
            "total_policies": total,
            "categories": categories,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving stats: {str(e)}")

# DYNAMIC ROUTES - Must come after static routes

@router.get("/{policy_id}")
async def get_policy(policy_id: int, db: Session = Depends(get_db)):
    """Get specific policy by ID with detailed information"""
    try:
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            raise HTTPException(status_code=500, detail="Database URL not configured")
        
        result = subprocess.run([
            "psql", database_url,
            "-c", f"SELECT * FROM bills_bill WHERE id = {policy_id}",
            "-t", "-A"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode != 0 or not result.stdout.strip():
            raise HTTPException(status_code=404, detail="Policy not found")
        
        fields = result.stdout.strip().split('|')
        policy = {
            "id": fields[0] if len(fields) > 0 else None,
            "title": fields[1] if len(fields) > 1 else None,
            "classification": fields[2] if len(fields) > 2 else None,
            "session": fields[3] if len(fields) > 3 else None
        }
        
        return policy
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving policy: {str(e)}")

@router.get("/{policy_id}/analysis")
async def analyze_policy(policy_id: int, db: Session = Depends(get_db)):
    """Analyze a specific policy"""
    try:
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            raise HTTPException(status_code=500, detail="Database URL not configured")
        
        result = subprocess.run([
            "psql", database_url,
            "-c", f"SELECT title, classification FROM bills_bill WHERE id = {policy_id}",
            "-t", "-A"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode != 0 or not result.stdout.strip():
            raise HTTPException(status_code=404, detail="Policy not found")
        
        fields = result.stdout.strip().split('|')
        title = fields[0] if len(fields) > 0 else ""
        classification = fields[1] if len(fields) > 1 else ""
        
        word_count = len(title.split()) if title else 0
        char_count = len(title) if title else 0
        sentence_count = title.count('.') + title.count('!') + title.count('?') if title else 0
        
        analysis = {
            "policy_id": policy_id,
            "title": title,
            "classification": classification,
            "metrics": {
                "word_count": word_count,
                "character_count": char_count,
                "sentence_count": sentence_count,
                "complexity_score": "low" if word_count < 10 else "medium" if word_count < 20 else "high"
            },
            "timestamp": datetime.now().isoformat()
        }
        
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing policy: {str(e)}")

# POST/PUT/DELETE ROUTES

@router.post("/")
async def create_policy(policy: PolicyCreate, db: Session = Depends(get_db)):
    """Create a new policy"""
    try:
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            raise HTTPException(status_code=500, detail="Database URL not configured")
        
        insert_query = f"""
        INSERT INTO bills_bill (title, classification, session)
        VALUES ('{policy.title}', '{policy.category}', '{policy.jurisdiction}')
        RETURNING id;
        """
        
        result = subprocess.run([
            "psql", database_url,
            "-c", insert_query,
            "-t", "-A"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail="Failed to create policy")
        
        policy_id = result.stdout.strip()
        
        return {
            "message": "Policy created successfully",
            "policy_id": policy_id,
            "policy": policy.dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating policy: {str(e)}")

@router.put("/{policy_id}")
async def update_policy(policy_id: int, policy_update: PolicyUpdate, db: Session = Depends(get_db)):
    """Update an existing policy"""
    try:
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            raise HTTPException(status_code=500, detail="Database URL not configured")
        
        update_parts = []
        if policy_update.title:
            update_parts.append(f"title = '{policy_update.title}'")
        if policy_update.category:
            update_parts.append(f"classification = '{policy_update.category}'")
        if policy_update.jurisdiction:
            update_parts.append(f"session = '{policy_update.jurisdiction}'")
        
        if not update_parts:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        update_query = f"UPDATE bills_bill SET {', '.join(update_parts)} WHERE id = {policy_id};"
        
        result = subprocess.run([
            "psql", database_url,
            "-c", update_query,
            "-t", "-A"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail="Failed to update policy")
        
        return {
            "message": "Policy updated successfully",
            "policy_id": policy_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating policy: {str(e)}")

@router.delete("/{policy_id}")
async def delete_policy(policy_id: int, db: Session = Depends(get_db)):
    """Delete a policy"""
    try:
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            raise HTTPException(status_code=500, detail="Database URL not configured")
        
        result = subprocess.run([
            "psql", database_url,
            "-c", f"DELETE FROM bills_bill WHERE id = {policy_id};",
            "-t", "-A"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail="Failed to delete policy")
        
        return {
            "message": "Policy deleted successfully",
            "policy_id": policy_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting policy: {str(e)}")
