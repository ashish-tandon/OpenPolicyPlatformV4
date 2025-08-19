-- OpenPolicy Platform Database Schema
-- This script creates all necessary tables for the platform

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Parliament Sessions
CREATE TABLE IF NOT EXISTS parliament_sessions (
    id SERIAL PRIMARY KEY,
    parliament_number INTEGER NOT NULL,
    session_number INTEGER NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE,
    status VARCHAR(50) DEFAULT 'active',
    dissolution_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(parliament_number, session_number)
);

-- Representatives/MPs
CREATE TABLE IF NOT EXISTS representatives (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(50),
    party VARCHAR(100),
    constituency VARCHAR(255),
    province VARCHAR(100),
    photo_url TEXT,
    bio TEXT,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Committees
CREATE TABLE IF NOT EXISTS committees (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    abbreviation VARCHAR(10) UNIQUE,
    type VARCHAR(50),
    description TEXT,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Bills
CREATE TABLE IF NOT EXISTS bills (
    id SERIAL PRIMARY KEY,
    bill_number VARCHAR(50) NOT NULL,
    title TEXT NOT NULL,
    summary TEXT,
    sponsor VARCHAR(255),
    status VARCHAR(100),
    parliament INTEGER NOT NULL,
    session INTEGER NOT NULL,
    introduction_date DATE,
    latest_activity_date DATE,
    committee VARCHAR(255),
    subjects JSONB,
    url TEXT,
    full_text_url TEXT,
    scraped_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(bill_number, parliament, session)
);

-- Parliament Votes
CREATE TABLE IF NOT EXISTS parliament_votes (
    id SERIAL PRIMARY KEY,
    vote_number INTEGER NOT NULL,
    parliament INTEGER NOT NULL,
    session INTEGER NOT NULL,
    sitting INTEGER,
    bill_number VARCHAR(50),
    vote_date DATE NOT NULL,
    vote_description TEXT,
    result VARCHAR(50),
    yeas INTEGER DEFAULT 0,
    nays INTEGER DEFAULT 0,
    paired INTEGER DEFAULT 0,
    total INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(vote_number, parliament, session)
);

-- Debates
CREATE TABLE IF NOT EXISTS debates (
    id SERIAL PRIMARY KEY,
    debate_date DATE NOT NULL,
    parliament INTEGER NOT NULL,
    session INTEGER NOT NULL,
    sitting INTEGER,
    title VARCHAR(500),
    hansard_number VARCHAR(100),
    url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(debate_date, parliament, session)
);

-- Politician Activity Logs
CREATE TABLE IF NOT EXISTS politician_activity_logs (
    id SERIAL PRIMARY KEY,
    politician_id INTEGER REFERENCES representatives(id),
    activity_type VARCHAR(100),
    activity_date DATE,
    description TEXT,
    details JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Committee Members
CREATE TABLE IF NOT EXISTS committee_members (
    id SERIAL PRIMARY KEY,
    committee_id INTEGER REFERENCES committees(id),
    representative_id INTEGER REFERENCES representatives(id),
    role VARCHAR(100),
    start_date DATE,
    end_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(committee_id, representative_id, start_date)
);

-- Vote Records (how each MP voted)
CREATE TABLE IF NOT EXISTS vote_records (
    id SERIAL PRIMARY KEY,
    vote_id INTEGER REFERENCES parliament_votes(id),
    representative_id INTEGER REFERENCES representatives(id),
    vote_type VARCHAR(20), -- yes, no, abstain, absent
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(vote_id, representative_id)
);

-- User Saved Items
CREATE TABLE IF NOT EXISTS user_saved_bills (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    bill_id INTEGER REFERENCES bills(id),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, bill_id)
);

CREATE TABLE IF NOT EXISTS user_saved_representatives (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    representative_id INTEGER REFERENCES representatives(id),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, representative_id)
);

-- Notifications
CREATE TABLE IF NOT EXISTS user_notifications (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    type VARCHAR(50),
    title VARCHAR(255),
    message TEXT,
    data JSONB,
    read BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX idx_bills_status ON bills(status);
CREATE INDEX idx_bills_parliament_session ON bills(parliament, session);
CREATE INDEX idx_bills_latest_activity ON bills(latest_activity_date DESC);
CREATE INDEX idx_representatives_party ON representatives(party);
CREATE INDEX idx_representatives_province ON representatives(province);
CREATE INDEX idx_representatives_active ON representatives(active);
CREATE INDEX idx_votes_date ON parliament_votes(vote_date DESC);
CREATE INDEX idx_votes_bill ON parliament_votes(bill_number);
CREATE INDEX idx_debates_date ON debates(debate_date DESC);
CREATE INDEX idx_activity_logs_politician ON politician_activity_logs(politician_id);
CREATE INDEX idx_activity_logs_date ON politician_activity_logs(activity_date DESC);
CREATE INDEX idx_notifications_user ON user_notifications(user_id, read);

-- Create update timestamp trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update trigger to all tables
CREATE TRIGGER update_parliament_sessions_updated_at BEFORE UPDATE ON parliament_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_representatives_updated_at BEFORE UPDATE ON representatives
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_committees_updated_at BEFORE UPDATE ON committees
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_bills_updated_at BEFORE UPDATE ON bills
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_parliament_votes_updated_at BEFORE UPDATE ON parliament_votes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_debates_updated_at BEFORE UPDATE ON debates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_politician_activity_logs_updated_at BEFORE UPDATE ON politician_activity_logs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_committee_members_updated_at BEFORE UPDATE ON committee_members
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();