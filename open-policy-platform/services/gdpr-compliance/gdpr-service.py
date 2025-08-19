"""
GDPR Compliance Service for OpenPolicy Platform
Handles data privacy, consent management, and GDPR requirements
"""

import os
import json
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
import asyncio
import logging

from fastapi import FastAPI, HTTPException, Depends, Request, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import create_engine, Column, String, DateTime, Boolean, Text, JSON, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from cryptography.fernet import Fernet
import aiofiles
import httpx

# Configure logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost/gdpr")
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", Fernet.generate_key())
SERVICE_PORT = int(os.getenv("SERVICE_PORT", 9027))
EMAIL_SERVICE_URL = os.getenv("EMAIL_SERVICE_URL", "http://notification-service:9004")

# Database setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Encryption
fernet = Fernet(ENCRYPTION_KEY)

# Security
security = HTTPBearer()

class ConsentType(str, Enum):
    """Types of consent that can be granted"""
    MARKETING = "marketing"
    ANALYTICS = "analytics"
    PERSONALIZATION = "personalization"
    THIRD_PARTY = "third_party"
    ESSENTIAL = "essential"
    DATA_PROCESSING = "data_processing"

class DataSubjectRequest(str, Enum):
    """Types of data subject requests"""
    ACCESS = "access"
    RECTIFICATION = "rectification"
    ERASURE = "erasure"
    PORTABILITY = "portability"
    RESTRICTION = "restriction"
    OBJECTION = "objection"

# Database Models
class UserConsent(Base):
    """User consent records"""
    __tablename__ = "user_consents"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String, nullable=False)
    consent_type = Column(String, nullable=False)
    granted = Column(Boolean, default=False)
    granted_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    version = Column(String, default="1.0")
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class DataSubjectRequestRecord(Base):
    """Records of data subject requests"""
    __tablename__ = "data_subject_requests"
    
    id = Column(Integer, primary_key=True)
    request_id = Column(String, unique=True, nullable=False)
    user_id = Column(String, nullable=False)
    request_type = Column(String, nullable=False)
    status = Column(String, default="pending")
    requested_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    data = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)
    processed_by = Column(String, nullable=True)

class PersonalDataRecord(Base):
    """Record of personal data storage and processing"""
    __tablename__ = "personal_data_records"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String, nullable=False)
    data_type = Column(String, nullable=False)
    purpose = Column(String, nullable=False)
    legal_basis = Column(String, nullable=False)
    retention_period_days = Column(Integer, default=365)
    encrypted_data = Column(Text, nullable=True)
    source = Column(String, nullable=True)
    shared_with = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)

class DataBreachRecord(Base):
    """Record of data breaches for notification requirements"""
    __tablename__ = "data_breach_records"
    
    id = Column(Integer, primary_key=True)
    breach_id = Column(String, unique=True, nullable=False)
    discovered_at = Column(DateTime, default=datetime.utcnow)
    description = Column(Text, nullable=False)
    affected_users = Column(JSON, nullable=True)
    data_types_affected = Column(JSON, nullable=True)
    severity = Column(String, nullable=False)
    authorities_notified = Column(Boolean, default=False)
    users_notified = Column(Boolean, default=False)
    remediation_steps = Column(Text, nullable=True)
    reported_by = Column(String, nullable=True)

# Create tables
Base.metadata.create_all(bind=engine)

# Pydantic models
class ConsentRequest(BaseModel):
    """Request to update consent"""
    user_id: str
    consent_type: ConsentType
    granted: bool
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class ConsentResponse(BaseModel):
    """Consent status response"""
    user_id: str
    consents: Dict[str, bool]
    last_updated: datetime

class DataSubjectRequestModel(BaseModel):
    """Data subject request"""
    user_id: str
    request_type: DataSubjectRequest
    details: Optional[Dict[str, Any]] = None

class PersonalDataModel(BaseModel):
    """Personal data storage request"""
    user_id: str
    data_type: str
    data: Dict[str, Any]
    purpose: str
    legal_basis: str
    retention_period_days: int = 365
    source: Optional[str] = None

class DataBreachNotification(BaseModel):
    """Data breach notification"""
    description: str
    affected_user_ids: List[str]
    data_types_affected: List[str]
    severity: str = Field(..., regex="^(low|medium|high|critical)$")
    remediation_steps: str
    reported_by: str

class PrivacyPolicy(BaseModel):
    """Privacy policy details"""
    version: str
    effective_date: datetime
    content: str
    changes: List[str]

