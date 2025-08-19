-- Seed Data for OpenPolicy Platform
-- This script populates the database with initial data

-- Insert current parliament session
INSERT INTO parliament_sessions (parliament_number, session_number, start_date, status)
VALUES (44, 1, '2021-11-22', 'active')
ON CONFLICT (parliament_number, session_number) DO NOTHING;

-- Insert sample representatives
INSERT INTO representatives (name, email, phone, party, constituency, province, bio, active) VALUES
('Justin Trudeau', 'justin.trudeau@parl.gc.ca', '613-995-0253', 'Liberal', 'Papineau', 'Quebec', 'Prime Minister of Canada and Leader of the Liberal Party', true),
('Pierre Poilievre', 'pierre.poilievre@parl.gc.ca', '613-992-2772', 'Conservative', 'Carleton', 'Ontario', 'Leader of the Official Opposition and Leader of the Conservative Party', true),
('Jagmeet Singh', 'jagmeet.singh@parl.gc.ca', '613-996-5597', 'NDP', 'Burnaby South', 'British Columbia', 'Leader of the New Democratic Party', true),
('Yves-François Blanchet', 'yves-francois.blanchet@parl.gc.ca', '613-992-6361', 'Bloc Québécois', 'Beloeil—Chambly', 'Quebec', 'Leader of the Bloc Québécois', true),
('Elizabeth May', 'elizabeth.may@parl.gc.ca', '613-996-1119', 'Green', 'Saanich—Gulf Islands', 'British Columbia', 'Parliamentary Leader of the Green Party', true),
('Chrystia Freeland', 'chrystia.freeland@parl.gc.ca', '613-992-5234', 'Liberal', 'University—Rosedale', 'Ontario', 'Deputy Prime Minister and Minister of Finance', true),
('Candice Bergen', 'candice.bergen@parl.gc.ca', '613-995-0579', 'Conservative', 'Portage—Lisgar', 'Manitoba', 'Deputy Leader of the Conservative Party', true),
('Michael Chong', 'michael.chong@parl.gc.ca', '613-992-4179', 'Conservative', 'Wellington—Halton Hills', 'Ontario', 'Shadow Minister for Foreign Affairs', true)
ON CONFLICT (email) DO NOTHING;

-- Insert sample committees
INSERT INTO committees (name, abbreviation, type, description, active) VALUES
('Standing Committee on Finance', 'FINA', 'standing', 'Reviews and reports on all matters relating to the mandate, management, and operation of the Department of Finance', true),
('Standing Committee on Health', 'HESA', 'standing', 'Reviews health-related legislation and policies', true),
('Standing Committee on Environment and Sustainable Development', 'ENVI', 'standing', 'Studies environmental issues and sustainable development', true),
('Standing Committee on Justice and Human Rights', 'JUST', 'standing', 'Reviews justice system and human rights issues', true),
('Standing Committee on Foreign Affairs and International Development', 'FAAE', 'standing', 'Studies Canada''s foreign policy and international development', true),
('Standing Committee on National Defence', 'NDDN', 'standing', 'Reviews matters relating to national defence and the Canadian Armed Forces', true),
('Standing Committee on Indigenous and Northern Affairs', 'INAN', 'standing', 'Studies issues affecting Indigenous peoples and Northern communities', true),
('Standing Committee on Public Safety and National Security', 'SECU', 'standing', 'Reviews public safety and national security matters', true)
ON CONFLICT (abbreviation) DO NOTHING;

