"""
Feature Flag Service for OpenPolicy Platform
Supports both custom flags and LaunchDarkly integration
"""

import os
import json
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, asdict
import asyncio

import redis
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import launchdarkly_server_sdk as ld
from sqlalchemy import create_engine, Column, String, Boolean, JSON, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.postgresql import UUID

# Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/openpolicy_prod")
LAUNCHDARKLY_SDK_KEY = os.getenv("LAUNCHDARKLY_SDK_KEY", "")
SERVICE_PORT = int(os.getenv("SERVICE_PORT", "9024"))

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Redis setup
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

# LaunchDarkly setup
if LAUNCHDARKLY_SDK_KEY:
    ld.set_config(ld.Config(LAUNCHDARKLY_SDK_KEY))
    launchdarkly_client = ld.get()
else:
    launchdarkly_client = None
    logger.warning("LaunchDarkly SDK key not provided, using local flags only")

# FastAPI app
app = FastAPI(
    title="Feature Flag Service",
    description="Manage feature flags for OpenPolicy Platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class FlagType(str, Enum):
    BOOLEAN = "boolean"
    STRING = "string"
    NUMBER = "number"
    JSON = "json"

class FlagStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"

class TargetingRule(BaseModel):
    attribute: str
    operator: str  # eq, neq, in, nin, gt, lt, gte, lte, contains, regex
    values: List[Any]
    serve: Any

class FeatureFlag(Base):
    __tablename__ = "feature_flags"
    
    id = Column(UUID, primary_key=True, server_default="uuid_generate_v4()")
    key = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(String(1000))
    flag_type = Column(String(20), nullable=False, default=FlagType.BOOLEAN)
    default_value = Column(JSON, nullable=False)
    variations = Column(JSON)  # List of possible values
    targeting_rules = Column(JSON)  # List of TargetingRule objects
    percentage_rollout = Column(JSON)  # {variation_key: percentage}
    status = Column(String(20), nullable=False, default=FlagStatus.ACTIVE)
    tags = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(255))
    metadata = Column(JSON, default=dict)

class FlagContext(BaseModel):
    """Context for evaluating feature flags"""
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    user_role: Optional[str] = None
    organization_id: Optional[str] = None
    environment: str = "production"
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    custom_attributes: Dict[str, Any] = Field(default_factory=dict)

class FlagEvaluation(BaseModel):
    """Result of flag evaluation"""
    key: str
    value: Any
    variation_index: Optional[int] = None
    reason: str
    source: str  # "local" or "launchdarkly"

# Database initialization
Base.metadata.create_all(bind=engine)

# Dependencies
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Feature flag evaluation engine
class FlagEvaluator:
    @staticmethod
    def evaluate_rule(rule: TargetingRule, context: FlagContext) -> bool:
        """Evaluate a single targeting rule"""
        # Get attribute value from context
        if rule.attribute == "user_id":
            attr_value = context.user_id
        elif rule.attribute == "user_email":
            attr_value = context.user_email
        elif rule.attribute == "user_role":
            attr_value = context.user_role
        elif rule.attribute == "organization_id":
            attr_value = context.organization_id
        elif rule.attribute == "environment":
            attr_value = context.environment
        else:
            attr_value = context.custom_attributes.get(rule.attribute)
        
        # Apply operator
        if rule.operator == "eq":
            return attr_value == rule.values[0]
        elif rule.operator == "neq":
            return attr_value != rule.values[0]
        elif rule.operator == "in":
            return attr_value in rule.values
        elif rule.operator == "nin":
            return attr_value not in rule.values
        elif rule.operator == "gt":
            return float(attr_value) > float(rule.values[0])
        elif rule.operator == "lt":
            return float(attr_value) < float(rule.values[0])
        elif rule.operator == "gte":
            return float(attr_value) >= float(rule.values[0])
        elif rule.operator == "lte":
            return float(attr_value) <= float(rule.values[0])
        elif rule.operator == "contains":
            return rule.values[0] in str(attr_value)
        elif rule.operator == "regex":
            import re
            return bool(re.match(rule.values[0], str(attr_value)))
        
        return False
    
    @staticmethod
    def evaluate_percentage_rollout(flag: FeatureFlag, context: FlagContext) -> Any:
        """Evaluate percentage-based rollout"""
        if not flag.percentage_rollout:
            return flag.default_value
        
        # Generate consistent hash for user
        import hashlib
        user_key = context.user_id or context.user_email or "anonymous"
        hash_key = f"{flag.key}:{user_key}"
        hash_value = int(hashlib.md5(hash_key.encode()).hexdigest(), 16)
        bucket = hash_value % 100
        
        # Determine which variation to serve
        cumulative = 0
        for variation, percentage in flag.percentage_rollout.items():
            cumulative += percentage
            if bucket < cumulative:
                return variation
        
        return flag.default_value
    
    @staticmethod
    def evaluate_flag(flag: FeatureFlag, context: FlagContext) -> FlagEvaluation:
        """Evaluate a feature flag"""
        # Check if flag is active
        if flag.status != FlagStatus.ACTIVE:
            return FlagEvaluation(
                key=flag.key,
                value=flag.default_value,
                reason="Flag is not active",
                source="local"
            )
        
        # Evaluate targeting rules
        if flag.targeting_rules:
            for rule_data in flag.targeting_rules:
                rule = TargetingRule(**rule_data)
                if FlagEvaluator.evaluate_rule(rule, context):
                    return FlagEvaluation(
                        key=flag.key,
                        value=rule.serve,
                        reason=f"Matched rule: {rule.attribute} {rule.operator} {rule.values}",
                        source="local"
                    )
        
        # Evaluate percentage rollout
        if flag.percentage_rollout:
            value = FlagEvaluator.evaluate_percentage_rollout(flag, context)
            return FlagEvaluation(
                key=flag.key,
                value=value,
                reason="Percentage rollout",
                source="local"
            )
        
        # Return default value
        return FlagEvaluation(
            key=flag.key,
            value=flag.default_value,
            reason="Default value",
            source="local"
        )

