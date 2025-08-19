"""
SSO (Single Sign-On) Service for OpenPolicy Platform
Supports SAML 2.0, OAuth 2.0, OpenID Connect, and Active Directory
"""

import os
import json
import secrets
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from enum import Enum
import xml.etree.ElementTree as ET
from urllib.parse import urlencode, quote_plus
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Request, Response, Query, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, EmailStr, HttpUrl, validator
from sqlalchemy import create_engine, Column, String, DateTime, Boolean, Text, JSON, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.x509 import load_pem_x509_certificate
from cryptography.hazmat.backends import default_backend
import jwt
import httpx
import redis.asyncio as redis
from onelogin.saml2.auth import OneLogin_Saml2_Auth
from onelogin.saml2.utils import OneLogin_Saml2_Utils
import ldap3
from prometheus_client import Counter, Histogram, generate_latest

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost/sso")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/6")
SERVICE_PORT = int(os.getenv("SERVICE_PORT", 9030))
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", 24))
BASE_URL = os.getenv("BASE_URL", "https://openpolicy.com")
TENANT_SERVICE_URL = os.getenv("TENANT_SERVICE_URL", "http://tenant-service:9029")

# Metrics
sso_logins = Counter('sso_logins_total', 'Total SSO login attempts', ['provider', 'status'])
sso_latency = Histogram('sso_login_duration_seconds', 'SSO login duration')
active_sso_sessions = Counter('active_sso_sessions', 'Number of active SSO sessions')

# Database setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Security
security = HTTPBearer()

class SSOProvider(str, Enum):
    """Supported SSO providers"""
    SAML = "saml"
    OAUTH2 = "oauth2"
    OIDC = "oidc"
    LDAP = "ldap"
    AZURE_AD = "azure_ad"
    GOOGLE = "google"
    OKTA = "okta"
    AUTH0 = "auth0"
    CUSTOM = "custom"

class AuthFlow(str, Enum):
    """OAuth/OIDC flow types"""
    AUTHORIZATION_CODE = "authorization_code"
    IMPLICIT = "implicit"
    CLIENT_CREDENTIALS = "client_credentials"
    PASSWORD = "password"
    DEVICE_CODE = "device_code"

# Database Models
class SSOConfiguration(Base):
    """SSO provider configuration"""
    __tablename__ = "sso_configurations"
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(String, nullable=False, index=True)
    provider = Column(String, nullable=False)
    name = Column(String, nullable=False)
    
    # Common settings
    enabled = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    allow_signup = Column(Boolean, default=True)
    
    # SAML Configuration
    saml_entity_id = Column(String)
    saml_sso_url = Column(String)
    saml_slo_url = Column(String)
    saml_x509_cert = Column(Text)
    saml_metadata_url = Column(String)
    saml_attribute_mapping = Column(JSON)
    
    # OAuth/OIDC Configuration
    oauth_client_id = Column(String)
    oauth_client_secret = Column(Text)  # Encrypted
    oauth_authorization_url = Column(String)
    oauth_token_url = Column(String)
    oauth_userinfo_url = Column(String)
    oauth_scopes = Column(JSON)
    oauth_flow_type = Column(String, default=AuthFlow.AUTHORIZATION_CODE.value)
    
    # LDAP Configuration
    ldap_server_url = Column(String)
    ldap_bind_dn = Column(String)
    ldap_bind_password = Column(Text)  # Encrypted
    ldap_base_dn = Column(String)
    ldap_user_filter = Column(String)
    ldap_group_filter = Column(String)
    ldap_attribute_mapping = Column(JSON)
    
    # Advanced settings
    custom_claims = Column(JSON)
    role_mapping = Column(JSON)
    group_mapping = Column(JSON)
    mfa_required = Column(Boolean, default=False)
    allowed_domains = Column(JSON)
    blocked_domains = Column(JSON)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SSOSession(Base):
    """SSO session tracking"""
    __tablename__ = "sso_sessions"
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String, unique=True, nullable=False)
    tenant_id = Column(String, nullable=False)
    user_id = Column(String, nullable=False)
    provider = Column(String, nullable=False)
    
    # Session data
    access_token = Column(Text)
    refresh_token = Column(Text)
    id_token = Column(Text)
    
    # User info
    email = Column(String, nullable=False)
    name = Column(String)
    groups = Column(JSON)
    attributes = Column(JSON)
    
    # Session management
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    last_accessed = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String)
    user_agent = Column(String)

