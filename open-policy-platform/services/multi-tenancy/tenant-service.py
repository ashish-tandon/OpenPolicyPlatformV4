"""
Multi-Tenancy Service for OpenPolicy Platform
Provides complete tenant isolation and management for enterprise customers
"""

import os
import json
import uuid
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from enum import Enum
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Request, Query, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, EmailStr, HttpUrl, validator
from sqlalchemy import create_engine, Column, String, DateTime, Boolean, Text, JSON, Integer, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
import redis.asyncio as redis
from cryptography.fernet import Fernet
import httpx
import stripe
from prometheus_client import Counter, Histogram, Gauge, generate_latest

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost/tenants")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/5")
SERVICE_PORT = int(os.getenv("SERVICE_PORT", 9029))
ENCRYPTION_KEY = os.getenv("TENANT_ENCRYPTION_KEY", Fernet.generate_key())
STRIPE_API_KEY = os.getenv("STRIPE_API_KEY", "")
AUDIT_SERVICE_URL = os.getenv("AUDIT_SERVICE_URL", "http://audit-service:9028")

# Metrics
tenants_created = Counter('tenants_created_total', 'Total tenants created')
tenants_active = Gauge('tenants_active', 'Number of active tenants')
tenant_operations = Counter('tenant_operations_total', 'Tenant operations', ['operation', 'status'])
tenant_storage_bytes = Gauge('tenant_storage_bytes', 'Storage used by tenant', ['tenant_id'])

# Database setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Encryption
fernet = Fernet(ENCRYPTION_KEY)

# Security
security = HTTPBearer()

class TenantStatus(str, Enum):
    """Tenant account status"""
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    INACTIVE = "inactive"
    DELETED = "deleted"

class TenantTier(str, Enum):
    """Tenant subscription tiers"""
    TRIAL = "trial"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    CUSTOM = "custom"

class IsolationLevel(str, Enum):
    """Data isolation levels"""
    SHARED = "shared"           # Shared database, row-level isolation
    SCHEMA = "schema"           # Separate schema per tenant
    DATABASE = "database"       # Separate database per tenant
    CLUSTER = "cluster"         # Separate cluster per tenant

# Association tables
tenant_users = Table(
    'tenant_users',
    Base.metadata,
    Column('tenant_id', UUID(as_uuid=True), ForeignKey('tenants.id')),
    Column('user_id', String, ForeignKey('tenant_user_accounts.id')),
    Column('role', String, default='member'),
    Column('joined_at', DateTime, default=datetime.utcnow)
)

tenant_features = Table(
    'tenant_features',
    Base.metadata,
    Column('tenant_id', UUID(as_uuid=True), ForeignKey('tenants.id')),
    Column('feature_id', Integer, ForeignKey('features.id')),
    Column('enabled', Boolean, default=True),
    Column('configuration', JSONB)
)

# Database Models
class Tenant(Base):
    """Main tenant model"""
    __tablename__ = "tenants"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    display_name = Column(String)
    description = Column(Text)
    
    # Contact information
    admin_email = Column(String, nullable=False)
    billing_email = Column(String)
    support_email = Column(String)
    
    # Configuration
    status = Column(String, default=TenantStatus.PENDING.value)
    tier = Column(String, default=TenantTier.TRIAL.value)
    isolation_level = Column(String, default=IsolationLevel.SHARED.value)
    
    # Customization
    logo_url = Column(String)
    primary_color = Column(String, default="#1976d2")
    custom_domain = Column(String, unique=True, nullable=True)
    
    # Limits and quotas
    max_users = Column(Integer, default=10)
    max_storage_gb = Column(Integer, default=10)
    max_api_calls_per_month = Column(Integer, default=100000)
    
    # Billing
    stripe_customer_id = Column(String, unique=True)
    stripe_subscription_id = Column(String)
    trial_ends_at = Column(DateTime)
    
    # Security
    api_key = Column(String, unique=True)
    webhook_secret = Column(String)
    allowed_ips = Column(JSON)
    
    # Settings
    settings = Column(JSONB, default={})
    features = Column(JSONB, default={})
    metadata = Column(JSONB, default={})
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    
    # Relationships
    users = relationship("TenantUserAccount", secondary=tenant_users, back_populates="tenants")
    databases = relationship("TenantDatabase", back_populates="tenant")
    api_keys = relationship("TenantAPIKey", back_populates="tenant")
    audit_logs = relationship("TenantAuditLog", back_populates="tenant")

