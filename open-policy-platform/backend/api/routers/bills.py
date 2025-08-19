"""
Bills API Router - Complete Implementation

Provides comprehensive endpoints for bill tracking, feedback, comments, and pro/con profiles
across federal, provincial, and municipal jurisdictions.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, and_, func
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from uuid import UUID
import logging

from ..dependencies import get_db
from ..models import (
    Bill, BillFeedback, BillComment, BillProCon, 
    Representative, Jurisdiction, User, 
    ProConVote, CommentVote, BillStatusChange
)
from ..schemas import (
    BillResponse, BillCreateRequest, BillUpdateRequest,
    BillFeedbackRequest, BillFeedbackResponse,
    BillCommentRequest, BillCommentResponse,
    BillProConRequest, BillProConResponse,
    BillSearchRequest, BillTimelineResponse
)
from ..auth import get_current_user, get_current_user_optional

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=List[BillResponse])
async def list_bills(
    jurisdiction: Optional[str] = Query(None, description="Filter by jurisdiction (federal, provincial, municipal)"),
    province: Optional[str] = Query(None, description="Filter by province code (ON, BC, etc.)"),
    status: Optional[str] = Query(None, description="Filter by bill status"),
    search: Optional[str] = Query(None, description="Search in title and summary"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    List bills with filtering and pagination.
    
    Supports filtering by:
    - Jurisdiction type (federal, provincial, municipal)
    - Province/territory
    - Bill status
    - Text search in title and summary
    """
    query = db.query(Bill).join(Jurisdiction)
    
    # Apply filters
    if jurisdiction:
        query = query.filter(Jurisdiction.type == jurisdiction)
    
    if province:
        query = query.filter(Jurisdiction.code.like(f"{province}%"))
    
    if status:
        query = query.filter(Bill.status == status)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Bill.title.ilike(search_term),
                Bill.summary.ilike(search_term),
                Bill.number.ilike(search_term)
            )
        )
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * limit
    bills = query.order_by(Bill.introduction_date.desc()).offset(offset).limit(limit).all()
    
    return {
        "items": bills,
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit
    }