class SSOAuditLog(Base):
    """SSO audit trail"""
    __tablename__ = "sso_audit_logs"
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(String, nullable=False)
    user_id = Column(String)
    provider = Column(String)
    event_type = Column(String, nullable=False)
    
    success = Column(Boolean)
    error_message = Column(Text)
    
    ip_address = Column(String)
    user_agent = Column(String)
    
    metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

# Create tables
Base.metadata.create_all(bind=engine)

# Pydantic models
class SSOConfigCreate(BaseModel):
    """Create SSO configuration"""
    provider: SSOProvider
    name: str
    enabled: bool = True
    allow_signup: bool = True
    
    # Provider-specific fields
    saml_config: Optional[Dict[str, Any]] = None
    oauth_config: Optional[Dict[str, Any]] = None
    ldap_config: Optional[Dict[str, Any]] = None
    
    # Common settings
    allowed_domains: Optional[List[str]] = None
    role_mapping: Optional[Dict[str, str]] = None
    mfa_required: bool = False

class SSOConfigResponse(BaseModel):
    """SSO configuration response"""
    id: int
    provider: str
    name: str
    enabled: bool
    is_default: bool
    created_at: datetime
    
    # Metadata without secrets
    metadata: Dict[str, Any]

class SSOLoginRequest(BaseModel):
    """SSO login request"""
    provider_id: Optional[int] = None
    provider_name: Optional[str] = None
    return_url: Optional[HttpUrl] = None
    state: Optional[str] = None

class SSOUser(BaseModel):
    """User info from SSO provider"""
    id: str
    email: EmailStr
    name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    picture: Optional[str] = None
    groups: List[str] = Field(default_factory=list)
    attributes: Dict[str, Any] = Field(default_factory=dict)
    tenant_id: str
    provider: str

