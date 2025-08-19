-- Open Policy Platform V4 - Database Population Script
-- This script populates all tables with realistic sample data

-- 1. POPULATE ENHANCED BILL DATA
INSERT INTO bill_sponsors (bill_id, politician_id, sponsor_type) VALUES
(1, 1, 'primary'),
(2, 2, 'primary'),
(3, 3, 'primary')
ON CONFLICT DO NOTHING;

INSERT INTO bill_co_sponsors (bill_id, politician_id) VALUES
(1, 2),
(1, 3),
(2, 1),
(3, 1)
ON CONFLICT DO NOTHING;

INSERT INTO bill_amendments (bill_id, amendment_number, description, status, created_by) VALUES
(1, 1, 'Added environmental impact assessment requirement', 'approved', 2),
(1, 2, 'Modified funding allocation for rural areas', 'proposed', 3),
(2, 1, 'Extended implementation timeline to 2025', 'approved', 1)
ON CONFLICT DO NOTHING;

INSERT INTO bill_reading_stages (bill_id, reading_number, date, status, notes) VALUES
(1, 1, '2024-01-15', 'completed', 'First reading passed unanimously'),
(1, 2, '2024-02-20', 'completed', 'Second reading with minor amendments'),
(1, 3, '2024-03-10', 'scheduled', 'Third reading scheduled for next session'),
(2, 1, '2024-01-20', 'completed', 'First reading passed'),
(2, 2, '2024-02-25', 'scheduled', 'Second reading scheduled'),
(3, 1, '2024-02-01', 'completed', 'First reading passed with discussion')
ON CONFLICT DO NOTHING;

-- 2. POPULATE VOTING SESSIONS
INSERT INTO voting_sessions (bill_id, session_date, session_type, quorum_met, total_votes, yes_votes, no_votes, abstentions) VALUES
(1, '2024-02-20', 'regular', true, 3, 2, 1, 0),
(2, '2024-01-20', 'regular', true, 3, 3, 0, 0),
(3, '2024-02-01', 'regular', true, 3, 2, 0, 1)
ON CONFLICT DO NOTHING;

INSERT INTO vote_details (voting_session_id, politician_id, vote, reason, party_whip) VALUES
(1, 1, 'yes', 'Supports environmental protection', false),
(1, 2, 'no', 'Concerns about economic impact', false),
(1, 3, 'yes', 'Balanced approach to development', false),
(2, 1, 'yes', 'Supports healthcare improvements', false),
(2, 2, 'yes', 'Agrees with healthcare reforms', false),
(2, 3, 'yes', 'Supports public health initiatives', false),
(3, 1, 'yes', 'Supports education funding', false),
(3, 2, 'yes', 'Agrees with education priorities', false),
(3, 3, 'abstain', 'Needs more information', false)
ON CONFLICT DO NOTHING;

-- 3. POPULATE PUBLIC OPINION DATA
INSERT INTO public_opinion_polls (bill_id, poll_date, pollster, sample_size, support_percentage, oppose_percentage, undecided_percentage, margin_of_error) VALUES
(1, '2024-02-15', 'Ipsos Canada', 1000, 65.5, 25.3, 9.2, 3.1),
(1, '2024-02-25', 'Angus Reid', 1200, 68.2, 22.1, 9.7, 2.8),
(2, '2024-01-25', 'Leger', 800, 78.4, 15.6, 6.0, 3.5),
(3, '2024-02-05', 'Ipsos Canada', 900, 72.1, 18.9, 9.0, 3.2)
ON CONFLICT DO NOTHING;

INSERT INTO public_comments (bill_id, commenter_name, commenter_email, comment, sentiment, is_verified) VALUES
(1, 'John Smith', 'john.smith@email.com', 'This bill will help protect our environment for future generations', 'positive', true),
(1, 'Sarah Johnson', 'sarah.j@email.com', 'I have concerns about the economic impact on local businesses', 'negative', true),
(1, 'Mike Wilson', 'mike.w@email.com', 'Good initiative but needs more funding for implementation', 'neutral', false),
(2, 'Dr. Emily Brown', 'emily.brown@healthcare.org', 'This healthcare reform is long overdue and will benefit many Canadians', 'positive', true),
(2, 'Robert Davis', 'robert.d@email.com', 'The timeline seems too aggressive for proper implementation', 'negative', false),
(3, 'Lisa Chen', 'lisa.chen@education.ca', 'Increased funding for education is always a good investment', 'positive', true)
ON CONFLICT DO NOTHING;

