"""
Security Tests
Tests that verify all security measures are properly implemented
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
import re
import jwt
from datetime import datetime, timedelta

class TestSecurityMeasures:
    """Test security measures implementation"""
    
    def test_password_strength_validation(self, client, db_session):
        """Test password strength validation"""
        
        # Test weak passwords
        weak_passwords = [
            "123",  # Too short
            "password",  # Common password
            "abc123",  # Too simple
            "qwerty",  # Common pattern
            "1234567890",  # Only numbers
            "abcdefghij",  # Only letters
        ]
        
        for weak_password in weak_passwords:
            account_data = {
                "username": "testuser",
                "email": "test@example.com",
                "password": weak_password,
                "first_name": "Test",
                "last_name": "User"
            }
            
            response = client.post("/api/auth/register", json=account_data)
            
            # Verify: Weak passwords are rejected
            assert response.status_code == 422
            data = response.json()
            assert "detail" in data
            assert "password" in str(data["detail"]).lower()
        
        # Test strong password
        strong_password = "SecurePass123!@#"
        account_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": strong_password,
            "first_name": "Test",
            "last_name": "User"
        }
        
        response = client.post("/api/auth/register", json=account_data)
        
        # Verify: Strong password is accepted
        assert response.status_code in [200, 201]
    
    def test_jwt_token_security(self, client, db_session):
        """Test JWT token security measures"""
        
        # Setup: Create test user
        db_session.execute(text("""
            INSERT INTO auth_user (username, email, password, is_active, is_staff)
            VALUES ('testuser', 'test@example.com', 'hashed_password', true, false)
        """))
        db_session.commit()
        
        # Test token expiration
        expired_payload = {
            "sub": "testuser",
            "exp": datetime.utcnow() - timedelta(hours=1),  # Expired
            "type": "access"
        }
        expired_token = jwt.encode(expired_payload, "test_secret", algorithm="HS256")
        
        headers = {"Authorization": f"Bearer {expired_token}"}
        response = client.get("/api/auth/me", headers=headers)
        
        # Verify: Expired token is rejected
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "expired" in data["detail"].lower()
        
        # Test invalid token signature
        invalid_payload = {
            "sub": "testuser",
            "exp": datetime.utcnow() + timedelta(hours=1),
            "type": "access"
        }
        invalid_token = jwt.encode(invalid_payload, "wrong_secret", algorithm="HS256")
        
        headers = {"Authorization": f"Bearer {invalid_token}"}
        response = client.get("/api/auth/me", headers=headers)
        
        # Verify: Invalid signature is rejected
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "invalid" in data["detail"].lower()
        
        # Test token without required claims
        incomplete_payload = {
            "sub": "testuser"
            # Missing exp and type
        }
        incomplete_token = jwt.encode(incomplete_payload, "test_secret", algorithm="HS256")
        
        headers = {"Authorization": f"Bearer {incomplete_token}"}
        response = client.get("/api/auth/me", headers=headers)
        
        # Verify: Incomplete token is rejected
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "invalid" in data["detail"].lower()
    
    def test_csrf_protection(self, client, db_session):
        """Test CSRF protection measures"""
        
        # Setup: Create test user and get session
        db_session.execute(text("""
            INSERT INTO auth_user (username, email, password, is_active, is_staff)
            VALUES ('testuser', 'test@example.com', 'hashed_password', true, false)
        """))
        db_session.commit()
        
        # Test CSRF token requirement for state-changing operations
        # First, get CSRF token
        response = client.get("/api/auth/csrf-token")
        assert response.status_code == 200
        csrf_token = response.json()["csrf_token"]
        
        # Test POST without CSRF token
        bill_data = {
            "title": "Test Bill",
            "description": "Test Description",
            "bill_number": "C-123",
            "jurisdiction": "federal"
        }
        
        response = client.post("/api/policies", json=bill_data)
        
        # Verify: Request without CSRF token is rejected
        assert response.status_code == 403
        data = response.json()
        assert "detail" in data
        assert "csrf" in data["detail"].lower()
        
        # Test POST with CSRF token
        headers = {"X-CSRF-Token": csrf_token}
        response = client.post("/api/policies", json=bill_data, headers=headers)
        
        # Verify: Request with CSRF token is accepted
        assert response.status_code in [200, 201]
        
        # Test PUT without CSRF token
        update_data = {
            "title": "Updated Bill Title"
        }
        
        response = client.put("/api/policies/1", json=update_data)
        
        # Verify: PUT without CSRF token is rejected
        assert response.status_code == 403
        
        # Test DELETE without CSRF token
        response = client.delete("/api/policies/1")
        
        # Verify: DELETE without CSRF token is rejected
        assert response.status_code == 403
    
    def test_sql_injection_prevention(self, client, db_session):
        """Test SQL injection prevention"""
        
        # Test SQL injection in search query
        sql_injection_payloads = [
            "'; DROP TABLE bills_bill; --",
            "' OR '1'='1",
            "' UNION SELECT * FROM auth_user --",
            "'; INSERT INTO bills_bill VALUES (999, 'Hacked', 'Hacked', 'H-999', '2024-01-01', 'Hacker', 'federal'); --",
            "' OR 1=1; --",
        ]
        
        for payload in sql_injection_payloads:
            search_data = {
                "query": payload,
                "jurisdiction": "federal"
            }
            
            response = client.post("/api/policies/search", json=search_data)
            
            # Verify: SQL injection attempts are handled safely
            assert response.status_code in [200, 400, 422]
            
            # Verify: No unauthorized data is returned
            if response.status_code == 200:
                data = response.json()
                assert "results" in data
                # Should not return all data or unauthorized data
                assert len(data["results"]) == 0 or "Hacked" not in str(data["results"])
        
        # Test SQL injection in filter parameters
        filter_data = {
            "jurisdiction": "federal'; DROP TABLE bills_bill; --",
            "status": "introduced"
        }
        
        response = client.post("/api/policies/filter", json=filter_data)
        
        # Verify: SQL injection in filters is handled safely
        assert response.status_code in [200, 400, 422]
        
        # Test SQL injection in URL parameters
        response = client.get(f"/api/policies?search={payload}")
        
        # Verify: SQL injection in URL is handled safely
        assert response.status_code in [200, 400, 422]
    
    def test_xss_prevention(self, client, db_session):
        """Test XSS prevention measures"""
        
        # Test XSS payloads in user input
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<svg onload=alert('XSS')>",
            "'><script>alert('XSS')</script>",
            "<iframe src=javascript:alert('XSS')>",
        ]
        
        for payload in xss_payloads:
            # Test XSS in bill title
            bill_data = {
                "title": payload,
                "description": "Test Description",
                "bill_number": "C-123",
                "jurisdiction": "federal"
            }
            
            response = client.post("/api/policies", json=bill_data)
            
            # Verify: XSS payloads are sanitized or rejected
            if response.status_code in [200, 201]:
                data = response.json()
                # Verify: Script tags are removed or escaped
                assert "<script>" not in str(data)
                assert "javascript:" not in str(data)
                assert "onerror=" not in str(data)
                assert "onload=" not in str(data)
            
            # Test XSS in search query
            search_data = {
                "query": payload,
                "jurisdiction": "federal"
            }
            
            response = client.post("/api/policies/search", json=search_data)
            
            # Verify: XSS in search is handled safely
            if response.status_code == 200:
                data = response.json()
                # Verify: Script tags are removed or escaped
                assert "<script>" not in str(data)
                assert "javascript:" not in str(data)
            
            # Test XSS in user profile
            profile_data = {
                "first_name": payload,
                "last_name": "User",
                "email": "test@example.com"
            }
            
            response = client.put("/api/auth/profile", json=profile_data)
            
            # Verify: XSS in profile is handled safely
            if response.status_code == 200:
                data = response.json()
                # Verify: Script tags are removed or escaped
                assert "<script>" not in str(data)
                assert "javascript:" not in str(data)
        
        # Test content security policy headers
        response = client.get("/api/policies")
        
        # Verify: CSP headers are present
        headers = response.headers
        assert "Content-Security-Policy" in headers
        
        csp_header = headers["Content-Security-Policy"]
        
        # Verify: CSP policy includes script-src restrictions
        assert "script-src" in csp_header
        assert "unsafe-inline" not in csp_header
        assert "unsafe-eval" not in csp_header
        
        # Verify: CSP policy includes object-src restrictions
        assert "object-src" in csp_header
        assert "data:" not in csp_header
