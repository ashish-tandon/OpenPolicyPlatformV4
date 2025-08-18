"""
Enhanced API Authentication Tests
Tests that verify all authentication endpoints work correctly
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
import jwt
from datetime import datetime, timedelta

class TestEnhancedAuthenticationAPI:
    """Test enhanced authentication API endpoints"""
    
    def test_login_success(self, client, db_session):
        """Test successful user login"""
        
        # Setup: Create test user
        db_session.execute(text("""
            INSERT INTO auth_user (username, email, password, is_active, is_staff)
            VALUES ('testuser', 'test@example.com', 'hashed_password', true, false)
        """))
        db_session.commit()
        
        # Execute: Login request
        login_data = {
            "username": "testuser",
            "password": "testpassword123"
        }
        
        response = client.post("/api/auth/login", json=login_data)
        
        # Verify: Login successful
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["username"] == "testuser"
    
    def test_login_invalid_credentials(self, client, db_session):
        """Test login with invalid credentials"""
        
        # Setup: Create test user
        db_session.execute(text("""
            INSERT INTO auth_user (username, email, password, is_active, is_staff)
            VALUES ('testuser', 'test@example.com', 'hashed_password', true, false)
        """))
        db_session.commit()
        
        # Execute: Login with wrong password
        login_data = {
            "username": "testuser",
            "password": "wrongpassword"
        }
        
        response = client.post("/api/auth/login", json=login_data)
        
        # Verify: Login failed
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Invalid credentials" in data["detail"]
    
    def test_token_validation(self, client, db_session):
        """Test JWT token validation"""
        
        # Setup: Create test user and generate token
        db_session.execute(text("""
            INSERT INTO auth_user (username, email, password, is_active, is_staff)
            VALUES ('testuser', 'test@example.com', 'hashed_password', true, false)
        """))
        db_session.commit()
        
        # Generate valid token
        payload = {
            "sub": "testuser",
            "exp": datetime.utcnow() + timedelta(hours=1),
            "type": "access"
        }
        token = jwt.encode(payload, "test_secret", algorithm="HS256")
        
        # Execute: Validate token
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/auth/me", headers=headers)
        
        # Verify: Token is valid
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
    
    def test_password_reset(self, client, db_session):
        """Test password reset functionality"""
        
        # Setup: Create test user
        db_session.execute(text("""
            INSERT INTO auth_user (username, email, password, is_active, is_staff)
            VALUES ('testuser', 'test@example.com', 'hashed_password', true, false)
        """))
        db_session.commit()
        
        # Execute: Request password reset
        reset_data = {
            "email": "test@example.com"
        }
        
        response = client.post("/api/auth/password-reset", json=reset_data)
        
        # Verify: Password reset request successful
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Password reset email sent" in data["message"]
        
        # Execute: Reset password with token
        reset_token = "test_reset_token"  # In real implementation, this would be generated
        new_password_data = {
            "token": reset_token,
            "new_password": "newpassword123"
        }
        
        response = client.post("/api/auth/password-reset/confirm", json=new_password_data)
        
        # Verify: Password reset successful
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Password reset successful" in data["message"]
    
    def test_account_creation(self, client, db_session):
        """Test user account creation"""
        
        # Execute: Create new account
        account_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "securepassword123",
            "first_name": "New",
            "last_name": "User"
        }
        
        response = client.post("/api/auth/register", json=account_data)
        
        # Verify: Account creation successful
        assert response.status_code == 201
        data = response.json()
        assert "user" in data
        assert data["user"]["username"] == "newuser"
        assert data["user"]["email"] == "newuser@example.com"
        assert "access_token" in data
        
        # Verify: User exists in database
        result = db_session.execute(text("""
            SELECT username, email, is_active 
            FROM auth_user 
            WHERE username = 'newuser'
        """))
        user = result.fetchone()
        assert user is not None
        assert user.username == "newuser"
        assert user.email == "newuser@example.com"
        assert user.is_active == True