# SSO Manager
class SSOManager:
    """Manages SSO operations"""
    
    def __init__(self, db: Session, redis_client: redis.Redis):
        self.db = db
        self.redis = redis_client
        
    async def create_provider(
        self,
        tenant_id: str,
        config: SSOConfigCreate
    ) -> SSOConfiguration:
        """Create new SSO provider configuration"""
        # Create configuration
        sso_config = SSOConfiguration(
            tenant_id=tenant_id,
            provider=config.provider.value,
            name=config.name,
            enabled=config.enabled,
            allow_signup=config.allow_signup,
            allowed_domains=config.allowed_domains,
            role_mapping=config.role_mapping,
            mfa_required=config.mfa_required
        )
        
        # Set provider-specific configuration
        if config.provider == SSOProvider.SAML and config.saml_config:
            sso_config.saml_entity_id = config.saml_config.get("entity_id")
            sso_config.saml_sso_url = config.saml_config.get("sso_url")
            sso_config.saml_slo_url = config.saml_config.get("slo_url")
            sso_config.saml_x509_cert = config.saml_config.get("x509_cert")
            sso_config.saml_metadata_url = config.saml_config.get("metadata_url")
            sso_config.saml_attribute_mapping = config.saml_config.get("attribute_mapping", {})
            
        elif config.provider in [SSOProvider.OAUTH2, SSOProvider.OIDC] and config.oauth_config:
            sso_config.oauth_client_id = config.oauth_config.get("client_id")
            sso_config.oauth_client_secret = self._encrypt(config.oauth_config.get("client_secret"))
            sso_config.oauth_authorization_url = config.oauth_config.get("authorization_url")
            sso_config.oauth_token_url = config.oauth_config.get("token_url")
            sso_config.oauth_userinfo_url = config.oauth_config.get("userinfo_url")
            sso_config.oauth_scopes = config.oauth_config.get("scopes", ["openid", "email", "profile"])
            sso_config.oauth_flow_type = config.oauth_config.get("flow_type", AuthFlow.AUTHORIZATION_CODE.value)
            
        elif config.provider == SSOProvider.LDAP and config.ldap_config:
            sso_config.ldap_server_url = config.ldap_config.get("server_url")
            sso_config.ldap_bind_dn = config.ldap_config.get("bind_dn")
            sso_config.ldap_bind_password = self._encrypt(config.ldap_config.get("bind_password"))
            sso_config.ldap_base_dn = config.ldap_config.get("base_dn")
            sso_config.ldap_user_filter = config.ldap_config.get("user_filter", "(uid={username})")
            sso_config.ldap_group_filter = config.ldap_config.get("group_filter")
            sso_config.ldap_attribute_mapping = config.ldap_config.get("attribute_mapping", {})
        
        # Set as default if it's the first provider
        existing_count = self.db.query(SSOConfiguration).filter(
            SSOConfiguration.tenant_id == tenant_id
        ).count()
        if existing_count == 0:
            sso_config.is_default = True
        
        self.db.add(sso_config)
        self.db.commit()
        
        # Log configuration
        await self._audit_log(
            tenant_id=tenant_id,
            event_type="sso_provider_created",
            provider=config.provider.value,
            success=True,
            metadata={"provider_name": config.name}
        )
        
        return sso_config
    
    async def initiate_login(
        self,
        tenant_id: str,
        provider_id: int,
        return_url: Optional[str] = None,
        request: Request = None
    ) -> str:
        """Initiate SSO login flow"""
        # Get provider configuration
        provider = self.db.query(SSOConfiguration).filter(
            SSOConfiguration.id == provider_id,
            SSOConfiguration.tenant_id == tenant_id,
            SSOConfiguration.enabled == True
        ).first()
        
        if not provider:
            raise HTTPException(status_code=404, detail="SSO provider not found or disabled")
        
        # Generate state for CSRF protection
        state = secrets.token_urlsafe(32)
        await self.redis.setex(
            f"sso:state:{state}",
            600,  # 10 minutes
            json.dumps({
                "tenant_id": tenant_id,
                "provider_id": provider_id,
                "return_url": return_url or f"{BASE_URL}/dashboard",
                "timestamp": datetime.utcnow().isoformat()
            })
        )
        
        # Route to appropriate provider
        if provider.provider == SSOProvider.SAML:
            return await self._initiate_saml_login(provider, state, request)
        elif provider.provider in [SSOProvider.OAUTH2, SSOProvider.OIDC]:
            return await self._initiate_oauth_login(provider, state)
        elif provider.provider == SSOProvider.LDAP:
            # LDAP doesn't redirect, return login form URL
            return f"{BASE_URL}/auth/ldap?provider={provider_id}&state={state}"
        else:
            raise HTTPException(status_code=400, detail="Unsupported provider type")
    
    async def handle_callback(
        self,
        provider_id: int,
        request: Request,
        code: Optional[str] = None,
        state: Optional[str] = None,
        saml_response: Optional[str] = None
    ) -> SSOUser:
        """Handle SSO callback"""
        # Validate state
        if state:
            state_data = await self._validate_state(state)
            tenant_id = state_data["tenant_id"]
        else:
            raise HTTPException(status_code=400, detail="Invalid state")
        
        # Get provider
        provider = self.db.query(SSOConfiguration).filter(
            SSOConfiguration.id == provider_id
        ).first()
        
        if not provider:
            raise HTTPException(status_code=404, detail="Provider not found")
        
        try:
            # Route to appropriate handler
            if provider.provider == SSOProvider.SAML:
                user = await self._handle_saml_callback(provider, request, saml_response)
            elif provider.provider in [SSOProvider.OAUTH2, SSOProvider.OIDC]:
                user = await self._handle_oauth_callback(provider, code, state)
            else:
                raise HTTPException(status_code=400, detail="Unsupported provider")
            
            # Create session
            session = await self._create_session(tenant_id, user, provider.provider)
            
            # Audit log
            await self._audit_log(
                tenant_id=tenant_id,
                user_id=user.id,
                event_type="sso_login_success",
                provider=provider.provider,
                success=True,
                metadata={"email": user.email}
            )
            
            # Update metrics
            sso_logins.labels(provider=provider.provider, status="success").inc()
            active_sso_sessions.inc()
            
            return user
            
        except Exception as e:
            # Audit log failure
            await self._audit_log(
                tenant_id=tenant_id,
                event_type="sso_login_failed",
                provider=provider.provider,
                success=False,
                error_message=str(e)
            )
            
            sso_logins.labels(provider=provider.provider, status="failed").inc()
            raise
    
    async def validate_session(self, session_id: str) -> Optional[SSOSession]:
        """Validate SSO session"""
        # Check cache first
        cached = await self.redis.get(f"sso:session:{session_id}")
        if cached:
            return json.loads(cached)
        
        # Check database
        session = self.db.query(SSOSession).filter(
            SSOSession.session_id == session_id,
            SSOSession.expires_at > datetime.utcnow()
        ).first()
        
        if session:
            # Update last accessed
            session.last_accessed = datetime.utcnow()
            self.db.commit()
            
            # Cache session
            await self.redis.setex(
                f"sso:session:{session_id}",
                300,  # 5 minutes
                json.dumps({
                    "tenant_id": session.tenant_id,
                    "user_id": session.user_id,
                    "email": session.email,
                    "provider": session.provider
                })
            )
            
            return session
        
        return None
    
    async def logout(self, session_id: str):
        """Logout SSO session"""
        session = self.db.query(SSOSession).filter(
            SSOSession.session_id == session_id
        ).first()
        
        if session:
            # Get provider for SLO
            provider = self.db.query(SSOConfiguration).filter(
                SSOConfiguration.tenant_id == session.tenant_id,
                SSOConfiguration.provider == session.provider
            ).first()
            
            # Initiate Single Logout if supported
            if provider and provider.provider == SSOProvider.SAML and provider.saml_slo_url:
                # TODO: Implement SAML SLO
                pass
            
            # Delete session
            self.db.delete(session)
            self.db.commit()
            
            # Clear cache
            await self.redis.delete(f"sso:session:{session_id}")
            
            # Update metrics
            active_sso_sessions.dec()
            
            # Audit log
            await self._audit_log(
                tenant_id=session.tenant_id,
                user_id=session.user_id,
                event_type="sso_logout",
                provider=session.provider,
                success=True
            )
    
    # SAML handlers
    async def _initiate_saml_login(
        self,
        provider: SSOConfiguration,
        state: str,
        request: Request
    ) -> str:
        """Initiate SAML login"""
        # Build SAML request
        saml_settings = {
            "sp": {
                "entityId": f"{BASE_URL}/sso/saml/metadata",
                "assertionConsumerService": {
                    "url": f"{BASE_URL}/sso/saml/callback/{provider.id}",
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
                },
                "x509cert": "",  # SP certificate if needed
                "privateKey": ""  # SP private key if needed
            },
            "idp": {
                "entityId": provider.saml_entity_id,
                "singleSignOnService": {
                    "url": provider.saml_sso_url,
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
                },
                "x509cert": provider.saml_x509_cert
            }
        }
        
        auth = OneLogin_Saml2_Auth(self._prepare_flask_request(request), saml_settings)
        return auth.login(return_to=state)
    
    async def _handle_saml_callback(
        self,
        provider: SSOConfiguration,
        request: Request,
        saml_response: str
    ) -> SSOUser:
        """Handle SAML callback"""
        # Process SAML response
        saml_settings = {
            "sp": {
                "entityId": f"{BASE_URL}/sso/saml/metadata",
                "assertionConsumerService": {
                    "url": f"{BASE_URL}/sso/saml/callback/{provider.id}",
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
                }
            },
            "idp": {
                "entityId": provider.saml_entity_id,
                "singleSignOnService": {
                    "url": provider.saml_sso_url,
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
                },
                "x509cert": provider.saml_x509_cert
            }
        }
        
        auth = OneLogin_Saml2_Auth(self._prepare_flask_request(request), saml_settings)
        auth.process_response()
        
        if not auth.is_authenticated():
            errors = auth.get_errors()
            raise HTTPException(status_code=400, detail=f"SAML authentication failed: {errors}")
        
        # Extract user attributes
        attributes = auth.get_attributes()
        nameid = auth.get_nameid()
        
        # Map attributes
        mapping = provider.saml_attribute_mapping or {}
        email = attributes.get(mapping.get("email", "email"), [nameid])[0]
        name = attributes.get(mapping.get("name", "displayName"), [""])[0]
        groups = attributes.get(mapping.get("groups", "memberOf"), [])
        
        return SSOUser(
            id=nameid,
            email=email,
            name=name,
            groups=groups,
            attributes=attributes,
            tenant_id=provider.tenant_id,
            provider=provider.provider
        )
    
    # OAuth/OIDC handlers
    async def _initiate_oauth_login(
        self,
        provider: SSOConfiguration,
        state: str
    ) -> str:
        """Initiate OAuth login"""
        # Build authorization URL
        params = {
            "client_id": provider.oauth_client_id,
            "redirect_uri": f"{BASE_URL}/sso/oauth/callback/{provider.id}",
            "response_type": "code",
            "scope": " ".join(provider.oauth_scopes or ["openid", "email", "profile"]),
            "state": state
        }
        
        # Add provider-specific parameters
        if provider.provider == SSOProvider.OIDC:
            params["nonce"] = secrets.token_urlsafe(32)
        
        auth_url = f"{provider.oauth_authorization_url}?{urlencode(params)}"
        return auth_url
    
    async def _handle_oauth_callback(
        self,
        provider: SSOConfiguration,
        code: str,
        state: str
    ) -> SSOUser:
        """Handle OAuth callback"""
        async with httpx.AsyncClient() as client:
            # Exchange code for tokens
            token_data = {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": f"{BASE_URL}/sso/oauth/callback/{provider.id}",
                "client_id": provider.oauth_client_id,
                "client_secret": self._decrypt(provider.oauth_client_secret)
            }
            
            token_response = await client.post(
                provider.oauth_token_url,
                data=token_data
            )
            
            if token_response.status_code != 200:
                raise HTTPException(status_code=400, detail="Failed to exchange code for token")
            
            tokens = token_response.json()
            access_token = tokens.get("access_token")
            id_token = tokens.get("id_token")
            
            # Get user info
            if provider.oauth_userinfo_url:
                userinfo_response = await client.get(
                    provider.oauth_userinfo_url,
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                
                if userinfo_response.status_code != 200:
                    raise HTTPException(status_code=400, detail="Failed to get user info")
                
                userinfo = userinfo_response.json()
            elif id_token:
                # Decode ID token for user info
                userinfo = jwt.decode(id_token, options={"verify_signature": False})
            else:
                raise HTTPException(status_code=400, detail="No user info available")
            
            # Extract user data
            return SSOUser(
                id=userinfo.get("sub", userinfo.get("id")),
                email=userinfo.get("email"),
                name=userinfo.get("name"),
                first_name=userinfo.get("given_name"),
                last_name=userinfo.get("family_name"),
                picture=userinfo.get("picture"),
                groups=userinfo.get("groups", []),
                attributes=userinfo,
                tenant_id=provider.tenant_id,
                provider=provider.provider
            )
    
    # LDAP handler
    async def authenticate_ldap(
        self,
        provider_id: int,
        username: str,
        password: str
    ) -> SSOUser:
        """Authenticate via LDAP"""
        provider = self.db.query(SSOConfiguration).filter(
            SSOConfiguration.id == provider_id
        ).first()
        
        if not provider or provider.provider != SSOProvider.LDAP:
            raise HTTPException(status_code=404, detail="LDAP provider not found")
        
        try:
            # Connect to LDAP server
            server = ldap3.Server(provider.ldap_server_url, get_info=ldap3.ALL)
            
            # Bind with service account
            conn = ldap3.Connection(
                server,
                user=provider.ldap_bind_dn,
                password=self._decrypt(provider.ldap_bind_password),
                auto_bind=True
            )
            
            # Search for user
            user_filter = provider.ldap_user_filter.format(username=username)
            conn.search(
                provider.ldap_base_dn,
                user_filter,
                attributes=ldap3.ALL_ATTRIBUTES
            )
            
            if not conn.entries:
                raise HTTPException(status_code=401, detail="User not found")
            
            user_entry = conn.entries[0]
            user_dn = user_entry.entry_dn
            
            # Verify password
            user_conn = ldap3.Connection(server, user=user_dn, password=password)
            if not user_conn.bind():
                raise HTTPException(status_code=401, detail="Invalid credentials")
            
            # Get user attributes
            attributes = json.loads(user_entry.entry_to_json())["attributes"]
            mapping = provider.ldap_attribute_mapping or {}
            
            # Get groups if configured
            groups = []
            if provider.ldap_group_filter:
                conn.search(
                    provider.ldap_base_dn,
                    provider.ldap_group_filter.format(user_dn=user_dn),
                    attributes=["cn"]
                )
                groups = [entry.cn.value for entry in conn.entries]
            
            return SSOUser(
                id=attributes.get(mapping.get("id", "uid"), [username])[0],
                email=attributes.get(mapping.get("email", "mail"), [""])[0],
                name=attributes.get(mapping.get("name", "cn"), [""])[0],
                groups=groups,
                attributes=attributes,
                tenant_id=provider.tenant_id,
                provider=provider.provider
            )
            
        except ldap3.core.exceptions.LDAPException as e:
            raise HTTPException(status_code=500, detail=f"LDAP error: {str(e)}")
        finally:
            if conn:
                conn.unbind()
    
    # Helper methods
    async def _validate_state(self, state: str) -> Dict[str, Any]:
        """Validate CSRF state token"""
        state_key = f"sso:state:{state}"
        state_data = await self.redis.get(state_key)
        
        if not state_data:
            raise HTTPException(status_code=400, detail="Invalid or expired state")
        
        # Delete state to prevent reuse
        await self.redis.delete(state_key)
        
        return json.loads(state_data)
    
    async def _create_session(
        self,
        tenant_id: str,
        user: SSOUser,
        provider: str
    ) -> SSOSession:
        """Create SSO session"""
        session_id = secrets.token_urlsafe(32)
        
        session = SSOSession(
            session_id=session_id,
            tenant_id=tenant_id,
            user_id=user.id,
            provider=provider,
            email=user.email,
            name=user.name,
            groups=user.groups,
            attributes=user.attributes,
            expires_at=datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
        )
        
        self.db.add(session)
        self.db.commit()
        
        return session
    
    def _encrypt(self, data: str) -> str:
        """Encrypt sensitive data"""
        # Simple base64 encoding for demo - use proper encryption in production
        return base64.b64encode(data.encode()).decode()
    
    def _decrypt(self, data: str) -> str:
        """Decrypt sensitive data"""
        return base64.b64decode(data.encode()).decode()
    
    def _prepare_flask_request(self, request: Request) -> Dict:
        """Prepare request dict for SAML library"""
        return {
            "https": request.url.scheme == "https",
            "http_host": request.headers.get("host"),
            "script_name": request.url.path,
            "get_data": dict(request.query_params),
            "post_data": {}  # Would need to parse form data
        }
    
    async def _audit_log(
        self,
        tenant_id: str,
        event_type: str,
        provider: str = None,
        user_id: str = None,
        success: bool = True,
        error_message: str = None,
        metadata: Dict = None
    ):
        """Create audit log entry"""
        log = SSOAuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            provider=provider,
            event_type=event_type,
            success=success,
            error_message=error_message,
            metadata=metadata
        )
        self.db.add(log)
        self.db.commit()

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

