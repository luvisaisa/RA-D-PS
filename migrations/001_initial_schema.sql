-- =====================================================================
-- RA-D-PS Schema-Agnostic Data Ingestion System
-- PostgreSQL Database Schema v1.0
-- =====================================================================
-- Purpose: Flexible document ingestion with profile-based normalization
-- Supports: XML, JSON, CSV, PDF, and extensible to other formats
-- =====================================================================

-- Enable UUID extension for primary keys
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For full-text search optimization

-- =====================================================================
-- CORE TABLES
-- =====================================================================

-- ---------------------------------------------------------------------
-- documents: Metadata for all ingested files
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_file_name VARCHAR(500) NOT NULL,
    source_file_path TEXT NOT NULL,
    file_type VARCHAR(50) NOT NULL CHECK (file_type IN ('XML', 'JSON', 'CSV', 'PDF', 'DOCX', 'OTHER')),
    file_size_bytes BIGINT,
    file_hash VARCHAR(64),  -- SHA-256 hash for deduplication
    profile_id UUID,  -- Foreign key added after profiles table creation
    
    -- Ingestion tracking
    ingestion_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_modified TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    uploaded_by VARCHAR(255),
    
    -- Status tracking
    status VARCHAR(50) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'archived')),
    error_message TEXT,
    processing_duration_ms INTEGER,
    
    -- Metadata
    original_format_version VARCHAR(50),  -- e.g., "LIDC-IDRI v3.2"
    source_system VARCHAR(255),
    batch_id UUID,
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for documents
CREATE INDEX idx_documents_file_type ON documents(file_type);
CREATE INDEX idx_documents_status ON documents(status);
CREATE INDEX idx_documents_profile_id ON documents(profile_id);
CREATE INDEX idx_documents_ingestion_timestamp ON documents(ingestion_timestamp DESC);
CREATE INDEX idx_documents_batch_id ON documents(batch_id);
CREATE INDEX idx_documents_file_hash ON documents(file_hash);  -- For deduplication
CREATE UNIQUE INDEX idx_documents_unique_path ON documents(source_file_path) WHERE status != 'archived';

-- Comment documentation
COMMENT ON TABLE documents IS 'Metadata for all ingested documents regardless of source format';
COMMENT ON COLUMN documents.file_hash IS 'SHA-256 hash for detecting duplicate uploads';
COMMENT ON COLUMN documents.profile_id IS 'Reference to the profile used for parsing and normalization';
COMMENT ON COLUMN documents.batch_id IS 'Groups documents uploaded together for batch operations';

-- ---------------------------------------------------------------------
-- document_content: Flexible canonical data storage
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS document_content (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL UNIQUE REFERENCES documents(id) ON DELETE CASCADE,
    
    -- Canonical data (flexible JSONB structure)
    canonical_data JSONB NOT NULL,
    
    -- Full-text search optimization
    searchable_text TEXT,
    
    -- Extracted entities (structured extraction)
    extracted_entities JSONB DEFAULT '{}'::jsonb,
    
    -- User-defined tags for categorization
    tags TEXT[],
    
    -- Schema versioning for migrations
    schema_version INTEGER DEFAULT 1,
    
    -- Quality metrics
    confidence_score DECIMAL(5, 4),  -- 0.0000 to 1.0000
    validation_errors JSONB,
    
    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for document_content
CREATE INDEX idx_content_document_id ON document_content(document_id);
CREATE INDEX idx_content_canonical_data_gin ON document_content USING GIN (canonical_data);
CREATE INDEX idx_content_entities_gin ON document_content USING GIN (extracted_entities);
CREATE INDEX idx_content_tags_gin ON document_content USING GIN (tags);
CREATE INDEX idx_content_searchable_text_gin ON document_content USING GIN (to_tsvector('english', searchable_text));

-- Comment documentation
COMMENT ON TABLE document_content IS 'Normalized canonical data extracted from source documents';
COMMENT ON COLUMN document_content.canonical_data IS 'Flexible JSONB storage for normalized data in canonical schema';
COMMENT ON COLUMN document_content.searchable_text IS 'Concatenated text from all fields for full-text search';
COMMENT ON COLUMN document_content.extracted_entities IS 'Structured entities: dates, people, organizations, amounts, etc.';
COMMENT ON COLUMN document_content.confidence_score IS 'Overall extraction confidence (0-1), null if not calculated';

-- ---------------------------------------------------------------------
-- profiles: Profile definitions for format mappings
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    profile_name VARCHAR(255) NOT NULL UNIQUE,
    file_type VARCHAR(50) NOT NULL CHECK (file_type IN ('XML', 'JSON', 'CSV', 'PDF', 'DOCX', 'OTHER')),
    
    -- Profile metadata
    description TEXT,
    source_format_description TEXT,
    canonical_schema_version INTEGER DEFAULT 1,
    
    -- Mapping configuration (stored as JSONB)
    mapping_definition JSONB NOT NULL,
    
    -- Validation rules (stored as JSONB)
    validation_rules JSONB DEFAULT '{}'::jsonb,
    
    -- Transformation library references
    transformations JSONB DEFAULT '[]'::jsonb,
    
    -- Entity extraction patterns
    entity_patterns JSONB DEFAULT '{}'::jsonb,
    
    -- Profile status
    is_active BOOLEAN DEFAULT TRUE,
    is_default BOOLEAN DEFAULT FALSE,  -- Default profile for a file type
    
    -- Version control
    version VARCHAR(50) DEFAULT '1.0.0',
    parent_profile_id UUID REFERENCES profiles(id),  -- For profile inheritance
    
    -- Audit fields
    created_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP WITH TIME ZONE
);

