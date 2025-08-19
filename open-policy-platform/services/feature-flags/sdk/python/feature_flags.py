"""
Python SDK for OpenPolicy Platform Feature Flags
"""

import os
import json
import logging
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, asdict
import requests
from functools import lru_cache
import threading
import time

logger = logging.getLogger(__name__)

@dataclass
class FlagContext:
    """Context for evaluating feature flags"""
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    user_role: Optional[str] = None
    organization_id: Optional[str] = None
    environment: str = "production"
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    custom_attributes: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.custom_attributes is None:
            self.custom_attributes = {}

class FeatureFlagClient:
    """Client for feature flag service"""
    
    def __init__(
        self,
        service_url: str = None,
        api_key: Optional[str] = None,
        default_timeout: int = 5,
        enable_cache: bool = True,
        cache_ttl: int = 300,
        fallback_values: Optional[Dict[str, Any]] = None
    ):
        self.service_url = service_url or os.getenv("FEATURE_FLAG_SERVICE_URL", "http://localhost:9024")
        self.api_key = api_key or os.getenv("FEATURE_FLAG_API_KEY")
        self.timeout = default_timeout
        self.enable_cache = enable_cache
        self.cache_ttl = cache_ttl
        self.fallback_values = fallback_values or {}
        self._cache = {}
        self._cache_timestamps = {}
        self._lock = threading.Lock()
        
        # Session for connection pooling
        self.session = requests.Session()
        if self.api_key:
            self.session.headers["X-API-Key"] = self.api_key
    
    def _is_cache_valid(self, key: str) -> bool:
        """Check if cached value is still valid"""
        if key not in self._cache_timestamps:
            return False
        return time.time() - self._cache_timestamps[key] < self.cache_ttl
    
    def _get_from_cache(self, key: str) -> Optional[Any]:
        """Get value from cache if valid"""
        with self._lock:
            if self.enable_cache and self._is_cache_valid(key):
                return self._cache.get(key)
        return None
    
    def _set_cache(self, key: str, value: Any):
        """Set value in cache"""
        with self._lock:
            self._cache[key] = value
            self._cache_timestamps[key] = time.time()
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Make HTTP request to feature flag service"""
        url = f"{self.service_url}{endpoint}"
        kwargs.setdefault("timeout", self.timeout)
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Feature flag request failed: {e}")
            return None
    
    def evaluate(
        self,
        flag_key: str,
        context: Union[FlagContext, Dict[str, Any]],
        default_value: Any = None
    ) -> Any:
        """Evaluate a single feature flag"""
        # Convert dict to FlagContext if needed
        if isinstance(context, dict):
            context = FlagContext(**context)
        
        # Generate cache key
        cache_key = f"{flag_key}:{hash(json.dumps(asdict(context), sort_keys=True))}"
        
        # Check cache
        cached_value = self._get_from_cache(cache_key)
        if cached_value is not None:
            return cached_value
        
        # Make request
        response = self._make_request(
            "POST",
            f"/evaluate/{flag_key}",
            json=asdict(context)
        )
        
        if response:
            value = response.get("value", default_value)
            self._set_cache(cache_key, value)
            return value
        
        # Fall back to configured fallback or provided default
        return self.fallback_values.get(flag_key, default_value)
    
    def evaluate_batch(
        self,
        flag_keys: List[str],
        context: Union[FlagContext, Dict[str, Any]],
        default_values: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Evaluate multiple feature flags"""
        # Convert dict to FlagContext if needed
        if isinstance(context, dict):
            context = FlagContext(**context)
        
        default_values = default_values or {}
        
        # Check cache for all flags
        results = {}
        uncached_keys = []
        
        for flag_key in flag_keys:
            cache_key = f"{flag_key}:{hash(json.dumps(asdict(context), sort_keys=True))}"
            cached_value = self._get_from_cache(cache_key)
            if cached_value is not None:
                results[flag_key] = cached_value
            else:
                uncached_keys.append(flag_key)
        
        # Fetch uncached flags
        if uncached_keys:
            response = self._make_request(
                "POST",
                "/evaluate/batch",
                json={
                    "flag_keys": uncached_keys,
                    "context": asdict(context)
                }
            )
            
            if response and "evaluations" in response:
                for flag_key, evaluation in response["evaluations"].items():
                    value = evaluation.get("value")
                    if value is not None:
                        results[flag_key] = value
                        # Cache the result
                        cache_key = f"{flag_key}:{hash(json.dumps(asdict(context), sort_keys=True))}"
                        self._set_cache(cache_key, value)
        
        # Apply defaults for missing flags
        for flag_key in flag_keys:
            if flag_key not in results:
                results[flag_key] = default_values.get(
                    flag_key,
                    self.fallback_values.get(flag_key)
                )
        
        return results
    
    def get_all_flags(self) -> Optional[List[Dict[str, Any]]]:
        """Get all feature flags"""
        response = self._make_request("GET", "/flags")
        if response:
            return response.get("flags", [])
        return None
    
    def clear_cache(self):
        """Clear local cache"""
        with self._lock:
            self._cache.clear()
            self._cache_timestamps.clear()

# Decorator for feature flags
class feature_flag:
    """Decorator for feature flag controlled functions"""
    
    def __init__(
        self,
        flag_key: str,
        default_value: bool = False,
        client: Optional[FeatureFlagClient] = None
    ):
        self.flag_key = flag_key
        self.default_value = default_value
        self.client = client or _default_client
    
    def __call__(self, func):
        def wrapper(*args, **kwargs):
            # Extract context from function arguments
            context = kwargs.get("flag_context") or FlagContext()
            
            # Evaluate flag
            if self.client.evaluate(self.flag_key, context, self.default_value):
                return func(*args, **kwargs)
            else:
                # Return None or raise exception based on function
                return None
        
        return wrapper

# Global default client
_default_client = FeatureFlagClient()

# Convenience functions
def init(
    service_url: str = None,
    api_key: str = None,
    **kwargs
):
    """Initialize the default feature flag client"""
    global _default_client
    _default_client = FeatureFlagClient(
        service_url=service_url,
        api_key=api_key,
        **kwargs
    )

def evaluate(flag_key: str, context: Union[FlagContext, Dict[str, Any]], default_value: Any = None) -> Any:
    """Evaluate a feature flag using the default client"""
    return _default_client.evaluate(flag_key, context, default_value)

def evaluate_batch(
    flag_keys: List[str],
    context: Union[FlagContext, Dict[str, Any]],
    default_values: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Evaluate multiple feature flags using the default client"""
    return _default_client.evaluate_batch(flag_keys, context, default_values)

# Example usage
if __name__ == "__main__":
    # Initialize client
    client = FeatureFlagClient(
        service_url="http://localhost:9024",
        fallback_values={
            "new_ui": False,
            "dark_mode": True,
            "api_v2": False
        }
    )
    
    # Create context
    context = FlagContext(
        user_id="user-123",
        user_email="user@example.com",
        user_role="admin",
        organization_id="org-456",
        custom_attributes={
            "plan": "premium",
            "country": "US"
        }
    )
    
    # Evaluate single flag
    new_ui_enabled = client.evaluate("new_ui", context, default_value=False)
    print(f"New UI enabled: {new_ui_enabled}")
    
    # Evaluate multiple flags
    flags = client.evaluate_batch(
        ["new_ui", "dark_mode", "api_v2"],
        context
    )
    print(f"Flags: {flags}")
    
    # Using decorator
    @feature_flag("experimental_feature", default_value=False)
    def experimental_function():
        return "This is experimental!"
    
    result = experimental_function(flag_context=context)
    print(f"Experimental result: {result}")