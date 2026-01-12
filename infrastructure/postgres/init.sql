
-- LearnFlow Database Initialization
-- Created: 2026-01-12

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Students table
CREATE TABLE IF NOT EXISTS students (
    student_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    external_id VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Mastery scores table (long-term storage)
CREATE TABLE IF NOT EXISTS mastery_scores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID NOT NULL REFERENCES students(student_id),
    date DATE NOT NULL,
    completion_score DECIMAL(5,4),
    quiz_score DECIMAL(5,4),
    quality_score DECIMAL(5,4),
    consistency_score DECIMAL(5,4),
    final_score DECIMAL(5,4),
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(student_id, date)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_mastery_student_date ON mastery_scores(student_id, date);
CREATE INDEX IF NOT EXISTS idx_students_external_id ON students(external_id);

-- Audit log for tracking changes
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    table_name VARCHAR(100),
    record_id VARCHAR(255),
    action VARCHAR(50),
    old_value JSONB,
    new_value JSONB,
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    changed_by VARCHAR(255)
);

-- Add triggers for updated_at
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

-- Initial admin user (for testing)
INSERT INTO students (external_id, email)
VALUES ('student_001', 'admin@learnflow.io')
ON CONFLICT DO NOTHING;
