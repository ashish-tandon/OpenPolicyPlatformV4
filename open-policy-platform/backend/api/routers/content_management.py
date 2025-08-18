"""
Open Policy Platform V4 - Content Management Router
Handles polls, quizzes, content moderation, and user-generated content
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# Content Models
class PollOption(BaseModel):
    id: str
    text: str
    votes: int = 0
    percentage: float = 0.0

class Poll(BaseModel):
    id: str
    title: str
    description: str
    options: List[PollOption]
    creator_id: str
    creator_role: str
    status: str = "active"  # active, closed, archived
    visibility: str = "public"  # public, private, restricted
    start_date: datetime
    end_date: Optional[datetime] = None
    max_votes_per_user: int = 1
    allow_multiple_votes: bool = False
    total_votes: int = 0
    created_at: datetime
    updated_at: datetime

class QuizQuestion(BaseModel):
    id: str
    question: str
    question_type: str  # multiple_choice, true_false, text
    options: List[str] = []
    correct_answer: str
    points: int = 1
    explanation: Optional[str] = None

class Quiz(BaseModel):
    id: str
    title: str
    description: str
    questions: List[QuizQuestion]
    creator_id: str
    creator_role: str
    status: str = "draft"  # draft, active, closed, archived
    visibility: str = "public"  # public, private, restricted
    time_limit_minutes: Optional[int] = None
    passing_score_percentage: float = 70.0
    max_attempts: int = 1
    total_participants: int = 0
    average_score: float = 0.0
    created_at: datetime
    updated_at: datetime

class Comment(BaseModel):
    id: str
    content: str
    author_id: str
    author_role: str
    parent_id: Optional[str] = None  # For replies
    content_type: str = "general"  # general, policy, poll, quiz
    content_id: Optional[str] = None
    status: str = "active"  # active, flagged, removed, hidden
    flags: int = 0
    created_at: datetime
    updated_at: datetime

class ContentFlag(BaseModel):
    id: str
    content_id: str
    content_type: str  # comment, poll, quiz, user
    reporter_id: str
    reason: str
    description: Optional[str] = None
    status: str = "pending"  # pending, reviewed, resolved, dismissed
    moderator_id: Optional[str] = None
    moderator_notes: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None

# Mock Databases
POLLS_DB = {}
QUIZZES_DB = {}
COMMENTS_DB = {}
CONTENT_FLAGS_DB = {}
USER_VOTES_DB = {}
QUIZ_ATTEMPTS_DB = {}

# Content Management Endpoints

## Poll Management
@router.post("/polls")
async def create_poll(
    title: str = Body(..., description="Poll title"),
    description: str = Body(..., description="Poll description"),
    options: List[str] = Body(..., description="Poll options"),
    end_date: Optional[str] = Body(None, description="End date (ISO format)"),
    max_votes_per_user: int = Body(1, description="Maximum votes per user"),
    allow_multiple_votes: bool = Body(False, description="Allow multiple votes"),
    visibility: str = Body("public", description="Poll visibility")
):
    """Create a new poll (MP Office Admin and above)"""
    try:
        # Validate creator permissions (in production, check actual user role)
        creator_role = "mp_office_admin"  # Mock for now
        
        if creator_role not in ["mp_office_admin", "moderator", "system_admin"]:
            raise HTTPException(status_code=403, detail="Insufficient permissions to create polls")
        
        # Create poll options
        poll_options = [
            PollOption(
                id=str(uuid.uuid4()),
                text=option,
                votes=0,
                percentage=0.0
            ) for option in options
        ]
        
        # Parse end date
        end_date_obj = None
        if end_date:
            try:
                end_date_obj = datetime.fromisoformat(end_date)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end date format")
        
        # Create poll
        poll_id = str(uuid.uuid4())
        poll = Poll(
            id=poll_id,
            title=title,
            description=description,
            options=poll_options,
            creator_id="mock_creator_id",  # In production, get from auth
            creator_role=creator_role,
            start_date=datetime.now(),
            end_date=end_date_obj,
            max_votes_per_user=max_votes_per_user,
            allow_multiple_votes=allow_multiple_votes,
            visibility=visibility,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        POLLS_DB[poll_id] = poll
        
        return {
            "status": "success",
            "message": "Poll created successfully",
            "poll_id": poll_id,
            "poll": poll
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating poll: {e}")
        raise HTTPException(status_code=500, detail=f"Poll creation error: {str(e)}")

@router.get("/polls")
async def list_polls(
    status: str = Query("active", description="Filter by status"),
    visibility: str = Query("public", description="Filter by visibility"),
    limit: int = Query(10, description="Number of polls to return"),
    offset: int = Query(0, description="Number of polls to skip")
):
    """List polls with filtering"""
    try:
        filtered_polls = []
        
        for poll in POLLS_DB.values():
            if poll.status == status and poll.visibility == visibility:
                filtered_polls.append(poll)
        
        # Apply pagination
        paginated_polls = filtered_polls[offset:offset + limit]
        
        return {
            "status": "success",
            "polls": paginated_polls,
            "total": len(filtered_polls),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Error listing polls: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing polls: {str(e)}")

@router.post("/polls/{poll_id}/vote")
async def vote_on_poll(
    poll_id: str,
    option_ids: List[str] = Body(..., description="Selected option IDs")
):
    """Vote on a poll"""
    try:
        if poll_id not in POLLS_DB:
            raise HTTPException(status_code=404, detail="Poll not found")
        
        poll = POLLS_DB[poll_id]
        
        # Check if poll is active
        if poll.status != "active":
            raise HTTPException(status_code=400, detail="Poll is not active")
        
        # Check if poll has ended
        if poll.end_date and datetime.now() > poll.end_date:
            raise HTTPException(status_code=400, detail="Poll has ended")
        
        # Validate option IDs
        valid_option_ids = [opt.id for opt in poll.options]
        for option_id in option_ids:
            if option_id not in valid_option_ids:
                raise HTTPException(status_code=400, detail=f"Invalid option ID: {option_id}")
        
        # Check voting limits
        user_id = "mock_user_id"  # In production, get from auth
        user_vote_key = f"{user_id}_{poll_id}"
        
        if not poll.allow_multiple_votes and len(option_ids) > 1:
            raise HTTPException(status_code=400, detail="Multiple votes not allowed")
        
        if user_vote_key in USER_VOTES_DB:
            if not poll.allow_multiple_votes:
                raise HTTPException(status_code=400, detail="User has already voted")
            elif len(USER_VOTES_DB[user_vote_key]) + len(option_ids) > poll.max_votes_per_user:
                raise HTTPException(status_code=400, detail="Vote limit exceeded")
        
        # Record votes
        if user_vote_key not in USER_VOTES_DB:
            USER_VOTES_DB[user_vote_key] = []
        
        USER_VOTES_DB[user_vote_key].extend(option_ids)
        
        # Update poll statistics
        for option_id in option_ids:
            for option in poll.options:
                if option.id == option_id:
                    option.votes += 1
                    break
        
        poll.total_votes += len(option_ids)
        
        # Recalculate percentages
        for option in poll.options:
            if poll.total_votes > 0:
                option.percentage = (option.votes / poll.total_votes) * 100
            else:
                option.percentage = 0.0
        
        poll.updated_at = datetime.now()
        
        return {
            "status": "success",
            "message": "Vote recorded successfully",
            "poll_id": poll_id,
            "total_votes": poll.total_votes
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error voting on poll: {e}")
        raise HTTPException(status_code=500, detail=f"Voting error: {str(e)}")

## Quiz Management
@router.post("/quizzes")
async def create_quiz(
    title: str = Body(..., description="Quiz title"),
    description: str = Body(..., description="Quiz description"),
    questions: List[Dict[str, Any]] = Body(..., description="Quiz questions"),
    time_limit_minutes: Optional[int] = Body(None, description="Time limit in minutes"),
    passing_score_percentage: float = Body(70.0, description="Passing score percentage"),
    max_attempts: int = Body(1, description="Maximum attempts allowed"),
    visibility: str = Body("public", description="Quiz visibility")
):
    """Create a new quiz (MP Office Admin and above)"""
    try:
        # Validate creator permissions
        creator_role = "mp_office_admin"  # Mock for now
        
        if creator_role not in ["mp_office_admin", "moderator", "system_admin"]:
            raise HTTPException(status_code=403, detail="Insufficient permissions to create quizzes")
        
        # Create quiz questions
        quiz_questions = []
        for q_data in questions:
            question = QuizQuestion(
                id=str(uuid.uuid4()),
                question=q_data["question"],
                question_type=q_data["question_type"],
                options=q_data.get("options", []),
                correct_answer=q_data["correct_answer"],
                points=q_data.get("points", 1),
                explanation=q_data.get("explanation")
            )
            quiz_questions.append(question)
        
        # Create quiz
        quiz_id = str(uuid.uuid4())
        quiz = Quiz(
            id=quiz_id,
            title=title,
            description=description,
            questions=quiz_questions,
            creator_id="mock_creator_id",  # In production, get from auth
            creator_role=creator_role,
            time_limit_minutes=time_limit_minutes,
            passing_score_percentage=passing_score_percentage,
            max_attempts=max_attempts,
            visibility=visibility,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        QUIZZES_DB[quiz_id] = quiz
        
        return {
            "status": "success",
            "message": "Quiz created successfully",
            "quiz_id": quiz_id,
            "quiz": quiz
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating quiz: {e}")
        raise HTTPException(status_code=500, detail=f"Quiz creation error: {str(e)}")

@router.get("/quizzes")
async def list_quizzes(
    status: str = Query("active", description="Filter by status"),
    visibility: str = Query("public", description="Filter by visibility"),
    limit: int = Query(10, description="Number of quizzes to return"),
    offset: int = Query(0, description="Number of quizzes to skip")
):
    """List quizzes with filtering"""
    try:
        filtered_quizzes = []
        
        for quiz in QUIZZES_DB.values():
            if quiz.status == status and quiz.visibility == visibility:
                filtered_quizzes.append(quiz)
        
        # Apply pagination
        paginated_quizzes = filtered_quizzes[offset:offset + limit]
        
        return {
            "status": "success",
            "quizzes": paginated_quizzes,
            "total": len(filtered_quizzes),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Error listing quizzes: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing quizzes: {str(e)}")

## Comment Management
@router.post("/comments")
async def create_comment(
    content: str = Body(..., description="Comment content"),
    content_type: str = Body("general", description="Type of content being commented on"),
    content_id: Optional[str] = Body(None, description="ID of the content being commented on"),
    parent_id: Optional[str] = Body(None, description="Parent comment ID for replies")
):
    """Create a new comment"""
    try:
        # Validate content length
        if len(content.strip()) < 1:
            raise HTTPException(status_code=400, detail="Comment cannot be empty")
        
        if len(content) > 1000:
            raise HTTPException(status_code=400, detail="Comment too long (max 1000 characters)")
        
        # Create comment
        comment_id = str(uuid.uuid4())
        comment = Comment(
            id=comment_id,
            content=content.strip(),
            author_id="mock_user_id",  # In production, get from auth
            author_role="consumer",  # In production, get from auth
            parent_id=parent_id,
            content_type=content_type,
            content_id=content_id,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        COMMENTS_DB[comment_id] = comment
        
        return {
            "status": "success",
            "message": "Comment created successfully",
            "comment_id": comment_id,
            "comment": comment
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating comment: {e}")
        raise HTTPException(status_code=500, detail=f"Comment creation error: {str(e)}")

@router.get("/comments")
async def list_comments(
    content_type: Optional[str] = Query(None, description="Filter by content type"),
    content_id: Optional[str] = Query(None, description="Filter by content ID"),
    parent_id: Optional[str] = Query(None, description="Filter by parent comment ID"),
    status: str = Query("active", description="Filter by status"),
    limit: int = Query(20, description="Number of comments to return"),
    offset: int = Query(0, description="Number of comments to skip")
):
    """List comments with filtering"""
    try:
        filtered_comments = []
        
        for comment in COMMENTS_DB.values():
            if (content_type is None or comment.content_type == content_type) and \
               (content_id is None or comment.content_id == content_id) and \
               (parent_id is None or comment.parent_id == parent_id) and \
               comment.status == status:
                filtered_comments.append(comment)
        
        # Sort by creation date (newest first)
        filtered_comments.sort(key=lambda x: x.created_at, reverse=True)
        
        # Apply pagination
        paginated_comments = filtered_comments[offset:offset + limit]
        
        return {
            "status": "success",
            "comments": paginated_comments,
            "total": len(filtered_comments),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Error listing comments: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing comments: {str(e)}")

## Content Moderation
@router.post("/comments/{comment_id}/flag")
async def flag_comment(
    comment_id: str,
    reason: str = Body(..., description="Reason for flagging"),
    description: Optional[str] = Body(None, description="Additional details")
):
    """Flag a comment for moderation"""
    try:
        if comment_id not in COMMENTS_DB:
            raise HTTPException(status_code=404, detail="Comment not found")
        
        comment = COMMENTS_DB[comment_id]
        
        # Create flag
        flag_id = str(uuid.uuid4())
        flag = ContentFlag(
            id=flag_id,
            content_id=comment_id,
            content_type="comment",
            reporter_id="mock_user_id",  # In production, get from auth
            reason=reason,
            description=description,
            created_at=datetime.now()
        )
        
        CONTENT_FLAGS_DB[flag_id] = flag
        
        # Update comment flag count
        comment.flags += 1
        
        # Auto-hide comment if too many flags
        if comment.flags >= 5:
            comment.status = "hidden"
        
        return {
            "status": "success",
            "message": "Comment flagged successfully",
            "flag_id": flag_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error flagging comment: {e}")
        raise HTTPException(status_code=500, detail=f"Flagging error: {str(e)}")

@router.put("/comments/{comment_id}/moderate")
async def moderate_comment(
    comment_id: str,
    action: str = Body(..., description="Moderation action: remove, hide, approve"),
    notes: Optional[str] = Body(None, description="Moderator notes")
):
    """Moderate a comment (Moderator and above)"""
    try:
        # Validate moderator permissions
        moderator_role = "moderator"  # Mock for now
        
        if moderator_role not in ["moderator", "system_admin"]:
            raise HTTPException(status_code=403, detail="Insufficient permissions to moderate content")
        
        if comment_id not in COMMENTS_DB:
            raise HTTPException(status_code=404, detail="Comment not found")
        
        comment = COMMENTS_DB[comment_id]
        
        # Apply moderation action
        if action == "remove":
            comment.status = "removed"
        elif action == "hide":
            comment.status = "hidden"
        elif action == "approve":
            comment.status = "active"
            comment.flags = 0
        else:
            raise HTTPException(status_code=400, detail="Invalid moderation action")
        
        comment.updated_at = datetime.now()
        
        # Update related flags
        for flag in CONTENT_FLAGS_DB.values():
            if flag.content_id == comment_id and flag.status == "pending":
                flag.status = "resolved"
                flag.moderator_id = "mock_moderator_id"  # In production, get from auth
                flag.moderator_notes = notes
                flag.resolved_at = datetime.now()
        
        return {
            "status": "success",
            "message": f"Comment {action}ed successfully",
            "comment_id": comment_id,
            "new_status": comment.status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error moderating comment: {e}")
        raise HTTPException(status_code=500, detail=f"Moderation error: {str(e)}")

## Content Statistics
@router.get("/content/stats")
async def get_content_statistics():
    """Get content management statistics"""
    try:
        total_polls = len(POLLS_DB)
        active_polls = len([p for p in POLLS_DB.values() if p.status == "active"])
        
        total_quizzes = len(QUIZZES_DB)
        active_quizzes = len([q for q in QUIZZES_DB.values() if q.status == "active"])
        
        total_comments = len(COMMENTS_DB)
        active_comments = len([c for c in COMMENTS_DB.values() if c.status == "active"])
        flagged_comments = len([c for c in COMMENTS_DB.values() if c.flags > 0])
        
        pending_flags = len([f for f in CONTENT_FLAGS_DB.values() if f.status == "pending"])
        
        return {
            "status": "success",
            "statistics": {
                "polls": {
                    "total": total_polls,
                    "active": active_polls,
                    "closed": total_polls - active_polls
                },
                "quizzes": {
                    "total": total_quizzes,
                    "active": active_quizzes,
                    "draft": total_quizzes - active_quizzes
                },
                "comments": {
                    "total": total_comments,
                    "active": active_comments,
                    "flagged": flagged_comments,
                    "moderated": total_comments - active_comments
                },
                "moderation": {
                    "pending_flags": pending_flags,
                    "total_flags": len(CONTENT_FLAGS_DB)
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting content statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting statistics: {str(e)}")
