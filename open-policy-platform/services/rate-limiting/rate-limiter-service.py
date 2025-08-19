"""
Rate Limiting and DDoS Protection Service for OpenPolicy Platform
Provides distributed rate limiting with Redis backend
"""

import os
import time
import json
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import ipaddress

from fastapi import FastAPI, Request, Response, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import redis
from redis.sentinel import Sentinel
import aioredis
from pydantic import BaseModel, Field

# Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
REDIS_SENTINEL_HOSTS = os.getenv("REDIS_SENTINEL_HOSTS", "").split(",")
SERVICE_PORT = int(os.getenv("SERVICE_PORT", "9026"))
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Rate Limiting Service",
    description="API rate limiting and DDoS protection",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting algorithms
class RateLimitAlgorithm(str, Enum):
    TOKEN_BUCKET = "token_bucket"
    SLIDING_WINDOW = "sliding_window"
    FIXED_WINDOW = "fixed_window"
    LEAKY_BUCKET = "leaky_bucket"

# Models
class RateLimitRule(BaseModel):
    """Rate limit rule configuration"""
    key: str = Field(..., description="Unique identifier for the rule")
    name: str = Field(..., description="Human-readable name")
    description: Optional[str] = None
    
    # Limits
    requests_per_second: Optional[float] = None
    requests_per_minute: Optional[int] = None
    requests_per_hour: Optional[int] = None
    requests_per_day: Optional[int] = None
    
    # Burst allowance
    burst_size: Optional[int] = Field(None, description="Maximum burst size")
    
    # Algorithm
    algorithm: RateLimitAlgorithm = RateLimitAlgorithm.SLIDING_WINDOW
    
    # Scope
    scope: str = Field("global", description="Scope: global, user, ip, endpoint")
    endpoints: List[str] = Field(default_factory=list, description="Specific endpoints")
    
    # Actions
    block_duration: int = Field(60, description="Block duration in seconds when limit exceeded")
    response_code: int = Field(429, description="HTTP response code")
    
    # Conditions
    enabled: bool = True
    exempt_roles: List[str] = Field(default_factory=list)
    exempt_ips: List[str] = Field(default_factory=list)
    
    # Priority (lower number = higher priority)
    priority: int = Field(100)

class RateLimitContext(BaseModel):
    """Context for rate limit evaluation"""
    client_ip: str
    user_id: Optional[str] = None
    user_role: Optional[str] = None
    endpoint: str
    method: str = "GET"
    api_key: Optional[str] = None
    request_size: Optional[int] = None
    custom_attributes: Dict[str, Any] = Field(default_factory=dict)

class RateLimitResponse(BaseModel):
    """Rate limit check response"""
    allowed: bool
    limit: int
    remaining: int
    reset_at: datetime
    retry_after: Optional[int] = None
    reason: Optional[str] = None

# Redis connection
if REDIS_SENTINEL_HOSTS and REDIS_SENTINEL_HOSTS[0]:
    # Redis Sentinel for HA
    sentinel = Sentinel([(host.split(":")[0], int(host.split(":")[1])) for host in REDIS_SENTINEL_HOSTS])
    redis_master = sentinel.master_for('mymaster', socket_timeout=0.1)
else:
    # Single Redis instance
    redis_master = redis.from_url(REDIS_URL, decode_responses=True)

# Async Redis for high performance
async_redis = None

async def get_async_redis():
    global async_redis
    if not async_redis:
        async_redis = await aioredis.from_url(REDIS_URL, decode_responses=True)
    return async_redis

