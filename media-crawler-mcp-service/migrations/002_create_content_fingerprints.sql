-- 内容指纹表
CREATE TABLE IF NOT EXISTS content_fingerprints (
    id SERIAL PRIMARY KEY,
    note_id VARCHAR(255) UNIQUE NOT NULL,
    title VARCHAR(500),
    content_hash VARCHAR(64) NOT NULL,
    title_hash VARCHAR(64) NOT NULL,
    combined_hash VARCHAR(64) NOT NULL,
    title_preview VARCHAR(200),
    content_preview TEXT,
    source VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_duplicate BOOLEAN DEFAULT FALSE,
    duplicate_type VARCHAR(50),
    similar_to JSONB
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_content_fingerprints_note_id ON content_fingerprints(note_id);
CREATE INDEX IF NOT EXISTS idx_content_fingerprints_content_hash ON content_fingerprints(content_hash);
CREATE INDEX IF NOT EXISTS idx_content_fingerprints_combined_hash ON content_fingerprints(combined_hash);
CREATE INDEX IF NOT EXISTS idx_content_fingerprints_created_at ON content_fingerprints(created_at);
CREATE INDEX IF NOT EXISTS idx_content_fingerprints_source ON content_fingerprints(source);
CREATE INDEX IF NOT EXISTS idx_content_fingerprints_is_duplicate ON content_fingerprints(is_duplicate) WHERE is_duplicate = TRUE;