-- Add foreign key now that profiles table exists
ALTER TABLE documents ADD CONSTRAINT fk_documents_profile 
    FOREIGN KEY (profile_id) REFERENCES profiles(id) ON DELETE SET NULL;

-- Indexes for profiles
CREATE INDEX idx_profiles_file_type ON profiles(file_type);
CREATE INDEX idx_profiles_is_active ON profiles(is_active);
CREATE INDEX idx_profiles_is_default ON profiles(is_default, file_type);
CREATE INDEX idx_profiles_mapping_gin ON profiles USING GIN (mapping_definition);

-- Ensure only one default profile per file type
CREATE UNIQUE INDEX idx_profiles_unique_default ON profiles(file_type, is_default) 
    WHERE is_default = TRUE;

-- Comment documentation
COMMENT ON TABLE profiles IS 'Profile definitions for mapping source formats to canonical schema';
COMMENT ON COLUMN profiles.mapping_definition IS 'JSONB array of field mappings from source to canonical schema';
COMMENT ON COLUMN profiles.validation_rules IS 'JSONB object defining required fields and validation constraints';
COMMENT ON COLUMN profiles.entity_patterns IS 'JSONB object with regex patterns for entity extraction';
COMMENT ON COLUMN profiles.parent_profile_id IS 'Allows profile inheritance for similar formats';

