"""
Citizen Engagement Models for OpenPolicy Platform

This module defines database models for citizen engagement features including:
- Bill feedback and ratings
- Pro/con profiles for bills
- Comments and discussions
- User engagement tracking
"""

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean,
    ForeignKey, JSON, Enum, UniqueConstraint, Index, Float
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
import enum
from .models import Base


class FeedbackType(enum.Enum):
    """Types of feedback citizens can provide"""
    SUPPORT = "support"
    OPPOSE = "oppose"
    NEUTRAL = "neutral"
    CONCERN = "concern"
    SUGGESTION = "suggestion"
    QUESTION = "question"


class CommentStatus(enum.Enum):
    """Status of user comments"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    FLAGGED = "flagged"
    HIDDEN = "hidden"


class BillFeedback(Base):
    """Citizen feedback on bills"""
    __tablename__ = 'bill_feedback'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bill_id = Column(UUID(as_uuid=True), ForeignKey('bills.id'), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    
    # Feedback details
    feedback_type = Column(Enum(FeedbackType), nullable=False)
    rating = Column(Integer)  # 1-5 star rating
    title = Column(String(200))
    content = Column(Text, nullable=False)
    
    # Engagement metrics
    helpful_count = Column(Integer, default=0)
    not_helpful_count = Column(Integer, default=0)
    
    # Status
    verified = Column(Boolean, default=False)  # Verified citizen
    anonymous = Column(Boolean, default=False)
    status = Column(Enum(CommentStatus), default=CommentStatus.PENDING)
    
    # Location (optional)
    postal_code = Column(String(10))  # For geographic analysis
    riding = Column(String(100))  # Electoral district
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    bill = relationship("Bill", backref="feedback")
    user = relationship("User", backref="bill_feedback")
    
    __table_args__ = (
        Index('ix_bill_feedback_bill', 'bill_id'),
        Index('ix_bill_feedback_user', 'user_id'),
        Index('ix_bill_feedback_type', 'feedback_type'),
        Index('ix_bill_feedback_created', 'created_at'),
        UniqueConstraint('bill_id', 'user_id', 'feedback_type', name='uq_bill_user_feedback'),
    )


class BillProCon(Base):
    """Pro and con arguments for bills"""
    __tablename__ = 'bill_pro_cons'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bill_id = Column(UUID(as_uuid=True), ForeignKey('bills.id'), nullable=False)
    
    # Argument details
    is_pro = Column(Boolean, nullable=False)  # True for pro, False for con
    title = Column(String(200), nullable=False)
    argument = Column(Text, nullable=False)
    source = Column(String(100))  # Expert, citizen, organization, etc.
    source_name = Column(String(200))  # Name of source
    source_url = Column(String(500))  # Link to source
    
    # Voting
    upvotes = Column(Integer, default=0)
    downvotes = Column(Integer, default=0)
    
    # Quality metrics
    verified = Column(Boolean, default=False)
    fact_checked = Column(Boolean, default=False)
    quality_score = Column(Float, default=0.0)  # ML-based quality score
    
    # Display order
    display_order = Column(Integer, default=0)
    featured = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    
    # Relationships
    bill = relationship("Bill", backref="pro_cons")
    creator = relationship("User", backref="created_pro_cons")
    
    __table_args__ = (
        Index('ix_bill_procon_bill', 'bill_id'),
        Index('ix_bill_procon_type', 'is_pro'),
        Index('ix_bill_procon_votes', 'upvotes', 'downvotes'),
    )


class BillComment(Base):
    """Comments and discussions on bills"""
    __tablename__ = 'bill_comments'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bill_id = Column(UUID(as_uuid=True), ForeignKey('bills.id'), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey('bill_comments.id'))  # For threading
    
    # Comment content
    content = Column(Text, nullable=False)
    
    # Engagement
    likes = Column(Integer, default=0)
    dislikes = Column(Integer, default=0)
    reply_count = Column(Integer, default=0)
    
    # Moderation
    status = Column(Enum(CommentStatus), default=CommentStatus.PENDING)
    flagged_count = Column(Integer, default=0)
    moderation_notes = Column(Text)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    edited = Column(Boolean, default=False)
    
    # Relationships
    bill = relationship("Bill", backref="comments")
    user = relationship("User", backref="bill_comments")
    parent = relationship("BillComment", remote_side=[id], backref="replies")
    
    __table_args__ = (
        Index('ix_bill_comment_bill', 'bill_id'),
        Index('ix_bill_comment_user', 'user_id'),
        Index('ix_bill_comment_parent', 'parent_id'),
        Index('ix_bill_comment_created', 'created_at'),
        Index('ix_bill_comment_status', 'status'),
    )


class RepresentativeFeedback(Base):
    """Feedback on representatives' performance"""
    __tablename__ = 'representative_feedback'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    representative_id = Column(UUID(as_uuid=True), ForeignKey('representatives.id'), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    
    # Ratings
    overall_rating = Column(Integer)  # 1-5
    communication_rating = Column(Integer)  # 1-5
    effectiveness_rating = Column(Integer)  # 1-5
    accessibility_rating = Column(Integer)  # 1-5
    
    # Feedback
    title = Column(String(200))
    content = Column(Text)
    
    # Context
    issue_area = Column(String(100))  # Healthcare, education, etc.
    interaction_type = Column(String(50))  # Email, meeting, town hall, etc.
    
    # Verification
    verified_constituent = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    representative = relationship("Representative", backref="feedback")
    user = relationship("User", backref="representative_feedback")
    
    __table_args__ = (
        Index('ix_rep_feedback_rep', 'representative_id'),
        Index('ix_rep_feedback_user', 'user_id'),
        Index('ix_rep_feedback_rating', 'overall_rating'),
        UniqueConstraint('representative_id', 'user_id', name='uq_rep_user_feedback'),
    )


class UserEngagement(Base):
    """Track user engagement with platform features"""
    __tablename__ = 'user_engagement'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    
    # Engagement metrics
    bills_viewed = Column(Integer, default=0)
    bills_feedback_given = Column(Integer, default=0)
    comments_posted = Column(Integer, default=0)
    pro_cons_voted = Column(Integer, default=0)
    representatives_contacted = Column(Integer, default=0)
    
    # Activity tracking
    last_activity = Column(DateTime, default=datetime.utcnow)
    total_sessions = Column(Integer, default=0)
    total_time_minutes = Column(Integer, default=0)
    
    # Preferences
    preferred_jurisdiction = Column(String(50))  # federal, provincial, municipal
    interests = Column(JSON)  # List of policy areas of interest
    
    # Achievements/Badges
    badges = Column(JSON)  # List of earned badges
    reputation_score = Column(Integer, default=0)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", backref="engagement", uselist=False)
    
    __table_args__ = (
        Index('ix_user_engagement_user', 'user_id'),
        Index('ix_user_engagement_activity', 'last_activity'),
    )


class ProConVote(Base):
    """Track user votes on pro/con arguments"""
    __tablename__ = 'pro_con_votes'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pro_con_id = Column(UUID(as_uuid=True), ForeignKey('bill_pro_cons.id'), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    
    # Vote
    is_upvote = Column(Boolean, nullable=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    pro_con = relationship("BillProCon", backref="votes")
    user = relationship("User", backref="pro_con_votes")
    
    __table_args__ = (
        UniqueConstraint('pro_con_id', 'user_id', name='uq_procon_user_vote'),
        Index('ix_procon_vote_procon', 'pro_con_id'),
        Index('ix_procon_vote_user', 'user_id'),
    )


class CommentVote(Base):
    """Track user votes on comments"""
    __tablename__ = 'comment_votes'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    comment_id = Column(UUID(as_uuid=True), ForeignKey('bill_comments.id'), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    
    # Vote
    is_like = Column(Boolean, nullable=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    comment = relationship("BillComment", backref="votes")
    user = relationship("User", backref="comment_votes")
    
    __table_args__ = (
        UniqueConstraint('comment_id', 'user_id', name='uq_comment_user_vote'),
        Index('ix_comment_vote_comment', 'comment_id'),
        Index('ix_comment_vote_user', 'user_id'),
    )


class User(Base):
    """User model for citizen engagement"""
    __tablename__ = 'users'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Authentication
    email = Column(String(255), unique=True, nullable=False)
    username = Column(String(100), unique=True)
    password_hash = Column(String(255))
    
    # Profile
    full_name = Column(String(200))
    display_name = Column(String(100))
    avatar_url = Column(String(500))
    bio = Column(Text)
    
    # Location
    postal_code = Column(String(10))
    city = Column(String(100))
    province = Column(String(50))
    riding_federal = Column(String(100))
    riding_provincial = Column(String(100))
    
    # Verification
    email_verified = Column(Boolean, default=False)
    phone_verified = Column(Boolean, default=False)
    identity_verified = Column(Boolean, default=False)  # For official verification
    
    # Permissions
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    is_moderator = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)
    
    __table_args__ = (
        Index('ix_user_email', 'email'),
        Index('ix_user_username', 'username'),
        Index('ix_user_postal', 'postal_code'),
    )