# Rate limiting algorithms implementation
class RateLimiter:
    @staticmethod
    async def token_bucket(
        redis_client,
        key: str,
        rate: float,
        capacity: int,
        requested: int = 1
    ) -> Tuple[bool, int]:
        """
        Token bucket algorithm
        Returns: (allowed, tokens_remaining)
        """
        now = time.time()
        
        # Lua script for atomic token bucket
        lua_script = """
        local key = KEYS[1]
        local rate = tonumber(ARGV[1])
        local capacity = tonumber(ARGV[2])
        local now = tonumber(ARGV[3])
        local requested = tonumber(ARGV[4])
        
        local bucket = redis.call('HMGET', key, 'tokens', 'last_update')
        local tokens = tonumber(bucket[1]) or capacity
        local last_update = tonumber(bucket[2]) or now
        
        -- Calculate tokens to add
        local elapsed = math.max(0, now - last_update)
        local new_tokens = math.min(capacity, tokens + (elapsed * rate))
        
        if new_tokens >= requested then
            -- Allow request
            new_tokens = new_tokens - requested
            redis.call('HMSET', key, 'tokens', new_tokens, 'last_update', now)
            redis.call('EXPIRE', key, 3600)
            return {1, math.floor(new_tokens)}
        else
            -- Deny request
            redis.call('HMSET', key, 'tokens', new_tokens, 'last_update', now)
            redis.call('EXPIRE', key, 3600)
            return {0, math.floor(new_tokens)}
        end
        """
        
        result = await redis_client.eval(lua_script, 1, key, rate, capacity, now, requested)
        return bool(result[0]), result[1]
    
    @staticmethod
    async def sliding_window(
        redis_client,
        key: str,
        window_size: int,
        limit: int
    ) -> Tuple[bool, int]:
        """
        Sliding window algorithm using Redis sorted sets
        Returns: (allowed, requests_in_window)
        """
        now = time.time()
        window_start = now - window_size
        
        # Lua script for atomic sliding window
        lua_script = """
        local key = KEYS[1]
        local now = tonumber(ARGV[1])
        local window_start = tonumber(ARGV[2])
        local limit = tonumber(ARGV[3])
        
        -- Remove old entries
        redis.call('ZREMRANGEBYSCORE', key, 0, window_start)
        
        -- Count requests in window
        local count = redis.call('ZCARD', key)
        
        if count < limit then
            -- Allow request
            redis.call('ZADD', key, now, now)
            redis.call('EXPIRE', key, ARGV[4])
            return {1, count + 1}
        else
            -- Deny request
            return {0, count}
        end
        """
        
        result = await redis_client.eval(
            lua_script, 1, key, now, window_start, limit, window_size + 60
        )
        return bool(result[0]), result[1]
    
    @staticmethod
    async def fixed_window(
        redis_client,
        key: str,
        window_size: int,
        limit: int
    ) -> Tuple[bool, int]:
        """
        Fixed window counter algorithm
        Returns: (allowed, requests_in_window)
        """
        now = int(time.time())
        window_id = now // window_size
        window_key = f"{key}:{window_id}"
        
        # Atomic increment
        count = await redis_client.incr(window_key)
        
        if count == 1:
            # First request in window, set expiry
            await redis_client.expire(window_key, window_size + 60)
        
        allowed = count <= limit
        return allowed, min(count, limit)
    
    @staticmethod
    async def leaky_bucket(
        redis_client,
        key: str,
        rate: float,
        capacity: int
    ) -> Tuple[bool, int]:
        """
        Leaky bucket algorithm
        Returns: (allowed, queue_size)
        """
        now = time.time()
        
        # Lua script for atomic leaky bucket
        lua_script = """
        local key = KEYS[1]
        local rate = tonumber(ARGV[1])
        local capacity = tonumber(ARGV[2])
        local now = tonumber(ARGV[3])
        
        local bucket = redis.call('HMGET', key, 'volume', 'last_leak')
        local volume = tonumber(bucket[1]) or 0
        local last_leak = tonumber(bucket[2]) or now
        
        -- Calculate leaked amount
        local elapsed = math.max(0, now - last_leak)
        local leaked = elapsed * rate
        volume = math.max(0, volume - leaked)
        
        if volume < capacity then
            -- Allow request
            volume = volume + 1
            redis.call('HMSET', key, 'volume', volume, 'last_leak', now)
            redis.call('EXPIRE', key, 3600)
            return {1, math.floor(volume)}
        else
            -- Deny request
            redis.call('HMSET', key, 'volume', volume, 'last_leak', now)
            redis.call('EXPIRE', key, 3600)
            return {0, math.floor(volume)}
        end
        """
        
        result = await redis_client.eval(lua_script, 1, key, rate, capacity, now)
        return bool(result[0]), result[1]

