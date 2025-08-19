-- Open Policy Platform V4 - Database Structure Expansion
-- This script adds comprehensive tables for a full-featured policy platform

-- 1. POLICY CATEGORIES AND CLASSIFICATIONS
CREATE TABLE IF NOT EXISTS policy_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    parent_id INTEGER REFERENCES policy_categories(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS policy_classifications (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    risk_level VARCHAR(20) CHECK (risk_level IN ('low', 'medium', 'high', 'critical')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. JURISDICTIONS AND REGIONS
CREATE TABLE IF NOT EXISTS jurisdictions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    level VARCHAR(50) NOT NULL CHECK (level IN ('federal', 'provincial', 'municipal', 'regional')),
    parent_id INTEGER REFERENCES jurisdictions(id),
    country VARCHAR(50) DEFAULT 'Canada',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS regions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    jurisdiction_id INTEGER REFERENCES jurisdictions(id),
    population INTEGER,
    area_km2 DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. ENHANCED POLITICIAN INFORMATION
CREATE TABLE IF NOT EXISTS politician_roles (
    id SERIAL PRIMARY KEY,
    politician_id INTEGER REFERENCES core_politician(id) ON DELETE CASCADE,
    role_name VARCHAR(100) NOT NULL,
    organization_id INTEGER REFERENCES core_organization(id),
    start_date DATE,
    end_date DATE,
    is_current BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS politician_committees (
    id SERIAL PRIMARY KEY,
    politician_id INTEGER REFERENCES core_politician(id) ON DELETE CASCADE,
    committee_id INTEGER REFERENCES core_organization(id),
    role VARCHAR(50) DEFAULT 'member',
    start_date DATE,
    end_date DATE,
    is_current BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. ENHANCED BILL/POLICY INFORMATION
CREATE TABLE IF NOT EXISTS bill_sponsors (
    id SERIAL PRIMARY KEY,
    bill_id INTEGER REFERENCES bills_bill(id) ON DELETE CASCADE,
    politician_id INTEGER REFERENCES core_politician(id),
    sponsor_type VARCHAR(50) DEFAULT 'primary',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bill_co_sponsors (
    id SERIAL PRIMARY KEY,
    bill_id INTEGER REFERENCES bills_bill(id) ON DELETE CASCADE,
    politician_id INTEGER REFERENCES core_politician(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bill_amendments (
    id SERIAL PRIMARY KEY,
    bill_id INTEGER REFERENCES bills_bill(id) ON DELETE CASCADE,
    amendment_number INTEGER,
    description TEXT,
    status VARCHAR(50) DEFAULT 'proposed',
    created_by INTEGER REFERENCES core_politician(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bill_reading_stages (
    id SERIAL PRIMARY KEY,
    bill_id INTEGER REFERENCES bills_bill(id) ON DELETE CASCADE,
    reading_number INTEGER NOT NULL,
    date DATE,
    status VARCHAR(50) DEFAULT 'scheduled',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. VOTING AND DECISION TRACKING
CREATE TABLE IF NOT EXISTS voting_sessions (
    id SERIAL PRIMARY KEY,
    bill_id INTEGER REFERENCES bills_bill(id) ON DELETE CASCADE,
    session_date DATE NOT NULL,
    session_type VARCHAR(50) DEFAULT 'regular',
    quorum_met BOOLEAN DEFAULT false,
    total_votes INTEGER,
    yes_votes INTEGER,
    no_votes INTEGER,
    abstentions INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS vote_details (
    id SERIAL PRIMARY KEY,
    voting_session_id INTEGER REFERENCES voting_sessions(id) ON DELETE CASCADE,
    politician_id INTEGER REFERENCES core_politician(id),
    vote VARCHAR(50) NOT NULL CHECK (vote IN ('yes', 'no', 'abstain', 'absent')),
    reason TEXT,
    party_whip BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. PUBLIC OPINION AND FEEDBACK
CREATE TABLE IF NOT EXISTS public_opinion_polls (
    id SERIAL PRIMARY KEY,
    bill_id INTEGER REFERENCES bills_bill(id) ON DELETE CASCADE,
    poll_date DATE NOT NULL,
    pollster VARCHAR(100),
    sample_size INTEGER,
    support_percentage DECIMAL(5,2),
    oppose_percentage DECIMAL(5,2),
    undecided_percentage DECIMAL(5,2),
    margin_of_error DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS public_comments (
    id SERIAL PRIMARY KEY,
    bill_id INTEGER REFERENCES bills_bill(id) ON DELETE CASCADE,
    commenter_name VARCHAR(100),
    commenter_email VARCHAR(255),
    comment TEXT NOT NULL,
    sentiment VARCHAR(20) CHECK (sentiment IN ('positive', 'negative', 'neutral')),
    is_verified BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. MEDIA AND DOCUMENTATION
CREATE TABLE IF NOT EXISTS bill_documents (
    id SERIAL PRIMARY KEY,
    bill_id INTEGER REFERENCES bills_bill(id) ON DELETE CASCADE,
    document_type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    file_path VARCHAR(500),
    file_size INTEGER,
    mime_type VARCHAR(100),
    uploaded_by INTEGER REFERENCES core_politician(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS media_coverage (
    id SERIAL PRIMARY KEY,
    bill_id INTEGER REFERENCES bills_bill(id) ON DELETE CASCADE,
    media_outlet VARCHAR(100),
    headline VARCHAR(255),
    url VARCHAR(500),
    publication_date DATE,
    sentiment VARCHAR(20) CHECK (sentiment IN ('positive', 'negative', 'neutral')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 8. TIMELINE AND EVENTS
CREATE TABLE IF NOT EXISTS bill_timeline (
    id SERIAL PRIMARY KEY,
    bill_id INTEGER REFERENCES bills_bill(id) ON DELETE CASCADE,
    event_type VARCHAR(100) NOT NULL,
    event_date DATE NOT NULL,
    description TEXT,
    related_politician_id INTEGER REFERENCES core_politician(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS legislative_events (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(100) NOT NULL,
    event_date DATE NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    location VARCHAR(255),
    attendees_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 9. ANALYTICS AND METRICS
CREATE TABLE IF NOT EXISTS bill_analytics (
    id SERIAL PRIMARY KEY,
    bill_id INTEGER REFERENCES bills_bill(id) ON DELETE CASCADE,
    metric_date DATE NOT NULL,
    social_media_mentions INTEGER DEFAULT 0,
    news_mentions INTEGER DEFAULT 0,
    public_support_score DECIMAL(5,2),
    controversy_score DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS politician_analytics (
    id SERIAL PRIMARY KEY,
    politician_id INTEGER REFERENCES core_politician(id) ON DELETE CASCADE,
    metric_date DATE NOT NULL,
    social_media_followers INTEGER DEFAULT 0,
    approval_rating DECIMAL(5,2),
    bill_success_rate DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 10. RELATIONSHIPS AND NETWORKS
CREATE TABLE IF NOT EXISTS politician_relationships (
    id SERIAL PRIMARY KEY,
    politician_id_1 INTEGER REFERENCES core_politician(id) ON DELETE CASCADE,
    politician_id_2 INTEGER REFERENCES core_politician(id) ON DELETE CASCADE,
    relationship_type VARCHAR(50) DEFAULT 'colleague',
    strength DECIMAL(3,2) CHECK (strength >= 0 AND strength <= 1),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(politician_id_1, politician_id_2)
);

CREATE TABLE IF NOT EXISTS organization_memberships (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER REFERENCES core_organization(id) ON DELETE CASCADE,
    politician_id INTEGER REFERENCES core_politician(id) ON DELETE CASCADE,
    membership_type VARCHAR(50) DEFAULT 'member',
    start_date DATE,
    end_date DATE,
    is_current BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample data for new tables
INSERT INTO policy_categories (name, description) VALUES
('Healthcare', 'Health-related policies and regulations'),
('Education', 'Educational policies and reforms'),
('Environment', 'Environmental protection and climate policies'),
('Economy', 'Economic and fiscal policies'),
('Security', 'National security and defense policies')
ON CONFLICT DO NOTHING;

INSERT INTO policy_classifications (name, description, risk_level) VALUES
('Routine', 'Standard policy with minimal impact', 'low'),
('Significant', 'Policy with moderate impact', 'medium'),
('Major', 'Policy with substantial impact', 'high'),
('Critical', 'Policy with critical national impact', 'critical')
ON CONFLICT DO NOTHING;

INSERT INTO jurisdictions (name, level, country) VALUES
('Federal Government', 'federal', 'Canada'),
('Ontario', 'provincial', 'Canada'),
('Quebec', 'provincial', 'Canada'),
('Toronto', 'municipal', 'Canada'),
('Montreal', 'municipal', 'Canada')
ON CONFLICT DO NOTHING;

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_bill_sponsors_bill_id ON bill_sponsors(bill_id);
CREATE INDEX IF NOT EXISTS idx_bill_sponsors_politician_id ON bill_sponsors(politician_id);
CREATE INDEX IF NOT EXISTS idx_voting_sessions_bill_id ON voting_sessions(bill_id);
CREATE INDEX IF NOT EXISTS idx_vote_details_session_id ON vote_details(voting_session_id);
CREATE INDEX IF NOT EXISTS idx_bill_timeline_bill_id ON bill_timeline(bill_id);
CREATE INDEX IF NOT EXISTS idx_politician_roles_politician_id ON politician_roles(politician_id);
CREATE INDEX IF NOT EXISTS idx_organization_memberships_org_id ON organization_memberships(organization_id);

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO openpolicy;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO openpolicy;

-- Verify the expanded structure
SELECT 'Database structure expansion complete!' as status;
SELECT COUNT(*) as total_tables FROM information_schema.tables WHERE table_schema = 'public';
SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;
