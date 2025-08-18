-- Open Policy Platform V4 - Database Security Setup
-- Enhanced user management and security tables

-- ========================================
-- USER MANAGEMENT TABLES
-- ========================================

-- Users table with enhanced security
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(20) DEFAULT 'user' CHECK (role IN ('admin', 'user', 'guest')),
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP,
    permissions TEXT[] DEFAULT ARRAY['read']
);

-- User sessions table for enhanced session management
CREATE TABLE IF NOT EXISTS user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    refresh_token_hash VARCHAR(255),
    ip_address INET,
    user_agent TEXT,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_revoked BOOLEAN DEFAULT FALSE
);

-- User roles and permissions table
CREATE TABLE IF NOT EXISTS user_roles (
    id SERIAL PRIMARY KEY,
    role_name VARCHAR(20) UNIQUE NOT NULL,
    description TEXT,
    permissions TEXT[] NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Audit logs table for security monitoring
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    resource VARCHAR(100),
    resource_id INTEGER,
    ip_address INET,
    user_agent TEXT,
    request_data JSONB,
    response_status INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    session_id VARCHAR(100)
);

-- Password reset tokens table
CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    used_at TIMESTAMP,
    is_used BOOLEAN DEFAULT FALSE
);

-- Email verification tokens table
CREATE TABLE IF NOT EXISTS email_verification_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    verified_at TIMESTAMP,
    is_verified BOOLEAN DEFAULT FALSE
);

-- ========================================
-- SECURITY INDEXES
-- ========================================

-- Indexes for performance and security
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active);
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_token_hash ON user_sessions(token_hash);
CREATE INDEX IF NOT EXISTS idx_sessions_expires ON user_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_password_reset_user_id ON password_reset_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_password_reset_token ON password_reset_tokens(token_hash);

-- ========================================
-- DEFAULT ROLE DATA
-- ========================================

-- Insert default roles with permissions
INSERT INTO user_roles (role_name, description, permissions) VALUES
    ('admin', 'System Administrator', ARRAY['read', 'write', 'admin', 'delete', 'manage_users', 'manage_roles', 'view_audit_logs']),
    ('user', 'Standard User', ARRAY['read', 'write', 'edit_profile', 'change_password']),
    ('guest', 'Guest User', ARRAY['read'])
ON CONFLICT (role_name) DO NOTHING;

-- ========================================
-- DEFAULT ADMIN USER
-- ========================================

-- Insert default admin user (password: AdminSecure123!)
-- In production, this should be changed immediately
INSERT INTO users (username, email, password_hash, full_name, role, is_active, is_verified, permissions) VALUES
    ('admin', 'admin@openpolicy.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/vHhHhHh', 'System Administrator', 'admin', TRUE, TRUE, ARRAY['read', 'write', 'admin', 'delete', 'manage_users', 'manage_roles', 'view_audit_logs'])
ON CONFLICT (username) DO NOTHING;

-- ========================================
-- SECURITY VIEWS
-- ========================================

-- View for active user sessions
CREATE OR REPLACE VIEW active_sessions AS
SELECT 
    us.id,
    us.user_id,
    u.username,
    u.role,
    us.ip_address,
    us.user_agent,
    us.created_at,
    us.expires_at,
    us.last_used
FROM user_sessions us
JOIN users u ON us.user_id = u.id
WHERE us.expires_at > CURRENT_TIMESTAMP 
AND us.is_revoked = FALSE;

-- View for user permissions
CREATE OR REPLACE VIEW user_permissions AS
SELECT 
    u.id,
    u.username,
    u.role,
    u.permissions,
    ur.permissions as role_permissions
FROM users u
LEFT JOIN user_roles ur ON u.role = ur.role_name;

-- ========================================
-- SECURITY FUNCTIONS
-- ========================================

-- Function to update user's last login
CREATE OR REPLACE FUNCTION update_user_last_login(user_id INTEGER)
RETURNS VOID AS $$
BEGIN
    UPDATE users 
    SET last_login = CURRENT_TIMESTAMP,
        failed_login_attempts = 0,
        locked_until = NULL
    WHERE id = user_id;
END;
$$ LANGUAGE plpgsql;

