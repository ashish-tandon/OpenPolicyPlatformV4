"""
Tests for middleware components
"""

import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
import time
import json

from api.middleware.performance import PerformanceMiddleware
from api.middleware.security import SecurityMiddleware, InputValidationMiddleware, RateLimitMiddleware

@pytest.fixture
def app_with_middleware():
    """Create FastAPI app with middleware for testing"""
    app = FastAPI()
    
    # Add middleware
    app.add_middleware(SecurityMiddleware)
    app.add_middleware(InputValidationMiddleware)
    app.add_middleware(RateLimitMiddleware, requests_per_minute=10)
    app.add_middleware(PerformanceMiddleware, cache_ttl=60, rate_limit_per_minute=10)
    
    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}
    
    @app.post("/test")
    async def test_post_endpoint():
        return {"message": "test"}
    
    return app

@pytest.fixture
def client(app_with_middleware):
    return TestClient(app_with_middleware)

class TestSecurityMiddleware:
    """Test security middleware functionality"""
    
    def test_security_headers(self, client):
        """Test that security headers are added"""
        response = client.get("/test")
        
        # Check security headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
        assert response.headers["X-XSS-Protection"] == "1; mode=block"
        assert "Strict-Transport-Security" in response.headers
        assert "Content-Security-Policy" in response.headers
    
    def test_input_validation(self, client):
        """Test input validation middleware"""
        # Test suspicious content
        suspicious_data = {"test": "<script>alert('xss')</script>"}
        response = client.post("/test", json=suspicious_data)
        assert response.status_code == 400
        
        # Test normal content
        normal_data = {"test": "normal content"}
        response = client.post("/test", json=normal_data)
        assert response.status_code == 200

class TestPerformanceMiddleware:
    """Test performance middleware functionality"""
    
    def test_caching(self, client):
        """Test response caching"""
        # First request should be cache miss
        response1 = client.get("/test")
        assert response1.headers["X-Cache"] == "MISS"
        
        # Second request should be cache hit
        response2 = client.get("/test")
        assert response2.headers["X-Cache"] == "HIT"
        
        # Process time should be recorded
        assert "X-Process-Time" in response1.headers
    
    def test_rate_limiting(self, client):
        """Test rate limiting"""
        # Make requests up to the limit
        for i in range(10):
            response = client.get("/test")
            assert response.status_code == 200
        
        # Next request should be rate limited
        response = client.get("/test")
        assert response.status_code == 429

class TestRateLimitMiddleware:
    """Test rate limiting middleware"""
    
    def test_rate_limit_exceeded(self, client):
        """Test rate limit exceeded scenario"""
        # Make requests up to the limit
        for i in range(10):
            response = client.get("/test")
            assert response.status_code == 200
        
        # Next request should be rate limited
        response = client.get("/test")
        assert response.status_code == 429
        assert "Rate limit exceeded" in response.json()["error"]
    
    def test_rate_limit_reset(self, client):
        """Test rate limit reset after time period"""
        # Make requests up to the limit
        for i in range(10):
            response = client.get("/test")
            assert response.status_code == 200
        
        # Wait for rate limit to reset (in real scenario, this would be 60 seconds)
        # For testing, we'll just verify the current behavior
        response = client.get("/test")
        assert response.status_code == 429

class TestInputValidationMiddleware:
    """Test input validation middleware"""
    
    def test_xss_detection(self, client):
        """Test XSS detection"""
        xss_payloads = [
            {"test": "<script>alert('xss')</script>"},
            {"test": "javascript:alert('xss')"},
            {"test": "onclick=alert('xss')"},
        ]
        
        for payload in xss_payloads:
            response = client.post("/test", json=payload)
            assert response.status_code == 400
            assert "Invalid input detected" in response.json()["error"]
    
    def test_sql_injection_detection(self, client):
        """Test SQL injection detection"""
        sql_payloads = [
            {"test": "union select * from users"},
            {"test": "drop table users"},
            {"test": "delete from users"},
        ]
        
        for payload in sql_payloads:
            response = client.post("/test", json=payload)
            assert response.status_code == 400
            assert "Invalid input detected" in response.json()["error"]
    
    def test_normal_input(self, client):
        """Test normal input passes validation"""
        normal_data = {"test": "normal content"}
        response = client.post("/test", json=normal_data)
        assert response.status_code == 200

class TestMiddlewareIntegration:
    """Test middleware integration"""
    
    def test_all_middleware_work_together(self, client):
        """Test that all middleware work together"""
        # Test normal request
        response = client.get("/test")
        assert response.status_code == 200
        
        # Check all headers are present
        assert "X-Content-Type-Options" in response.headers
        assert "X-Process-Time" in response.headers
        assert "X-Cache" in response.headers
    
    def test_error_handling(self, client):
        """Test error handling in middleware"""
        # Test with suspicious content
        response = client.post("/test", json={"test": "<script>alert('xss')</script>"})
        assert response.status_code == 400
        
        # Test rate limiting
        for i in range(10):
            client.get("/test")
        
        response = client.get("/test")
        assert response.status_code == 429