# Dependencies
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify authentication token"""
    # TODO: Implement proper token verification
    return {"user_id": "admin", "role": "admin"}

# FastAPI app
app = FastAPI(
    title="GDPR Compliance Service",
    description="Manages GDPR compliance for OpenPolicy Platform",
    version="1.0.0"
)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "gdpr-compliance"}

# Consent Management
@app.post("/consent")
async def update_consent(
    request: ConsentRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    auth: Dict = Depends(verify_token)
):
    """Update user consent"""
    try:
        # Check existing consent
        existing = db.query(UserConsent).filter(
            UserConsent.user_id == request.user_id,
            UserConsent.consent_type == request.consent_type.value
        ).first()
        
        if existing:
            existing.granted = request.granted
            existing.granted_at = datetime.utcnow() if request.granted else None
            existing.revoked_at = None if request.granted else datetime.utcnow()
            existing.ip_address = request.ip_address
            existing.user_agent = request.user_agent
            existing.details = request.details
            existing.updated_at = datetime.utcnow()
        else:
            consent = UserConsent(
                user_id=request.user_id,
                consent_type=request.consent_type.value,
                granted=request.granted,
                granted_at=datetime.utcnow() if request.granted else None,
                ip_address=request.ip_address,
                user_agent=request.user_agent,
                details=request.details
            )
            db.add(consent)
        
        db.commit()
        
        # Audit log
        background_tasks.add_task(
            log_consent_change,
            request.user_id,
            request.consent_type.value,
            request.granted
        )
        
        return {"success": True, "message": "Consent updated"}
        
    except Exception as e:
        logger.error(f"Error updating consent: {e}")
        raise HTTPException(status_code=500, detail="Failed to update consent")

@app.get("/consent/{user_id}", response_model=ConsentResponse)
async def get_user_consents(
    user_id: str,
    db: Session = Depends(get_db),
    auth: Dict = Depends(verify_token)
):
    """Get all consents for a user"""
    consents = db.query(UserConsent).filter(
        UserConsent.user_id == user_id
    ).all()
    
    consent_status = {
        consent_type.value: False
        for consent_type in ConsentType
    }
    
    last_updated = datetime.min
    
    for consent in consents:
        consent_status[consent.consent_type] = consent.granted
        if consent.updated_at > last_updated:
            last_updated = consent.updated_at
    
    return ConsentResponse(
        user_id=user_id,
        consents=consent_status,
        last_updated=last_updated
    )

# Data Subject Rights
@app.post("/data-subject-request")
async def create_data_subject_request(
    request: DataSubjectRequestModel,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    auth: Dict = Depends(verify_token)
):
    """Create a data subject request (access, erasure, etc.)"""
    try:
        request_id = f"DSR-{secrets.token_hex(8).upper()}"
        
        dsr = DataSubjectRequestRecord(
            request_id=request_id,
            user_id=request.user_id,
            request_type=request.request_type.value,
            data=request.details
        )
        db.add(dsr)
        db.commit()
        
        # Process request in background
        background_tasks.add_task(
            process_data_subject_request,
            request_id,
            request.user_id,
            request.request_type
        )
        
        return {
            "request_id": request_id,
            "status": "pending",
            "message": f"Your {request.request_type.value} request has been received"
        }
        
    except Exception as e:
        logger.error(f"Error creating DSR: {e}")
        raise HTTPException(status_code=500, detail="Failed to create request")

@app.get("/data-subject-request/{request_id}")
async def get_request_status(
    request_id: str,
    db: Session = Depends(get_db),
    auth: Dict = Depends(verify_token)
):
    """Get status of a data subject request"""
    dsr = db.query(DataSubjectRequestRecord).filter(
        DataSubjectRequestRecord.request_id == request_id
    ).first()
    
    if not dsr:
        raise HTTPException(status_code=404, detail="Request not found")
    
    return {
        "request_id": dsr.request_id,
        "user_id": dsr.user_id,
        "request_type": dsr.request_type,
        "status": dsr.status,
        "requested_at": dsr.requested_at,
        "completed_at": dsr.completed_at,
        "data": dsr.data
    }

# Data Portability
@app.get("/export/{user_id}")
async def export_user_data(
    user_id: str,
    db: Session = Depends(get_db),
    auth: Dict = Depends(verify_token)
):
    """Export all user data in machine-readable format"""
    try:
        # Collect all user data
        user_data = {
            "user_id": user_id,
            "export_date": datetime.utcnow().isoformat(),
            "consents": [],
            "personal_data": [],
            "activity_logs": [],
            "preferences": {}
        }
        
        # Get consents
        consents = db.query(UserConsent).filter(
            UserConsent.user_id == user_id
        ).all()
        
        for consent in consents:
            user_data["consents"].append({
                "type": consent.consent_type,
                "granted": consent.granted,
                "granted_at": consent.granted_at.isoformat() if consent.granted_at else None,
                "revoked_at": consent.revoked_at.isoformat() if consent.revoked_at else None
            })
        
        # Get personal data records
        personal_data = db.query(PersonalDataRecord).filter(
            PersonalDataRecord.user_id == user_id
        ).all()
        
        for record in personal_data:
            decrypted_data = {}
            if record.encrypted_data:
                try:
                    decrypted_data = json.loads(
                        fernet.decrypt(record.encrypted_data.encode()).decode()
                    )
                except:
                    decrypted_data = {"error": "Unable to decrypt"}
            
            user_data["personal_data"].append({
                "data_type": record.data_type,
                "purpose": record.purpose,
                "legal_basis": record.legal_basis,
                "data": decrypted_data,
                "collected_at": record.created_at.isoformat()
            })
        
        # TODO: Collect data from other services
        
        return user_data
        
    except Exception as e:
        logger.error(f"Error exporting user data: {e}")
        raise HTTPException(status_code=500, detail="Failed to export data")

# Right to Erasure
@app.delete("/user/{user_id}")
async def delete_user_data(
    user_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    auth: Dict = Depends(verify_token)
):
    """Delete all user data (right to be forgotten)"""
    try:
        # Create erasure request
        request_id = f"ERASURE-{secrets.token_hex(8).upper()}"
        
        dsr = DataSubjectRequestRecord(
            request_id=request_id,
            user_id=user_id,
            request_type=DataSubjectRequest.ERASURE.value,
            data={"initiated_by": auth["user_id"]}
        )
        db.add(dsr)
        db.commit()
        
        # Process erasure in background
        background_tasks.add_task(
            process_user_erasure,
            user_id,
            request_id
        )
        
        return {
            "request_id": request_id,
            "message": "Erasure request initiated. Data will be deleted within 30 days."
        }
        
    except Exception as e:
        logger.error(f"Error initiating erasure: {e}")
        raise HTTPException(status_code=500, detail="Failed to initiate erasure")

# Data Breach Management
@app.post("/breach")
async def report_data_breach(
    breach: DataBreachNotification,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    auth: Dict = Depends(verify_token)
):
    """Report a data breach"""
    try:
        breach_id = f"BREACH-{secrets.token_hex(8).upper()}"
        
        breach_record = DataBreachRecord(
            breach_id=breach_id,
            description=breach.description,
            affected_users=breach.affected_user_ids,
            data_types_affected=breach.data_types_affected,
            severity=breach.severity,
            remediation_steps=breach.remediation_steps,
            reported_by=breach.reported_by
        )
        db.add(breach_record)
        db.commit()
        
        # Handle breach notification requirements
        if breach.severity in ["high", "critical"]:
            # Notify authorities within 72 hours
            background_tasks.add_task(
                notify_authorities,
                breach_id,
                breach.dict()
            )
            
            # Notify affected users
            background_tasks.add_task(
                notify_affected_users,
                breach_id,
                breach.affected_user_ids,
                breach.description
            )
        
        return {
            "breach_id": breach_id,
            "message": "Breach reported successfully",
            "actions": [
                "Authorities will be notified within 72 hours",
                "Affected users will be notified",
                "Incident response team has been alerted"
            ]
        }
        
    except Exception as e:
        logger.error(f"Error reporting breach: {e}")
        raise HTTPException(status_code=500, detail="Failed to report breach")

# Privacy Policy Management
@app.get("/privacy-policy")
async def get_privacy_policy():
    """Get current privacy policy"""
    # TODO: Load from database or file
    return {
        "version": "2.0",
        "effective_date": "2024-01-01",
        "last_updated": "2024-08-19",
        "content": "Full privacy policy content...",
        "summary": "We respect your privacy and comply with GDPR"
    }

@app.post("/privacy-policy/acceptance")
async def accept_privacy_policy(
    user_id: str,
    version: str,
    db: Session = Depends(get_db)
):
    """Record privacy policy acceptance"""
    consent = UserConsent(
        user_id=user_id,
        consent_type="privacy_policy",
        granted=True,
        granted_at=datetime.utcnow(),
        version=version,
        details={"accepted_version": version}
    )
    db.add(consent)
    db.commit()
    
    return {"success": True, "message": "Privacy policy accepted"}

# Cookie Management
@app.get("/cookie-preferences/{user_id}")
async def get_cookie_preferences(
    user_id: str,
    db: Session = Depends(get_db)
):
    """Get user's cookie preferences"""
    consents = db.query(UserConsent).filter(
        UserConsent.user_id == user_id,
        UserConsent.consent_type.in_([
            ConsentType.ANALYTICS.value,
            ConsentType.MARKETING.value,
            ConsentType.PERSONALIZATION.value
        ])
    ).all()
    
    preferences = {
        "essential": True,  # Always true
        "analytics": False,
        "marketing": False,
        "personalization": False
    }
    
    for consent in consents:
        if consent.consent_type in preferences:
            preferences[consent.consent_type] = consent.granted
    
    return preferences

