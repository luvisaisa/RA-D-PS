-- PostgreSQL Database Schema for Parse Case Management
-- RA-D-PS Parse Case Repository
-- Created: 2025-10-19

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Parse Cases Table
-- Stores definitions of all XML structure parse cases
CREATE TABLE IF NOT EXISTS parse_cases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    version VARCHAR(20) NOT NULL DEFAULT '1.0',
    
    -- Detection criteria stored as JSON
    detection_criteria JSONB NOT NULL,
    -- Example structure:
    -- {
    --   "min_chars": 3,
    --   "requires_reason": true,
    --   "requires_header": true,
    --   "requires_modality": true,
    --   "characteristic_fields": ["confidence", "subtlety", "obscuration"],
    --   "session_count": 4,
    --   "v2_fields": ["malignancy", "internalStructure", "calcification"]
    -- }
    
    -- Field mappings for this parse case (JSON array)
    field_mappings JSONB DEFAULT '[]'::jsonb,
    -- Example structure:
    -- [
    --   {"source": "confidence", "target": "Confidence", "type": "float"},
    --   {"source": "subtlety", "target": "Subtlety", "type": "float"}
    -- ]
    
    -- Characteristic fields as array
    characteristic_fields TEXT[] DEFAULT ARRAY[]::TEXT[],
    
    -- Structural requirements
    requires_header BOOLEAN DEFAULT false,
    requires_modality BOOLEAN DEFAULT false,
    min_session_count INTEGER DEFAULT 0,
    max_session_count INTEGER DEFAULT NULL,
    
    -- Priority for detection (higher = check first)
    detection_priority INTEGER DEFAULT 50,
    
    -- Status and metadata
    is_active BOOLEAN DEFAULT true,
    is_legacy_format BOOLEAN DEFAULT true,
    format_type VARCHAR(50) DEFAULT 'LIDC',  -- LIDC, LIDC_v2, CXR, etc.
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    notes TEXT,
    
    -- Indexes
    CONSTRAINT valid_priority CHECK (detection_priority >= 0 AND detection_priority <= 100)
);

-- Parse Case Profiles Table
-- Links parse cases to their profile configurations
CREATE TABLE IF NOT EXISTS parse_case_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    parse_case_id UUID NOT NULL REFERENCES parse_cases(id) ON DELETE CASCADE,
    profile_name VARCHAR(100) NOT NULL,
    profile_config JSONB NOT NULL,
    -- Example structure:
    -- {
    --   "profile_id": "lidc-v2-standard",
    --   "profile_name": "LIDC v2 Standard Profile",
    --   "field_mappings": [...],
    --   "entity_extraction": {...}
    -- }
    
    is_default BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT unique_parse_case_profile UNIQUE(parse_case_id, profile_name)
);

-- Parse Case Detection History
-- Tracks which parse cases were detected for which files (audit trail)
CREATE TABLE IF NOT EXISTS parse_case_detection_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    file_path TEXT NOT NULL,
    file_checksum VARCHAR(64),  -- MD5 or SHA256
    parse_case_id UUID REFERENCES parse_cases(id) ON DELETE SET NULL,
    parse_case_name VARCHAR(100) NOT NULL,
    detection_metadata JSONB,
    -- Example:
    -- {
    --   "char_count": 5,
    --   "session_count": 4,
    --   "has_header": true,
    --   "v2_characteristics": ["malignancy", "subtlety"],
    --   "confidence_score": 0.95
    -- }
    
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    detection_duration_ms INTEGER,
    
    -- Indexes on file_path and detected_at for performance
    CONSTRAINT idx_file_detection UNIQUE(file_path, detected_at)
);

-- Parse Case Statistics
-- Aggregated statistics about parse case usage
CREATE TABLE IF NOT EXISTS parse_case_statistics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    parse_case_id UUID NOT NULL REFERENCES parse_cases(id) ON DELETE CASCADE,
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    
    detection_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    avg_detection_time_ms NUMERIC(10,2),
    
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT unique_parse_case_date UNIQUE(parse_case_id, date)
);

-- Create indexes for performance
CREATE INDEX idx_parse_cases_name ON parse_cases(name);
CREATE INDEX idx_parse_cases_format_type ON parse_cases(format_type);
CREATE INDEX idx_parse_cases_priority ON parse_cases(detection_priority DESC);
CREATE INDEX idx_parse_cases_active ON parse_cases(is_active) WHERE is_active = true;
CREATE INDEX idx_parse_cases_detection_criteria ON parse_cases USING GIN(detection_criteria);

CREATE INDEX idx_parse_case_profiles_parse_case ON parse_case_profiles(parse_case_id);
CREATE INDEX idx_parse_case_profiles_default ON parse_case_profiles(is_default) WHERE is_default = true;

CREATE INDEX idx_detection_history_file ON parse_case_detection_history(file_path);
CREATE INDEX idx_detection_history_parse_case ON parse_case_detection_history(parse_case_id);
CREATE INDEX idx_detection_history_detected_at ON parse_case_detection_history(detected_at DESC);

CREATE INDEX idx_statistics_parse_case ON parse_case_statistics(parse_case_id);
CREATE INDEX idx_statistics_date ON parse_case_statistics(date DESC);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at triggers
CREATE TRIGGER update_parse_cases_updated_at
    BEFORE UPDATE ON parse_cases
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_parse_case_profiles_updated_at
    BEFORE UPDATE ON parse_case_profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_parse_case_statistics_updated_at
    BEFORE UPDATE ON parse_case_statistics
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Comments for documentation
COMMENT ON TABLE parse_cases IS 'Stores all XML parse case definitions with detection criteria';
COMMENT ON TABLE parse_case_profiles IS 'Links parse cases to their profile configurations';
COMMENT ON TABLE parse_case_detection_history IS 'Audit trail of parse case detections';
COMMENT ON TABLE parse_case_statistics IS 'Aggregated statistics for parse case usage';

COMMENT ON COLUMN parse_cases.detection_criteria IS 'JSON object defining how to detect this parse case';
COMMENT ON COLUMN parse_cases.field_mappings IS 'JSON array of source->target field mappings';
COMMENT ON COLUMN parse_cases.detection_priority IS 'Higher priority parse cases are checked first (0-100)';
COMMENT ON COLUMN parse_cases.format_type IS 'Format category: LIDC, LIDC_v2, CXR, etc.';
