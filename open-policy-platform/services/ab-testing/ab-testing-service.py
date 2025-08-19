"""
A/B Testing Service for OpenPolicy Platform
Manages experiments, variants, and statistical analysis
"""

import os
import json
import logging
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, asdict
import numpy as np
from scipy import stats
import hashlib

from fastapi import FastAPI, HTTPException, Depends, Header, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, String, Float, Integer, Boolean, JSON, DateTime, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.dialects.postgresql import UUID
import redis

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/openpolicy_prod")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
SERVICE_PORT = int(os.getenv("SERVICE_PORT", "9025"))
FEATURE_FLAG_SERVICE = os.getenv("FEATURE_FLAG_SERVICE", "http://feature-flags:9024")

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Redis setup
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

# FastAPI app
app = FastAPI(
    title="A/B Testing Service",
    description="Manage A/B tests and experiments for OpenPolicy Platform",
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
class ExperimentStatus(str, Enum):
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"

class ExperimentType(str, Enum):
    AB = "ab"  # Simple A/B
    MULTIVARIATE = "multivariate"  # Multiple variants
    SPLIT_URL = "split_url"  # Different URLs
    FEATURE = "feature"  # Feature flag based

class MetricType(str, Enum):
    CONVERSION = "conversion"  # Binary (converted/not converted)
    CONTINUOUS = "continuous"  # Numeric value (e.g., revenue)
    COUNT = "count"  # Count of events
    DURATION = "duration"  # Time-based

class Experiment(Base):
    __tablename__ = "experiments"
    
    id = Column(UUID, primary_key=True, server_default="uuid_generate_v4()")
    key = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(String(1000))
    hypothesis = Column(String(1000))
    experiment_type = Column(String(20), nullable=False, default=ExperimentType.AB)
    status = Column(String(20), nullable=False, default=ExperimentStatus.DRAFT)
    
    # Targeting
    audience_percentage = Column(Float, default=100.0)  # % of users to include
    audience_criteria = Column(JSON)  # Additional targeting rules
    
    # Schedule
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    
    # Statistics
    min_sample_size = Column(Integer)  # Minimum sample size per variant
    confidence_level = Column(Float, default=0.95)  # Statistical confidence
    
    # Metadata
    created_by = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    tags = Column(JSON, default=list)
    metadata = Column(JSON, default=dict)
    
    # Relationships
    variants = relationship("Variant", back_populates="experiment", cascade="all, delete-orphan")
    metrics = relationship("Metric", back_populates="experiment", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_experiment_status', 'status'),
        Index('idx_experiment_dates', 'start_date', 'end_date'),
    )

class Variant(Base):
    __tablename__ = "variants"
    
    id = Column(UUID, primary_key=True, server_default="uuid_generate_v4()")
    experiment_id = Column(UUID, ForeignKey("experiments.id"), nullable=False)
    key = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(String(500))
    
    # Allocation
    allocation_percentage = Column(Float, nullable=False)  # % of experiment traffic
    is_control = Column(Boolean, default=False)
    
    # Configuration
    config = Column(JSON, default=dict)  # Variant-specific configuration
    feature_flags = Column(JSON, default=dict)  # Feature flag overrides
    
    # Relationships
    experiment = relationship("Experiment", back_populates="variants")
    
    # Constraints
    __table_args__ = (
        Index('idx_variant_experiment', 'experiment_id'),
        Index('idx_variant_key', 'experiment_id', 'key', unique=True),
    )

class Metric(Base):
    __tablename__ = "experiment_metrics"
    
    id = Column(UUID, primary_key=True, server_default="uuid_generate_v4()")
    experiment_id = Column(UUID, ForeignKey("experiments.id"), nullable=False)
    key = Column(String(100), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(String(500))
    
    metric_type = Column(String(20), nullable=False, default=MetricType.CONVERSION)
    is_primary = Column(Boolean, default=False)  # Primary success metric
    
    # Goal settings
    improvement_direction = Column(String(10), default="increase")  # increase/decrease
    minimum_detectable_effect = Column(Float)  # MDE for sample size calculation
    
    # Relationships
    experiment = relationship("Experiment", back_populates="metrics")
    
    __table_args__ = (
        Index('idx_metric_experiment', 'experiment_id'),
    )

class Assignment(Base):
    __tablename__ = "experiment_assignments"
    
    id = Column(UUID, primary_key=True, server_default="uuid_generate_v4()")
    experiment_id = Column(UUID, nullable=False, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    variant_key = Column(String(50), nullable=False)
    assigned_at = Column(DateTime, default=datetime.utcnow)
    
    # Prevent reassignment
    __table_args__ = (
        Index('idx_assignment_unique', 'experiment_id', 'user_id', unique=True),
    )

class Event(Base):
    __tablename__ = "experiment_events"
    
    id = Column(UUID, primary_key=True, server_default="uuid_generate_v4()")
    experiment_id = Column(UUID, nullable=False, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    variant_key = Column(String(50), nullable=False)
    metric_key = Column(String(100), nullable=False)
    
    # Event data
    value = Column(Float, default=1.0)  # For conversion: 1 or 0, for continuous: actual value
    metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

# Create tables
Base.metadata.create_all(bind=engine)

# Pydantic models
class ExperimentContext(BaseModel):
    user_id: str
    user_attributes: Dict[str, Any] = Field(default_factory=dict)

class VariantAssignment(BaseModel):
    experiment_key: str
    variant_key: str
    variant_config: Dict[str, Any]
    is_control: bool

class ExperimentResults(BaseModel):
    experiment_id: str
    status: str
    variants: List[Dict[str, Any]]
    primary_metric: Optional[Dict[str, Any]]
    secondary_metrics: List[Dict[str, Any]]
    statistical_significance: Optional[float]
    winner: Optional[str]
    confidence_interval: Optional[Tuple[float, float]]

# Statistical analysis functions
class StatisticalAnalyzer:
    @staticmethod
    def calculate_sample_size(
        baseline_rate: float,
        minimum_detectable_effect: float,
        alpha: float = 0.05,
        power: float = 0.8
    ) -> int:
        """Calculate required sample size for statistical significance"""
        from statsmodels.stats.power import NormalIndPower
        
        power_analysis = NormalIndPower()
        effect_size = minimum_detectable_effect / baseline_rate
        sample_size = power_analysis.solve_power(
            effect_size=effect_size,
            alpha=alpha,
            power=power
        )
        
        return int(np.ceil(sample_size))
    
    @staticmethod
    def perform_ab_test(
        control_conversions: int,
        control_total: int,
        variant_conversions: int,
        variant_total: int
    ) -> Dict[str, Any]:
        """Perform statistical test for A/B experiment"""
        # Conversion rates
        control_rate = control_conversions / control_total if control_total > 0 else 0
        variant_rate = variant_conversions / variant_total if variant_total > 0 else 0
        
        # Pooled probability
        pooled_prob = (control_conversions + variant_conversions) / (control_total + variant_total)
        pooled_se = np.sqrt(pooled_prob * (1 - pooled_prob) * (1/control_total + 1/variant_total))
        
        # Z-score
        z_score = (variant_rate - control_rate) / pooled_se if pooled_se > 0 else 0
        
        # P-value (two-tailed)
        p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))
        
        # Confidence interval
        se_diff = np.sqrt(
            control_rate * (1 - control_rate) / control_total +
            variant_rate * (1 - variant_rate) / variant_total
        )
        ci_lower = (variant_rate - control_rate) - 1.96 * se_diff
        ci_upper = (variant_rate - control_rate) + 1.96 * se_diff
        
        # Relative improvement
        relative_improvement = ((variant_rate - control_rate) / control_rate * 100) if control_rate > 0 else 0
        
        return {
            "control_rate": control_rate,
            "variant_rate": variant_rate,
            "relative_improvement": relative_improvement,
            "p_value": p_value,
            "is_significant": p_value < 0.05,
            "z_score": z_score,
            "confidence_interval": (ci_lower, ci_upper)
        }
    
    @staticmethod
    def perform_multivariate_test(
        variant_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Perform statistical test for multivariate experiment"""
        # Chi-square test for multiple proportions
        observed = []
        expected = []
        
        total_conversions = sum(v["conversions"] for v in variant_data)
        total_visitors = sum(v["visitors"] for v in variant_data)
        overall_rate = total_conversions / total_visitors if total_visitors > 0 else 0
        
        for variant in variant_data:
            observed.append([variant["conversions"], variant["visitors"] - variant["conversions"]])
            expected_conversions = variant["visitors"] * overall_rate
            expected.append([expected_conversions, variant["visitors"] - expected_conversions])
        
        chi2, p_value = stats.chi2_contingency(observed)[:2]
        
        return {
            "chi_squared": chi2,
            "p_value": p_value,
            "is_significant": p_value < 0.05,
            "overall_conversion_rate": overall_rate
        }

# Assignment logic
class ExperimentAssigner:
    @staticmethod
    def should_include_in_experiment(
        experiment: Experiment,
        context: ExperimentContext
    ) -> bool:
        """Check if user should be included in experiment"""
        # Check audience percentage
        user_hash = int(hashlib.md5(f"{experiment.id}:{context.user_id}".encode()).hexdigest(), 16)
        if (user_hash % 100) >= experiment.audience_percentage:
            return False
        
        # Check audience criteria
        if experiment.audience_criteria:
            for criterion in experiment.audience_criteria:
                attr_name = criterion.get("attribute")
                operator = criterion.get("operator")
                value = criterion.get("value")
                
                user_value = context.user_attributes.get(attr_name)
                
                if operator == "equals" and user_value != value:
                    return False
                elif operator == "contains" and value not in str(user_value):
                    return False
                elif operator == "greater_than" and float(user_value) <= float(value):
                    return False
                elif operator == "less_than" and float(user_value) >= float(value):
                    return False
        
        return True
    
    @staticmethod
    def assign_variant(
        experiment: Experiment,
        context: ExperimentContext,
        variants: List[Variant]
    ) -> Variant:
        """Assign user to variant based on allocation"""
        # Generate consistent hash
        assignment_hash = int(
            hashlib.md5(f"{experiment.id}:{context.user_id}:variant".encode()).hexdigest(), 16
        )
        bucket = assignment_hash % 100
        
        # Assign based on allocation percentages
        cumulative = 0
        for variant in sorted(variants, key=lambda v: v.key):
            cumulative += variant.allocation_percentage
            if bucket < cumulative:
                return variant
        
        # Fallback to control
        return next((v for v in variants if v.is_control), variants[0])

# Dependencies
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# API Endpoints
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "ab-testing",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/experiments")
async def create_experiment(
    experiment_data: Dict[str, Any],
    db: Session = Depends(get_db),
    x_user_id: Optional[str] = Header(None)
):
    """Create a new experiment"""
    # Create experiment
    experiment = Experiment(
        key=experiment_data["key"],
        name=experiment_data["name"],
        description=experiment_data.get("description"),
        hypothesis=experiment_data.get("hypothesis"),
        experiment_type=experiment_data.get("experiment_type", ExperimentType.AB),
        audience_percentage=experiment_data.get("audience_percentage", 100.0),
        audience_criteria=experiment_data.get("audience_criteria"),
        start_date=experiment_data.get("start_date"),
        end_date=experiment_data.get("end_date"),
        min_sample_size=experiment_data.get("min_sample_size"),
        confidence_level=experiment_data.get("confidence_level", 0.95),
        created_by=x_user_id,
        tags=experiment_data.get("tags", [])
    )
    
    db.add(experiment)
    db.flush()
    
    # Create variants
    for variant_data in experiment_data.get("variants", []):
        variant = Variant(
            experiment_id=experiment.id,
            key=variant_data["key"],
            name=variant_data["name"],
            description=variant_data.get("description"),
            allocation_percentage=variant_data["allocation_percentage"],
            is_control=variant_data.get("is_control", False),
            config=variant_data.get("config", {}),
            feature_flags=variant_data.get("feature_flags", {})
        )
        db.add(variant)
    
    # Create metrics
    for metric_data in experiment_data.get("metrics", []):
        metric = Metric(
            experiment_id=experiment.id,
            key=metric_data["key"],
            name=metric_data["name"],
            description=metric_data.get("description"),
            metric_type=metric_data.get("metric_type", MetricType.CONVERSION),
            is_primary=metric_data.get("is_primary", False),
            improvement_direction=metric_data.get("improvement_direction", "increase"),
            minimum_detectable_effect=metric_data.get("minimum_detectable_effect")
        )
        db.add(metric)
    
    db.commit()
    db.refresh(experiment)
    
    return {"experiment": experiment}

@app.get("/experiments")
async def list_experiments(
    status: Optional[ExperimentStatus] = None,
    tag: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List experiments"""
    query = db.query(Experiment)
    
    if status:
        query = query.filter(Experiment.status == status)
    
    if tag:
        query = query.filter(Experiment.tags.contains([tag]))
    
    experiments = query.all()
    return {"experiments": experiments}

@app.get("/experiments/{experiment_key}")
async def get_experiment(
    experiment_key: str,
    db: Session = Depends(get_db)
):
    """Get experiment details"""
    experiment = db.query(Experiment).filter(
        Experiment.key == experiment_key
    ).first()
    
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    return {
        "experiment": experiment,
        "variants": experiment.variants,
        "metrics": experiment.metrics
    }

@app.post("/assign/{experiment_key}")
async def assign_variant(
    experiment_key: str,
    context: ExperimentContext,
    db: Session = Depends(get_db)
):
    """Assign user to experiment variant"""
    # Get experiment
    experiment = db.query(Experiment).filter(
        Experiment.key == experiment_key,
        Experiment.status == ExperimentStatus.RUNNING
    ).first()
    
    if not experiment:
        raise HTTPException(status_code=404, detail="Active experiment not found")
    
    # Check if already assigned
    existing = db.query(Assignment).filter(
        Assignment.experiment_id == experiment.id,
        Assignment.user_id == context.user_id
    ).first()
    
    if existing:
        # Return existing assignment
        variant = next(v for v in experiment.variants if v.key == existing.variant_key)
        return VariantAssignment(
            experiment_key=experiment_key,
            variant_key=variant.key,
            variant_config=variant.config,
            is_control=variant.is_control
        )
    
    # Check if user should be in experiment
    if not ExperimentAssigner.should_include_in_experiment(experiment, context):
        # Return control variant
        control = next((v for v in experiment.variants if v.is_control), experiment.variants[0])
        return VariantAssignment(
            experiment_key=experiment_key,
            variant_key=control.key,
            variant_config=control.config,
            is_control=True
        )
    
    # Assign variant
    variant = ExperimentAssigner.assign_variant(experiment, context, experiment.variants)
    
    # Save assignment
    assignment = Assignment(
        experiment_id=experiment.id,
        user_id=context.user_id,
        variant_key=variant.key
    )
    db.add(assignment)
    db.commit()
    
    # Cache assignment
    cache_key = f"assignment:{experiment_key}:{context.user_id}"
    redis_client.setex(cache_key, 86400, variant.key)  # 24 hour cache
    
    return VariantAssignment(
        experiment_key=experiment_key,
        variant_key=variant.key,
        variant_config=variant.config,
        is_control=variant.is_control
    )

@app.post("/track/{experiment_key}")
async def track_event(
    experiment_key: str,
    event_data: Dict[str, Any],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Track experiment event"""
    # Get experiment
    experiment = db.query(Experiment).filter(
        Experiment.key == experiment_key
    ).first()
    
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    # Get user's assignment
    user_id = event_data["user_id"]
    assignment = db.query(Assignment).filter(
        Assignment.experiment_id == experiment.id,
        Assignment.user_id == user_id
    ).first()
    
    if not assignment:
        raise HTTPException(status_code=400, detail="User not assigned to experiment")
    
    # Record event
    event = Event(
        experiment_id=experiment.id,
        user_id=user_id,
        variant_key=assignment.variant_key,
        metric_key=event_data["metric_key"],
        value=event_data.get("value", 1.0),
        metadata=event_data.get("metadata", {})
    )
    db.add(event)
    db.commit()
    
    # Update real-time metrics in background
    background_tasks.add_task(update_experiment_metrics, experiment.id, event_data["metric_key"])
    
    return {"status": "tracked"}

async def update_experiment_metrics(experiment_id: str, metric_key: str):
    """Update cached experiment metrics"""
    # This would update real-time dashboards
    cache_key = f"metrics:{experiment_id}:{metric_key}"
    redis_client.incr(cache_key)

@app.get("/results/{experiment_key}")
async def get_experiment_results(
    experiment_key: str,
    db: Session = Depends(get_db)
):
    """Get experiment results and analysis"""
    # Get experiment
    experiment = db.query(Experiment).filter(
        Experiment.key == experiment_key
    ).first()
    
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    # Get primary metric
    primary_metric = next((m for m in experiment.metrics if m.is_primary), None)
    if not primary_metric:
        raise HTTPException(status_code=400, detail="No primary metric defined")
    
    # Calculate results for each variant
    variant_results = []
    
    for variant in experiment.variants:
        # Get assignments
        assignments = db.query(Assignment).filter(
            Assignment.experiment_id == experiment.id,
            Assignment.variant_key == variant.key
        ).count()
        
        # Get conversions
        conversions = db.query(Event).filter(
            Event.experiment_id == experiment.id,
            Event.variant_key == variant.key,
            Event.metric_key == primary_metric.key,
            Event.value > 0
        ).count()
        
        variant_results.append({
            "variant_key": variant.key,
            "variant_name": variant.name,
            "is_control": variant.is_control,
            "visitors": assignments,
            "conversions": conversions,
            "conversion_rate": conversions / assignments if assignments > 0 else 0
        })
    
    # Perform statistical analysis
    control_data = next(v for v in variant_results if v["is_control"])
    
    analysis_results = []
    winner = None
    max_improvement = 0
    
    for variant_data in variant_results:
        if not variant_data["is_control"]:
            analysis = StatisticalAnalyzer.perform_ab_test(
                control_conversions=control_data["conversions"],
                control_total=control_data["visitors"],
                variant_conversions=variant_data["conversions"],
                variant_total=variant_data["visitors"]
            )
            
            variant_data.update(analysis)
            
            if analysis["is_significant"] and analysis["relative_improvement"] > max_improvement:
                winner = variant_data["variant_key"]
                max_improvement = analysis["relative_improvement"]
        else:
            variant_data.update({
                "relative_improvement": 0,
                "p_value": 1.0,
                "is_significant": False,
                "confidence_interval": (0, 0)
            })
    
    return ExperimentResults(
        experiment_id=str(experiment.id),
        status=experiment.status,
        variants=variant_results,
        primary_metric={
            "key": primary_metric.key,
            "name": primary_metric.name,
            "type": primary_metric.metric_type
        },
        secondary_metrics=[],  # TODO: Add secondary metrics
        statistical_significance=min(v.get("p_value", 1) for v in variant_results),
        winner=winner,
        confidence_interval=None  # TODO: Add overall confidence interval
    )

@app.put("/experiments/{experiment_key}/status")
async def update_experiment_status(
    experiment_key: str,
    status_data: Dict[str, str],
    db: Session = Depends(get_db)
):
    """Update experiment status"""
    experiment = db.query(Experiment).filter(
        Experiment.key == experiment_key
    ).first()
    
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    new_status = status_data["status"]
    
    # Validate status transition
    if experiment.status == ExperimentStatus.COMPLETED and new_status != ExperimentStatus.ARCHIVED:
        raise HTTPException(status_code=400, detail="Completed experiments can only be archived")
    
    experiment.status = new_status
    experiment.updated_at = datetime.utcnow()
    
    db.commit()
    
    return {"status": "updated"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=SERVICE_PORT)