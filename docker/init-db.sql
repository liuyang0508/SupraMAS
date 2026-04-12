-- Wukong AI Platform - Database Initialization Script
-- PostgreSQL 15+ required

-- ===== 用户表 =====
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(100),
    avatar_url TEXT,
    role VARCHAR(20) DEFAULT 'user',
    organization_id UUID,
    permissions JSONB DEFAULT '[]'::jsonb,
    settings JSONB DEFAULT '{}'::jsonb,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_login_at TIMESTAMPTZ
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);

-- ===== 会话表 =====
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255),
    summary TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    is_archived BOOLEAN DEFAULT false
);
CREATE INDEX idx_sessions_user ON sessions(user_id, created_at DESC);

-- ===== 消息表 (对话历史) =====
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system', 'tool')),
    content TEXT NOT NULL,
    content_type VARCHAR(20) DEFAULT 'text',
    metadata JSONB DEFAULT '{}'::jsonb,
    token_count INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_messages_session_time ON messages(session_id, created_at);

-- ===== 技能注册表 =====
CREATE TABLE IF NOT EXISTS skills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    skill_id VARCHAR(200) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    version VARCHAR(20) NOT NULL,
    author_id UUID REFERENCES users(id),
    category VARCHAR(100),
    manifest JSONB NOT NULL,
    code_storage_path TEXT,
    status VARCHAR(20) DEFAULT 'draft',
    rating DECIMAL(2,1) DEFAULT 0,
    install_count INTEGER DEFAULT 0,
    is_builtin BOOLEAN DEFAULT false,
    auto_improve BOOLEAN DEFAULT false,
    security_scan_result JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ===== 已安装技能表 =====
CREATE TABLE IF NOT EXISTS installed_skills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    skill_id UUID NOT NULL REFERENCES skills(id),
    config JSONB DEFAULT '{}'::jsonb,
    install_status VARCHAR(20) DEFAULT 'installed',
    installed_at TIMESTAMPTZ DEFAULT NOW(),
    last_used_at TIMESTAMPTZ,
    UNIQUE(user_id, skill_id)
);

-- ===== 任务表 =====
CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    session_id UUID REFERENCES sessions(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    trigger_type VARCHAR(20) DEFAULT 'manual',
    schedule_cron VARCHAR(100),
    task_plan JSONB,
    status VARCHAR(20) DEFAULT 'pending',
    priority INTEGER DEFAULT 5,
    progress_percent INTEGER DEFAULT 0,
    result_summary TEXT,
    result_data JSONB,
    error_message TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_tasks_user_status ON tasks(user_id, status, created_at DESC);

-- ===== 子任务表 =====
CREATE TABLE IF NOT EXISTS subtasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    parent_task_id UUID REFERENCES subtasks(id),
    agent_type VARCHAR(100) NOT NULL,
    action VARCHAR(200) NOT NULL,
    params JSONB DEFAULT '{}'::jsonb,
    status VARCHAR(20) DEFAULT 'pending',
    retry_count INTEGER DEFAULT 0,
    result JSONB,
    error_message TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    duration_ms INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_subtasks_task_status ON subtasks(task_id, status);

-- ===== 审计日志表 (WORM - Write Once Read Many) =====
CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGSERIAL PRIMARY KEY,
    trace_id VARCHAR(64) NOT NULL,
    user_id UUID REFERENCES users(id),
    session_id UUID REFERENCES sessions(id),
    agent_id VARCHAR(100),
    action_type VARCHAR(100) NOT NULL,
    action_params JSONB,
    result_status VARCHAR(20),
    risk_level VARCHAR(20) DEFAULT 'low',
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT audit_immutable CHECK (created_at IS NOT NULL)
);
CREATE INDEX idx_audit_trace ON audit_logs(trace_id);
CREATE INDEX idx_audit_user_time ON audit_logs(user_id, created_at DESC);

-- ===== 文件版本表 (RealDoc风格) =====
CREATE TABLE IF NOT EXISTS file_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_id UUID NOT NULL,
    version_number INTEGER NOT NULL,
    storage_path TEXT NOT NULL,
    operation_type VARCHAR(50),
    operation_detail JSONB,
    checksum VARCHAR(128),
    size_bytes BIGINT,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(file_id, version_number)
);
CREATE INDEX idx_file_versions_file ON file_versions(file_id, version_number DESC);

-- ===== 向量集合映射表 =====
CREATE TABLE IF NOT EXISTS vector_collections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    collection_name VARCHAR(200) UNIQUE NOT NULL,
    owner_type VARCHAR(50),
    owner_id UUID,
    dimension INTEGER NOT NULL,
    index_type VARCHAR(50) DEFAULT 'IVF_FLAT',
    metric_type VARCHAR(20) DEFAULT 'COSINE',
    document_count INTEGER DEFAULT 0,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ===== 插入默认管理员用户 (密码: admin123) =====
INSERT INTO users (username, email, password_hash, display_name, role, is_active)
VALUES (
    'admin',
    'admin@wukong.ai',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOaZv9d0kWBvKlJlH9oG/0fD8yJ8pXe6',
    'Wukong Admin',
    'admin',
    true
) ON CONFLICT (email) DO NOTHING;

-- ===== 创建默认技能目录的SQL (供参考) =====
COMMENT ON TABLE skills IS '技能注册表 - 存储所有可用技能的元数据和代码';
COMMENT ON TABLE audit_logs IS '审计日志表 - WORM模式，记录所有操作用于安全合规';
COMMENT ON TABLE file_versions IS '文件版本表 - RealDoc风格的原子级版本管理';