# DDoS protection
class DDoSProtection:
    # Suspicious patterns
    SUSPICIOUS_USER_AGENTS = [
        "bot", "crawler", "spider", "scraper", "curl", "wget",
        "python-requests", "go-http-client", "java"
    ]
    
    # Known bad IPs (would be loaded from threat intelligence)
    BLOCKED_IPS = set()
    
    # GeoIP blocking (simplified)
    BLOCKED_COUNTRIES = {"CN", "RU", "KP"}  # Example
    
    @staticmethod
    async def check_ip_reputation(ip: str) -> Tuple[bool, Optional[str]]:
        """Check IP reputation"""
        # Check if IP is in blocked list
        if ip in DDoSProtection.BLOCKED_IPS:
            return False, "IP is blocked"
        
        # Check if IP is private/local
        try:
            ip_obj = ipaddress.ip_address(ip)
            if ip_obj.is_private or ip_obj.is_loopback:
                return True, None  # Allow local IPs in dev
        except ValueError:
            return False, "Invalid IP address"
        
        # Check rate of new IPs
        redis_client = await get_async_redis()
        first_seen_key = f"ip:first_seen:{ip}"
        
        first_seen = await redis_client.get(first_seen_key)
        if not first_seen:
            # New IP, track it
            await redis_client.setex(first_seen_key, 86400, time.time())
            
            # Check new IP rate
            new_ip_key = "ddos:new_ips:count"
            new_ip_count = await redis_client.incr(new_ip_key)
            if new_ip_count == 1:
                await redis_client.expire(new_ip_key, 60)
            
            if new_ip_count > 100:  # More than 100 new IPs per minute
                return False, "Too many new IPs"
        
        return True, None
    
    @staticmethod
    async def check_user_agent(user_agent: str) -> Tuple[bool, Optional[str]]:
        """Check user agent for suspicious patterns"""
        if not user_agent:
            return False, "Missing user agent"
        
        ua_lower = user_agent.lower()
        
        # Check suspicious patterns
        for pattern in DDoSProtection.SUSPICIOUS_USER_AGENTS:
            if pattern in ua_lower and "googlebot" not in ua_lower:
                # Additional verification for claimed bots
                return False, f"Suspicious user agent: {pattern}"
        
        return True, None
    
    @staticmethod
    async def check_request_pattern(
        client_ip: str,
        endpoint: str,
        method: str
    ) -> Tuple[bool, Optional[str]]:
        """Check for suspicious request patterns"""
        redis_client = await get_async_redis()
        
        # Track endpoint diversity
        endpoint_key = f"ddos:ip:{client_ip}:endpoints"
        await redis_client.sadd(endpoint_key, endpoint)
        await redis_client.expire(endpoint_key, 60)
        
        endpoint_count = await redis_client.scard(endpoint_key)
        
        # Suspicious if hitting too many different endpoints rapidly
        if endpoint_count > 50:  # More than 50 different endpoints per minute
            return False, "Suspicious request pattern"
        
        # Check for credential stuffing
        if endpoint in ["/api/auth/login", "/api/auth/register"]:
            auth_key = f"ddos:ip:{client_ip}:auth_attempts"
            auth_attempts = await redis_client.incr(auth_key)
            if auth_attempts == 1:
                await redis_client.expire(auth_key, 300)  # 5 minutes
            
            if auth_attempts > 10:  # More than 10 auth attempts in 5 minutes
                return False, "Too many authentication attempts"
        
        return True, None