-- ---------------------------------------------------------------------
-- ingestion_logs: Audit trail for all ingestion operations
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ingestion_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    batch_id UUID,
    
    -- Log details
    log_level VARCHAR(20) NOT NULL CHECK (log_level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')),
    message TEXT NOT NULL,
    details JSONB,
    
    -- Context
    operation VARCHAR(100),  -- e.g., 'parse', 'validate', 'transform', 'store'
    duration_ms INTEGER,
    
    -- Location tracking
    file_location TEXT,  -- Path within source file where issue occurred
    line_number INTEGER,
    
    -- Timestamp
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for ingestion_logs
CREATE INDEX idx_logs_document_id ON ingestion_logs(document_id);
CREATE INDEX idx_logs_batch_id ON ingestion_logs(batch_id);
CREATE INDEX idx_logs_level ON ingestion_logs(log_level);
CREATE INDEX idx_logs_timestamp ON ingestion_logs(timestamp DESC);
CREATE INDEX idx_logs_operation ON ingestion_logs(operation);

-- Comment documentation
COMMENT ON TABLE ingestion_logs IS 'Comprehensive audit trail for all ingestion and processing operations';
COMMENT ON COLUMN ingestion_logs.details IS 'JSONB object with additional context (stack traces, field values, etc.)';

-- =====================================================================
-- SUPPORTING TABLES
-- =====================================================================

-- ---------------------------------------------------------------------
-- batch_metadata: Track batch upload operations
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS batch_metadata (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    batch_name VARCHAR(255),
    profile_id UUID REFERENCES profiles(id),
    
    -- Statistics
    total_files INTEGER DEFAULT 0,
    successful INTEGER DEFAULT 0,
    failed INTEGER DEFAULT 0,
    skipped INTEGER DEFAULT 0,
    
    -- Performance
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    total_duration_ms INTEGER,
    
    -- Uploaded by
    uploaded_by VARCHAR(255),
    
    -- Status
    status VARCHAR(50) DEFAULT 'in_progress' CHECK (status IN ('in_progress', 'completed', 'failed', 'cancelled'))
);

CREATE INDEX idx_batch_started_at ON batch_metadata(started_at DESC);
CREATE INDEX idx_batch_status ON batch_metadata(status);

-- ---------------------------------------------------------------------
-- user_queries: Save user search queries for analytics and UX
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_queries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    query_text TEXT,
    filters JSONB,
    results_count INTEGER,
    executed_by VARCHAR(255),
    execution_time_ms INTEGER,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_user_queries_timestamp ON user_queries(timestamp DESC);
CREATE INDEX idx_user_queries_executed_by ON user_queries(executed_by);

-- =====================================================================
-- VIEWS FOR COMMON QUERIES
-- =====================================================================

-- ---------------------------------------------------------------------
-- v_document_summary: Combined document metadata and content preview
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW v_document_summary AS
SELECT 
    d.id,
    d.source_file_name,
    d.file_type,
    d.status,
    d.ingestion_timestamp,
    p.profile_name,
    c.tags,
    c.schema_version,
    c.confidence_score,
    -- Extract key fields from canonical data
    c.canonical_data->>'document_type' AS document_type,
    c.canonical_data->'document_metadata'->>'title' AS title,
    c.canonical_data->'document_metadata'->>'date' AS document_date,
    -- Preview of searchable text (first 200 chars)
    LEFT(c.searchable_text, 200) AS text_preview,
    d.file_size_bytes,
    d.uploaded_by
FROM documents d
LEFT JOIN document_content c ON d.id = c.document_id
LEFT JOIN profiles p ON d.profile_id = p.id
WHERE d.status != 'archived';

COMMENT ON VIEW v_document_summary IS 'Denormalized view for quick document listing and search results';

-- ---------------------------------------------------------------------
-- v_ingestion_health: Health metrics for monitoring
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW v_ingestion_health AS
SELECT 
    DATE(ingestion_timestamp) AS date,
    file_type,
    COUNT(*) AS total_documents,
    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS successful,
    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed,
    AVG(processing_duration_ms) AS avg_duration_ms,
    AVG(file_size_bytes) AS avg_file_size_bytes
FROM documents
WHERE ingestion_timestamp >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(ingestion_timestamp), file_type
ORDER BY date DESC, file_type;

COMMENT ON VIEW v_ingestion_health IS 'Daily ingestion statistics for monitoring dashboard';

-- =====================================================================
-- FUNCTIONS AND TRIGGERS
-- =====================================================================

-- ---------------------------------------------------------------------
-- Function: Update updated_at timestamp automatically
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to relevant tables
CREATE TRIGGER documents_updated_at BEFORE UPDATE ON documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER document_content_updated_at BEFORE UPDATE ON document_content
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER profiles_updated_at BEFORE UPDATE ON profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ---------------------------------------------------------------------
-- Function: Update searchable_text from canonical_data
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION update_searchable_text()
RETURNS TRIGGER AS $$
BEGIN
    -- Extract all text values from canonical_data JSONB and concatenate
    NEW.searchable_text = (
        SELECT STRING_AGG(value::text, ' ')
        FROM jsonb_each_text(NEW.canonical_data)
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER document_content_searchable_text 
    BEFORE INSERT OR UPDATE OF canonical_data ON document_content
    FOR EACH ROW EXECUTE FUNCTION update_searchable_text();

-- ---------------------------------------------------------------------
-- Function: Log document status changes
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION log_status_change()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.status IS DISTINCT FROM NEW.status THEN
        INSERT INTO ingestion_logs (document_id, log_level, message, details, operation)
        VALUES (
            NEW.id,
            CASE 
                WHEN NEW.status = 'failed' THEN 'ERROR'
                WHEN NEW.status = 'completed' THEN 'INFO'
                ELSE 'WARNING'
            END,
            'Status changed from ' || COALESCE(OLD.status, 'NULL') || ' to ' || NEW.status,
            jsonb_build_object(
                'old_status', OLD.status,
                'new_status', NEW.status,
                'error_message', NEW.error_message
            ),
            'status_change'
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER documents_status_change AFTER UPDATE OF status ON documents
    FOR EACH ROW EXECUTE FUNCTION log_status_change();

-- =====================================================================
-- SAMPLE DATA / INITIAL PROFILES
-- =====================================================================

-- Insert a default "passthrough" profile for unknown formats
INSERT INTO profiles (profile_name, file_type, description, mapping_definition, is_active, is_default)
VALUES (
    'generic_xml_passthrough',
    'XML',
    'Generic XML profile that extracts all elements without specific mapping',
    '{
        "mode": "passthrough",
        "extract_all_elements": true,
        "preserve_structure": true
    }'::jsonb,
    true,
    false
) ON CONFLICT (profile_name) DO NOTHING;

-- =====================================================================
-- GRANTS (Adjust based on your user roles)
-- =====================================================================
-- Example: Grant all privileges to application user
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ra_d_ps_app;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO ra_d_ps_app;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO ra_d_ps_app;

-- =====================================================================
-- SCHEMA VERSION TRACKING
-- =====================================================================
CREATE TABLE IF NOT EXISTS schema_versions (
    version INTEGER PRIMARY KEY,
    description TEXT,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO schema_versions (version, description) 
VALUES (1, 'Initial schema for schema-agnostic data ingestion system');

-- =====================================================================
-- END OF MIGRATION
-- =====================================================================