# Cache management
class FlagCache:
    CACHE_TTL = 300  # 5 minutes
    
    @staticmethod
    def cache_key(flag_key: str, context_hash: str) -> str:
        return f"flag:{flag_key}:{context_hash}"
    
    @staticmethod
    def context_hash(context: FlagContext) -> str:
        """Generate hash for context"""
        import hashlib
        context_str = json.dumps(asdict(context), sort_keys=True)
        return hashlib.md5(context_str.encode()).hexdigest()[:8]
    
    @staticmethod
    def get(flag_key: str, context: FlagContext) -> Optional[Any]:
        """Get cached flag value"""
        cache_key = FlagCache.cache_key(flag_key, FlagCache.context_hash(context))
        cached = redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
        return None
    
    @staticmethod
    def set(flag_key: str, context: FlagContext, evaluation: FlagEvaluation):
        """Cache flag evaluation"""
        cache_key = FlagCache.cache_key(flag_key, FlagCache.context_hash(context))
        redis_client.setex(
            cache_key,
            FlagCache.CACHE_TTL,
            json.dumps(asdict(evaluation))
        )

# API Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "feature-flags",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/flags")
async def create_flag(
    flag_data: Dict[str, Any],
    db: Session = Depends(get_db),
    x_user_id: Optional[str] = Header(None)
):
    """Create a new feature flag"""
    flag = FeatureFlag(
        key=flag_data["key"],
        name=flag_data["name"],
        description=flag_data.get("description"),
        flag_type=flag_data.get("flag_type", FlagType.BOOLEAN),
        default_value=flag_data["default_value"],
        variations=flag_data.get("variations"),
        targeting_rules=flag_data.get("targeting_rules"),
        percentage_rollout=flag_data.get("percentage_rollout"),
        tags=flag_data.get("tags", []),
        created_by=x_user_id
    )
    
    db.add(flag)
    db.commit()
    db.refresh(flag)
    
    return {"flag": flag}