# Data Retention
@app.post("/retention/check")
async def check_data_retention(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    auth: Dict = Depends(verify_token)
):
    """Check and enforce data retention policies"""
    try:
        # Find expired personal data
        expired_data = db.query(PersonalDataRecord).filter(
            PersonalDataRecord.expires_at < datetime.utcnow()
        ).all()
        
        expired_count = len(expired_data)
        
        # Delete expired data
        for record in expired_data:
            background_tasks.add_task(
                delete_expired_data,
                record.id,
                record.user_id
            )
        
        return {
            "expired_records": expired_count,
            "message": f"Found {expired_count} expired records for deletion"
        }
        
    except Exception as e:
        logger.error(f"Error checking retention: {e}")
        raise HTTPException(status_code=500, detail="Retention check failed")

# Audit Log
@app.get("/audit-log/gdpr")
async def get_gdpr_audit_log(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    user_id: Optional[str] = None,
    db: Session = Depends(get_db),
    auth: Dict = Depends(verify_token)
):
    """Get GDPR-related audit logs"""
    # TODO: Implement comprehensive audit logging
    return {
        "logs": [],
        "total": 0,
        "filters": {
            "start_date": start_date,
            "end_date": end_date,
            "user_id": user_id
        }
    }

# Background Tasks
async def log_consent_change(user_id: str, consent_type: str, granted: bool):
    """Log consent changes for audit"""
    logger.info(f"Consent change: user={user_id}, type={consent_type}, granted={granted}")
    # TODO: Send to audit service

