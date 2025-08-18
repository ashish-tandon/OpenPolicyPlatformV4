from fastapi import FastAPI, Response, HTTPException, Depends, HTTPStatus, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest, Counter, Histogram
from typing import List, Optional, Dict, Any, Union
import os
import logging
from datetime import datetime, timedelta
import json
import uuid
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="mobile-api", version="1.0.0")
security = HTTPBearer()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics
mobile_operations = Counter('mobile_operations_total', 'Total mobile API operations', ['operation', 'status'])
mobile_duration = Histogram('mobile_duration_seconds', 'Mobile API operation duration')
mobile_users = Counter('mobile_users_total', 'Total mobile users', ['platform'])

# Mock database for development (replace with real database)
mobile_users_db = [
    {
        "id": "mobile_user_001",
        "username": "john_doe",
        "full_name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "+1234567890",
        "platform": "ios",
        "app_version": "2.1.0",
        "device_id": "ios_device_001",
        "push_token": "ios_push_token_001",
        "preferences": {
            "notifications": True,
            "dark_mode": False,
            "language": "en",
            "timezone": "America/New_York"
        },
        "last_active": "2024-01-20T10:00:00Z",
        "created_at": "2024-01-01T00:00:00Z",
        "status": "active"
    },
    {
        "id": "mobile_user_002",
        "username": "jane_smith",
        "full_name": "Jane Smith",
        "email": "jane.smith@example.com",
        "phone": "+1234567891",
        "platform": "android",
        "app_version": "2.1.0",
        "device_id": "android_device_001",
        "push_token": "android_push_token_001",
        "preferences": {
            "notifications": True,
            "dark_mode": True,
            "language": "en",
            "timezone": "America/Los_Angeles"
        },
        "last_active": "2024-01-20T09:30:00Z",
        "created_at": "2024-01-01T00:00:00Z",
        "status": "active"
    }
]

mobile_sessions_db = []
mobile_analytics_db = []

# Simple validation functions (replacing Pydantic)
def validate_platform(platform: str) -> bool:
    """Validate platform value"""
    return platform in ["ios", "android", "web"]

def validate_email(email: str) -> bool:
    """Validate email format"""
    return '@' in email and '.' in email

def validate_user_data(user_data: Dict[str, Any]) -> List[str]:
    """Validate user data and return list of errors"""
    errors = []
    
    if not user_data.get("username"):
        errors.append("Username is required")
    
    if not user_data.get("email") or not validate_email(user_data["email"]):
        errors.append("Valid email is required")
    
    if not user_data.get("platform") or not validate_platform(user_data["platform"]):
        errors.append("Platform must be one of: ios, android, web")
    
    if not user_data.get("full_name"):
        errors.append("Full name is required")
    
    if not user_data.get("phone"):
        errors.append("Phone number is required")
    
    if not user_data.get("app_version"):
        errors.append("App version is required")
    
    if not user_data.get("device_id"):
        errors.append("Device ID is required")
    
    return errors