async def get_sso_manager(
    db: Session = Depends(get_db),
    redis: redis.Redis = Depends(get_redis)
) -> SSOManager:
    return SSOManager(db, redis)

async def get_current_tenant(request: Request) -> str:
    """Get tenant ID from request"""
    # Get from header, subdomain, or token
    tenant_id = request.headers.get("x-tenant-id")
    if not tenant_id:
        # Extract from subdomain or token
        pass
    return tenant_id or "default"

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
    print("Starting SSO Service...")
    
    # Connect to Redis
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    await redis_client.ping()
    
    yield
    
    # Shutdown
    print("Shutting down SSO Service...")
    await redis_client.close()

# Create FastAPI app
app = FastAPI(
    title="SSO Service",
    description="Enterprise SSO integration for OpenPolicy Platform",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "sso"}

@app.get("/metrics")
async def metrics():
    """Prometheus metrics"""
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(generate_latest())

# SSO Configuration Endpoints
@app.post("/sso/providers")
async def create_sso_provider(
    config: SSOConfigCreate,
    tenant_id: str = Depends(get_current_tenant),
    manager: SSOManager = Depends(get_sso_manager),
    auth: Dict = Depends(verify_token)
):
    """Create new SSO provider configuration"""
    provider = await manager.create_provider(tenant_id, config)
    return SSOConfigResponse(
        id=provider.id,
        provider=provider.provider,
        name=provider.name,
        enabled=provider.enabled,
        is_default=provider.is_default,
        created_at=provider.created_at,
        metadata={
            "allow_signup": provider.allow_signup,
            "mfa_required": provider.mfa_required,
            "allowed_domains": provider.allowed_domains
        }
    )

