"""
Wukong AI Platform - Configuration Management
使用Pydantic Settings进行类型安全的配置管理
"""

from typing import List, Optional, Dict, Any
from pydantic_settings import BaseSettings
from pydantic import Field
import os


class DatabaseConfig(BaseSettings):
    """数据库配置"""
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "wukong"
    POSTGRES_PASSWORD: str = "wukong"
    POSTGRES_DB: str = "wukong"
    
    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    @property
    def sync_database_url(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"


class RedisConfig(BaseSettings):
    """Redis配置"""
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0
    
    @property
    def redis_url(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"


class MilvusConfig(BaseSettings):
    """Milvus向量数据库配置"""
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    MILVUS_INDEX_TYPE: str = "IVF_FLAT"
    MILVUS_METRIC_TYPE: str = "COSINE"
    MILVUS_DIMENSION: int = 1024  # BGE-large-zh维度


class MinIOConfig(BaseSettings):
    """MinIO对象存储配置"""
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "wukongadmin"
    MINIO_SECRET_KEY: str = "wukongadmin123"
    MINIO_BUCKET_NAME: str = "wukong-files"
    MINIO_SECURE: bool = False


class LLMConfig(BaseSettings):
    """LLM模型配置"""
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
    MAX_CONCURRENT_TASKS: int = 10
    TASK_TIMEOUT_SECONDS: float = 300.0
    MAX_SUBTASKS_PER_REQUEST: int = 20
    ENABLE_DYNAMIC_REPLANNING: bool = True
    ENABLE_CIRCUIT_BREAKER: bool = True
    CIRCUIT_BREAKER_THRESHOLD: int = 5  # 连续失败次数阈值
    TRACE_ENABLED: bool = True


class InputRouterConfig(BaseSettings):
    """Layer 1: Input Router配置"""
    INTENT_MODEL: str = "rule_based"  # rule_based, llm_based, hybrid
    INTENT_CONFIDENCE_THRESHOLD: float = 0.75
    ENABLE_SLOT_EXTRACTION: bool = True
    SUPPORTED_LANGUAGES: List[str] = ["zh", "en", "zh-en"]


class QueryOptimizerConfig(BaseSettings):
    """Layer 2: Query Optimizer配置"""
    REWRITE_MODEL: str = "t5_base"  # t5_base, llm_based
    CONTEXT_WINDOW_SIZE: int = 20  # 最近N轮对话
    ENABLE_QUERY_EXPANSION: bool = True
    EXPANSION_TERMS_COUNT: int = 5
    CACHE_REWRITE_RESULTS: bool = True
    CACHE_TTL_SECONDS: int = 3600


class TaskPlannerConfig(BaseSettings):
    """Layer 3: Task Planner配置"""
    PLANNING_MODEL: str = "gpt-4"  # 用于任务分解的模型
    MAX_TASK_DEPTH: int = 3  # 任务分解最大深度
    ESTIMATE_EXECUTION_TIME: bool = True
    PARALLELISM_THRESHOLD: float = 0.8  # 并行度阈值


class DispatcherConfig(BaseSettings):
    """Layer 4: Execution Dispatcher配置"""
    SCHEDULING_STRATEGY: str = "intelligent"  # round_robin, load_balanced, intelligent
    ENABLE_PARALLEL_EXECUTION: bool = True
    MAX_PARALLEL_SUBTASKS: int = 5
    RETRY_MAX_ATTEMPTS: int = 3
    RETRY_BACKOFF_BASE: float = 1.0  # 指数退避基数(秒)
    PROGRESS_REPORT_INTERVAL: float = 1.0  # 进度上报间隔(秒)


class SecurityConfig(BaseSettings):
    """Layer 5: Security Guard配置"""
    JWT_SECRET_KEY: str = "your-super-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    
    ENABLE_PERMISSION_INTERSECTION: bool = True  # 权限交集检查
    ENABLE_DATA_SANITIZATION: bool = True
    ENABLE_AUDIT_LOGGING: bool = True
    AUDIT_LOG_RETENTION_DAYS: int = 90
    
    RATE_LIMIT_PER_MINUTE: int = 60
    ENABLE_THREAT_DETECTION: bool = True
    
    SENSITIVE_PATTERNS: List[str] = [
        r"\d{15,19}",  # 身份证/银行卡号
        r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",  # 邮箱
        r"1[3-9]\d{9}",  # 手机号
        r"(?:sk-|api[_-]?key)[a-zA-Z0-9_-]{20,}",  # API Key
    ]


class SkillConfig(BaseSettings):
    """技能系统配置"""
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
    ENABLED_MCP_SERVERS: List[str] = ["filesystem", "postgres"]
    MCP_SERVER_CONFIGS: Dict[str, Any] = {}


class AppConfig(BaseSettings):
    """应用总配置 - 聚合所有子配置"""
    
    APP_NAME: str = "Wukong AI Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"  # development, staging, production
    
    API_PREFIX: str = "/api/v1"
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    LOG_LEVEL: str = "DEBUG"
    
    # 子配置
    database: DatabaseConfig = DatabaseConfig()
    redis: RedisConfig = RedisConfig()
    milvus: MilvusConfig = MilvusConfig()
    minio: MinIOConfig = MinIOConfig()
    llm: LLMConfig = LLMConfig()
    supervisor: SupervisorConfig = SupervisorConfig()
    input_router: InputRouterConfig = InputRouterConfig()
    query_optimizer: QueryOptimizerConfig = QueryOptimizerConfig()
    task_planner: TaskPlannerConfig = TaskPlannerConfig()
    dispatcher: DispatcherConfig = DispatcherConfig()
    security: SecurityConfig = SecurityConfig()
    skill: SkillConfig = SkillConfig()
    mcp: MCPConfig = MCPConfig()
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


def get_config() -> AppConfig:
    """获取应用配置单例"""
    return AppConfig()


config = get_config()