# Rule management
class RuleManager:
    @staticmethod
    async def load_rules() -> List[RateLimitRule]:
        """Load rate limit rules from Redis"""
        redis_client = await get_async_redis()
        
        # Default rules
        default_rules = [
            RateLimitRule(
                key="global_default",
                name="Global Default Rate Limit",
                description="Default rate limit for all endpoints",
                requests_per_second=10,
                requests_per_minute=100,
                requests_per_hour=1000,
                algorithm=RateLimitAlgorithm.SLIDING_WINDOW,
                scope="ip",
                priority=1000
            ),
            RateLimitRule(
                key="api_strict",
                name="Strict API Rate Limit",
                description="Strict limits for sensitive endpoints",
                requests_per_minute=20,
                requests_per_hour=100,
                algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
                burst_size=5,
                scope="user",
                endpoints=["/api/auth/*", "/api/admin/*"],
                priority=10
            ),
            RateLimitRule(
                key="public_api",
                name="Public API Rate Limit",
                description="Relaxed limits for public endpoints",
                requests_per_second=50,
                requests_per_minute=1000,
                algorithm=RateLimitAlgorithm.SLIDING_WINDOW,
                scope="ip",
                endpoints=["/api/v1/public/*"],
                exempt_roles=["premium", "enterprise"],
                priority=50
            ),
            RateLimitRule(
                key="search_limit",
                name="Search Rate Limit",
                description="Prevent search abuse",
                requests_per_minute=30,
                algorithm=RateLimitAlgorithm.LEAKY_BUCKET,
                scope="user",
                endpoints=["/api/search", "/api/v1/search"],
                priority=20
            )
        ]
        
        # Load custom rules from Redis
        custom_rules_data = await redis_client.get("rate_limit:rules")
        if custom_rules_data:
            custom_rules = json.loads(custom_rules_data)
            for rule_data in custom_rules:
                default_rules.append(RateLimitRule(**rule_data))
        
        # Sort by priority
        default_rules.sort(key=lambda r: r.priority)
        
        return default_rules
    
    @staticmethod
    async def save_rule(rule: RateLimitRule):
        """Save a rate limit rule"""
        redis_client = await get_async_redis()
        
        # Get existing rules
        rules_data = await redis_client.get("rate_limit:rules") or "[]"
        rules = json.loads(rules_data)
        
        # Update or add rule
        rule_dict = rule.dict()
        rules = [r for r in rules if r.get("key") != rule.key]
        rules.append(rule_dict)
        
        # Save back
        await redis_client.set("rate_limit:rules", json.dumps(rules))
    
    @staticmethod
    def match_endpoint(pattern: str, endpoint: str) -> bool:
        """Check if endpoint matches pattern"""
        import fnmatch
        return fnmatch.fnmatch(endpoint, pattern)