class TenantDatabase(Base):
    """Tenant database configuration"""
    __tablename__ = "tenant_databases"
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=False)
    
    database_name = Column(String, unique=True)
    schema_name = Column(String)
    connection_string = Column(Text)  # Encrypted
    
    host = Column(String)
    port = Column(Integer)
    username = Column(String)
    
    is_primary = Column(Boolean, default=True)
    is_read_replica = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    tenant = relationship("Tenant", back_populates="databases")

class TenantUserAccount(Base):
    """User accounts within tenants"""
    __tablename__ = "tenant_user_accounts"
    
    id = Column(String, primary_key=True)  # Format: tenant_slug:user_id
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=False)
    
    email = Column(String, nullable=False)
    username = Column(String)
    full_name = Column(String)
    
    role = Column(String, default="member")  # admin, manager, member, viewer
    permissions = Column(JSONB, default=[])
    
    is_active = Column(Boolean, default=True)
    is_tenant_admin = Column(Boolean, default=False)
    
    last_login = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    tenants = relationship("Tenant", secondary=tenant_users, back_populates="users")

class TenantAPIKey(Base):
    """API keys for tenant access"""
    __tablename__ = "tenant_api_keys"
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=False)
    
    key_hash = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    
    scopes = Column(JSONB, default=[])
    rate_limit = Column(Integer, default=1000)
    
    expires_at = Column(DateTime)
    last_used_at = Column(DateTime)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    tenant = relationship("Tenant", back_populates="api_keys")

class TenantAuditLog(Base):
    """Tenant-specific audit logs"""
    __tablename__ = "tenant_audit_logs"
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=False)
    
    event_type = Column(String, nullable=False)
    actor_id = Column(String)
    resource_type = Column(String)
    resource_id = Column(String)
    
    action = Column(String, nullable=False)
    details = Column(JSONB)
    
    ip_address = Column(String)
    user_agent = Column(String)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    tenant = relationship("Tenant", back_populates="audit_logs")

class Feature(Base):
    """Available features for tenants"""
    __tablename__ = "features"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    display_name = Column(String)
    description = Column(Text)
    
    category = Column(String)  # analytics, security, integration, etc.
    
    # Tier restrictions
    min_tier = Column(String, default=TenantTier.STARTER.value)
    is_addon = Column(Boolean, default=False)
    addon_price = Column(Integer, default=0)  # in cents
    
    configuration_schema = Column(JSONB)
    default_configuration = Column(JSONB)
    
    created_at = Column(DateTime, default=datetime.utcnow)

# Create tables
Base.metadata.create_all(bind=engine)

# Pydantic models
class TenantCreate(BaseModel):
    """Create a new tenant"""
    name: str = Field(..., min_length=3, max_length=100)
    slug: str = Field(..., regex="^[a-z0-9-]+$", min_length=3, max_length=50)
    admin_email: EmailStr
    tier: TenantTier = TenantTier.TRIAL
    isolation_level: IsolationLevel = IsolationLevel.SHARED
    custom_domain: Optional[HttpUrl] = None
    metadata: Optional[Dict[str, Any]] = None

class TenantUpdate(BaseModel):
    """Update tenant details"""
    name: Optional[str] = None
    display_name: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[HttpUrl] = None
    primary_color: Optional[str] = None
    custom_domain: Optional[HttpUrl] = None
    settings: Optional[Dict[str, Any]] = None

