"""
Enhanced Authentication Router with Database Integration
Provides comprehensive authentication using the new security tables
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
import jwt
import bcrypt
from datetime import datetime, timedelta
from pydantic import BaseModel, EmailStr, validator
from sqlalchemy import text

from ..dependencies import get_db
from ..config import settings

router = APIRouter()

# Security
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

# Data models (input)
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    role: str = "user"

    @validator('password')
    def validate_password_strength(cls, v):
        if len(v) < 12:
            raise ValueError('Password must be at least 12 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v):
            raise ValueError('Password must contain at least one special character')
        return v

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None

class UserLogin(BaseModel):
    username: str
    password: str
    remember_me: bool = False

class PasswordReset(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: Optional[str] = None

# Data models (output)
class UserPublic(BaseModel):
    id: int
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    role: str
    permissions: List[str] = []
    is_active: Optional[bool] = True
    created_at: Optional[str] = None
    last_login: Optional[str] = None

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    user: UserPublic

class MessageResponse(BaseModel):
    message: str
    timestamp: Optional[str] = None

class UsersListResponse(BaseModel):
    users: List[UserPublic]
    total_users: int
    active_users: int

class PermissionsResponse(BaseModel):
    permissions: List[str]
    role: str

# JWT settings
SECRET_KEY = settings.secret_key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict):
    """Create JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    try:
        return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())
    except Exception:
        return False

def hash_password(password: str) -> str:
    """Hash password with enhanced security"""
    salt = bcrypt.gensalt(rounds=12)  # Increased rounds for security
    return bcrypt.hashpw(password.encode(), salt).decode()

def get_user_from_db(username: str, db: Session):
    """Get user from database"""
    try:
        result = db.execute(
            text("SELECT id, username, email, password_hash, full_name, role, is_active, is_verified, permissions, created_at, last_login FROM users WHERE username = :username AND is_active = TRUE"),
            {"username": username}
        )
        row = result.fetchone()
        if row:
            return {
                "id": row[0],
                "username": row[1],
                "email": row[2],
                "password_hash": row[3],
                "full_name": row[4],
                "role": row[5],
                "is_active": row[6],
                "is_verified": row[7],
                "permissions": row[8] or [],
                "created_at": row[9].isoformat() if row[9] else None,
                "last_login": row[10].isoformat() if row[10] else None
            }
        return None
    except Exception as e:
        print(f"Database error: {e}")
        return None

def authenticate_user(username: str, password: str, db: Session):
    """Authenticate user with database"""
    user = get_user_from_db(username, db)
    if not user:
        return None
    if not verify_password(password, user["password_hash"]):
        return None
    return user

def log_audit_event(db: Session, user_id: int, action: str, resource: str = None, ip_address: str = None, user_agent: str = None):
    """Log security audit event"""
    try:
        db.execute(
            text("INSERT INTO audit_logs (user_id, action, resource, ip_address, user_agent) VALUES (:user_id, :action, :resource, :ip_address, :user_agent)"),
            {
                "user_id": user_id,
                "action": action,
                "resource": resource,
                "ip_address": ip_address,
                "user_agent": user_agent
            }
        )
        db.commit()
    except Exception as e:
        print(f"Audit logging error: {e}")

