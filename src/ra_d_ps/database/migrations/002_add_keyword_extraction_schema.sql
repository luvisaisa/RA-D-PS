-- Migration: Add Keyword Extraction Schema
-- Date: 2025-10-19
-- Description: Create tables for keyword extraction, normalization, and search

-- =============================================================================
-- KEYWORDS TABLE
-- =============================================================================
CREATE TABLE IF NOT EXISTS keywords (
    keyword_id SERIAL PRIMARY KEY,
    keyword_text VARCHAR(255) NOT NULL UNIQUE,
    normalized_form VARCHAR(255),
    category VARCHAR(100),  -- 'anatomy', 'characteristic', 'diagnosis', 'metadata', 'research'
    description TEXT,  -- optional description or definition
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for fast keyword lookup
CREATE INDEX IF NOT EXISTS idx_keywords_text ON keywords(keyword_text);
CREATE INDEX IF NOT EXISTS idx_keywords_normalized ON keywords(normalized_form);
CREATE INDEX IF NOT EXISTS idx_keywords_category ON keywords(category);

-- =============================================================================
-- KEYWORD SOURCES TABLE  
-- =============================================================================
CREATE TABLE IF NOT EXISTS keyword_sources (
    source_id SERIAL PRIMARY KEY,
    keyword_id INTEGER NOT NULL REFERENCES keywords(keyword_id) ON DELETE CASCADE,
    source_type VARCHAR(50) NOT NULL,  -- 'xml', 'pdf', 'research_paper', 'annotation'
    source_file VARCHAR(500) NOT NULL,  -- file path or identifier
    sector VARCHAR(100),  -- 'lidc_annotations', 'research_papers', 'metadata'
    frequency INTEGER DEFAULT 1,  -- count in this document
    tf_idf_score FLOAT DEFAULT 0.0,  -- term frequency-inverse document frequency
    context TEXT,  -- surrounding text for snippet (max 500 chars)
    page_number INTEGER,  -- for PDFs and multi-page documents
    position_start INTEGER,  -- character position in source (for highlighting)
    position_end INTEGER,  -- character position end
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Unique constraint: one keyword per source file
    UNIQUE(keyword_id, source_type, source_file, page_number)
);

-- Indexes for fast source lookup
CREATE INDEX IF NOT EXISTS idx_keyword_sources_keyword ON keyword_sources(keyword_id);
CREATE INDEX IF NOT EXISTS idx_keyword_sources_file ON keyword_sources(source_file);
CREATE INDEX IF NOT EXISTS idx_keyword_sources_sector ON keyword_sources(sector);
CREATE INDEX IF NOT EXISTS idx_keyword_sources_type ON keyword_sources(source_type);
CREATE INDEX IF NOT EXISTS idx_keyword_sources_tfidf ON keyword_sources(tf_idf_score DESC);

-- =============================================================================
-- KEYWORD STATISTICS TABLE
-- =============================================================================
CREATE TABLE IF NOT EXISTS keyword_statistics (
    keyword_id INTEGER PRIMARY KEY REFERENCES keywords(keyword_id) ON DELETE CASCADE,
    total_frequency INTEGER DEFAULT 0,  -- total occurrences across all documents
    document_count INTEGER DEFAULT 0,  -- number of documents containing keyword
    idf_score FLOAT DEFAULT 0.0,  -- inverse document frequency (cached)
    avg_tf_idf FLOAT DEFAULT 0.0,  -- average TF-IDF across documents
    last_calculated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for ranking queries
CREATE INDEX IF NOT EXISTS idx_keyword_statistics_freq ON keyword_statistics(total_frequency DESC);
CREATE INDEX IF NOT EXISTS idx_keyword_statistics_idf ON keyword_statistics(idf_score DESC);
CREATE INDEX IF NOT EXISTS idx_keyword_statistics_doc_count ON keyword_statistics(document_count DESC);

-- =============================================================================
-- KEYWORD SYNONYMS TABLE
-- =============================================================================
CREATE TABLE IF NOT EXISTS keyword_synonyms (
    synonym_id SERIAL PRIMARY KEY,
    synonym_text VARCHAR(255) NOT NULL,
    canonical_keyword_id INTEGER NOT NULL REFERENCES keywords(keyword_id) ON DELETE CASCADE,
    synonym_type VARCHAR(50),  -- 'abbreviation', 'medical_term', 'alternate_spelling', 'acronym'
    confidence_score FLOAT DEFAULT 1.0,  -- how confident we are in this synonym mapping (0-1)
    source VARCHAR(100),  -- 'umls', 'manual', 'auto_detected'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Unique constraint: each synonym text maps to one canonical form
    UNIQUE(synonym_text, canonical_keyword_id)
);

-- Indexes for synonym lookup
CREATE INDEX IF NOT EXISTS idx_keyword_synonyms_text ON keyword_synonyms(synonym_text);
CREATE INDEX IF NOT EXISTS idx_keyword_synonyms_canonical ON keyword_synonyms(canonical_keyword_id);
CREATE INDEX IF NOT EXISTS idx_keyword_synonyms_type ON keyword_synonyms(synonym_type);

-- =============================================================================
-- KEYWORD CO-OCCURRENCE TABLE (for semantic relationships)
-- =============================================================================
CREATE TABLE IF NOT EXISTS keyword_cooccurrence (
    cooccurrence_id SERIAL PRIMARY KEY,
    keyword_id_1 INTEGER NOT NULL REFERENCES keywords(keyword_id) ON DELETE CASCADE,
    keyword_id_2 INTEGER NOT NULL REFERENCES keywords(keyword_id) ON DELETE CASCADE,
    cooccurrence_count INTEGER DEFAULT 1,  -- how many times they appear together
    correlation_score FLOAT DEFAULT 0.0,  -- statistical correlation (0-1)
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Ensure keyword_id_1 < keyword_id_2 to avoid duplicates
    CHECK (keyword_id_1 < keyword_id_2),
    UNIQUE(keyword_id_1, keyword_id_2)
);

-- Indexes for co-occurrence queries
CREATE INDEX IF NOT EXISTS idx_keyword_cooccurrence_kw1 ON keyword_cooccurrence(keyword_id_1);
CREATE INDEX IF NOT EXISTS idx_keyword_cooccurrence_kw2 ON keyword_cooccurrence(keyword_id_2);
CREATE INDEX IF NOT EXISTS idx_keyword_cooccurrence_count ON keyword_cooccurrence(cooccurrence_count DESC);

-- =============================================================================
-- SEARCH HISTORY TABLE (analytics)
-- =============================================================================
CREATE TABLE IF NOT EXISTS keyword_search_history (
    search_id SERIAL PRIMARY KEY,
    query_text TEXT NOT NULL,
    result_count INTEGER DEFAULT 0,
    execution_time_ms FLOAT,  -- query execution time in milliseconds
    user_sector VARCHAR(100),  -- which sector was searched
    search_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for analytics
CREATE INDEX IF NOT EXISTS idx_search_history_timestamp ON keyword_search_history(search_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_search_history_query ON keyword_search_history(query_text);

-- =============================================================================
-- TRIGGERS FOR AUTOMATIC STATISTICS UPDATES
-- =============================================================================

-- Trigger: Update keyword statistics when a new source is added
CREATE OR REPLACE FUNCTION update_keyword_statistics()
RETURNS TRIGGER AS $$
BEGIN
    -- Update or insert statistics
    INSERT INTO keyword_statistics (
        keyword_id,
        total_frequency,
        document_count,
        last_updated
    )
    VALUES (
        NEW.keyword_id,
        NEW.frequency,
        1,
        CURRENT_TIMESTAMP
    )
    ON CONFLICT (keyword_id) DO UPDATE SET
        total_frequency = keyword_statistics.total_frequency + NEW.frequency,
        document_count = keyword_statistics.document_count + 1,
        last_updated = CURRENT_TIMESTAMP;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_keyword_statistics
AFTER INSERT ON keyword_sources
FOR EACH ROW
EXECUTE FUNCTION update_keyword_statistics();

-- Trigger: Update timestamp on keywords table
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_keywords_updated_at
BEFORE UPDATE ON keywords
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- VIEWS FOR COMMON QUERIES
-- =============================================================================

-- View: Top keywords by frequency
CREATE OR REPLACE VIEW v_top_keywords AS
SELECT 
    k.keyword_id,
    k.keyword_text,
    k.normalized_form,
    k.category,
    ks.total_frequency,
    ks.document_count,
    ks.idf_score,
    ks.avg_tf_idf
FROM keywords k
INNER JOIN keyword_statistics ks ON k.keyword_id = ks.keyword_id
ORDER BY ks.total_frequency DESC;

-- View: Keywords with all their synonyms
CREATE OR REPLACE VIEW v_keywords_with_synonyms AS
SELECT 
    k.keyword_id,
    k.keyword_text AS canonical_form,
    k.category,
    array_agg(DISTINCT s.synonym_text) FILTER (WHERE s.synonym_text IS NOT NULL) AS synonyms,
    count(DISTINCT s.synonym_id) AS synonym_count
FROM keywords k
LEFT JOIN keyword_synonyms s ON k.keyword_id = s.canonical_keyword_id
GROUP BY k.keyword_id, k.keyword_text, k.category;

-- View: Keyword sources with context
CREATE OR REPLACE VIEW v_keyword_sources_detail AS
SELECT 
    ks.source_id,
    k.keyword_text,
    k.category,
    ks.source_type,
    ks.source_file,
    ks.sector,
    ks.frequency,
    ks.tf_idf_score,
    ks.context,
    ks.page_number,
    ks.created_at
FROM keyword_sources ks
INNER JOIN keywords k ON ks.keyword_id = k.keyword_id;

-- =============================================================================
-- UTILITY FUNCTIONS
-- =============================================================================

-- Function: Calculate IDF score for a keyword
CREATE OR REPLACE FUNCTION calculate_idf_score(p_keyword_id INTEGER)
RETURNS FLOAT AS $$
DECLARE
    v_document_count INTEGER;
    v_total_documents INTEGER;
    v_idf FLOAT;
BEGIN
    -- Get document count for this keyword
    SELECT document_count INTO v_document_count
    FROM keyword_statistics
    WHERE keyword_id = p_keyword_id;
    
    -- Get total documents
    SELECT COUNT(DISTINCT source_file) INTO v_total_documents
    FROM keyword_sources;
    
    -- Calculate IDF: log(N / (1 + df))
    IF v_document_count > 0 AND v_total_documents > 0 THEN
        v_idf := LN(v_total_documents::FLOAT / (1 + v_document_count::FLOAT));
    ELSE
        v_idf := 0.0;
    END IF;
    
    -- Update statistics table
    UPDATE keyword_statistics
    SET idf_score = v_idf,
        last_calculated = CURRENT_TIMESTAMP
    WHERE keyword_id = p_keyword_id;
    
    RETURN v_idf;
END;
$$ LANGUAGE plpgsql;

-- Function: Calculate TF-IDF for all keywords in a document
CREATE OR REPLACE FUNCTION calculate_document_tfidf(p_source_file VARCHAR)
RETURNS VOID AS $$
DECLARE
    v_record RECORD;
    v_idf FLOAT;
    v_tf_idf FLOAT;
BEGIN
    -- For each keyword in this document
    FOR v_record IN 
        SELECT ks.source_id, ks.keyword_id, ks.frequency, stat.idf_score
        FROM keyword_sources ks
        INNER JOIN keyword_statistics stat ON ks.keyword_id = stat.keyword_id
        WHERE ks.source_file = p_source_file
    LOOP
        -- Calculate TF-IDF: frequency * idf_score
        v_tf_idf := v_record.frequency * v_record.idf_score;
        
        -- Update source with TF-IDF score
        UPDATE keyword_sources
        SET tf_idf_score = v_tf_idf
        WHERE source_id = v_record.source_id;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Function: Search keywords with synonym expansion
CREATE OR REPLACE FUNCTION search_keywords_with_synonyms(p_query TEXT)
RETURNS TABLE (
    keyword_id INTEGER,
    keyword_text VARCHAR,
    normalized_form VARCHAR,
    category VARCHAR,
    match_type VARCHAR,  -- 'exact', 'synonym', 'normalized'
    relevance_score FLOAT
) AS $$
BEGIN
    RETURN QUERY
    -- Exact matches
    SELECT 
        k.keyword_id,
        k.keyword_text,
        k.normalized_form,
        k.category,
        'exact'::VARCHAR AS match_type,
        1.0 AS relevance_score
    FROM keywords k
    WHERE k.keyword_text ILIKE '%' || p_query || '%'
    
    UNION
    
    -- Synonym matches
    SELECT 
        k.keyword_id,
        k.keyword_text,
        k.normalized_form,
        k.category,
        'synonym'::VARCHAR AS match_type,
        0.9 AS relevance_score
    FROM keywords k
    INNER JOIN keyword_synonyms s ON k.keyword_id = s.canonical_keyword_id
    WHERE s.synonym_text ILIKE '%' || p_query || '%'
    
    UNION
    
    -- Normalized form matches
    SELECT 
        k.keyword_id,
        k.keyword_text,
        k.normalized_form,
        k.category,
        'normalized'::VARCHAR AS match_type,
        0.8 AS relevance_score
    FROM keywords k
    WHERE k.normalized_form ILIKE '%' || p_query || '%'
    
    ORDER BY relevance_score DESC, keyword_text;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- COMMENTS FOR DOCUMENTATION
-- =============================================================================

COMMENT ON TABLE keywords IS 'Core keyword table storing unique keywords extracted from all sources';
COMMENT ON TABLE keyword_sources IS 'Links keywords to their source documents with context and TF-IDF scores';
COMMENT ON TABLE keyword_statistics IS 'Cached statistics for keyword frequency and IDF calculations';
COMMENT ON TABLE keyword_synonyms IS 'Maps synonyms and alternate forms to canonical keyword forms';
COMMENT ON TABLE keyword_cooccurrence IS 'Tracks which keywords appear together for semantic analysis';
COMMENT ON TABLE keyword_search_history IS 'Analytics table for tracking search queries and performance';

COMMENT ON COLUMN keywords.normalized_form IS 'Canonical/normalized version of keyword (e.g., "lung" -> "pulmonary")';
COMMENT ON COLUMN keyword_sources.tf_idf_score IS 'Term Frequency-Inverse Document Frequency score for ranking relevance';
COMMENT ON COLUMN keyword_statistics.idf_score IS 'Inverse Document Frequency: log(N / (1 + df)) where N=total docs, df=doc count';
COMMENT ON COLUMN keyword_synonyms.confidence_score IS 'Confidence in synonym mapping (0-1), useful for auto-detected synonyms';

-- =============================================================================
-- MIGRATION COMPLETE
-- =============================================================================

-- Verify tables created
SELECT 
    tablename, 
    schemaname 
FROM pg_tables 
WHERE schemaname = 'public' 
    AND tablename LIKE 'keyword%'
ORDER BY tablename;

-- Show indexes
SELECT 
    indexname, 
    tablename 
FROM pg_indexes 
WHERE schemaname = 'public' 
    AND tablename LIKE 'keyword%'
ORDER BY tablename, indexname;