class TenantResponse(BaseModel):
    """Tenant response model"""
    id: str
    slug: str
    name: str
    display_name: Optional[str]
    status: TenantStatus
    tier: TenantTier
    created_at: datetime
    
    # Usage
    user_count: Optional[int] = 0
    storage_used_gb: Optional[float] = 0
    api_calls_this_month: Optional[int] = 0
    
    # Limits
    max_users: int
    max_storage_gb: int
    max_api_calls_per_month: int

class TenantUserCreate(BaseModel):
    """Add user to tenant"""
    email: EmailStr
    username: Optional[str] = None
    full_name: Optional[str] = None
    role: str = "member"
    is_tenant_admin: bool = False

class TenantContext(BaseModel):
    """Current tenant context"""
    tenant_id: str
    tenant_slug: str
    user_id: str
    role: str
    permissions: List[str]

# Tenant Manager
class TenantManager:
    """Manages tenant operations"""
    
    def __init__(self, db: Session, redis_client: redis.Redis):
        self.db = db
        self.redis = redis_client
        
    async def create_tenant(self, tenant_data: TenantCreate) -> Tenant:
        """Create a new tenant with all required resources"""
        try:
            # Check if slug is available
            existing = self.db.query(Tenant).filter(
                Tenant.slug == tenant_data.slug
            ).first()
            if existing:
                raise HTTPException(status_code=400, detail="Slug already taken")
            
            # Create tenant
            tenant = Tenant(
                slug=tenant_data.slug,
                name=tenant_data.name,
                admin_email=tenant_data.admin_email,
                tier=tenant_data.tier.value,
                isolation_level=tenant_data.isolation_level.value,
                custom_domain=tenant_data.custom_domain,
                metadata=tenant_data.metadata or {},
                api_key=self._generate_api_key(),
                webhook_secret=secrets.token_urlsafe(32)
            )
            
            # Set trial period
            if tenant_data.tier == TenantTier.TRIAL:
                tenant.trial_ends_at = datetime.utcnow() + timedelta(days=14)
            
            self.db.add(tenant)
            self.db.flush()
            
            # Create tenant database/schema
            await self._provision_database(tenant)
            
            # Create Stripe customer
            if STRIPE_API_KEY:
                await self._create_stripe_customer(tenant)
            
            # Create default admin user
            admin_user = TenantUserAccount(
                id=f"{tenant.slug}:admin",
                tenant_id=tenant.id,
                email=tenant.admin_email,
                role="admin",
                is_tenant_admin=True
            )
            self.db.add(admin_user)
            
            # Add default features based on tier
            await self._assign_default_features(tenant)
            
            self.db.commit()
            
            # Update metrics
            tenants_created.inc()
            tenants_active.inc()
            
            # Cache tenant info
            await self._cache_tenant(tenant)
            
            # Audit log
            await self._audit_log(
                tenant_id=str(tenant.id),
                event_type="tenant.created",
                action="Tenant created",
                details={"tier": tenant.tier, "isolation": tenant.isolation_level}
            )
            
            return tenant
            
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create tenant: {str(e)}")
    
    async def get_tenant(self, tenant_id: str = None, slug: str = None) -> Optional[Tenant]:
        """Get tenant by ID or slug"""
        # Check cache first
        cache_key = f"tenant:{tenant_id or slug}"
        cached = await self.redis.get(cache_key)
        if cached:
            return json.loads(cached)
        
        # Query database
        query = self.db.query(Tenant)
        if tenant_id:
            tenant = query.filter(Tenant.id == tenant_id).first()
        elif slug:
            tenant = query.filter(Tenant.slug == slug).first()
        else:
            return None
        
        if tenant:
            await self._cache_tenant(tenant)
        
        return tenant
    
    async def update_tenant(self, tenant_id: str, update_data: TenantUpdate) -> Tenant:
        """Update tenant details"""
        tenant = await self.get_tenant(tenant_id=tenant_id)
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        # Update fields
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(tenant, field, value)
        
        tenant.updated_at = datetime.utcnow()
        self.db.commit()
        
        # Clear cache
        await self._clear_tenant_cache(tenant)
        
        # Audit log
        await self._audit_log(
            tenant_id=str(tenant.id),
            event_type="tenant.updated",
            action="Tenant updated",
            details=update_dict
        )
        
        return tenant
    
    async def suspend_tenant(self, tenant_id: str, reason: str) -> None:
        """Suspend a tenant"""
        tenant = await self.get_tenant(tenant_id=tenant_id)
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        tenant.status = TenantStatus.SUSPENDED.value
        self.db.commit()
        
        # Clear all tenant sessions
        await self._clear_tenant_sessions(tenant)
        
        # Audit log
        await self._audit_log(
            tenant_id=str(tenant.id),
            event_type="tenant.suspended",
            action="Tenant suspended",
            details={"reason": reason}
        )
        
        tenant_operations.labels(operation="suspend", status="success").inc()
    
    async def delete_tenant(self, tenant_id: str, hard_delete: bool = False) -> None:
        """Delete a tenant (soft or hard delete)"""
        tenant = await self.get_tenant(tenant_id=tenant_id)
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        if hard_delete:
            # Permanently delete all tenant data
            await self._hard_delete_tenant(tenant)
        else:
            # Soft delete
            tenant.status = TenantStatus.DELETED.value
            tenant.deleted_at = datetime.utcnow()
            self.db.commit()
        
        # Clear cache and sessions
        await self._clear_tenant_cache(tenant)
        await self._clear_tenant_sessions(tenant)
        
        # Update metrics
        tenants_active.dec()
        
        # Audit log
        await self._audit_log(
            tenant_id=str(tenant.id),
            event_type="tenant.deleted",
            action=f"Tenant {'hard' if hard_delete else 'soft'} deleted",
            details={}
        )
    
    async def add_user_to_tenant(
        self,
        tenant_id: str,
        user_data: TenantUserCreate
    ) -> TenantUserAccount:
        """Add a user to a tenant"""
        tenant = await self.get_tenant(tenant_id=tenant_id)
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        # Check user limit
        user_count = self.db.query(TenantUserAccount).filter(
            TenantUserAccount.tenant_id == tenant.id
        ).count()
        
        if user_count >= tenant.max_users:
            raise HTTPException(
                status_code=400,
                detail=f"User limit reached ({tenant.max_users})"
            )
        
        # Create user
        user_id = user_data.username or user_data.email.split('@')[0]
        user = TenantUserAccount(
            id=f"{tenant.slug}:{user_id}",
            tenant_id=tenant.id,
            email=user_data.email,
            username=user_data.username,
            full_name=user_data.full_name,
            role=user_data.role,
            is_tenant_admin=user_data.is_tenant_admin
        )
        
        self.db.add(user)
        self.db.commit()
        
        # Send invitation email
        # await self._send_invitation_email(tenant, user)
        
        # Audit log
        await self._audit_log(
            tenant_id=str(tenant.id),
            event_type="tenant.user_added",
            action="User added to tenant",
            details={"user_email": user.email, "role": user.role}
        )
        
        return user
    
    async def get_tenant_context(self, request: Request) -> TenantContext:
        """Extract tenant context from request"""
        # Check for tenant in various places
        tenant_id = None
        tenant_slug = None
        
        # 1. Check subdomain
        host = request.headers.get("host", "")
        if "." in host:
            subdomain = host.split(".")[0]
            tenant = await self.get_tenant(slug=subdomain)
            if tenant:
                tenant_id = str(tenant.id)
                tenant_slug = tenant.slug
        
        # 2. Check custom header
        if not tenant_id:
            tenant_header = request.headers.get("x-tenant-id")
            if tenant_header:
                tenant = await self.get_tenant(tenant_id=tenant_header)
                if tenant:
                    tenant_id = str(tenant.id)
                    tenant_slug = tenant.slug
        
        # 3. Check API key
        if not tenant_id:
            api_key = request.headers.get("x-api-key")
            if api_key:
                tenant = await self._get_tenant_by_api_key(api_key)
                if tenant:
                    tenant_id = str(tenant.id)
                    tenant_slug = tenant.slug
        
        if not tenant_id:
            raise HTTPException(status_code=400, detail="Tenant context not found")
        
        # Get user context
        user_id = getattr(request.state, "user_id", "anonymous")
        role = getattr(request.state, "role", "viewer")
        permissions = getattr(request.state, "permissions", [])
        
        return TenantContext(
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            user_id=user_id,
            role=role,
            permissions=permissions
        )
    
    async def get_tenant_usage(self, tenant_id: str) -> Dict[str, Any]:
        """Get current usage statistics for a tenant"""
        tenant = await self.get_tenant(tenant_id=tenant_id)
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        # Get user count
        user_count = self.db.query(TenantUserAccount).filter(
            TenantUserAccount.tenant_id == tenant.id
        ).count()
        
        # Get storage usage (mock for now)
        storage_gb = await self._get_storage_usage(tenant_id)
        
        # Get API usage from Redis
        api_calls = await self._get_api_usage(tenant_id)
        
        return {
            "tenant_id": str(tenant.id),
            "user_count": user_count,
            "user_limit": tenant.max_users,
            "storage_gb": storage_gb,
            "storage_limit_gb": tenant.max_storage_gb,
            "api_calls_this_month": api_calls,
            "api_calls_limit": tenant.max_api_calls_per_month,
            "status": tenant.status
        }
    
    # Private methods
    def _generate_api_key(self) -> str:
        """Generate a secure API key"""
        return f"opp_{secrets.token_urlsafe(32)}"
    
    async def _provision_database(self, tenant: Tenant):
        """Provision database resources for tenant"""
        if tenant.isolation_level == IsolationLevel.SHARED:
            # Row-level security in shared database
            return
        
        elif tenant.isolation_level == IsolationLevel.SCHEMA:
            # Create separate schema
            schema_name = f"tenant_{tenant.slug}"
            self.db.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")
            
            # Store configuration
            db_config = TenantDatabase(
                tenant_id=tenant.id,
                schema_name=schema_name,
                database_name="openpolicy",
                host="localhost",
                port=5432,
                username=f"tenant_{tenant.slug}"
            )
            self.db.add(db_config)
            
        elif tenant.isolation_level == IsolationLevel.DATABASE:
            # Create separate database
            db_name = f"openpolicy_tenant_{tenant.slug}"
            # This would need admin privileges
            # self.db.execute(f"CREATE DATABASE {db_name}")
            
        elif tenant.isolation_level == IsolationLevel.CLUSTER:
            # Provision separate cluster (would integrate with cloud provider)
            pass
    
    async def _create_stripe_customer(self, tenant: Tenant):
        """Create Stripe customer for billing"""
        if not STRIPE_API_KEY:
            return
        
        stripe.api_key = STRIPE_API_KEY
        
        customer = stripe.Customer.create(
            email=tenant.billing_email or tenant.admin_email,
            name=tenant.name,
            metadata={
                "tenant_id": str(tenant.id),
                "tenant_slug": tenant.slug
            }
        )
        
        tenant.stripe_customer_id = customer.id
    
    async def _assign_default_features(self, tenant: Tenant):
        """Assign default features based on tier"""
        tier_features = {
            TenantTier.TRIAL: ["basic_analytics", "basic_api", "email_support"],
            TenantTier.STARTER: ["basic_analytics", "basic_api", "email_support", "custom_branding"],
            TenantTier.PROFESSIONAL: ["advanced_analytics", "full_api", "priority_support", "custom_branding", "sso"],
            TenantTier.ENTERPRISE: ["all"]
        }
        
        features = tier_features.get(TenantTier(tenant.tier), [])
        tenant.features = {"enabled": features}
    
    async def _cache_tenant(self, tenant: Tenant):
        """Cache tenant information"""
        cache_data = {
            "id": str(tenant.id),
            "slug": tenant.slug,
            "name": tenant.name,
            "status": tenant.status,
            "tier": tenant.tier,
            "features": tenant.features
        }
        
        # Cache by ID and slug
        await self.redis.setex(
            f"tenant:{tenant.id}",
            3600,  # 1 hour
            json.dumps(cache_data)
        )
        await self.redis.setex(
            f"tenant:{tenant.slug}",
            3600,
            json.dumps(cache_data)
        )
    
    async def _clear_tenant_cache(self, tenant: Tenant):
        """Clear tenant cache"""
        await self.redis.delete(f"tenant:{tenant.id}")
        await self.redis.delete(f"tenant:{tenant.slug}")
    
    async def _clear_tenant_sessions(self, tenant: Tenant):
        """Clear all sessions for a tenant"""
        # Get all session keys for tenant
        pattern = f"session:tenant:{tenant.id}:*"
        async for key in self.redis.scan_iter(match=pattern):
            await self.redis.delete(key)
    
    async def _get_tenant_by_api_key(self, api_key: str) -> Optional[Tenant]:
        """Get tenant by API key"""
        tenant = self.db.query(Tenant).filter(
            Tenant.api_key == api_key
        ).first()
        return tenant
    
    async def _get_storage_usage(self, tenant_id: str) -> float:
        """Get storage usage for tenant in GB"""
        # This would query actual storage systems
        # For now, return mock data
        usage_bytes = await self.redis.get(f"tenant:storage:{tenant_id}") or 0
        return float(usage_bytes) / (1024 ** 3)
    
    async def _get_api_usage(self, tenant_id: str) -> int:
        """Get API usage for current month"""
        current_month = datetime.utcnow().strftime("%Y-%m")
        key = f"tenant:api_usage:{tenant_id}:{current_month}"
        usage = await self.redis.get(key) or 0
        return int(usage)
    
    async def _hard_delete_tenant(self, tenant: Tenant):
        """Permanently delete all tenant data"""
        # Delete from all tables
        self.db.query(TenantAuditLog).filter(
            TenantAuditLog.tenant_id == tenant.id
        ).delete()
        
        self.db.query(TenantAPIKey).filter(
            TenantAPIKey.tenant_id == tenant.id
        ).delete()
        
        self.db.query(TenantUserAccount).filter(
            TenantUserAccount.tenant_id == tenant.id
        ).delete()
        
        self.db.query(TenantDatabase).filter(
            TenantDatabase.tenant_id == tenant.id
        ).delete()
        
        # Finally delete tenant
        self.db.delete(tenant)
        self.db.commit()
        
        # Drop schema/database if exists
        if tenant.isolation_level == IsolationLevel.SCHEMA:
            self.db.execute(f"DROP SCHEMA IF EXISTS tenant_{tenant.slug} CASCADE")
    
    async def _audit_log(self, tenant_id: str, event_type: str, action: str, details: Dict):
        """Send audit log"""
        async with httpx.AsyncClient() as client:
            try:
                await client.post(
                    f"{AUDIT_SERVICE_URL}/log",
                    json={
                        "event_type": event_type,
                        "service": "multi-tenancy",
                        "action": action,
                        "resource_type": "tenant",
                        "resource_id": tenant_id,
                        "details": details
                    }
                )
            except:
                pass  # Don't fail on audit log errors

