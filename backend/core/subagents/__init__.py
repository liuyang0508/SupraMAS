"""
SubAgents Package - 专业子代理集合

架构分层说明：
═══════════════════════════════════════════════════════════
  Layer 1: Domain Agents (业务领域专家) ← 真正的"智能体"
  ────────────────────────────────────────────────────────
  • EcommerceDomainAgent       - 电商运营专家
  • DesignDomainAgent          - 设计创意专家  
  • FinanceDomainAgent         - 财税管理专家
  • DeveloperDomainAgent       - 开发者专家
  • ContentDomainAgent         - 内容创作专家
  • CustomerServiceDomainAgent - 客服专家
  
  特点：
  - 理解业务语义，做出专业决策
  - 由 Skill 组合驱动，能力可动态扩展
  - 调用 Infrastructure Agent 完成基础操作
  - 内置领域最佳实践工作流

═══════════════════════════════════════════════════════════
  Layer 2: Infrastructure Agents (基础设施/通用能力)
  ────────────────────────────────────────────────────────
  • RAGSubAgent           - 检索增强生成（知识问答）
  • SkillSubAgent         - 技能执行引擎（沙箱运行）
  • FileSubAgent          - 文件智能处理（RealDoc风格）
  • IntentSubAgent        - 意图识别 (三层: 规则→语义→LLM)
  • MemorySubAgent        - 长期记忆（待实现）
  
  特点：
  - 提供通用的技术能力
  - 被 Domain Agent 调用
  - 无业务语义，纯技术实现

═══════════════════════════════════════════════════════════
  Layer 3: External Integration (外部系统集成)
  ────────────────────────────────────────────────────────
  • MCPClient              - 统一MCP客户端
  • FileSystemMCPServer    - 文件系统MCP服务器
  • DatabaseMCPServer      - 数据库MCP服务器
  • SearchMCPServer        - 搜索MCP服务器
  
  通过 Model Context Protocol 连接外部数据源和工具
"""

# ========== 基础设施层 (Infrastructure Agents) ==========
from .base import BaseSubAgent, AgentCapability, AgentExecutionContext, AgentExecutionResult
from .rag.agent import RAGSubAgent
from .skill.agent import SkillSubAgent
from .file.agent import FileSubAgent
from .intent.agent import IntentSubAgent

# ========== 业务领域层 (Domain Agents) ==========
from .domain.base import (
    BaseDomainAgent,
    DomainCapability,
    DomainWorkflow,
    SkillBinding,
    DomainExecutionResult,
    DomainAgentFactory
)
from .domain.ecommerce import EcommerceDomainAgent
from .domain.design import DesignDomainAgent
from .domain.finance import FinanceDomainAgent
from .domain.developer import DeveloperDomainAgent
from .domain.content import ContentDomainAgent
from .domain.customer_service import CustomerServiceDomainAgent

__all__ = [
    # 基础类
    "BaseSubAgent",
    "BaseDomainAgent", 
    "AgentCapability",
    "DomainCapability",
    "AgentExecutionContext",
    "AgentExecutionResult",
    
    # Infrastructure Agents
    "RAGSubAgent",
    "SkillSubAgent", 
    "FileSubAgent",
    "IntentSubAgent",
    
    # Domain 相关
    "DomainWorkflow",
    "SkillBinding",
    "DomainExecutionResult",
    "DomainAgentFactory",
    
    # Domain Agents (业务专家) - 共6个领域
    "EcommerceDomainAgent",
    "DesignDomainAgent",
    "FinanceDomainAgent",
    "DeveloperDomainAgent",
    "ContentDomainAgent",
    "CustomerServiceDomainAgent"
]