-- Function to increment failed login attempts
CREATE OR REPLACE FUNCTION increment_failed_login(username_param VARCHAR)
RETURNS VOID AS $$
BEGIN
    UPDATE users 
    SET failed_login_attempts = failed_login_attempts + 1,
        locked_until = CASE 
            WHEN failed_login_attempts >= 4 THEN CURRENT_TIMESTAMP + INTERVAL '15 minutes'
            ELSE locked_until
        END
    WHERE username = username_param;
END;
$$ LANGUAGE plpgsql;

-- Function to log audit events
CREATE OR REPLACE FUNCTION log_audit_event(
    user_id_param INTEGER,
    action_param VARCHAR,
    resource_param VARCHAR DEFAULT NULL,
    resource_id_param INTEGER DEFAULT NULL,
    ip_address_param INET DEFAULT NULL,
    user_agent_param TEXT DEFAULT NULL,
    request_data_param JSONB DEFAULT NULL,
    response_status_param INTEGER DEFAULT NULL,
    session_id_param VARCHAR DEFAULT NULL
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO audit_logs (
        user_id, action, resource, resource_id, ip_address, 
        user_agent, request_data, response_status, session_id
    ) VALUES (
        user_id_param, action_param, resource_param, resource_id_param, ip_address_param,
        user_agent_param, request_data_param, response_status_param, session_id_param
    );
END;
$$ LANGUAGE plpgsql;

-- ========================================
-- SECURITY TRIGGERS
-- ========================================

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to users table
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ========================================
-- SECURITY POLICIES
-- ========================================

-- Enable Row Level Security (RLS) on sensitive tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- Create policies for users table
CREATE POLICY users_select_policy ON users
    FOR SELECT USING (is_active = TRUE);

CREATE POLICY users_update_policy ON users
    FOR UPDATE USING (auth.uid() = id OR auth.role() = 'admin');

-- Create policies for user_sessions table
CREATE POLICY sessions_select_policy ON user_sessions
    FOR SELECT USING (user_id = auth.uid() OR auth.role() = 'admin');

CREATE POLICY sessions_insert_policy ON user_sessions
    FOR INSERT WITH CHECK (user_id = auth.uid() OR auth.role() = 'admin');

-- Create policies for audit_logs table
CREATE POLICY audit_logs_select_policy ON audit_logs
    FOR SELECT USING (auth.role() = 'admin');

-- ========================================
-- SECURITY CONSTRAINTS
-- ========================================

-- Add constraints for data integrity
ALTER TABLE users ADD CONSTRAINT users_username_length CHECK (length(username) >= 3);
ALTER TABLE users ADD CONSTRAINT users_email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$');
ALTER TABLE users ADD CONSTRAINT users_password_hash_length CHECK (length(password_hash) >= 60);

-- ========================================
-- COMMENTS
-- ========================================

COMMENT ON TABLE users IS 'Enhanced user management table with security features';
COMMENT ON TABLE user_sessions IS 'User session management for enhanced security';
COMMENT ON TABLE user_roles IS 'Role-based access control definitions';
COMMENT ON TABLE audit_logs IS 'Security audit logging for compliance and monitoring';
COMMENT ON TABLE password_reset_tokens IS 'Secure password reset token management';
COMMENT ON TABLE email_verification_tokens IS 'Email verification token management';

COMMENT ON COLUMN users.failed_login_attempts IS 'Number of consecutive failed login attempts';
COMMENT ON COLUMN users.locked_until IS 'Account lockout until this timestamp';
COMMENT ON COLUMN users.is_verified IS 'Email verification status';

-- ========================================
-- SECURITY SETTINGS
-- ========================================

-- Set secure default values
ALTER TABLE users ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE users ALTER COLUMN updated_at SET DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE user_sessions ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE audit_logs ALTER COLUMN timestamp SET DEFAULT CURRENT_TIMESTAMP;

-- Grant appropriate permissions
GRANT USAGE ON SCHEMA public TO openpolicy;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO openpolicy;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO openpolicy;

-- ========================================
-- VERIFICATION
-- ========================================

-- Verify tables were created
SELECT 'Tables created successfully' as status;

-- Show table structure
\dt+

-- Show default roles
SELECT role_name, permissions FROM user_roles;

-- Show default admin user
SELECT username, role, is_active, is_verified FROM users WHERE role = 'admin';