# Main rate limiting logic
class RateLimitService:
    @staticmethod
    async def check_rate_limit(context: RateLimitContext) -> RateLimitResponse:
        """Check if request is allowed under rate limits"""
        redis_client = await get_async_redis()
        
        # DDoS protection checks first
        ip_allowed, ip_reason = await DDoSProtection.check_ip_reputation(context.client_ip)
        if not ip_allowed:
            return RateLimitResponse(
                allowed=False,
                limit=0,
                remaining=0,
                reset_at=datetime.utcnow() + timedelta(hours=24),
                retry_after=86400,
                reason=ip_reason
            )
        
        # Load rules
        rules = await RuleManager.load_rules()
        
        # Find applicable rule
        applicable_rule = None
        for rule in rules:
            if not rule.enabled:
                continue
            
            # Check exemptions
            if context.user_role and context.user_role in rule.exempt_roles:
                continue
            if context.client_ip in rule.exempt_ips:
                continue
            
            # Check endpoint match
            if rule.endpoints:
                matched = False
                for pattern in rule.endpoints:
                    if RuleManager.match_endpoint(pattern, context.endpoint):
                        matched = True
                        break
                if not matched:
                    continue
            
            applicable_rule = rule
            break
        
        if not applicable_rule:
            # No rate limit applies
            return RateLimitResponse(
                allowed=True,
                limit=999999,
                remaining=999999,
                reset_at=datetime.utcnow() + timedelta(hours=1)
            )
        
        # Generate rate limit key
        if applicable_rule.scope == "global":
            rate_key = f"rate_limit:{applicable_rule.key}:global"
        elif applicable_rule.scope == "ip":
            rate_key = f"rate_limit:{applicable_rule.key}:ip:{context.client_ip}"
        elif applicable_rule.scope == "user":
            user_id = context.user_id or context.client_ip
            rate_key = f"rate_limit:{applicable_rule.key}:user:{user_id}"
        elif applicable_rule.scope == "endpoint":
            rate_key = f"rate_limit:{applicable_rule.key}:endpoint:{context.endpoint}"
        else:
            rate_key = f"rate_limit:{applicable_rule.key}:custom"
        
        # Apply rate limiting algorithm
        allowed = True
        remaining = 0
        limit = 0
        reset_at = datetime.utcnow()
        
        # Check different time windows
        if applicable_rule.requests_per_second:
            if applicable_rule.algorithm == RateLimitAlgorithm.TOKEN_BUCKET:
                allowed, remaining = await RateLimiter.token_bucket(
                    redis_client,
                    f"{rate_key}:second",
                    applicable_rule.requests_per_second,
                    applicable_rule.burst_size or applicable_rule.requests_per_second * 2
                )
            else:
                allowed, count = await RateLimiter.sliding_window(
                    redis_client,
                    f"{rate_key}:second",
                    1,
                    applicable_rule.requests_per_second
                )
                remaining = max(0, applicable_rule.requests_per_second - count)
            
            limit = applicable_rule.requests_per_second
            reset_at = datetime.utcnow() + timedelta(seconds=1)
        
        if allowed and applicable_rule.requests_per_minute:
            if applicable_rule.algorithm == RateLimitAlgorithm.SLIDING_WINDOW:
                allowed, count = await RateLimiter.sliding_window(
                    redis_client,
                    f"{rate_key}:minute",
                    60,
                    applicable_rule.requests_per_minute
                )
                remaining = max(0, applicable_rule.requests_per_minute - count)
            else:
                allowed, count = await RateLimiter.fixed_window(
                    redis_client,
                    f"{rate_key}:minute",
                    60,
                    applicable_rule.requests_per_minute
                )
                remaining = max(0, applicable_rule.requests_per_minute - count)
            
            limit = applicable_rule.requests_per_minute
            reset_at = datetime.utcnow() + timedelta(minutes=1)
        
        if allowed and applicable_rule.requests_per_hour:
            allowed, count = await RateLimiter.sliding_window(
                redis_client,
                f"{rate_key}:hour",
                3600,
                applicable_rule.requests_per_hour
            )
            remaining = max(0, applicable_rule.requests_per_hour - count)
            limit = applicable_rule.requests_per_hour
            reset_at = datetime.utcnow() + timedelta(hours=1)
        
        if allowed and applicable_rule.requests_per_day:
            allowed, count = await RateLimiter.fixed_window(
                redis_client,
                f"{rate_key}:day",
                86400,
                applicable_rule.requests_per_day
            )
            remaining = max(0, applicable_rule.requests_per_day - count)
            limit = applicable_rule.requests_per_day
            reset_at = datetime.utcnow() + timedelta(days=1)
        
        # Handle rate limit exceeded
        if not allowed:
            # Track violations
            violation_key = f"rate_limit:violations:{context.client_ip}"
            violations = await redis_client.incr(violation_key)
            if violations == 1:
                await redis_client.expire(violation_key, 3600)
            
            # Auto-block repeat offenders
            if violations > 10:
                block_key = f"rate_limit:blocked:{context.client_ip}"
                await redis_client.setex(block_key, applicable_rule.block_duration, 1)
                
                return RateLimitResponse(
                    allowed=False,
                    limit=limit,
                    remaining=0,
                    reset_at=datetime.utcnow() + timedelta(seconds=applicable_rule.block_duration),
                    retry_after=applicable_rule.block_duration,
                    reason="Temporarily blocked due to repeated violations"
                )
        
        return RateLimitResponse(
            allowed=allowed,
            limit=limit,
            remaining=remaining,
            reset_at=reset_at,
            retry_after=int((reset_at - datetime.utcnow()).total_seconds()) if not allowed else None,
            reason=f"Rate limit exceeded for {applicable_rule.name}" if not allowed else None
        )

