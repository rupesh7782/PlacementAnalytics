-- ============================================================
-- Placement Analytics & Prediction System - Database Schema
-- ============================================================

-- Drop tables if they exist (for fresh setup)
DROP TABLE IF EXISTS placements CASCADE;
DROP TABLE IF EXISTS skills CASCADE;
DROP TABLE IF EXISTS companies CASCADE;
DROP TABLE IF EXISTS students CASCADE;

-- ============================================================
-- Table: students
-- Stores core student demographic and academic information
-- ============================================================
CREATE TABLE students (
    student_id      SERIAL PRIMARY KEY,
    student_code    VARCHAR(20) UNIQUE NOT NULL,       -- e.g. "STU001"
    name            VARCHAR(100) NOT NULL,
    branch          VARCHAR(100) NOT NULL,             -- e.g. "Computer Science"
    cgpa            NUMERIC(4, 2) CHECK (cgpa >= 0 AND cgpa <= 10),
    graduation_year INTEGER NOT NULL,
    email           VARCHAR(150) UNIQUE NOT NULL,
    phone           VARCHAR(15),
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- Table: skills
-- Stores technical and soft skill scores for each student
-- ============================================================
CREATE TABLE skills (
    skill_id            SERIAL PRIMARY KEY,
    student_id          INTEGER NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
    python_score        INTEGER DEFAULT 0 CHECK (python_score BETWEEN 0 AND 10),
    java_score          INTEGER DEFAULT 0 CHECK (java_score BETWEEN 0 AND 10),
    sql_score           INTEGER DEFAULT 0 CHECK (sql_score BETWEEN 0 AND 10),
    html_css_score      INTEGER DEFAULT 0 CHECK (html_css_score BETWEEN 0 AND 10),
    javascript_score    INTEGER DEFAULT 0 CHECK (javascript_score BETWEEN 0 AND 10),
    aptitude_score      NUMERIC(5, 2) CHECK (aptitude_score BETWEEN 0 AND 100),  -- out of 100
    communication_score NUMERIC(5, 2) CHECK (communication_score BETWEEN 0 AND 10), -- out of 10
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(student_id)  -- one skill record per student
);

-- ============================================================
-- Table: companies
-- Stores company/recruiter information
-- ============================================================
CREATE TABLE companies (
    company_id    SERIAL PRIMARY KEY,
    company_name  VARCHAR(150) UNIQUE NOT NULL,
    industry      VARCHAR(100),
    location      VARCHAR(100),
    website       VARCHAR(200),
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- Table: placements
-- Tracks each student's placement attempts and outcomes
-- ============================================================
CREATE TABLE placements (
    placement_id      SERIAL PRIMARY KEY,
    student_id        INTEGER NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
    company_id        INTEGER REFERENCES companies(company_id) ON DELETE SET NULL,
    package_offered   NUMERIC(10, 2),                 -- in LPA (Lakhs Per Annum)
    placement_status  VARCHAR(20) NOT NULL DEFAULT 'Not Placed'
                      CHECK (placement_status IN ('Placed', 'Not Placed', 'In Progress')),
    interview_date    DATE,
    selection_result  VARCHAR(20) DEFAULT 'Pending'
                      CHECK (selection_result IN ('Selected', 'Rejected', 'Pending', 'Waitlisted')),
    offer_letter_date DATE,
    notes             TEXT,
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- Indexes for performance
-- ============================================================
CREATE INDEX idx_students_branch ON students(branch);
CREATE INDEX idx_students_graduation_year ON students(graduation_year);
CREATE INDEX idx_placements_status ON placements(placement_status);
CREATE INDEX idx_placements_student ON placements(student_id);
CREATE INDEX idx_placements_company ON placements(company_id);

-- ============================================================
-- Trigger to auto-update updated_at on students
-- ============================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_students_updated_at
    BEFORE UPDATE ON students
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_placements_updated_at
    BEFORE UPDATE ON placements
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- Sample Companies (seed data)
-- ============================================================
INSERT INTO companies (company_name, industry, location) VALUES
('TCS', 'IT Services', 'Mumbai'),
('Infosys', 'IT Services', 'Bengaluru'),
('Wipro', 'IT Services', 'Bengaluru'),
('Accenture', 'Consulting', 'Mumbai'),
('Cognizant', 'IT Services', 'Chennai'),
('HCL Technologies', 'IT Services', 'Noida'),
('Tech Mahindra', 'IT Services', 'Pune'),
('Capgemini', 'IT Consulting', 'Mumbai'),
('IBM', 'Technology', 'Bengaluru'),
('Amazon', 'E-Commerce / Cloud', 'Hyderabad'),
('Microsoft', 'Software', 'Hyderabad'),
('Google', 'Internet / Cloud', 'Bengaluru'),
('Persistent Systems', 'Software', 'Pune'),
('Mphasis', 'IT Services', 'Bengaluru'),
('L&T Infotech', 'IT Services', 'Mumbai');