-- 4. POPULATE MEDIA COVERAGE
INSERT INTO media_coverage (bill_id, media_outlet, headline, url, publication_date, sentiment) VALUES
(1, 'CBC News', 'New Environmental Bill Aims to Protect Canadian Wilderness', 'https://cbc.ca/news/environmental-bill-2024', '2024-02-18', 'positive'),
(1, 'Toronto Star', 'Environmental Bill Faces Opposition from Business Groups', 'https://thestar.com/environmental-opposition', '2024-02-22', 'negative'),
(2, 'Global News', 'Healthcare Reform Bill Passes First Reading with Strong Support', 'https://globalnews.ca/healthcare-bill-passes', '2024-01-22', 'positive'),
(2, 'CTV News', 'Healthcare Bill to Improve Access in Rural Areas', 'https://ctvnews.ca/healthcare-rural-access', '2024-01-25', 'positive'),
(3, 'National Post', 'Education Funding Bill Receives Bipartisan Support', 'https://nationalpost.com/education-funding-bipartisan', '2024-02-03', 'positive')
ON CONFLICT DO NOTHING;

-- 5. POPULATE BILL DOCUMENTS
INSERT INTO bill_documents (bill_id, document_type, title, file_path, file_size, mime_type, uploaded_by) VALUES
(1, 'bill_text', 'Environmental Protection Act 2024 - Full Text', '/documents/bill1_full_text.pdf', 2048576, 'application/pdf', 1),
(1, 'summary', 'Environmental Protection Act 2024 - Executive Summary', '/documents/bill1_summary.pdf', 512000, 'application/pdf', 1),
(1, 'impact_assessment', 'Environmental Impact Assessment Report', '/documents/bill1_impact_assessment.pdf', 1536000, 'application/pdf', 2),
(2, 'bill_text', 'Healthcare Reform Act 2024 - Full Text', '/documents/bill2_full_text.pdf', 1792000, 'application/pdf', 2),
(2, 'summary', 'Healthcare Reform Act 2024 - Executive Summary', '/documents/bill2_summary.pdf', 384000, 'application/pdf', 2),
(3, 'bill_text', 'Education Funding Enhancement Act 2024 - Full Text', '/documents/bill3_full_text.pdf', 1280000, 'application/pdf', 3)
ON CONFLICT DO NOTHING;

-- 6. POPULATE BILL TIMELINE
INSERT INTO bill_timeline (bill_id, event_type, event_date, description, related_politician_id) VALUES
(1, 'introduced', '2024-01-10', 'Bill introduced to Parliament by Jane Doe', 1),
(1, 'first_reading', '2024-01-15', 'First reading completed successfully', 1),
(1, 'committee_review', '2024-01-25', 'Referred to Environment Committee for review', 2),
(1, 'second_reading', '2024-02-20', 'Second reading with amendments', 1),
(1, 'public_consultation', '2024-02-28', 'Public consultation period begins', 3),
(2, 'introduced', '2024-01-15', 'Bill introduced to Parliament by John Smith', 2),
(2, 'first_reading', '2024-01-20', 'First reading completed successfully', 2),
(2, 'committee_review', '2024-01-30', 'Referred to Health Committee for review', 1),
(3, 'introduced', '2024-01-25', 'Bill introduced to Parliament by Bob Johnson', 3),
(3, 'first_reading', '2024-02-01', 'First reading completed successfully', 3)
ON CONFLICT DO NOTHING;

-- 7. POPULATE LEGISLATIVE EVENTS
INSERT INTO legislative_events (event_type, event_date, title, description, location, attendees_count) VALUES
('public_hearing', '2024-02-15', 'Environmental Bill Public Hearing', 'Public hearing on Environmental Protection Act 2024', 'Parliament Hill, Ottawa', 150),
('committee_meeting', '2024-01-25', 'Environment Committee Review', 'Committee review of Environmental Protection Act', 'Parliament Building, Room 201', 25),
('public_hearing', '2024-01-25', 'Healthcare Bill Public Hearing', 'Public hearing on Healthcare Reform Act 2024', 'Parliament Hill, Ottawa', 200),
('committee_meeting', '2024-01-30', 'Health Committee Review', 'Committee review of Healthcare Reform Act', 'Parliament Building, Room 205', 30),
('public_hearing', '2024-02-05', 'Education Bill Public Hearing', 'Public hearing on Education Funding Enhancement Act', 'Parliament Hill, Ottawa', 120)
ON CONFLICT DO NOTHING;

