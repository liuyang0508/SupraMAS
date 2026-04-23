"""
Wukong AI Platform - Configuration Management
使用Pydantic Settings进行类型安全的配置管理
"""

import os
from typing import List, Optional, Dict, Any
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, ConfigDict

# 加载 .env 文件
from dotenv import load_dotenv
_dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(_dotenv_path)


class DatabaseConfig(BaseSettings):
    """数据库配置"""
    model_config = SettingsConfigDict(env_prefix='POSTGRES_', extra='ignore')

    HOST: str = "localhost"
    PORT: int = 5432
    USER: str = "wukong"
    PASSWORD: str = "wukong"
    DB: str = "wukong"

    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.USER}:{self.PASSWORD}@{self.HOST}:{self.PORT}/{self.DB}"

    @property
    def sync_database_url(self) -> str:
        return f"postgresql://{self.USER}:{self.PASSWORD}@{self.HOST}:{self.PORT}/{self.DB}"


class RedisConfig(BaseSettings):
    """Redis配置"""
    model_config = SettingsConfigDict(env_prefix='REDIS_', extra='ignore')

    HOST: str = "localhost"
    PORT: int = 6379
    PASSWORD: Optional[str] = None
    DB: int = 0

    @property
    def redis_url(self) -> str:
        if self.PASSWORD:
            return f"redis://:{self.PASSWORD}@{self.HOST}:{self.PORT}/{self.DB}"
        return f"redis://{self.HOST}:{self.PORT}/{self.DB}"


class MilvusConfig(BaseSettings):
    """Milvus向量数据库配置"""
    model_config = SettingsConfigDict(env_prefix='MILVUS_', extra='ignore')

    HOST: str = "localhost"
    PORT: int = 19530
    INDEX_TYPE: str = "IVF_FLAT"
    METRIC_TYPE: str = "COSINE"
    DIMENSION: int = 1024  # BGE-large-zh维度


class MinIOConfig(BaseSettings):
    """MinIO对象存储配置"""
    model_config = SettingsConfigDict(env_prefix='MINIO_', extra='ignore')

    ENDPOINT: str = "localhost:9000"
    ACCESS_KEY: str = "wukongadmin"
    SECRET_KEY: str = "wukongadmin123"
    BUCKET_NAME: str = "wukong-files"
    SECURE: bool = False


class LLMConfig(BaseSettings):
    """LLM模型配置"""
    model_config = SettingsConfigDict(env_prefix='', extra='ignore')

    LLM_PROVIDER: str = "openai"  # openai, anthropic, vllm, custom
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4-turbo-preview"

    EMBEDDING_MODEL: str = "BAAI/bge-large-zh-v1.5"
    EMBEDDING_DEVICE: str = "cpu"  # cpu, cuda, mps

    VLLM_BASE_URL: Optional[str] = None  # 本地vLLM服务地址

    MAX_TOKENS: int = 4096
    TEMPERATURE: float = 0.7
    STREAMING: bool = True


class SupervisorConfig(BaseSettings):
    """Supervisor中央调度器配置"""
    model_config = SettingsConfigDict(env_prefix='', extra='ignore')

    MAX_CONCURRENT_TASKS: int = 10
    TASK_TIMEOUT_SECONDS: float = 300.0
    MAX_SUBTASKS_PER_REQUEST: int = 20
    ENABLE_DYNAMIC_REPLANNING: bool = True
    ENABLE_CIRCUIT_BREAKER: bool = True
    CIRCUIT_BREAKER_THRESHOLD: int = 5
    TRACE_ENABLED: bool = True


class InputRouterConfig(BaseSettings):
    """Layer 1: Input Router配置"""
    model_config = SettingsConfigDict(env_prefix='', extra='ignore')

    INTENT_MODEL: str = "rule_based"
    INTENT_CONFIDENCE_THRESHOLD: float = 0.75
    ENABLE_SLOT_EXTRACTION: bool = True
    SUPPORTED_LANGUAGES: List[str] = ["zh", "en", "zh-en"]


class QueryOptimizerConfig(BaseSettings):
    """Layer 2: Query Optimizer配置"""
    model_config = SettingsConfigDict(env_prefix='', extra='ignore')

    REWRITE_MODEL: str = "t5_base"
    CONTEXT_WINDOW_SIZE: int = 20
    ENABLE_QUERY_EXPANSION: bool = True
    EXPANSION_TERMS_COUNT: int = 5
    CACHE_REWRITE_RESULTS: bool = True
    CACHE_TTL_SECONDS: int = 3600