# Mobile API service implementation
class MobileAPIService:
    def __init__(self):
        self.users = mobile_users_db
        self.sessions = mobile_sessions_db
        self.analytics = mobile_analytics_db
    
    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new mobile user"""
        # Validate user data
        validation_errors = validate_user_data(user_data)
        if validation_errors:
            raise ValueError("; ".join(validation_errors))
        
        # Check if username or email already exists
        if any(u["username"] == user_data["username"] for u in self.users):
            raise ValueError("Username already exists")
        
        if any(u["email"] == user_data["email"] for u in self.users):
            raise ValueError("Email already exists")
        
        # Create new user
        new_user = {
            "id": f"mobile_user_{len(self.users) + 1:03d}",
            **user_data,
            "preferences": {
                "notifications": True,
                "dark_mode": False,
                "language": "en",
                "timezone": "UTC"
            },
            "last_active": datetime.utcnow().isoformat(),
            "created_at": datetime.utcnow().isoformat(),
            "status": "active"
        }
        
        self.users.append(new_user)
        return new_user
    
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        return next((u for u in self.users if u["id"] == user_id), None)
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username"""
        return next((u for u in self.users if u["username"] == username), None)
    
    def update_user(self, user_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update user information"""
        user = self.get_user(user_id)
        if not user:
            return None
        
        # Update fields
        for field, value in update_data.items():
            if field in user:
                user[field] = value
        
        user["last_active"] = datetime.utcnow().isoformat()
        return user
    
    def create_session(self, user_id: str, device_id: str, platform: str, app_version: str) -> Dict[str, Any]:
        """Create a new mobile session"""
        session = {
            "user_id": user_id,
            "device_id": device_id,
            "platform": platform,
            "app_version": app_version,
            "session_token": str(uuid.uuid4()),
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(days=30),
            "is_active": True
        }
        
        self.sessions.append(session)
        return session
    
    def validate_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """Validate session token"""
        session = next((s for s in self.sessions if s["session_token"] == session_token and s["is_active"]), None)
        if not session:
            return None
        
        # Check if session expired
        if datetime.utcnow() > session["expires_at"]:
            session["is_active"] = False
            return None
        
        return session
    
    def track_analytics(self, analytics_data: Dict[str, Any]) -> Dict[str, Any]:
        """Track mobile analytics events"""
        analytics = {
            "id": str(uuid.uuid4()),
            **analytics_data,
            "timestamp": datetime.utcnow()
        }
        
        self.analytics.append(analytics)
        return analytics
    
    def get_user_analytics(self, user_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get user analytics for specified period"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return [
            a for a in self.analytics 
            if a["user_id"] == user_id and a["timestamp"] > cutoff_date
        ]

# Initialize service
mobile_service = MobileAPIService()

# Health check endpoints
@app.get("/healthz")
def healthz():
    """Health check endpoint"""
    return {
        "status": "ok", 
        "service": "mobile-api", 
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

@app.get("/readyz")
def readyz():
    """Readiness check endpoint"""
    return {
        "status": "ok", 
        "service": "mobile-api", 
        "ready": True,
        "users_count": len(mobile_users_db),
        "sessions_count": len(mobile_sessions_db)
    }

@app.get("/metrics")
def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

# User management endpoints
@app.post("/users", status_code=HTTPStatus.CREATED)
def create_mobile_user(user_data: Dict[str, Any]):
    """Create a new mobile user"""
    start_time = time.time()
    
    try:
        user = mobile_service.create_user(user_data)
        
        # Update metrics
        mobile_operations.labels(operation="create_user", status="success").inc()
        mobile_users.labels(platform=user["platform"]).inc()
        
        # Calculate duration for metrics
        duration = time.time() - start_time
        mobile_duration.observe(duration)
        
        logger.info(f"Mobile user created: {user['id']} on platform {user['platform']}")
        
        return {
            "status": "success",
            "message": "Mobile user created successfully",
            "user": user
        }
        
    except ValueError as e:
        mobile_operations.labels(operation="create_user", status="error").inc()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating mobile user: {str(e)}")
        mobile_operations.labels(operation="create_user", status="error").inc()
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/users/{user_id}")
def get_mobile_user(user_id: str):
    """Get mobile user by ID"""
    try:
        user = mobile_service.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        mobile_operations.labels(operation="get_user", status="success").inc()
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting mobile user {user_id}: {str(e)}")
        mobile_operations.labels(operation="get_user", status="error").inc()
        raise HTTPException(status_code=500, detail="Internal server error")

@app.put("/users/{user_id}")
def update_mobile_user(user_id: str, update_data: Dict[str, Any]):
    """Update mobile user information"""
    try:
        user = mobile_service.update_user(user_id, update_data)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        mobile_operations.labels(operation="update_user", status="success").inc()
        
        logger.info(f"Mobile user {user_id} updated")
        
        return {
            "status": "success",
            "message": "User updated successfully",
            "user": user
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating mobile user {user_id}: {str(e)}")
        mobile_operations.labels(operation="update_user", status="error").inc()
        raise HTTPException(status_code=500, detail="Internal server error")

# Session management endpoints
@app.post("/sessions", status_code=HTTPStatus.CREATED)
def create_mobile_session(
    user_id: str = Query(..., description="User ID"),
    device_id: str = Query(..., description="Device ID"),
    platform: str = Query(..., description="Platform (ios/android)"),
    app_version: str = Query(..., description="App version")
):
    """Create a new mobile session"""
    try:
        # Validate user exists
        user = mobile_service.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        session = mobile_service.create_session(user_id, device_id, platform, app_version)
        
        mobile_operations.labels(operation="create_session", status="success").inc()
        
        logger.info(f"Mobile session created for user {user_id} on {platform}")
        
        return {
            "status": "success",
            "message": "Session created successfully",
            "session": session
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating mobile session: {str(e)}")
        mobile_operations.labels(operation="create_session", status="error").inc()
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/sessions/validate")
def validate_mobile_session(session_token: str = Query(..., description="Session token")):
    """Validate mobile session token"""
    try:
        session = mobile_service.validate_session(session_token)
        if not session:
            raise HTTPException(status_code=401, detail="Invalid or expired session")
        
        mobile_operations.labels(operation="validate_session", status="success").inc()
        
        return {
            "status": "success",
            "valid": True,
            "session": session
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating mobile session: {str(e)}")
        mobile_operations.labels(operation="validate_session", status="error").inc()
        raise HTTPException(status_code=500, detail="Internal server error")

# Analytics endpoints
@app.post("/analytics", status_code=HTTPStatus.CREATED)
def track_mobile_analytics(
    user_id: str = Query(..., description="User ID"),
    event_type: str = Query(..., description="Event type"),
    event_data: str = Query(..., description="JSON encoded event data"),
    platform: str = Query(..., description="Platform (ios/android)"),
    app_version: str = Query(..., description="App version")
):
    """Track mobile analytics event"""
    try:
        # Parse event data
        try:
            parsed_event_data = json.loads(event_data)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid event data format")
        
        analytics = mobile_service.track_analytics({
            "user_id": user_id,
            "event_type": event_type,
            "event_data": parsed_event_data,
            "platform": platform,
            "app_version": app_version
        })
        
        mobile_operations.labels(operation="track_analytics", status="success").inc()
        
        logger.info(f"Mobile analytics tracked: {event_type} for user {user_id}")
        
        return {
            "status": "success",
            "message": "Analytics tracked successfully",
            "analytics": analytics
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error tracking mobile analytics: {str(e)}")
        mobile_operations.labels(operation="track_analytics", status="error").inc()
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/analytics/{user_id}")
def get_user_analytics(
    user_id: str,
    days: int = Query(30, ge=1, le=365, description="Number of days to look back")
):
    """Get user analytics for specified period"""
    try:
        analytics = mobile_service.get_user_analytics(user_id, days)
        
        mobile_operations.labels(operation="get_analytics", status="success").inc()
        
        return {
            "user_id": user_id,
            "period_days": days,
            "analytics": analytics,
            "total_events": len(analytics)
        }
        
    except Exception as e:
        logger.error(f"Error getting analytics for user {user_id}: {str(e)}")
        mobile_operations.labels(operation="get_analytics", status="error").inc()
        raise HTTPException(status_code=500, detail="Internal server error")

# User preferences endpoints
@app.get("/users/{user_id}/preferences")
def get_user_preferences(user_id: str):
    """Get user preferences"""
    try:
        user = mobile_service.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "user_id": user_id,
            "preferences": user.get("preferences", {})
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting preferences for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.put("/users/{user_id}/preferences")
def update_user_preferences(
    user_id: str,
    preferences: Dict[str, Any]
):
    """Update user preferences"""
    try:
        user = mobile_service.update_user(user_id, {"preferences": preferences})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        logger.info(f"Preferences updated for user {user_id}")
        
        return {
            "status": "success",
            "message": "Preferences updated successfully",
            "preferences": user["preferences"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating preferences for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Statistics endpoints
@app.get("/stats")
def get_mobile_stats():
    """Get mobile API statistics"""
    try:
        platform_stats = {}
        for user in mobile_users_db:
            platform = user["platform"]
            if platform not in platform_stats:
                platform_stats[platform] = 0
            platform_stats[platform] += 1
        
        return {
            "total_users": len(mobile_users_db),
            "active_sessions": len([s for s in mobile_sessions_db if s["is_active"]]),
            "platform_distribution": platform_stats,
            "total_analytics_events": len(mobile_analytics_db),
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting mobile stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Mock authentication dependency (replace with real auth service integration)
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Mock current user (replace with real JWT verification)"""
    # This is a mock implementation - replace with real JWT verification
    return {
        "id": "mobile_user_001",
        "username": "john_doe",
        "full_name": "John Doe",
        "role": "user"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 9009))
    uvicorn.run(app, host="0.0.0.0", port=port)