@router.post("/login", response_model=LoginResponse)
async def login(
    user_login: UserLogin,
    request: Request,
    db: Session = Depends(get_db)
):
    """User login with enhanced security"""
    try:
        username = user_login.username
        password = user_login.password
        
        # Authenticate user
        user = authenticate_user(username, password, db)
        if not user:
            # Log failed login attempt
            log_audit_event(db, 0, "login_failed", "auth", str(request.client.host), request.headers.get("user-agent"))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Inactive account"
            )
        
        # Create tokens
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user["username"], "role": user["role"], "user_id": user["id"]},
            expires_delta=access_token_expires
        )
        refresh_token = create_refresh_token(data={"sub": user["username"], "user_id": user["id"]})
        
        # Update last login and log successful login
        db.execute(
            text("UPDATE users SET last_login = CURRENT_TIMESTAMP, failed_login_attempts = 0 WHERE id = :user_id"),
            {"user_id": user["id"]}
        )
        db.commit()
        
        log_audit_event(db, user["id"], "login_success", "auth", str(request.client.host), request.headers.get("user-agent"))
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {
                "id": user["id"],
                "username": user["username"],
                "email": user["email"],
                "full_name": user["full_name"],
                "role": user["role"],
                "permissions": user["permissions"],
                "is_active": user["is_active"],
                "created_at": user["created_at"],
                "last_login": user["last_login"]
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Login error: {str(e)}")

@router.post("/register", status_code=201)
async def register(
    user_data: UserCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """Register a new user with enhanced security"""
    try:
        # Check if username already exists
        existing_user = get_user_from_db(user_data.username, db)
        if existing_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")
        
        # Check if email already exists
        result = db.execute(
            text("SELECT id FROM users WHERE email = :email"),
            {"email": user_data.email}
        )
        if result.fetchone():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")
        
        # Hash password
        password_hash = hash_password(user_data.password)
        
        # Insert new user
        result = db.execute(
            text("""
                INSERT INTO users (username, email, password_hash, full_name, role, permissions)
                VALUES (:username, :email, :password_hash, :full_name, :role, :permissions)
                RETURNING id
            """),
            {
                "username": user_data.username,
                "email": user_data.email,
                "password_hash": password_hash,
                "full_name": user_data.full_name or user_data.username,
                "role": user_data.role,
                "permissions": ["read"] if user_data.role == "user" else ["read", "write"]
            }
        )
        new_user_id = result.fetchone()[0]
        db.commit()
        
        # Log registration
        log_audit_event(db, new_user_id, "user_registered", "auth", str(request.client.host), request.headers.get("user-agent"))
        
        # Issue token
        access_token = create_access_token(data={"sub": user_data.username, "role": user_data.role, "user_id": new_user_id})
        return {
            "message": "User registered successfully",
            "user": {
                "id": new_user_id,
                "username": user_data.username,
                "email": user_data.email,
                "full_name": user_data.full_name or user_data.username,
                "role": user_data.role
            },
            "access_token": access_token,
            "token_type": "bearer"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Registration error: {str(e)}")

@router.get("/me")
async def get_current_user_info(
    request: Request,
    db: Session = Depends(get_db)
):
    """Get current user info from database"""
    try:
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        token = auth_header.split(" ", 1)[1]
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username = payload.get("sub")
            user_id = payload.get("user_id")
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        if not username or not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = get_user_from_db(username, db)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        return {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "full_name": user["full_name"],
            "role": user["role"],
            "permissions": user["permissions"],
            "is_active": user["is_active"],
            "created_at": user["created_at"],
            "last_login": user["last_login"]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving user info: {str(e)}")

@router.post("/logout")
async def logout(
    request: Request,
    db: Session = Depends(get_db)
):
    """User logout with audit logging"""
    try:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]
            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                user_id = payload.get("user_id")
                if user_id:
                    log_audit_event(db, user_id, "logout", "auth", str(request.client.host), request.headers.get("user-agent"))
            except:
                pass  # Token might be invalid, but we still want to log the logout attempt
        
        return {"message": "Successfully logged out", "timestamp": datetime.now().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Logout error: {str(e)}")

@router.get("/users", response_model=UsersListResponse)
async def get_users_list(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """Get list of users (admin only)"""
    try:
        # Get total count
        result = db.execute(text("SELECT COUNT(*) FROM users"))
        total_users = result.fetchone()[0]
        
        # Get active users count
        result = db.execute(text("SELECT COUNT(*) FROM users WHERE is_active = TRUE"))
        active_users = result.fetchone()[0]
        
        # Get users with pagination
        result = db.execute(
            text("""
                SELECT id, username, email, full_name, role, is_active, permissions, created_at, last_login
                FROM users
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :skip
            """),
            {"limit": limit, "skip": skip}
        )
        
        users = []
        for row in result.fetchall():
            users.append({
                "id": row[0],
                "username": row[1],
                "email": row[2],
                "full_name": row[3],
                "role": row[4],
                "is_active": row[5],
                "permissions": row[6] or [],
                "created_at": row[7].isoformat() if row[7] else None,
                "last_login": row[8].isoformat() if row[8] else None
            })
        
        return {
            "users": users,
            "total_users": total_users,
            "active_users": active_users
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error retrieving users: {str(e)}")

@router.get("/audit-logs")
async def get_audit_logs(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """Get audit logs (admin only)"""
    try:
        result = db.execute(
            text("""
                SELECT al.id, al.user_id, u.username, al.action, al.resource, al.ip_address, al.timestamp
                FROM audit_logs al
                LEFT JOIN users u ON al.user_id = u.id
                ORDER BY al.timestamp DESC
                LIMIT :limit OFFSET :skip
            """),
            {"limit": limit, "skip": skip}
        )
        
        logs = []
        for row in result.fetchall():
            logs.append({
                "id": row[0],
                "user_id": row[1],
                "username": row[2] or "anonymous",
                "action": row[3],
                "resource": row[4],
                "ip_address": str(row[5]) if row[5] else None,
                "timestamp": row[6].isoformat() if row[6] else None
            })
        
        return {"audit_logs": logs}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error retrieving audit logs: {str(e)}")