class TaskPlannerConfig(BaseSettings):
    """Layer 3: Task Planner配置"""
    model_config = SettingsConfigDict(env_prefix='', extra='ignore')

    PLANNING_MODEL: str = "gpt-4"
    MAX_TASK_DEPTH: int = 3
    ESTIMATE_EXECUTION_TIME: bool = True
    PARALLELISM_THRESHOLD: float = 0.8


class DispatcherConfig(BaseSettings):
    """Layer 4: Execution Dispatcher配置"""
    model_config = SettingsConfigDict(env_prefix='', extra='ignore')

    SCHEDULING_STRATEGY: str = "intelligent"
    ENABLE_PARALLEL_EXECUTION: bool = True
    MAX_PARALLEL_SUBTASKS: int = 5
    RETRY_MAX_ATTEMPTS: int = 3
    RETRY_BACKOFF_BASE: float = 1.0
    PROGRESS_REPORT_INTERVAL: float = 1.0


class SecurityConfig(BaseSettings):
    """Layer 5: Security Guard配置"""
    model_config = SettingsConfigDict(env_prefix='', extra='ignore')

    JWT_SECRET_KEY: str = "your-super-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24

    ENABLE_PERMISSION_INTERSECTION: bool = True
    ENABLE_DATA_SANITIZATION: bool = True
    ENABLE_AUDIT_LOGGING: bool = True
    AUDIT_LOG_RETENTION_DAYS: int = 90

    RATE_LIMIT_PER_MINUTE: int = 60
    ENABLE_THREAT_DETECTION: bool = True

    SENSITIVE_PATTERNS: List[str] = [
        r"\d{15,19}",
        r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        r"1[3-9]\d{9}",
        r"(?:sk-|api[_-]?key)[a-zA-Z0-9_-]{20,}",
    ]


class SkillConfig(BaseSettings):
    """技能系统配置"""
    model_config = SettingsConfigDict(env_prefix='', extra='ignore')

    SKILL_STORAGE_PATH: str = "./data/skills"
    DOCKER_NETWORK: str = "wukong-skill-net"
    DEFAULT_SKILL_IMAGE: str = "python:3.11-slim"
    SKILL_TIMEOUT_SECONDS: float = 300.0
    SKILL_MEMORY_LIMIT_MB: int = 512
    SKILL_CPU_LIMIT: float = 1.0
    ENABLE_AUTO_IMPROVE: bool = False
    SECURITY_SCAN_ON_UPLOAD: bool = True


class MCPConfig(BaseSettings):
    """MCP集成配置"""
    model_config = SettingsConfigDict(env_prefix='', extra='ignore')

    ENABLED_MCP_SERVERS: List[str] = ["filesystem", "postgres"]
    MCP_SERVER_CONFIGS: Dict[str, Any] = {}


class AppConfig(BaseSettings):
    """应用总配置 - 聚合所有子配置"""
    model_config = SettingsConfigDict(
        env_file="/Users/liuyang/Desktop/AIAgent/wukongbox/wukong/backend/.env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    APP_NAME: str = "Wukong AI Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"

    API_PREFIX: str = "/api/v1"
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    LOG_LEVEL: str = "DEBUG"

    # 子配置
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    milvus: MilvusConfig = Field(default_factory=MilvusConfig)
    minio: MinIOConfig = Field(default_factory=MinIOConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    supervisor: SupervisorConfig = Field(default_factory=SupervisorConfig)
    input_router: InputRouterConfig = Field(default_factory=InputRouterConfig)
    query_optimizer: QueryOptimizerConfig = Field(default_factory=QueryOptimizerConfig)
    task_planner: TaskPlannerConfig = Field(default_factory=TaskPlannerConfig)
    dispatcher: DispatcherConfig = Field(default_factory=DispatcherConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    skill: SkillConfig = Field(default_factory=SkillConfig)
    mcp: MCPConfig = Field(default_factory=MCPConfig)


def get_config() -> AppConfig:
    """获取应用配置单例"""
    return AppConfig()


config = get_config()
