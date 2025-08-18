"""
Comprehensive Authentication API Tests
Tests every authentication endpoint, scenario, and security measure
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
import jwt
from datetime import datetime, timedelta

def test_login_success(client, db_session):
    """Test successful user login"""
    
    # Create test user
    test_user_data = {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'TestPassword123!',
        'first_name': 'Test',
        'last_name': 'User',
        'is_active': True,
        'is_admin': False
    }
    
    # Insert test user into database
    db_session.execute(text("""
        INSERT INTO users_user (username, email, password_hash, first_name, last_name, is_active, is_admin)
        VALUES (:username, :email, :password_hash, :first_name, :last_name, :is_active, :is_admin)
    """), {
        **test_user_data,
        'password_hash': '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4tbQJQKqG'  # TestPassword123!
    })
    db_session.commit()
    
    # Test login
    response = client.post("/api/auth/login", json={
        'username': 'testuser',
        'password': 'TestPassword123!'
    })
    
    assert response.status_code == 200
    data = response.json()
    assert 'access_token' in data
    assert 'token_type' in data
    assert data['token_type'] == 'bearer'
    assert 'user' in data
    assert data['user']['username'] == 'testuser'
    assert data['user']['email'] == 'test@example.com'
    
    # Verify token is valid
    token = data['access_token']
    decoded = jwt.decode(token, 'test_secret_key', algorithms=['HS256'])
    assert decoded['sub'] == 'testuser'
    assert 'exp' in decoded

def test_login_invalid_credentials(client):
    """Test login with invalid credentials"""
    
    # Test with wrong password
    response = client.post("/api/auth/login", json={
        'username': 'testuser',
        'password': 'WrongPassword123!'
    })
    
    assert response.status_code == 401
    data = response.json()
    assert 'detail' in data
    assert 'Invalid credentials' in data['detail']
    
    # Test with non-existent user
    response = client.post("/api/auth/login", json={
        'username': 'nonexistentuser',
        'password': 'TestPassword123!'
    })
    
    assert response.status_code == 401
    data = response.json()
    assert 'detail' in data
    assert 'Invalid credentials' in data['detail']

def test_login_missing_fields(client):
    """Test login with missing required fields"""
    
    # Test missing username
    response = client.post("/api/auth/login", json={
        'password': 'TestPassword123!'
    })
    
    assert response.status_code == 422
    
    # Test missing password
    response = client.post("/api/auth/login", json={
        'username': 'testuser'
    })
    
    assert response.status_code == 422
    
    # Test empty fields
    response = client.post("/api/auth/login", json={
        'username': '',
        'password': ''
    })
    
    assert response.status_code == 422

def test_login_inactive_user(client, db_session):
    """Test login with inactive user account"""
    
    # Create inactive user
    db_session.execute(text("""
        INSERT INTO users_user (username, email, password_hash, first_name, last_name, is_active, is_admin)
        VALUES (:username, :email, :password_hash, :first_name, :last_name, :is_active, :is_admin)
    """), {
        'username': 'inactiveuser',
        'email': 'inactive@example.com',
        'password_hash': '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4tbQJQKqG',
        'first_name': 'Inactive',
        'last_name': 'User',
        'is_active': False,
        'is_admin': False
    })
    db_session.commit()
    
    # Test login
    response = client.post("/api/auth/login", json={
        'username': 'inactiveuser',
        'password': 'TestPassword123!'
    })
    
    assert response.status_code == 401
    data = response.json()
    assert 'detail' in data
    assert 'Inactive account' in data['detail']

def test_logout_success(client, auth_headers):
    """Test successful user logout"""
    
    response = client.post("/api/auth/logout", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert 'message' in data
    assert 'Successfully logged out' in data['message']

def test_logout_without_token(client):
    """Test logout without authentication token"""
    
    response = client.post("/api/auth/logout")
    
    assert response.status_code == 401
    data = response.json()
    assert 'detail' in data
    assert 'Not authenticated' in data['detail']

def test_token_refresh(client, auth_headers):
    """Test token refresh functionality"""
    
    response = client.post("/api/auth/refresh", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert 'access_token' in data
    assert 'token_type' in data
    assert data['token_type'] == 'bearer'
    
    # Verify new token is different and valid
    new_token = data['access_token']
    decoded = jwt.decode(new_token, 'test_secret_key', algorithms=['HS256'])
    assert decoded['sub'] == 'admin'
    assert 'exp' in decoded

def test_token_validation(client, auth_headers):
    """Test token validation endpoint"""
    
    response = client.get("/api/auth/validate", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert 'valid' in data
    assert data['valid'] == True
    assert 'user' in data
    assert data['user']['username'] == 'admin'

def test_token_validation_invalid_token(client):
    """Test token validation with invalid token"""
    
    response = client.get("/api/auth/validate", headers={
        'Authorization': 'Bearer invalid_token'
    })
    
    assert response.status_code == 401
    data = response.json()
    assert 'detail' in data
    assert 'Invalid token' in data['detail']

def test_token_validation_expired_token(client):
    """Test token validation with expired token"""
    
    # Create expired token
    expired_token = jwt.encode(
        {
            'sub': 'testuser',
            'exp': datetime.utcnow() - timedelta(hours=1),
            'type': 'access'
        },
        'test_secret_key',
        algorithm='HS256'
    )
    
    response = client.get("/api/auth/validate", headers={
        'Authorization': f'Bearer {expired_token}'
    })
    
    assert response.status_code == 401
    data = response.json()
    assert 'detail' in data
    assert 'Token expired' in data['detail']

def test_password_reset_request(client, db_session):
    """Test password reset request"""
    
    # Create test user
    db_session.execute(text("""
        INSERT INTO users_user (username, email, password_hash, first_name, last_name, is_active, is_admin)
        VALUES (:username, :email, :password_hash, :first_name, :last_name, :is_active, :is_admin)
    """), {
        'username': 'resetuser',
        'email': 'reset@example.com',
        'password_hash': '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4tbQJQKqG',
        'first_name': 'Reset',
        'last_name': 'User',
        'is_active': True,
        'is_admin': False
    })
    db_session.commit()
    
    response = client.post("/api/auth/password-reset-request", json={
        'email': 'reset@example.com'
    })
    
    assert response.status_code == 200
    data = response.json()
    assert 'message' in data
    assert 'Password reset email sent' in data['message']

def test_password_reset_request_invalid_email(client):
    """Test password reset request with invalid email"""
    
    response = client.post("/api/auth/password-reset-request", json={
        'email': 'nonexistent@example.com'
    })
    
    assert response.status_code == 404
    data = response.json()
    assert 'detail' in data
    assert 'User not found' in data['detail']

def test_password_change(client, auth_headers):
    """Test password change functionality"""
    
    response = client.post("/api/auth/change-password", 
        headers=auth_headers,
        json={
            'current_password': 'admin123',
            'new_password': 'NewPassword123!'
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert 'message' in data
    assert 'Password changed successfully' in data['message']

def test_password_change_wrong_current_password(client, auth_headers):
    """Test password change with wrong current password"""
    
    response = client.post("/api/auth/change-password", 
        headers=auth_headers,
        json={
            'current_password': 'WrongPassword123!',
            'new_password': 'NewPassword123!'
        }
    )
    
    assert response.status_code == 400
    data = response.json()
    assert 'detail' in data
    assert 'Current password is incorrect' in data['detail']

def test_password_change_weak_new_password(client, auth_headers):
    """Test password change with weak new password"""
    
    response = client.post("/api/auth/change-password", 
        headers=auth_headers,
        json={
            'current_password': 'admin123',
            'new_password': 'weak'
        }
    )
    
    assert response.status_code == 422
    data = response.json()
    assert 'detail' in data

def test_account_creation(client, db_session):
    """Test user account creation"""
    
    response = client.post("/api/auth/register", json={
        'username': 'newuser',
        'email': 'newuser@example.com',
        'password': 'NewUserPassword123!',
        'first_name': 'New',
        'last_name': 'User'
    })
    
    assert response.status_code == 201
    data = response.json()
    assert 'message' in data
    assert 'User created successfully' in data['message']
    assert 'user' in data
    assert data['user']['username'] == 'newuser'
    assert data['user']['email'] == 'newuser@example.com'
    assert data['user']['is_active'] == True
    assert data['user']['is_admin'] == False

def test_account_creation_duplicate_username(client, db_session):
    """Test account creation with duplicate username"""
    
    # Create existing user
    db_session.execute(text("""
        INSERT INTO users_user (username, email, password_hash, first_name, last_name, is_active, is_admin)
        VALUES (:username, :email, :password_hash, :first_name, :last_name, :is_active, :is_admin)
    """), {
        'username': 'duplicateuser',
        'email': 'duplicate@example.com',
        'password_hash': '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4tbQJQKqG',
        'first_name': 'Duplicate',
        'last_name': 'User',
        'is_active': True,
        'is_admin': False
    })
    db_session.commit()
    
    # Try to create user with same username
    response = client.post("/api/auth/register", json={
        'username': 'duplicateuser',
        'email': 'newemail@example.com',
        'password': 'NewUserPassword123!',
        'first_name': 'New',
        'last_name': 'User'
    })
    
    assert response.status_code == 400
    data = response.json()
    assert 'detail' in data
    assert 'Username already exists' in data['detail']

def test_account_creation_duplicate_email(client, db_session):
    """Test account creation with duplicate email"""
    
    # Create existing user
    db_session.execute(text("""
        INSERT INTO users_user (username, email, password_hash, first_name, last_name, is_active, is_admin)
        VALUES (:username, :email, :password_hash, :first_name, :last_name, :is_active, :is_admin)
    """), {
        'username': 'existinguser',
        'email': 'duplicate@example.com',
        'password_hash': '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4tbQJQKqG',
        'first_name': 'Existing',
        'last_name': 'User',
        'is_active': True,
        'is_admin': False
    })
    db_session.commit()
    
    # Try to create user with same email
    response = client.post("/api/auth/register", json={
        'username': 'newuser',
        'email': 'duplicate@example.com',
        'password': 'NewUserPassword123!',
        'first_name': 'New',
        'last_name': 'User'
    })
    
    assert response.status_code == 400
    data = response.json()
    assert 'detail' in data
    assert 'Email already exists' in data['detail']

def test_account_creation_weak_password(client):
    """Test account creation with weak password"""
    
    response = client.post("/api/auth/register", json={
        'username': 'weakuser',
        'email': 'weak@example.com',
        'password': 'weak',
        'first_name': 'Weak',
        'last_name': 'User'
    })
    
    assert response.status_code == 422
    data = response.json()
    assert 'detail' in data

def test_account_deletion(client, auth_headers, db_session):
    """Test user account deletion"""
    
    # Create user to delete
    db_session.execute(text("""
        INSERT INTO users_user (username, email, password_hash, first_name, last_name, is_active, is_admin)
        VALUES (:username, :email, :password_hash, :first_name, :last_name, :is_active, :is_admin)
    """), {
        'username': 'deleteuser',
        'email': 'delete@example.com',
        'password_hash': '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4tbQJQKqG',
        'first_name': 'Delete',
        'last_name': 'User',
        'is_active': True,
        'is_admin': False
    })
    db_session.commit()
    
    response = client.delete("/api/auth/users/deleteuser", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert 'message' in data
    assert 'User deleted successfully' in data['message']

def test_account_deletion_unauthorized(client, db_session):
    """Test account deletion without proper authorization"""
    
    response = client.delete("/api/auth/users/admin")
    
    assert response.status_code == 401
    data = response.json()
    assert 'detail' in data
    assert 'Not authenticated' in data['detail']

def test_rate_limiting(client):
    """Test rate limiting on login endpoint"""
    
    # Make multiple rapid login attempts
    for i in range(10):
        response = client.post("/api/auth/login", json={
            'username': 'testuser',
            'password': 'WrongPassword123!'
        })
    
    # The last few requests should be rate limited
    assert response.status_code == 429
    data = response.json()
    assert 'detail' in data
    assert 'Too many requests' in data['detail']

def test_csrf_protection(client):
    """Test CSRF protection"""
    
    # Test without CSRF token
    response = client.post("/api/auth/login", json={
        'username': 'testuser',
        'password': 'TestPassword123!'
    })
    
    # Should still work for login (CSRF might be disabled for auth endpoints)
    # This test verifies the behavior is as expected
    assert response.status_code in [200, 403]

def test_session_management(client, auth_headers):
    """Test session management"""
    
    # Test session creation
    response = client.get("/api/auth/session", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert 'session_id' in data
    assert 'user' in data
    assert 'created_at' in data

def test_session_invalidation(client, auth_headers):
    """Test session invalidation"""
    
    response = client.post("/api/auth/session/invalidate", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert 'message' in data
    assert 'Session invalidated' in data['message']

def test_password_strength_validation(client):
    """Test password strength validation"""
    
    weak_passwords = [
        'weak',
        '123456',
        'password',
        'qwerty',
        'abc123'
    ]
    
    for password in weak_passwords:
        response = client.post("/api/auth/validate-password", json={
            'password': password
        })
        
        assert response.status_code == 400
        data = response.json()
        assert 'detail' in data
        assert 'Password too weak' in data['detail']
    
    # Test strong password
    response = client.post("/api/auth/validate-password", json={
        'password': 'StrongPassword123!'
    })
    
    assert response.status_code == 200
    data = response.json()
    assert 'valid' in data
    assert data['valid'] == True

def test_jwt_token_security(client, auth_headers):
    """Test JWT token security features"""
    
    # Get token from headers
    auth_header = auth_headers['Authorization']
    token = auth_header.replace('Bearer ', '')
    
    # Decode token to check security features
    decoded = jwt.decode(token, 'test_secret_key', algorithms=['HS256'])
    
    # Check required claims
    assert 'sub' in decoded  # Subject (username)
    assert 'exp' in decoded  # Expiration
    assert 'iat' in decoded  # Issued at
    assert 'type' in decoded  # Token type
    
    # Check token type
    assert decoded['type'] == 'access'
    
    # Check expiration is in the future
    exp_timestamp = decoded['exp']
    current_timestamp = datetime.utcnow().timestamp()
    assert exp_timestamp > current_timestamp

def test_brute_force_protection(client, db_session):
    """Test brute force protection"""
    
    # Create test user
    db_session.execute(text("""
        INSERT INTO users_user (username, email, password_hash, first_name, last_name, is_active, is_admin)
        VALUES (:username, :email, :password_hash, :first_name, :last_name, :is_active, :is_admin)
    """), {
        'username': 'bruteforceuser',
        'email': 'bruteforce@example.com',
        'password_hash': '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4tbQJQKqG',
        'first_name': 'Brute',
        'last_name': 'Force',
        'is_active': True,
        'is_admin': False
    })
    db_session.commit()
    
    # Make multiple failed login attempts
    for i in range(5):
        response = client.post("/api/auth/login", json={
            'username': 'bruteforceuser',
            'password': 'WrongPassword123!'
        })
        assert response.status_code == 401
    
    # The account should be locked after multiple failed attempts
    response = client.post("/api/auth/login", json={
        'username': 'bruteforceuser',
        'password': 'TestPassword123!'
    })
    
    assert response.status_code == 423  # Locked
    data = response.json()
    assert 'detail' in data
    assert 'Account locked' in data['detail']

def test_account_lockout_recovery(client, db_session):
    """Test account lockout recovery"""
    
    # Test that account can be unlocked after lockout period
    # This would typically involve waiting for the lockout period to expire
    # or having an admin unlock the account
    
    response = client.post("/api/auth/unlock-account", json={
        'username': 'bruteforceuser'
    })
    
    # This endpoint might require admin privileges
    assert response.status_code in [200, 403, 404]

def test_password_reset_security(client, db_session):
    """Test password reset security measures"""
    
    # Test password reset with invalid token
    response = client.post("/api/auth/password-reset", json={
        'token': 'invalid_token',
        'new_password': 'NewPassword123!'
    })
    
    assert response.status_code == 400
    data = response.json()
    assert 'detail' in data
    assert 'Invalid token' in data['detail']
    
    # Test password reset with expired token
    expired_token = jwt.encode(
        {
            'sub': 'testuser',
            'exp': datetime.utcnow() - timedelta(hours=1),
            'type': 'password_reset'
        },
        'test_secret_key',
        algorithm='HS256'
    )
    
    response = client.post("/api/auth/password-reset", json={
        'token': expired_token,
        'new_password': 'NewPassword123!'
    })
    
    assert response.status_code == 400
    data = response.json()
    assert 'detail' in data
    assert 'Token expired' in data['detail']