@router.get("/{bill_id}", response_model=BillResponse)
async def get_bill(
    bill_id: UUID,
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific bill."""
    bill = db.query(Bill).options(
        joinedload(Bill.jurisdiction),
        joinedload(Bill.representatives),
        joinedload(Bill.status_changes),
        joinedload(Bill.pro_cons),
        joinedload(Bill.feedback)
    ).filter(Bill.id == bill_id).first()
    
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    
    return bill


@router.get("/{bill_id}/timeline", response_model=List[BillTimelineResponse])
async def get_bill_timeline(
    bill_id: UUID,
    db: Session = Depends(get_db)
):
    """Get the complete timeline of status changes for a bill."""
    timeline = db.query(BillStatusChange).filter(
        BillStatusChange.bill_id == bill_id
    ).order_by(BillStatusChange.date).all()
    
    return timeline


@router.get("/{bill_id}/feedback", response_model=List[BillFeedbackResponse])
async def get_bill_feedback(
    bill_id: UUID,
    feedback_type: Optional[str] = Query(None),
    verified_only: bool = Query(False),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get citizen feedback for a bill."""
    query = db.query(BillFeedback).filter(
        BillFeedback.bill_id == bill_id,
        BillFeedback.status == 'approved'
    )
    
    if feedback_type:
        query = query.filter(BillFeedback.feedback_type == feedback_type)
    
    if verified_only:
        query = query.filter(BillFeedback.verified == True)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * limit
    feedback = query.order_by(
        BillFeedback.helpful_count.desc(),
        BillFeedback.created_at.desc()
    ).offset(offset).limit(limit).all()
    
    return {
        "items": feedback,
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit
    }


@router.post("/{bill_id}/feedback", response_model=BillFeedbackResponse)
async def create_bill_feedback(
    bill_id: UUID,
    feedback: BillFeedbackRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit feedback on a bill."""
    # Check if bill exists
    bill = db.query(Bill).filter(Bill.id == bill_id).first()
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    
    # Check if user already submitted this type of feedback
    existing = db.query(BillFeedback).filter(
        BillFeedback.bill_id == bill_id,
        BillFeedback.user_id == current_user.id,
        BillFeedback.feedback_type == feedback.feedback_type
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400, 
            detail="You have already submitted this type of feedback for this bill"
        )
    
    # Create feedback
    db_feedback = BillFeedback(
        bill_id=bill_id,
        user_id=current_user.id,
        **feedback.dict()
    )
    
    # Auto-approve if user is verified
    if current_user.identity_verified:
        db_feedback.status = 'approved'
        db_feedback.verified = True
    
    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)
    
    return db_feedback


@router.get("/{bill_id}/procons", response_model=List[BillProConResponse])
async def get_bill_procons(
    bill_id: UUID,
    side: Optional[str] = Query(None, description="Filter by 'pro' or 'con'"),
    verified_only: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Get pro and con arguments for a bill."""
    query = db.query(BillProCon).filter(BillProCon.bill_id == bill_id)
    
    if side == "pro":
        query = query.filter(BillProCon.is_pro == True)
    elif side == "con":
        query = query.filter(BillProCon.is_pro == False)
    
    if verified_only:
        query = query.filter(BillProCon.verified == True)
    
    procons = query.order_by(
        BillProCon.featured.desc(),
        BillProCon.quality_score.desc(),
        (BillProCon.upvotes - BillProCon.downvotes).desc()
    ).all()
    
    # Add user vote status if authenticated
    if current_user:
        for procon in procons:
            vote = db.query(ProConVote).filter(
                ProConVote.pro_con_id == procon.id,
                ProConVote.user_id == current_user.id
            ).first()
            procon.user_vote = "up" if vote and vote.is_upvote else "down" if vote else None
    
    return procons


@router.post("/{bill_id}/procons", response_model=BillProConResponse)
async def create_bill_procon(
    bill_id: UUID,
    procon: BillProConRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit a pro or con argument for a bill."""
    # Check if bill exists
    bill = db.query(Bill).filter(Bill.id == bill_id).first()
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    
    # Create pro/con
    db_procon = BillProCon(
        bill_id=bill_id,
        created_by=current_user.id,
        **procon.dict()
    )
    
    # Auto-verify if user is verified
    if current_user.identity_verified:
        db_procon.verified = True
    
    db.add(db_procon)
    db.commit()
    db.refresh(db_procon)
    
    return db_procon


@router.post("/{bill_id}/procons/{procon_id}/vote")
async def vote_on_procon(
    bill_id: UUID,
    procon_id: UUID,
    vote: str = Query(..., description="Vote type: 'up' or 'down'"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Vote on a pro/con argument."""
    # Verify pro/con exists and belongs to bill
    procon = db.query(BillProCon).filter(
        BillProCon.id == procon_id,
        BillProCon.bill_id == bill_id
    ).first()
    
    if not procon:
        raise HTTPException(status_code=404, detail="Pro/con argument not found")
    
    # Check existing vote
    existing_vote = db.query(ProConVote).filter(
        ProConVote.pro_con_id == procon_id,
        ProConVote.user_id == current_user.id
    ).first()
    
    if vote not in ["up", "down"]:
        raise HTTPException(status_code=400, detail="Vote must be 'up' or 'down'")
    
    is_upvote = vote == "up"
    
    if existing_vote:
        if existing_vote.is_upvote == is_upvote:
            # Remove vote if clicking same button
            db.delete(existing_vote)
        else:
            # Change vote
            existing_vote.is_upvote = is_upvote
    else:
        # Create new vote
        new_vote = ProConVote(
            pro_con_id=procon_id,
            user_id=current_user.id,
            is_upvote=is_upvote
        )
        db.add(new_vote)
    
    db.commit()
    
    # Return updated counts
    procon = db.query(BillProCon).filter(BillProCon.id == procon_id).first()
    return {
        "upvotes": procon.upvotes,
        "downvotes": procon.downvotes,
        "user_vote": vote if not existing_vote or existing_vote.is_upvote != is_upvote else None
    }


@router.get("/{bill_id}/comments", response_model=List[BillCommentResponse])
async def get_bill_comments(
    bill_id: UUID,
    parent_id: Optional[UUID] = Query(None, description="Get replies to a specific comment"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Get comments on a bill."""
    query = db.query(BillComment).filter(
        BillComment.bill_id == bill_id,
        BillComment.status == 'approved'
    )
    
    if parent_id is None:
        # Get top-level comments only
        query = query.filter(BillComment.parent_id.is_(None))
    else:
        # Get replies to specific comment
        query = query.filter(BillComment.parent_id == parent_id)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * limit
    comments = query.order_by(
        (BillComment.likes - BillComment.dislikes).desc(),
        BillComment.created_at.desc()
    ).offset(offset).limit(limit).all()
    
    # Add user vote status if authenticated
    if current_user:
        for comment in comments:
            vote = db.query(CommentVote).filter(
                CommentVote.comment_id == comment.id,
                CommentVote.user_id == current_user.id
            ).first()
            comment.user_vote = "like" if vote and vote.is_like else "dislike" if vote else None
    
    return {
        "items": comments,
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit
    }


@router.post("/{bill_id}/comments", response_model=BillCommentResponse)
async def create_bill_comment(
    bill_id: UUID,
    comment: BillCommentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Post a comment on a bill."""
    # Check if bill exists
    bill = db.query(Bill).filter(Bill.id == bill_id).first()
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    
    # Check if parent comment exists (for replies)
    if comment.parent_id:
        parent = db.query(BillComment).filter(
            BillComment.id == comment.parent_id,
            BillComment.bill_id == bill_id
        ).first()
        if not parent:
            raise HTTPException(status_code=404, detail="Parent comment not found")
    
    # Create comment
    db_comment = BillComment(
        bill_id=bill_id,
        user_id=current_user.id,
        **comment.dict()
    )
    
    # Auto-approve if user is verified or moderator
    if current_user.identity_verified or current_user.is_moderator:
        db_comment.status = 'approved'
    
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    
    return db_comment


@router.get("/search/advanced", response_model=List[BillResponse])
async def search_bills_advanced(
    search_params: BillSearchRequest,
    db: Session = Depends(get_db)
):
    """
    Advanced bill search with multiple criteria.
    
    Supports searching by:
    - Text (in title, summary, or full text)
    - Date ranges
    - Multiple jurisdictions
    - Multiple statuses
    - Bill numbers
    - Sponsor names
    """
    query = db.query(Bill).join(Jurisdiction)
    
    # Text search
    if search_params.text:
        search_term = f"%{search_params.text}%"
        query = query.filter(
            or_(
                Bill.title.ilike(search_term),
                Bill.summary.ilike(search_term),
                Bill.bill_text.ilike(search_term),
                Bill.number.ilike(search_term)
            )
        )
    
    # Jurisdiction filters
    if search_params.jurisdictions:
        query = query.filter(Jurisdiction.type.in_(search_params.jurisdictions))
    
    if search_params.provinces:
        query = query.filter(
            or_(*[Jurisdiction.code.like(f"{p}%") for p in search_params.provinces])
        )
    
    # Status filter
    if search_params.statuses:
        query = query.filter(Bill.status.in_(search_params.statuses))
    
    # Date filters
    if search_params.introduced_after:
        query = query.filter(Bill.introduction_date >= search_params.introduced_after)
    
    if search_params.introduced_before:
        query = query.filter(Bill.introduction_date <= search_params.introduced_before)
    
    # Sponsor filter
    if search_params.sponsor_name:
        query = query.join(Bill.representatives).filter(
            Representative.name.ilike(f"%{search_params.sponsor_name}%")
        )
    
    # Ordering
    order_map = {
        "date_desc": Bill.introduction_date.desc(),
        "date_asc": Bill.introduction_date.asc(),
        "relevance": Bill.title  # Would use full-text search ranking in production
    }
    order_by = order_map.get(search_params.order_by, Bill.introduction_date.desc())
    
    # Execute query with pagination
    total = query.count()
    offset = (search_params.page - 1) * search_params.limit
    bills = query.order_by(order_by).offset(offset).limit(search_params.limit).all()
    
    return {
        "items": bills,
        "total": total,
        "page": search_params.page,
        "pages": (total + search_params.limit - 1) // search_params.limit
    }


@router.get("/stats/by-jurisdiction")
async def get_bill_stats_by_jurisdiction(
    db: Session = Depends(get_db)
):
    """Get bill statistics grouped by jurisdiction."""
    stats = db.query(
        Jurisdiction.type,
        Jurisdiction.name,
        func.count(Bill.id).label("total_bills"),
        func.count(Bill.id).filter(Bill.status == "passed").label("passed_bills"),
        func.count(Bill.id).filter(Bill.status == "active").label("active_bills")
    ).join(Bill).group_by(Jurisdiction.type, Jurisdiction.name).all()
    
    return [
        {
            "jurisdiction_type": s[0],
            "jurisdiction_name": s[1],
            "total_bills": s[2],
            "passed_bills": s[3],
            "active_bills": s[4]
        }
        for s in stats
    ]


@router.get("/trending")
async def get_trending_bills(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    Get trending bills based on citizen engagement.
    
    Ranking based on:
    - Recent feedback count
    - Comment activity
    - Pro/con argument quality and votes
    """
    # This would use a more sophisticated algorithm in production
    # For now, using simple engagement metrics
    recent_date = datetime.utcnow() - timedelta(days=7)
    
    trending = db.query(
        Bill,
        func.count(BillFeedback.id).label("feedback_count"),
        func.count(BillComment.id).label("comment_count")
    ).outerjoin(
        BillFeedback, and_(
            BillFeedback.bill_id == Bill.id,
            BillFeedback.created_at >= recent_date
        )
    ).outerjoin(
        BillComment, and_(
            BillComment.bill_id == Bill.id,
            BillComment.created_at >= recent_date
        )
    ).group_by(Bill.id).order_by(
        (func.count(BillFeedback.id) + func.count(BillComment.id)).desc()
    ).limit(limit).all()
    
    return [
        {
            "bill": t[0],
            "engagement_score": t[1] + t[2],
            "feedback_count": t[1],
            "comment_count": t[2]
        }
        for t in trending
    ]