-- 8. POPULATE ANALYTICS DATA
INSERT INTO bill_analytics (bill_id, metric_date, social_media_mentions, news_mentions, public_support_score, controversy_score) VALUES
(1, '2024-02-15', 1250, 45, 65.5, 45.2),
(1, '2024-02-16', 1380, 52, 66.1, 47.8),
(1, '2024-02-17', 1120, 38, 65.8, 46.3),
(1, '2024-02-18', 1560, 67, 68.2, 42.1),
(1, '2024-02-19', 1420, 58, 67.9, 43.5),
(2, '2024-01-25', 890, 32, 78.4, 25.6),
(2, '2024-01-26', 920, 35, 78.9, 24.8),
(2, '2024-01-27', 850, 30, 78.6, 25.2),
(3, '2024-02-05', 680, 28, 72.1, 28.9),
(3, '2024-02-06', 720, 31, 72.8, 28.1)
ON CONFLICT DO NOTHING;

INSERT INTO politician_analytics (politician_id, metric_date, social_media_followers, approval_rating, bill_success_rate) VALUES
(1, '2024-02-15', 15420, 68.5, 75.0),
(1, '2024-02-16', 15480, 68.7, 75.0),
(1, '2024-02-17', 15520, 68.9, 75.0),
(2, '2024-01-25', 12850, 72.3, 80.0),
(2, '2024-01-26', 12900, 72.5, 80.0),
(2, '2024-01-27', 12950, 72.8, 80.0),
(3, '2024-02-05', 9650, 65.2, 70.0),
(3, '2024-02-06', 9700, 65.4, 70.0)
ON CONFLICT DO NOTHING;

-- 9. POPULATE POLITICIAN ROLES AND COMMITTEES
INSERT INTO politician_roles (politician_id, role_name, organization_id, start_date, is_current) VALUES
(1, 'Member of Parliament', 1, '2020-10-19', true),
(1, 'Environment Committee Member', 1, '2021-01-15', true),
(2, 'Member of Parliament', 2, '2019-10-21', true),
(2, 'Health Committee Member', 2, '2020-02-10', true),
(3, 'Member of Parliament', 3, '2021-09-20', true),
(3, 'Education Committee Member', 3, '2021-11-05', true)
ON CONFLICT DO NOTHING;

INSERT INTO politician_committees (politician_id, committee_id, role, start_date, is_current) VALUES
(1, 1, 'member', '2021-01-15', true),
(1, 2, 'member', '2021-03-20', true),
(2, 2, 'member', '2020-02-10', true),
(2, 3, 'member', '2020-04-15', true),
(3, 3, 'member', '2021-11-05', true),
(3, 1, 'member', '2022-01-10', true)
ON CONFLICT DO NOTHING;

-- 10. POPULATE ORGANIZATION MEMBERSHIPS
INSERT INTO organization_memberships (organization_id, politician_id, membership_type, start_date, is_current) VALUES
(1, 1, 'member', '2021-01-15', true),
(1, 3, 'member', '2022-01-10', true),
(2, 2, 'member', '2020-02-10', true),
(2, 1, 'member', '2021-03-20', true),
(3, 3, 'member', '2021-11-05', true),
(3, 2, 'member', '2020-04-15', true)
ON CONFLICT DO NOTHING;

-- 11. POPULATE POLITICIAN RELATIONSHIPS
INSERT INTO politician_relationships (politician_id_1, politician_id_2, relationship_type, strength) VALUES
(1, 2, 'colleague', 0.8),
(1, 3, 'colleague', 0.7),
(2, 3, 'colleague', 0.6),
(2, 1, 'colleague', 0.8),
(3, 1, 'colleague', 0.7),
(3, 2, 'colleague', 0.6)
ON CONFLICT DO NOTHING;

-- 12. POPULATE REGIONS
INSERT INTO regions (name, jurisdiction_id, population, area_km2) VALUES
('Central Ontario', 2, 2500000, 150000.50),
('Greater Toronto Area', 4, 6500000, 7500.25),
('Montreal Metropolitan Area', 5, 4200000, 4200.75),
('Ottawa Valley', 1, 1200000, 85000.30),
('Quebec City Region', 3, 1800000, 45000.60)
ON CONFLICT DO NOTHING;

-- Verify the data population
SELECT 'Database population complete!' as status;
SELECT COUNT(*) as total_bills FROM bills_bill;
SELECT COUNT(*) as total_politicians FROM core_politician;
SELECT COUNT(*) as total_organizations FROM core_organization;
SELECT COUNT(*) as total_votes FROM bills_membervote;
SELECT COUNT(*) as total_sponsors FROM bill_sponsors;
SELECT COUNT(*) as total_voting_sessions FROM voting_sessions;
SELECT COUNT(*) as total_public_comments FROM public_comments;
SELECT COUNT(*) as total_media_coverage FROM media_coverage;
SELECT COUNT(*) as total_bill_documents FROM bill_documents;
SELECT COUNT(*) as total_analytics_records FROM bill_analytics;