@app.get("/flags")
async def list_flags(
    status: Optional[FlagStatus] = None,
    tag: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all feature flags"""
    query = db.query(FeatureFlag)
    
    if status:
        query = query.filter(FeatureFlag.status == status)
    
    if tag:
        query = query.filter(FeatureFlag.tags.contains([tag]))
    
    flags = query.all()
    return {"flags": flags}

@app.get("/flags/{flag_key}")
async def get_flag(flag_key: str, db: Session = Depends(get_db)):
    """Get a specific feature flag"""
    flag = db.query(FeatureFlag).filter(FeatureFlag.key == flag_key).first()
    if not flag:
        raise HTTPException(status_code=404, detail="Flag not found")
    return {"flag": flag}

@app.put("/flags/{flag_key}")
async def update_flag(
    flag_key: str,
    flag_data: Dict[str, Any],
    db: Session = Depends(get_db),
    x_user_id: Optional[str] = Header(None)
):
    """Update a feature flag"""
    flag = db.query(FeatureFlag).filter(FeatureFlag.key == flag_key).first()
    if not flag:
        raise HTTPException(status_code=404, detail="Flag not found")
    
    # Update fields
    for key, value in flag_data.items():
        if hasattr(flag, key):
            setattr(flag, key, value)
    
    flag.updated_at = datetime.utcnow()
    db.commit()
    
    # Clear cache for this flag
    redis_client.delete(f"flag:{flag_key}:*")
    
    return {"flag": flag}

@app.post("/evaluate/{flag_key}")
async def evaluate_flag(
    flag_key: str,
    context: FlagContext,
    db: Session = Depends(get_db)
):
    """Evaluate a feature flag"""
    # Check cache first
    cached = FlagCache.get(flag_key, context)
    if cached:
        return FlagEvaluation(**cached)
    
    # Try LaunchDarkly first if available
    if launchdarkly_client and LAUNCHDARKLY_SDK_KEY:
        try:
            ld_context = {
                "key": context.user_id or "anonymous",
                "email": context.user_email,
                "custom": {
                    "role": context.user_role,
                    "organization": context.organization_id,
                    "environment": context.environment,
                    **context.custom_attributes
                }
            }
            
            value = launchdarkly_client.variation(flag_key, ld_context, None)
            if value is not None:
                evaluation = FlagEvaluation(
                    key=flag_key,
                    value=value,
                    reason="LaunchDarkly evaluation",
                    source="launchdarkly"
                )
                FlagCache.set(flag_key, context, evaluation)
                return evaluation
        except Exception as e:
            logger.error(f"LaunchDarkly evaluation failed: {e}")
    
    # Fall back to local evaluation
    flag = db.query(FeatureFlag).filter(FeatureFlag.key == flag_key).first()
    if not flag:
        raise HTTPException(status_code=404, detail="Flag not found")
    
    evaluation = FlagEvaluator.evaluate_flag(flag, context)
    FlagCache.set(flag_key, context, evaluation)
    
    return evaluation

@app.post("/evaluate/batch")
async def evaluate_batch(
    flag_keys: List[str],
    context: FlagContext,
    db: Session = Depends(get_db)
):
    """Evaluate multiple feature flags"""
    results = {}
    
    for flag_key in flag_keys:
        try:
            evaluation = await evaluate_flag(flag_key, context, db)
            results[flag_key] = evaluation
        except HTTPException:
            results[flag_key] = FlagEvaluation(
                key=flag_key,
                value=None,
                reason="Flag not found",
                source="local"
            )
    
    return {"evaluations": results}

@app.post("/flags/{flag_key}/archive")
async def archive_flag(flag_key: str, db: Session = Depends(get_db)):
    """Archive a feature flag"""
    flag = db.query(FeatureFlag).filter(FeatureFlag.key == flag_key).first()
    if not flag:
        raise HTTPException(status_code=404, detail="Flag not found")
    
    flag.status = FlagStatus.ARCHIVED
    flag.updated_at = datetime.utcnow()
    db.commit()
    
    # Clear cache
    redis_client.delete(f"flag:{flag_key}:*")
    
    return {"message": "Flag archived successfully"}

@app.get("/metrics")
async def get_metrics(db: Session = Depends(get_db)):
    """Get feature flag metrics"""
    total_flags = db.query(FeatureFlag).count()
    active_flags = db.query(FeatureFlag).filter(FeatureFlag.status == FlagStatus.ACTIVE).count()
    
    # Get evaluation metrics from Redis
    evaluation_count = redis_client.get("metrics:evaluations:total") or 0
    cache_hits = redis_client.get("metrics:cache:hits") or 0
    cache_misses = redis_client.get("metrics:cache:misses") or 0
    
    return {
        "total_flags": total_flags,
        "active_flags": active_flags,
        "evaluations": {
            "total": int(evaluation_count),
            "cache_hit_rate": float(cache_hits) / (float(cache_hits) + float(cache_misses)) if cache_hits else 0
        }
    }

# Webhook for LaunchDarkly updates
@app.post("/webhooks/launchdarkly")
async def launchdarkly_webhook(payload: Dict[str, Any]):
    """Handle LaunchDarkly webhook events"""
    event_type = payload.get("kind")
    
    if event_type == "flag":
        # Clear cache for updated flag
        flag_key = payload.get("key")
        if flag_key:
            redis_client.delete(f"flag:{flag_key}:*")
            logger.info(f"Cleared cache for flag: {flag_key}")
    
    return {"status": "processed"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=SERVICE_PORT)