@app.get("/sso/providers")
async def list_sso_providers(
    tenant_id: str = Depends(get_current_tenant),
    db: Session = Depends(get_db),
    auth: Dict = Depends(verify_token)
):
    """List all SSO providers for tenant"""
    providers = db.query(SSOConfiguration).filter(
        SSOConfiguration.tenant_id == tenant_id
    ).all()
    
    return {
        "providers": [
            SSOConfigResponse(
                id=p.id,
                provider=p.provider,
                name=p.name,
                enabled=p.enabled,
                is_default=p.is_default,
                created_at=p.created_at,
                metadata={
                    "type": p.provider,
                    "allow_signup": p.allow_signup
                }
            )
            for p in providers
        ]
    }

# SSO Login Flow
@app.get("/sso/login")
async def initiate_sso_login(
    provider_id: int = Query(..., description="SSO provider ID"),
    return_url: Optional[str] = Query(None, description="URL to return after login"),
    tenant_id: str = Depends(get_current_tenant),
    request: Request = None,
    manager: SSOManager = Depends(get_sso_manager)
):
    """Initiate SSO login flow"""
    login_url = await manager.initiate_login(
        tenant_id=tenant_id,
        provider_id=provider_id,
        return_url=return_url,
        request=request
    )
    
    return RedirectResponse(url=login_url)

