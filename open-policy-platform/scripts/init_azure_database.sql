-- Azure PostgreSQL Database Initialization Script
-- This script will create the complete database schema for Open Policy Platform V4

-- Drop existing tables if they exist
DROP TABLE IF EXISTS bills_membervote CASCADE;
DROP TABLE IF EXISTS bills_bill CASCADE;
DROP TABLE IF EXISTS core_politician CASCADE;
DROP TABLE IF EXISTS core_organization CASCADE;

-- Create core tables
CREATE TABLE core_politician (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    party_name VARCHAR(255),
    district VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE core_organization (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    classification VARCHAR(100),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE bills_bill (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    classification VARCHAR(100),
    session VARCHAR(100),
    status VARCHAR(50) DEFAULT 'active',
    content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE bills_membervote (
    id SERIAL PRIMARY KEY,
    bill_id INTEGER REFERENCES bills_bill(id) ON DELETE CASCADE,
    member_name VARCHAR(255),
    vote VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample data
INSERT INTO core_politician (name, party_name, district, email, phone) VALUES
('Jane Doe', 'Independent', 'Central', 'jane@example.com', '555-0100'),
('John Smith', 'Democratic', 'North', 'john@example.com', '555-0101'),
('Bob Johnson', 'Republican', 'South', 'bob@example.com', '555-0102');

INSERT INTO core_organization (name, classification, description) VALUES
('Finance Committee', 'committee', 'Oversees financial matters'),
('Health Committee', 'committee', 'Oversees health policy'),
('Education Committee', 'committee', 'Oversees education policy');

INSERT INTO bills_bill (title, classification, session, status, content) VALUES
('Bill A', 'public', '43-1', 'active', 'This is a public bill for testing'),
('Bill B', 'private', '43-1', 'active', 'This is a private bill for testing'),
('Bill C', 'public', '43-2', 'draft', 'This is a draft bill for testing');

INSERT INTO bills_membervote (bill_id, member_name, vote) VALUES
(1, 'Jane Doe', 'yes'),
(1, 'John Smith', 'no'),
(1, 'Bob Johnson', 'abstain'),
(2, 'Jane Doe', 'yes'),
(2, 'John Smith', 'yes');

-- Create indexes for better performance
CREATE INDEX idx_bills_bill_classification ON bills_bill(classification);
CREATE INDEX idx_bills_bill_session ON bills_bill(session);
CREATE INDEX idx_bills_bill_status ON bills_bill(status);
CREATE INDEX idx_bills_membervote_bill_id ON bills_membervote(bill_id);

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO openpolicy;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO openpolicy;

-- Verify the setup
SELECT 'Database initialization complete!' as status;
SELECT COUNT(*) as politician_count FROM core_politician;
SELECT COUNT(*) as organization_count FROM core_organization;
SELECT COUNT(*) as bill_count FROM bills_bill;
SELECT COUNT(*) as vote_count FROM bills_membervote;