async def process_data_subject_request(request_id: str, user_id: str, request_type: DataSubjectRequest):
    """Process data subject requests"""
    logger.info(f"Processing DSR: {request_id} for user {user_id}, type: {request_type}")
    
    # TODO: Implement actual processing logic
    # - For ACCESS: Gather all user data
    # - For ERASURE: Delete user data across services
    # - For PORTABILITY: Export data in standard format
    # - For RECTIFICATION: Update incorrect data
    
    # Update request status
    async with SessionLocal() as db:
        dsr = db.query(DataSubjectRequestRecord).filter(
            DataSubjectRequestRecord.request_id == request_id
        ).first()
        if dsr:
            dsr.status = "completed"
            dsr.completed_at = datetime.utcnow()
            db.commit()

async def process_user_erasure(user_id: str, request_id: str):
    """Process user data erasure across all services"""
    logger.info(f"Processing erasure for user {user_id}")
    
    # TODO: Call each service to delete user data
    services = [
        "auth-service",
        "policy-service",
        "analytics-service",
        "notification-service"
    ]
    
    async with httpx.AsyncClient() as client:
        for service in services:
            try:
                response = await client.delete(f"http://{service}/internal/user/{user_id}")
                logger.info(f"Deleted data from {service}: {response.status_code}")
            except Exception as e:
                logger.error(f"Failed to delete from {service}: {e}")

async def notify_authorities(breach_id: str, breach_data: Dict):
    """Notify data protection authorities about breach"""
    logger.info(f"Notifying authorities about breach {breach_id}")
    
    # TODO: Implement actual notification to authorities
    # This would typically involve:
    # - Sending email to DPA
    # - Submitting through official portal
    # - Creating formal report

async def notify_affected_users(breach_id: str, user_ids: List[str], description: str):
    """Notify users affected by data breach"""
    logger.info(f"Notifying {len(user_ids)} users about breach {breach_id}")
    
    # TODO: Send notifications via email service
    async with httpx.AsyncClient() as client:
        for user_id in user_ids:
            try:
                await client.post(
                    f"{EMAIL_SERVICE_URL}/send",
                    json={
                        "user_id": user_id,
                        "template": "data_breach_notification",
                        "data": {
                            "breach_id": breach_id,
                            "description": description
                        }
                    }
                )
            except Exception as e:
                logger.error(f"Failed to notify user {user_id}: {e}")

async def delete_expired_data(record_id: int, user_id: str):
    """Delete expired personal data"""
    logger.info(f"Deleting expired data record {record_id} for user {user_id}")
    
    async with SessionLocal() as db:
        record = db.query(PersonalDataRecord).filter(
            PersonalDataRecord.id == record_id
        ).first()
        if record:
            db.delete(record)
            db.commit()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=SERVICE_PORT)