@app.get("/sso/saml/callback/{provider_id}")
@app.post("/sso/saml/callback/{provider_id}")
async def handle_saml_callback(
    provider_id: int,
    request: Request,
    manager: SSOManager = Depends(get_sso_manager)
):
    """Handle SAML callback"""
    # Get SAML response from form data
    form = await request.form()
    saml_response = form.get("SAMLResponse")
    relay_state = form.get("RelayState")  # Contains our state
    
    user = await manager.handle_callback(
        provider_id=provider_id,
        request=request,
        state=relay_state,
        saml_response=saml_response
    )
    
    # Generate JWT token
    token = jwt.encode(
        {
            "sub": user.id,
            "email": user.email,
            "name": user.name,
            "tenant_id": user.tenant_id,
            "provider": user.provider,
            "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
        },
        JWT_SECRET,
        algorithm=JWT_ALGORITHM
    )
    
    # Get return URL from state
    state_data = await manager._validate_state(relay_state)
    return_url = state_data.get("return_url", f"{BASE_URL}/dashboard")
    
    # Redirect with token
    return RedirectResponse(url=f"{return_url}?token={token}")

@app.get("/sso/oauth/callback/{provider_id}")
async def handle_oauth_callback(
    provider_id: int,
    code: str = Query(...),
    state: str = Query(...),
    manager: SSOManager = Depends(get_sso_manager)
):
    """Handle OAuth/OIDC callback"""
    user = await manager.handle_callback(
        provider_id=provider_id,
        code=code,
        state=state
    )
    
    # Generate JWT token
    token = jwt.encode(
        {
            "sub": user.id,
            "email": user.email,
            "name": user.name,
            "tenant_id": user.tenant_id,
            "provider": user.provider,
            "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
        },
        JWT_SECRET,
        algorithm=JWT_ALGORITHM
    )
    
    # Get return URL from state
    state_data = await manager._validate_state(state)
    return_url = state_data.get("return_url", f"{BASE_URL}/dashboard")
    
    # Redirect with token
    return RedirectResponse(url=f"{return_url}?token={token}")

