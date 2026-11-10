-- DeepShield PostgreSQL Schema
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'analyst', -- admin, analyst, viewer
    organization VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    key_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    last_used TIMESTAMP
);

CREATE TABLE media_files (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    filename VARCHAR(500),
    file_type VARCHAR(20), -- image, video, audio
    storage_path VARCHAR(1000),
    file_hash VARCHAR(64),
    uploaded_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE detections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    media_id UUID REFERENCES media_files(id),
    user_id UUID REFERENCES users(id),
    model_version VARCHAR(50),
    label VARCHAR(10), -- REAL / FAKE
    confidence FLOAT,
    processing_time_ms INTEGER,
    heatmap_path VARCHAR(1000),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    action VARCHAR(100),
    resource_type VARCHAR(50),
    resource_id UUID,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization VARCHAR(255),
    plan VARCHAR(50), -- government, enterprise, media
    quota_monthly INTEGER,
    used_this_month INTEGER DEFAULT 0,
    expires_at TIMESTAMP
);

CREATE INDEX idx_detections_user ON detections(user_id);
CREATE INDEX idx_detections_created ON detections(created_at);