-- Insert sample bills
INSERT INTO bills (bill_number, title, summary, sponsor, status, parliament, session, introduction_date, latest_activity_date) VALUES
('C-1', 'An Act respecting the administration of oaths of office', 'Pro forma bill to assert the right of the House of Commons to give precedence to matters other than those expressed in the Speech from the Throne', 'Prime Minister', 'First Reading', 44, 1, '2021-11-23', '2021-11-23'),
('C-2', 'An Act to provide further support in response to COVID-19', 'This enactment amends the Employment Insurance Act to provide additional support to workers affected by COVID-19', 'Deputy Prime Minister and Minister of Finance', 'Royal Assent', 44, 1, '2021-11-24', '2021-12-17'),
('C-3', 'An Act to amend the Criminal Code and the Canada Labour Code', 'This enactment amends the Criminal Code and the Canada Labour Code to provide ten days of paid sick leave for workers in the federally regulated private sector', 'Minister of Labour', 'Royal Assent', 44, 1, '2021-11-26', '2021-12-17'),
('C-4', 'An Act to amend the Criminal Code (conversion therapy)', 'This enactment amends the Criminal Code to prohibit conversion therapy practices', 'Minister of Justice', 'Royal Assent', 44, 1, '2021-11-29', '2021-12-08'),
('C-5', 'An Act to amend the Bills of Exchange Act, the Interpretation Act and the Canada Labour Code (National Day for Truth and Reconciliation)', 'This enactment establishes September 30 as a federal statutory holiday to be called the National Day for Truth and Reconciliation', 'Minister of Canadian Heritage', 'Committee', 44, 1, '2021-12-13', '2024-01-15'),
('S-1', 'An Act relating to railways', 'Pro forma bill introduced in the Senate', 'Leader of the Government in the Senate', 'First Reading', 44, 1, '2021-11-23', '2021-11-23')
ON CONFLICT (bill_number, parliament, session) DO NOTHING;

-- Insert sample votes
INSERT INTO parliament_votes (vote_number, parliament, session, sitting, bill_number, vote_date, vote_description, result, yeas, nays, paired, total) VALUES
(1, 44, 1, 2, NULL, '2021-11-24', 'Motion for Address in Reply to the Speech from the Throne', 'Agreed To', 214, 119, 0, 333),
(2, 44, 1, 5, 'C-2', '2021-11-25', 'Motion for second reading of Bill C-2', 'Agreed To', 214, 119, 0, 333),
(3, 44, 1, 8, 'C-3', '2021-11-26', 'Motion for second reading of Bill C-3', 'Agreed To', 332, 0, 0, 332),
(4, 44, 1, 10, 'C-4', '2021-12-01', 'Motion for second reading of Bill C-4', 'Agreed To', 304, 7, 0, 311),
(5, 44, 1, 15, 'C-2', '2021-12-16', 'Motion for third reading of Bill C-2', 'Agreed To', 330, 0, 0, 330)
ON CONFLICT (vote_number, parliament, session) DO NOTHING;

-- Insert sample debates
INSERT INTO debates (debate_date, parliament, session, sitting, title, hansard_number) VALUES
('2021-11-22', 44, 1, 1, 'Opening of Parliament - Speech from the Throne', 'Vol. 151, No. 001'),
('2021-11-23', 44, 1, 2, 'Business of the House - Address in Reply to the Speech from the Throne', 'Vol. 151, No. 002'),
('2021-11-24', 44, 1, 3, 'Government Business - Bill C-2', 'Vol. 151, No. 003'),
('2021-11-25', 44, 1, 4, 'Government Business - Bill C-3', 'Vol. 151, No. 004'),
('2021-11-26', 44, 1, 5, 'Private Members'' Business', 'Vol. 151, No. 005')
ON CONFLICT (debate_date, parliament, session) DO NOTHING;

-- Insert admin user (password: admin123)
INSERT INTO users (first_name, last_name, phone, postal_code, email, password, role, email_verified_at, created_at, updated_at)
VALUES ('Admin', 'User', '000-000-0000', 'K1A0A6', 'admin@openpolicy.ca', '$2y$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', '490', NOW(), NOW(), NOW())
ON CONFLICT (email) DO NOTHING;

-- Insert test user (password: user123)
INSERT INTO users (first_name, last_name, phone, postal_code, email, password, role, email_verified_at, created_at, updated_at)
VALUES ('Test', 'User', '111-111-1111', 'M5V3A8', 'user@example.com', '$2y$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', '111', NOW(), NOW(), NOW())
ON CONFLICT (email) DO NOTHING;