# FastAPI middleware
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware"""
    # Skip rate limiting for health checks
    if request.url.path == "/health":
        return await call_next(request)
    
    # Extract context
    client_ip = request.client.host
    user_id = request.headers.get("X-User-ID")
    user_role = request.headers.get("X-User-Role")
    api_key = request.headers.get("X-API-Key")
    
    context = RateLimitContext(
        client_ip=client_ip,
        user_id=user_id,
        user_role=user_role,
        endpoint=request.url.path,
        method=request.method,
        api_key=api_key
    )
    
    # Check rate limit
    result = await RateLimitService.check_rate_limit(context)
    
    if not result.allowed:
        # Rate limit exceeded
        headers = {
            "X-RateLimit-Limit": str(result.limit),
            "X-RateLimit-Remaining": str(result.remaining),
            "X-RateLimit-Reset": str(int(result.reset_at.timestamp())),
            "Retry-After": str(result.retry_after)
        }
        
        return JSONResponse(
            status_code=429,
            content={
                "error": "Rate limit exceeded",
                "message": result.reason or "Too many requests",
                "retry_after": result.retry_after
            },
            headers=headers
        )
    
    # Add rate limit headers
    response = await call_next(request)
    response.headers["X-RateLimit-Limit"] = str(result.limit)
    response.headers["X-RateLimit-Remaining"] = str(result.remaining)
    response.headers["X-RateLimit-Reset"] = str(int(result.reset_at.timestamp()))
    
    return response

# API endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "rate-limiting",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/check")
async def check_rate_limit(context: RateLimitContext):
    """Check if a request would be rate limited"""
    result = await RateLimitService.check_rate_limit(context)
    return result

@app.get("/rules")
async def get_rules():
    """Get all rate limit rules"""
    rules = await RuleManager.load_rules()
    return {"rules": rules}

@app.post("/rules")
async def create_rule(rule: RateLimitRule):
    """Create or update a rate limit rule"""
    await RuleManager.save_rule(rule)
    return {"status": "created", "rule": rule}

@app.delete("/rules/{rule_key}")
async def delete_rule(rule_key: str):
    """Delete a rate limit rule"""
    redis_client = await get_async_redis()
    
    # Get existing rules
    rules_data = await redis_client.get("rate_limit:rules") or "[]"
    rules = json.loads(rules_data)
    
    # Remove rule
    rules = [r for r in rules if r.get("key") != rule_key]
    
    # Save back
    await redis_client.set("rate_limit:rules", json.dumps(rules))
    
    return {"status": "deleted"}

@app.get("/blocked")
async def get_blocked_ips():
    """Get list of blocked IPs"""
    redis_client = await get_async_redis()
    
    # Scan for blocked IPs
    blocked_ips = []
    cursor = 0
    
    while True:
        cursor, keys = await redis_client.scan(
            cursor, match="rate_limit:blocked:*", count=100
        )
        
        for key in keys:
            ip = key.split(":")[-1]
            ttl = await redis_client.ttl(key)
            blocked_ips.append({
                "ip": ip,
                "expires_in": ttl
            })
        
        if cursor == 0:
            break
    
    return {"blocked_ips": blocked_ips}

@app.delete("/blocked/{ip}")
async def unblock_ip(ip: str):
    """Unblock an IP address"""
    redis_client = await get_async_redis()
    
    block_key = f"rate_limit:blocked:{ip}"
    await redis_client.delete(block_key)
    
    # Clear violation counter
    violation_key = f"rate_limit:violations:{ip}"
    await redis_client.delete(violation_key)
    
    return {"status": "unblocked", "ip": ip}

@app.get("/stats")
async def get_stats():
    """Get rate limiting statistics"""
    redis_client = await get_async_redis()
    
    # Get current stats
    stats = {
        "total_requests": await redis_client.get("rate_limit:stats:total_requests") or 0,
        "blocked_requests": await redis_client.get("rate_limit:stats:blocked_requests") or 0,
        "unique_ips": await redis_client.scard("rate_limit:stats:unique_ips"),
        "blocked_ips_count": 0,
        "rules_count": len(await RuleManager.load_rules())
    }
    
    # Count blocked IPs
    cursor = 0
    while True:
        cursor, keys = await redis_client.scan(
            cursor, match="rate_limit:blocked:*", count=100
        )
        stats["blocked_ips_count"] += len(keys)
        
        if cursor == 0:
            break
    
    return stats

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=SERVICE_PORT)