# Dependencies
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

redis_client: Optional[redis.Redis] = None

async def get_redis() -> redis.Redis:
    return redis_client

async def get_tenant_manager(
    db: Session = Depends(get_db),
    redis: redis.Redis = Depends(get_redis)
) -> TenantManager:
    return TenantManager(db, redis)

async def get_current_tenant(
    request: Request,
    manager: TenantManager = Depends(get_tenant_manager)
) -> TenantContext:
    """Get current tenant context from request"""
    return await manager.get_tenant_context(request)

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify authentication token"""
    # TODO: Implement proper token verification
    return {"user_id": "admin", "role": "admin"}

# Lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    global redis_client
    
    # Startup
    print("Starting Multi-Tenancy Service...")
    
    # Connect to Redis
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    await redis_client.ping()
    
    # Initialize metrics
    active_tenants = SessionLocal().query(Tenant).filter(
        Tenant.status == TenantStatus.ACTIVE.value
    ).count()
    tenants_active.set(active_tenants)
    
    yield
    
    # Shutdown
    print("Shutting down Multi-Tenancy Service...")
    await redis_client.close()

# Create FastAPI app
app = FastAPI(
    title="Multi-Tenancy Service",
    description="Enterprise multi-tenancy management for OpenPolicy Platform",
    version="1.0.0",
    lifespan=lifespan
)

# Middleware for tenant context
@app.middleware("http")
async def tenant_context_middleware(request: Request, call_next):
    """Add tenant context to all requests"""
    try:
        # Skip for health/metrics endpoints
        if request.url.path in ["/health", "/metrics"]:
            return await call_next(request)
        
        # Get tenant manager
        async with SessionLocal() as db:
            manager = TenantManager(db, redis_client)
            context = await manager.get_tenant_context(request)
            
            # Add to request state
            request.state.tenant_id = context.tenant_id
            request.state.tenant_slug = context.tenant_slug
            
            # Track API usage
            await redis_client.incr(
                f"tenant:api_usage:{context.tenant_id}:{datetime.utcnow().strftime('%Y-%m')}"
            )
    except HTTPException:
        pass  # Allow request to continue without tenant context
    
    return await call_next(request)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "multi-tenancy"}

@app.get("/metrics")
async def metrics():
    """Prometheus metrics"""
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(generate_latest())

# Tenant Management Endpoints
@app.post("/tenants", response_model=TenantResponse)
async def create_tenant(
    tenant_data: TenantCreate,
    manager: TenantManager = Depends(get_tenant_manager),
    auth: Dict = Depends(verify_token)
):
    """Create a new tenant"""
    tenant = await manager.create_tenant(tenant_data)
    
    # Get usage for response
    usage = await manager.get_tenant_usage(str(tenant.id))
    
    return TenantResponse(
        id=str(tenant.id),
        slug=tenant.slug,
        name=tenant.name,
        display_name=tenant.display_name,
        status=TenantStatus(tenant.status),
        tier=TenantTier(tenant.tier),
        created_at=tenant.created_at,
        user_count=usage["user_count"],
        storage_used_gb=usage["storage_gb"],
        api_calls_this_month=usage["api_calls_this_month"],
        max_users=tenant.max_users,
        max_storage_gb=tenant.max_storage_gb,
        max_api_calls_per_month=tenant.max_api_calls_per_month
    )

@app.get("/tenants/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: str,
    manager: TenantManager = Depends(get_tenant_manager),
    auth: Dict = Depends(verify_token)
):
    """Get tenant details"""
    tenant = await manager.get_tenant(tenant_id=tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    usage = await manager.get_tenant_usage(tenant_id)
    
    return TenantResponse(
        id=str(tenant.id),
        slug=tenant.slug,
        name=tenant.name,
        display_name=tenant.display_name,
        status=TenantStatus(tenant.status),
        tier=TenantTier(tenant.tier),
        created_at=tenant.created_at,
        user_count=usage["user_count"],
        storage_used_gb=usage["storage_gb"],
        api_calls_this_month=usage["api_calls_this_month"],
        max_users=tenant.max_users,
        max_storage_gb=tenant.max_storage_gb,
        max_api_calls_per_month=tenant.max_api_calls_per_month
    )

@app.put("/tenants/{tenant_id}")
async def update_tenant(
    tenant_id: str,
    update_data: TenantUpdate,
    manager: TenantManager = Depends(get_tenant_manager),
    auth: Dict = Depends(verify_token)
):
    """Update tenant details"""
    tenant = await manager.update_tenant(tenant_id, update_data)
    return {"success": True, "tenant_id": str(tenant.id)}

@app.post("/tenants/{tenant_id}/suspend")
async def suspend_tenant(
    tenant_id: str,
    reason: str = Query(..., description="Reason for suspension"),
    manager: TenantManager = Depends(get_tenant_manager),
    auth: Dict = Depends(verify_token)
):
    """Suspend a tenant"""
    await manager.suspend_tenant(tenant_id, reason)
    return {"success": True, "message": "Tenant suspended"}

@app.delete("/tenants/{tenant_id}")
async def delete_tenant(
    tenant_id: str,
    hard_delete: bool = Query(default=False, description="Permanently delete all data"),
    manager: TenantManager = Depends(get_tenant_manager),
    auth: Dict = Depends(verify_token)
):
    """Delete a tenant"""
    await manager.delete_tenant(tenant_id, hard_delete)
    return {"success": True, "message": f"Tenant {'permanently' if hard_delete else 'soft'} deleted"}

# User Management
@app.post("/tenants/{tenant_id}/users")
async def add_user_to_tenant(
    tenant_id: str,
    user_data: TenantUserCreate,
    manager: TenantManager = Depends(get_tenant_manager),
    auth: Dict = Depends(verify_token)
):
    """Add a user to tenant"""
    user = await manager.add_user_to_tenant(tenant_id, user_data)
    return {
        "success": True,
        "user_id": user.id,
        "email": user.email,
        "role": user.role
    }

@app.get("/tenants/{tenant_id}/users")
async def list_tenant_users(
    tenant_id: str,
    manager: TenantManager = Depends(get_tenant_manager),
    db: Session = Depends(get_db),
    auth: Dict = Depends(verify_token)
):
    """List all users in a tenant"""
    users = db.query(TenantUserAccount).filter(
        TenantUserAccount.tenant_id == tenant_id
    ).all()
    
    return {
        "users": [
            {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "full_name": user.full_name,
                "role": user.role,
                "is_active": user.is_active,
                "is_tenant_admin": user.is_tenant_admin,
                "last_login": user.last_login,
                "created_at": user.created_at
            }
            for user in users
        ]
    }

# Usage and Billing
@app.get("/tenants/{tenant_id}/usage")
async def get_tenant_usage(
    tenant_id: str,
    manager: TenantManager = Depends(get_tenant_manager),
    auth: Dict = Depends(verify_token)
):
    """Get tenant usage statistics"""
    return await manager.get_tenant_usage(tenant_id)

@app.post("/tenants/{tenant_id}/upgrade")
async def upgrade_tenant_tier(
    tenant_id: str,
    new_tier: TenantTier,
    manager: TenantManager = Depends(get_tenant_manager),
    auth: Dict = Depends(verify_token)
):
    """Upgrade tenant to a higher tier"""
    tenant = await manager.get_tenant(tenant_id=tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Validate tier upgrade
    current_tier_index = list(TenantTier).index(TenantTier(tenant.tier))
    new_tier_index = list(TenantTier).index(new_tier)
    
    if new_tier_index <= current_tier_index:
        raise HTTPException(status_code=400, detail="Can only upgrade to a higher tier")
    
    # Update tier and limits
    tier_limits = {
        TenantTier.STARTER: {"users": 50, "storage": 50, "api_calls": 500000},
        TenantTier.PROFESSIONAL: {"users": 200, "storage": 200, "api_calls": 2000000},
        TenantTier.ENTERPRISE: {"users": -1, "storage": -1, "api_calls": -1},  # Unlimited
    }
    
    limits = tier_limits.get(new_tier, {})
    update_data = TenantUpdate(
        settings={
            **tenant.settings,
            "tier_upgraded_at": datetime.utcnow().isoformat()
        }
    )
    
    tenant = await manager.update_tenant(tenant_id, update_data)
    tenant.tier = new_tier.value
    tenant.max_users = limits.get("users", tenant.max_users)
    tenant.max_storage_gb = limits.get("storage", tenant.max_storage_gb)
    tenant.max_api_calls_per_month = limits.get("api_calls", tenant.max_api_calls_per_month)
    
    # Update features
    await manager._assign_default_features(tenant)
    
    SessionLocal().commit()
    
    return {"success": True, "new_tier": new_tier, "limits": limits}

# Current Tenant Context
@app.get("/context")
async def get_current_context(
    context: TenantContext = Depends(get_current_tenant)
):
    """Get current tenant context"""
    return context

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=SERVICE_PORT)