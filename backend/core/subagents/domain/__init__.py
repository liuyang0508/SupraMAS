"""
Domain Agents Package - 业务领域专家型子代理

架构说明：
═════════════════════════════════════════════════════════════
  Layer 1: Domain Agents (业务领域专家) ← 真正的"智能体"
  ────────────────────────────────────────────────────────
  • EcommerceDomainAgent   - 电商运营专家
  • DesignDomainAgent      - 设计创意专家  
  • FinanceDomainAgent     - 财税管理专家
  • DeveloperDomainAgent    - 软件开发专家      ★ NEW
  • ContentDomainAgent     - 内容创作专家      ★ NEW
  • CustomerServiceAgent  - 智能客服专家      ★ NEW
  
  特点：
  - 理解业务语义，做出专业决策
  - 由 Skill 组合驱动，能力可动态扩展
  - 调用 Infrastructure Agent 完成基础操作
  - 内置领域最佳实践工作流

═════════════════════════════════════════════════════════════
  Layer 2: Infrastructure Agents (基础设施/通用能力)
  ────────────────────────────────────────────────────────
  • RAGSubAgent           - 检索增强生成（知识问答）
  • SkillSubAgent         - 技能执行引擎（沙箱运行）
  • FileSubAgent          - 文件智能处理（RealDoc风格）
  • IntentSubAgent        - 意图识别（深度理解）★ NEW
  • MemorySubAgent        - 长期记忆（待实现）
  • MCPSubAgent           - 外部系统集成（待实现）

═════════════════════════════════════════════════════════════
"""

# ========== 基础类 ==========
from .base import (
    BaseDomainAgent,
    DomainCapability,
    DomainWorkflow,
    SkillBinding,
    DomainExecutionResult,
    DomainAgentFactory
)

# ========== 业务领域层 (6个Domain Agent) ==========
from .ecommerce import EcommerceDomainAgent
from .design import DesignDomainAgent
from .finance import FinanceDomainAgent
from .developer import DeveloperDomainAgent       # ★ NEW
from .content import ContentDomainAgent             # ★ NEW
from .customer_service import CustomerServiceDomainAgent # ★ NEW

__all__ = [
    # 基础类
    "BaseDomainAgent",
    "DomainCapability",
    "DomainWorkflow", 
    "SkillBinding",
    "DomainExecutionResult",
    "DomainAgentFactory",
    
    # Infrastructure Agents (从subagents包导入)
    
    # Domain Agents (业务专家) - 全部6个
    "EcommerceDomainAgent",      # 🛒 电商运营
    "DesignDomainAgent",         # 🎨 设计创意
    "FinanceDomainAgent",        # 💰 财税管理
    "DeveloperDomainAgent",     # 💻 软件开发
    "ContentDomainAgent",        # ✍️ 内容创作
    "CustomerServiceDomainAgent" # 🎧 智能客服
]

# ===== 领域注册表（供Supervisor使用）=====
ALL_DOMAINS = {
    "ecommerce": {
        "class": EcommerceDomainAgent,
        "display_name": "电商运营专家",
        "icon": "🛒",
        "color": "orange"
    },
    "design": {
        "class": DesignDomainAgent,
        "display_name": "设计创意专家",
        "icon": "🎨",
        "color": "pink"
    },
    "finance": {
        "class": FinanceDomainAgent,
        "display_name": "财税管理专家",
        "icon": "💰",
        "color": "green"
    },
    "development": {
        "class": DeveloperDomainAgent,
        "display_name": "软件开发专家",
        "icon": "💻",
        "color": "blue"
    },
    "content": {
        "class": ContentDomainAgent,
        "display_name": "内容创作专家",
        "icon": "✍️",
        "color": "purple"
    },
    "customer-service": {
        "class": CustomerServiceDomainAgent,
        "display_name": "智能客服专家",
        "icon": "🎧",
        "color": "yellow"
    }
}