@app.post("/sso/ldap/login")
async def ldap_login(
    provider_id: int = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    manager: SSOManager = Depends(get_sso_manager)
):
    """LDAP authentication"""
    user = await manager.authenticate_ldap(provider_id, username, password)
    
    # Generate JWT token
    token = jwt.encode(
        {
            "sub": user.id,
            "email": user.email,
            "name": user.name,
            "tenant_id": user.tenant_id,
            "provider": user.provider,
            "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
        },
        JWT_SECRET,
        algorithm=JWT_ALGORITHM
    )
    
    return {"token": token, "user": user.dict()}

@app.post("/sso/logout")
async def logout(
    session_id: str,
    manager: SSOManager = Depends(get_sso_manager)
):
    """Logout SSO session"""
    await manager.logout(session_id)
    return {"success": True, "message": "Logged out successfully"}

# SAML Metadata
@app.get("/sso/saml/metadata")
async def get_saml_metadata():
    """Get SP metadata for SAML configuration"""
    metadata = f"""<?xml version="1.0"?>
<EntityDescriptor xmlns="urn:oasis:names:tc:SAML:2.0:metadata"
                  entityID="{BASE_URL}/sso/saml/metadata">
    <SPSSODescriptor protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">
        <AssertionConsumerService 
            Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
            Location="{BASE_URL}/sso/saml/callback"
            index="0" />
    </SPSSODescriptor>
</EntityDescriptor>"""
    
    return Response(content=metadata, media_type="application/xml")

# Session Validation
@app.get("/sso/validate")
async def validate_session(
    session_id: str = Query(...),
    manager: SSOManager = Depends(get_sso_manager)
):
    """Validate SSO session"""
    session = await manager.validate_session(session_id)
    if session:
        return {
            "valid": True,
            "user_id": session.user_id,
            "email": session.email,
            "tenant_id": session.tenant_id,
            "expires_at": session.expires_at
        }
    else:
        return {"valid": False}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=SERVICE_PORT)