"""
Open Policy Platform V4 - OAuth Authentication Router
Multi-provider OAuth, user management, and role-based access control
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Form, Request
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any, Union
import json
import logging
from datetime import datetime, timedelta
import random
import uuid
import jwt
import bcrypt
from enum import Enum

from ..dependencies import get_db

router = APIRouter()
logger = logging.getLogger(__name__)

# OAuth Configuration - Using Environment Variables for Security
import os

# Auth0 Configuration (Primary OAuth Provider)
AUTH0_CONFIG = {
    "domain": os.getenv("AUTH0_DOMAIN", "dev-openpolicy.auth0.com"),
    "client_id": os.getenv("AUTH0_CLIENT_ID", ""),
    "client_secret": os.getenv("AUTH0_CLIENT_SECRET", ""),
    "audience": os.getenv("AUTH0_AUDIENCE", "https://api.openpolicy.com"),
    "authorization_url": f"https://{os.getenv('AUTH0_DOMAIN', 'dev-openpolicy.auth0.com')}/authorize",
    "token_url": f"https://{os.getenv('AUTH0_DOMAIN', 'dev-openpolicy.auth0.com')}/oauth/token",
    "userinfo_url": f"https://{os.getenv('AUTH0_DOMAIN', 'dev-openpolicy.auth0.com')}/userinfo",
    "scopes": ["openid", "profile", "email", "read:user"]
}

# Fallback OAuth Providers (Optional)
OAUTH_CONFIG = {
    "auth0": AUTH0_CONFIG,
    "google": {
        "client_id": os.getenv("GOOGLE_CLIENT_ID", ""),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET", ""),
        "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "userinfo_url": "https://www.googleapis.com/oauth2/v2/userinfo",
        "scopes": ["openid", "email", "profile"]
    },
    "microsoft": {
        "client_id": os.getenv("MICROSOFT_CLIENT_ID", ""),
        "client_secret": os.getenv("MICROSOFT_CLIENT_SECRET", ""),
        "authorization_url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
        "token_url": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
        "userinfo_url": "https://graph.microsoft.com/v1.0/me",
        "scopes": ["openid", "email", "profile", "User.Read"]
    },
    "github": {
        "client_id": os.getenv("GITHUB_CLIENT_ID", ""),
        "client_secret": os.getenv("GITHUB_CLIENT_SECRET", ""),
        "authorization_url": "https://github.com/login/oauth/authorize",
        "token_url": "https://github.com/login/oauth/access_token",
        "userinfo_url": "https://api.github.com/user",
        "scopes": ["read:user", "user:email"]
    }
}

# JWT Configuration - Using Environment Variables for Security
JWT_SECRET = os.getenv("JWT_SECRET", "")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_MINUTES = int(os.getenv("JWT_EXPIRY_MINUTES", "30"))
JWT_REFRESH_EXPIRY_DAYS = int(os.getenv("JWT_REFRESH_EXPIRY_DAYS", "7"))

# Validate required environment variables
if not JWT_SECRET:
    raise ValueError("JWT_SECRET environment variable is required")
if not AUTH0_CONFIG["client_id"]:
    raise ValueError("AUTH0_CLIENT_ID environment variable is required")
if not AUTH0_CONFIG["client_secret"]:
    raise ValueError("AUTH0_CLIENT_SECRET environment variable is required")

# User Role Models
class UserRole(str, Enum):
    CONSUMER = "consumer"
    MP_OFFICE_ADMIN = "mp_office_admin"
    MODERATOR = "moderator"
    SYSTEM_ADMIN = "system_admin"
    INTERNAL_SERVICE = "internal_service"

class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"

class UserAccountType(str, Enum):
    FREE = "free"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"

# User Models
class UserBase(BaseModel):
    email: EmailStr
    username: str
    first_name: str
    last_name: str
    role: UserRole
    account_type: UserAccountType = UserAccountType.FREE
    is_verified: bool = False
    is_active: bool = True

class UserCreate(UserBase):
    password: str
    confirm_password: str

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[UserRole] = None
    account_type: Optional[UserAccountType] = None
    is_verified: Optional[bool] = None
    is_active: Optional[bool] = None

class UserResponse(UserBase):
    id: str
    created_at: datetime
    last_login: Optional[datetime] = None
    status: UserStatus

class UserLogin(BaseModel):
    email: str
    password: str
    remember_me: bool = False

class OAuthLogin(BaseModel):
    provider: str
    code: str
    state: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse

class RefreshTokenRequest(BaseModel):
    refresh_token: str

# User Database - No hardcoded passwords, users created via OAuth
USERS_DB = {}

# Initialize with system admin if environment variable is set
def initialize_system_admin():
    """Initialize system admin user from environment variables"""
    admin_email = os.getenv("SYSTEM_ADMIN_EMAIL")
    if admin_email and admin_email not in USERS_DB:
        USERS_DB[admin_email] = {
            "id": "admin_001",
            "email": admin_email,
            "username": "admin",
            "first_name": "System",
            "last_name": "Administrator",
            "password_hash": "",  # No password for OAuth users
            "role": UserRole.SYSTEM_ADMIN,
            "account_type": UserAccountType.ENTERPRISE,
            "is_verified": True,
            "is_active": True,
            "status": UserStatus.ACTIVE,
            "created_at": datetime.now(),
            "last_login": None,
            "permissions": ["*"]  # All permissions
        }

# Initialize system admin on module load
initialize_system_admin()

# Mock Token Storage
ACTIVE_TOKENS = {}
REFRESH_TOKENS = {}

# OAuth Authentication Endpoints
@router.get("/providers")
async def get_oauth_providers():
    """Get available OAuth providers"""
    try:
        providers = []
        for provider, config in OAUTH_CONFIG.items():
            providers.append({
                "provider": provider,
                "name": provider.title(),
                "authorization_url": config["authorization_url"],
                "scopes": config["scopes"],
                "client_id": config["client_id"]
            })
        
        return {
            "status": "success",
            "providers": providers,
            "total_providers": len(providers)
        }
        
    except Exception as e:
        logger.error(f"Error getting OAuth providers: {e}")
        raise HTTPException(status_code=500, detail=f"OAuth providers error: {str(e)}")

@router.get("/login/{provider}")
async def initiate_oauth_login(provider: str, request: Request):
    """Initiate OAuth login flow"""
    try:
        if provider not in OAUTH_CONFIG:
            raise HTTPException(status_code=400, detail="Unsupported OAuth provider")
        
        config = OAUTH_CONFIG[provider]
        state = str(uuid.uuid4())
        
        # Store state for CSRF protection
        # In production, store this in Redis or database
        
        # Build authorization URL with provider-specific parameters
        if provider == "auth0":
            auth_params = {
                "client_id": config["client_id"],
                "redirect_uri": f"{request.base_url}api/v1/oauth/callback/{provider}",
                "response_type": "code",
                "scope": " ".join(config["scopes"]),
                "state": state,
                "audience": config["audience"]
            }
        else:
            auth_params = {
                "client_id": config["client_id"],
                "redirect_uri": f"{request.base_url}api/v1/oauth/callback/{provider}",
                "response_type": "code",
                "scope": " ".join(config["scopes"]),
                "state": state
            }
        
        auth_url = f"{config['authorization_url']}?{'&'.join([f'{k}={v}' for k, v in auth_params.items()])}"
        
        return {
            "status": "success",
            "authorization_url": auth_url,
            "provider": provider,
            "state": state
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error initiating OAuth login: {e}")
        raise HTTPException(status_code=500, detail=f"OAuth login error: {str(e)}")

@router.get("/callback/{provider}")
async def oauth_callback(
    provider: str,
    code: str = Query(...),
    state: str = Query(...),
    error: Optional[str] = Query(None)
):
    """Handle OAuth callback"""
    try:
        if error:
            raise HTTPException(status_code=400, detail=f"OAuth error: {error}")
        
        if provider not in OAUTH_CONFIG:
            raise HTTPException(status_code=400, detail="Unsupported OAuth provider")
        
        # In production, validate state parameter and exchange code for token
        # For now, simulate successful OAuth flow
        
        # Simulate user info from OAuth provider
        user_info = {
            "email": f"user_{uuid.uuid4().hex[:8]}@example.com",
            "username": f"user_{uuid.uuid4().hex[:8]}",
            "first_name": "OAuth",
            "last_name": "User",
            "provider": provider
        }
        
        # Create or get user
        user = await get_or_create_oauth_user(user_info)
        
        # Generate tokens
        access_token = create_access_token(user["id"])
        refresh_token = create_refresh_token(user["id"])
        
        return {
            "status": "success",
            "message": f"OAuth login successful via {provider}",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": user
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error handling OAuth callback: {e}")
        raise HTTPException(status_code=500, detail=f"OAuth callback error: {str(e)}")

# OAuth-Only Authentication - No Traditional Password Login
@router.post("/register")
async def register_user(user_data: UserCreate):
    """Register a new user via OAuth only"""
    raise HTTPException(
        status_code=400, 
        detail="User registration is only available through OAuth providers. Please use the OAuth login options."
    )

@router.post("/login")
async def login_user(login_data: UserLogin):
    """Traditional login disabled - OAuth only"""
    raise HTTPException(
        status_code=400, 
        detail="Traditional login is disabled. Please use OAuth authentication providers."
    )

@router.post("/refresh")
async def refresh_token(refresh_data: RefreshTokenRequest):
    """Refresh access token"""
    try:
        # Validate refresh token
        if refresh_data.refresh_token not in REFRESH_TOKENS:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        
        user_id = REFRESH_TOKENS[refresh_data.refresh_token]
        
        # Generate new access token
        access_token = create_access_token(user_id)
        
        return {
            "status": "success",
            "access_token": access_token,
            "expires_in": JWT_EXPIRY_MINUTES * 60
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refreshing token: {e}")
        raise HTTPException(status_code=500, detail=f"Token refresh error: {str(e)}")

@router.post("/logout")
async def logout_user(request: Request):
    """User logout"""
    try:
        # Get token from request header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            
            # Invalidate tokens
            if token in ACTIVE_TOKENS:
                del ACTIVE_TOKENS[token]
            
            # Find and invalidate refresh token
            for refresh_token, user_id in REFRESH_TOKENS.items():
                if user_id == ACTIVE_TOKENS.get(token):
                    del REFRESH_TOKENS[refresh_token]
                    break
        
        return {
            "status": "success",
            "message": "Logout successful"
        }
        
    except Exception as e:
        logger.error(f"Error during logout: {e}")
        raise HTTPException(status_code=500, detail=f"Logout error: {str(e)}")

# User Management Endpoints
@router.get("/users")
async def list_users(
    role: Optional[UserRole] = Query(None),
    status: Optional[UserStatus] = Query(None),
    limit: int = Query(50)
):
    """List users with filtering"""
    try:
        users = list(USERS_DB.values())
        
        # Apply filters
        if role:
            users = [u for u in users if u["role"] == role]
        if status:
            users = [u for u in users if u["status"] == status]
        
        # Apply limit
        users = users[:limit]
        
        # Convert to response models
        user_responses = [UserResponse(**user) for user in users]
        
        return {
            "status": "success",
            "users": user_responses,
            "total_users": len(user_responses),
            "filters_applied": {
                "role": role,
                "status": status,
                "limit": limit
            }
        }
        
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        raise HTTPException(status_code=500, detail=f"User listing error: {str(e)}")

@router.get("/users/{user_id}")
async def get_user(user_id: str):
    """Get user details"""
    try:
        user = None
        for u in USERS_DB.values():
            if u["id"] == user_id:
                user = u
                break
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "status": "success",
            "user": UserResponse(**user)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user: {e}")
        raise HTTPException(status_code=500, detail=f"User retrieval error: {str(e)}")

@router.put("/users/{user_id}")
async def update_user(user_id: str, user_data: UserUpdate):
    """Update user"""
    try:
        user = None
        for u in USERS_DB.values():
            if u["id"] == user_id:
                user = u
                break
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update user fields
        for field, value in user_data.dict(exclude_unset=True).items():
            user[field] = value
        
        return {
            "status": "success",
            "message": "User updated successfully",
            "user": UserResponse(**user)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        raise HTTPException(status_code=500, detail=f"User update error: {str(e)}")

@router.delete("/users/{user_id}")
async def delete_user(user_id: str):
    """Delete user"""
    try:
        user = None
        user_email = None
        for email, u in USERS_DB.items():
            if u["id"] == user_id:
                user = u
                user_email = email
                break
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Delete user
        del USERS_DB[user_email]
        
        return {
            "status": "success",
            "message": "User deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        raise HTTPException(status_code=500, detail=f"User deletion error: {str(e)}")

# Helper Functions
def create_access_token(user_id: str) -> str:
    """Create JWT access token"""
    payload = {
        "sub": user_id,
        "exp": datetime.utcnow() + timedelta(minutes=JWT_EXPIRY_MINUTES),
        "iat": datetime.utcnow(),
        "type": "access"
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    ACTIVE_TOKENS[token] = user_id
    return token

def create_refresh_token(user_id: str) -> str:
    """Create JWT refresh token"""
    payload = {
        "sub": user_id,
        "exp": datetime.utcnow() + timedelta(days=JWT_REFRESH_EXPIRY_DAYS),
        "iat": datetime.utcnow(),
        "type": "refresh"
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    REFRESH_TOKENS[token] = user_id
    return token

async def get_or_create_oauth_user(user_info: Dict[str, Any]) -> Dict[str, Any]:
    """Get or create user from OAuth info"""
    # Check if user exists
    for user in USERS_DB.values():
        if user["email"] == user_info["email"]:
            return user
    
    # Create new user
    user_id = f"user_{uuid.uuid4().hex[:8]}"
    user = {
        "id": user_id,
        "email": user_info["email"],
        "username": user_info["username"],
        "first_name": user_info["first_name"],
        "last_name": user_info["last_name"],
        "password_hash": "",  # OAuth users don't have passwords
        "role": UserRole.CONSUMER,
        "account_type": UserAccountType.FREE,
        "is_verified": True,  # OAuth users are pre-verified
        "is_active": True,
        "status": UserStatus.ACTIVE,
        "created_at": datetime.now(),
        "last_login": datetime.now(),
        "permissions": get_default_permissions(UserRole.CONSUMER)
    }
    
    USERS_DB[user_info["email"]] = user
    return user

def get_default_permissions(role: UserRole) -> List[str]:
    """Get default permissions for user role"""
    permissions = {
        UserRole.CONSUMER: ["read_content", "comment", "vote"],
        UserRole.MP_OFFICE_ADMIN: ["read_content", "comment", "vote", "create_polls", "create_quizzes", "manage_office_content"],
        UserRole.MODERATOR: ["read_content", "comment", "vote", "moderate_content", "remove_comments", "manage_users"],
        UserRole.SYSTEM_ADMIN: ["*"],  # All permissions
        UserRole.INTERNAL_SERVICE: ["internal_access", "service_communication"]
    }
    return permissions.get(role, [])

def verify_token(token: str) -> Optional[str]:
    """Verify JWT token and return user ID"""
    try:
        if token not in ACTIVE_TOKENS:
            return None
        
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        
        if user_id and user_id == ACTIVE_TOKENS[token]:
            return user_id
        
        return None
        
    except jwt.ExpiredSignatureError:
        return None
    except jwt.JWTError:
        return None
    except Exception:
        return None
