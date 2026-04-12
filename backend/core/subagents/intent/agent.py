"""
Intent SubAgent - 意图识别与槽位提取Agent

核心能力：
- 深度意图分类（支持多层级意图体系）
- 精准槽位提取（实体识别 + 语义理解）
- Domain路由决策（将用户导向正确的业务领域专家）
- 歧义检测与澄清建议
- 多轮对话上下文融合

架构定位：Infrastructure Agent (被Supervisor Layer1调用)
"""

import re
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from ..base import (
    BaseSubAgent,
    AgentCapability,
    AgentExecutionContext,
    AgentExecutionResult,
    AgentHealthCheckResult,
    AgentHealthStatus
)

logger = logging.getLogger(__name__)


class IntentCategory(str, Enum):
    """意图类别枚举 - 支持多层级分类"""
    
    # ===== 核心意图 =====
    CHAT = "chat"
    TASK_EXECUTION = "task_execution"
    QUESTION_ANSWERING = "question_answering"
    
    # ===== 业务领域意图 =====
    ECOMMERCE = "ecommerce_operation"
    DESIGN = "design_work"
    FINANCE = "finance_management"
    DEVELOPMENT = "software_development"
    CONTENT_CREATION = "content_creation"
    CUSTOMER_SERVICE = "customer_service"
    DATA_ANALYSIS = "data_analysis"
    
    # ===== 系统操作意图 =====
    FILE_OPERATION = "file_operation"
    SKILL_MANAGEMENT = "skill_management"
    SYSTEM_CONFIG = "system_config"
    
    # ===== 元意图 =====
    CLARIFICATION = "clarification"
    CORRECTION = "correction"
    CANCEL = "cancel"


@dataclass
class IntentResult:
    """意图识别结果"""
    intent: IntentCategory
    confidence: float
    target_domain: Optional[str] = None       # 目标Domain Agent
    target_agent_type: Optional[str] = None   # 目标Infra Agent
    slots: Dict[str, Any] = field(default_factory=dict)
    alternative_intents: List[Dict] = field(default_factory=list)
    reasoning: str = ""
    needs_clarification: bool = False
    clarification_question: Optional[str] = None
    ambiguity_score: float = 0.0


@dataclass
class SlotDefinition:
    """槽位定义"""
    name: str
    description: str
    data_type: str  # string, number, date, enum, list
    required: bool = False
    examples: List[str] = field(default_factory=list)
    extraction_patterns: List[str] = field(default_factory=list)
    validation_rules: Dict[str, Any] = field(default_factory=dict)


class IntentSubAgent(BaseSubAgent):
    """
    意图识别与路由Agent
    
    核心价值：
    1. 将自然语言转化为结构化的意图+槽位
    2. 智能判断应该由哪个Domain Agent处理
    3. 处理歧义和模糊请求
    
    分层策略：
    - L1: 规则快速匹配（关键词/正则）→ 高置信度直接返回
    - L2: 语义相似度匹配 → 中等置信度
    - L3: LLM深度推理 → 低置信度或复杂场景兜底
    """
    
    # ===== 领域关键词映射表 =====
    DOMAIN_KEYWORDS = {
        "ecommerce": {
            "primary": ["亚马逊", "amazon", "1688", "淘宝", "天猫", "电商", "选品", 
                      "产品", "商品", "listing", "库存", "供应商", "跨境"],
            "secondary": ["价格", "销量", "竞品", "类目", "市场", "采购", "物流"]
        },
        "design": {
            "primary": ["设计", "logo", "海报", "UI", "界面", "原型", "方案", "初稿",
                       "品牌", "VI", "视觉", "插画", "排版", "配色"],
            "secondary": ["需求", "创意", "风格", "素材", "PPT", "演示文稿"]
        },
        "finance": {
            "primary": ["财务", "发票", "报销", "账目", "报表", "税务", "预算",
                       "会计", "凭证", "对账", "结算", "工资", "成本"],
            "secondary": ["利润", "现金流", "资产负债", "合规", "审计"]
        },
        "development": {
            "primary": ["代码", "编程", "开发", "bug", "部署", "API", "接口", "测试",
                       "git", "数据库", "后端", "前端", "全栈", "DevOps"],
            "secondary": ["框架", "库", "依赖", "重构", "性能", "安全"]
        },
        "content": {
            "primary": ["内容", "文章", "文案", "写作", "博客", "公众号", "小红书",
                       "视频脚本", "SEO", "标题", "营销文案", "推广"],
            "secondary": ["选题", "热点", "爆款", "转化率", "阅读量"]
        },
        "customer_service": {
            "primary": ["客服", "工单", "投诉", "咨询", "售后", "退换货", "订单查询",
                       "用户反馈", "满意度", "FAQ", "常见问题"],
            "secondary": ["回复模板", "话术", "SLA", "优先级"]
        }
    }
    
    # ===== 槽位定义表 =====
    SLOT_DEFINITIONS: Dict[str, SlotDefinition] = {
        "platform": SlotDefinition(
            name="platform",
            description="平台名称",
            data_type="enum",
            examples=["Amazon", "1688", "淘宝", "天猫", "京东"],
            extraction_patterns=[r"亚马逊|amazon|Amazon", r"1688|阿里巴巴", r"淘宝|taobao"]
        ),
        "category": SlotDefinition(
            name="category",
            description="产品/内容类目",
            data_type="string",
            examples=["户外运动", "电子产品", "服装", "家居", "科技"],
            extraction_patterns=[]
        ),
        "time_range": SlotDefinition(
            name="time_range",
            description="时间范围",
            data_type="enum",
            examples=["上周", "本月", "昨天", "最近7天", "Q1", "2026年3月"],
            extraction_patterns=[
                r"上周|last week", r"本月|这个月|this month", 
                r"昨天|yesterday", r"\d{4}年?\d{1,2}月?"
            ]
        ),
        "file_path": SlotDefinition(
            name="file_path",
            description="文件路径",
            data_type="string",
            examples=["./report.md", "/data/invoices/", "document.pdf"],
            extraction_patterns=[r"[a-zA-Z0-9_/\-\.]+\.(md|txt|pdf|docx|xlsx|json|py)"]
        ),
        "task_type": SlotDefinition(
            name="task_type",
            description="任务类型",
            data_type="enum",
            examples=["research", "sourcing", "listing", "analysis", "design", "writing"],
            extraction_patterns=[]
        )
    }
    
    def __init__(self, config: Optional[Dict] = None):
        capability = AgentCapability(
            name="intent_recognition",
            description="深度意图识别、槽位提取、Domain智能路由",
            version="2.0.0",
            
            input_schema={
                "text": {"type": "string", "required": True},
                "conversation_history": {"type": "array"},
                "user_context": {"type": "object"}
            },
            
            output_schema={
                "intent": {"type": "string"},
                "confidence": {"type": "number"},
                "target_domain": {"type": "string"},
                "slots": {"type": "object"},
                "needs_clarification": {"type": "boolean"}
            },
            
            supported_intents=["*"],  # 支持所有意图
            max_concurrent_tasks=20,
            estimated_latency_ms=200
        )
        
        super().__init__("intent-agent-001", capability)
        
        self.config = config or {}
        
        # 意图到Domain的映射
        self.INTENT_TO_DOMAIN_MAP = {
            IntentCategory.ECOMMERCE: "ecommerce",
            IntentCategory.DESIGN: "design",
            IntentCategory.FINANCE: "finance",
            IntentCategory.DEVELOPMENT: "development",
            IntentCategory.CONTENT_CREATION: "content",
            IntentCategory.CUSTOMER_SERVICE: "customer_service",
            IntentCategory.FILE_OPERATION: "file",
            IntentCategory.SKILL_MANAGEMENT: "skill",
            IntentCategory.QUESTION_ANSWERING: "rag",
            IntentCategory.CHAT: "chat"
        }
        
        # 已注册的Domain列表（动态更新）
        self._registered_domains: List[str] = []
    
    def update_registered_domains(self, domains: List[str]):
        """更新已注册的Domain列表（由Supervisor调用）"""
        self._registered_domains = domains
        logger.info(f"[{self.agent_id}] Updated registered domains: {domains}")
    
    async def execute(self, task: Dict[str, Any], context: AgentExecutionContext) -> AgentExecutionResult:
        """执行意图识别"""
        text = task.get("text", "")
        history = task.get("conversation_history", [])
        user_context = task.get("user_context", {})
        
        logger.debug(f"[{self.agent_id}] Recognizing intent for: {text[:60]}...")
        
        # 三层策略执行
        result = await self._recognize_with_strategy(text, history, user_context)
        
        return AgentExecutionResult(
            success=True,
            data={
                "intent": result.intent.value if isinstance(result.intent, IntentCategory) else result.intent,
                "confidence": result.confidence,
                "target_domain": result.target_domain,
                "target_agent_type": result.target_agent_type,
                "slots": result.slots,
                "needs_clarification": result.needs_clarification,
                "clarification_question": result.clarification_question,
                "alternative_intents": result.alternative_intents,
                "reasoning": result.reasoning,
                "ambiguity_score": result.ambiguity_score
            },
            metrics={"strategy_used": result.reasoning.split(":")[0] if result.reasoning else "unknown"}
        )
    
    async def _recognize_with_strategy(
        self, 
        text: str, 
        history: List[Dict], 
        user_context: Dict
    ) -> IntentResult:
        """三层策略：规则 → 语义 → LLM"""
        
        # L1: 规则快速匹配
        rule_result = self._match_by_rules(text)
        if rule_result and rule_result.confidence >= 0.85:
            return rule_result
        
        # L2: 关键词语义匹配
        semantic_result = self._match_by_semantics(text)
        if semantic_result and semantic_result.confidence >= 0.70:
            return semantic_result
        
        # L3: 上下文增强 + 综合决策
        enhanced_result = self._enhance_with_context(text, history, user_context, rule_result, semantic_result)
        
        return enhanced_result
    
    def _match_by_rules(self, text: str) -> Optional[IntentResult]:
        """L1: 基于规则的快速匹配"""
        text_lower = text.lower()
        best_match = None
        best_score = 0
        
        for domain, keywords in self.DOMAIN_KEYWORDS.items():
            primary_score = sum(1 for kw in keywords["primary"] if kw.lower() in text_lower)
            secondary_score = sum(0.5 for kw in keywords["secondary"] if kw.lower() in text_lower)
            total_score = primary_score + secondary_score
            
            if total_score > best_score:
                best_score = total_score
                domain_intent_map = {
                    "ecommerce": IntentCategory.ECOMMERCE,
                    "design": IntentCategory.DESIGN,
                    "finance": IntentCategory.FINANCE,
                    "development": IntentCategory.DEVELOPMENT,
                    "content": IntentCategory.CONTENT_CREATION,
                    "customer_service": IntentCategory.CUSTOMER_SERVICE
                }
                
                best_match = IntentResult(
                    intent=domain_intent_map.get(domain, IntentCategory.TASK_EXECUTION),
                    confidence=min(0.5 + total_score * 0.1, 0.95),
                    target_domain=domain if domain in self._registered_domains else None,
                    slots=self._extract_slots_by_rules(text),
                    reasoning=f"rule_based:{domain}(score={total_score})"
                )
        
        return best_match if best_score > 0 else None
    
    def _match_by_semantics(self, text: str) -> Optional[IntentResult]:
        """L2: 语义相似度匹配（基于关键词向量近似）"""
        text_lower = text.lower()
        
        scores = {}
        for domain, keywords in self.DOMAIN_KEYWORDS.items():
            all_keywords = keywords["primary"] + keywords["secondary"]
            matches = [kw for kw in all_keywords if any(part in text_lower for part in kw.lower().split())]
            scores[domain] = len(matches)
        
        if not scores or max(scores.values()) == 0:
            return None
        
        top_domain = max(scores.keys(), key=lambda k: scores[k])
        score_normalized = min(scores[top_domain] / 10, 0.80)
        
        domain_intent_map = {
            "ecommerce": IntentCategory.ECOMMERCE,
            "design": IntentCategory.DESIGN,
            "finance": IntentCategory.FINANCE,
            "development": IntentCategory.DEVELOPMENT,
            "content": IntentCategory.CONTENT_CREATION,
            "customer_service": IntentCategory.CUSTOMER_SERVICE
        }
        
        return IntentResult(
            intent=domain_intent_map.get(top_domain, IntentCategory.TASK_EXECUTION),
            confidence=score_normalized,
            target_domain=top_domain if top_domain in self._registered_domains else None,
            slots=self._extract_slots_by_rules(text),
            reasoning=f"semantic:{top_domain}"
        )
    
    def _enhance_with_context(
        self,
        text: str,
        history: List[Dict],
        user_context: Dict,
        rule_result: Optional[IntentResult],
        semantic_result: Optional[IntentResult]
    ) -> IntentResult:
        """L3: 上下文增强的综合决策"""
        
        candidates = []
        if rule_result:
            candidates.append(("rule", rule_result))
        if semantic_result:
            candidates.append(("semantic", semantic_result))
        
        # 如果有历史对话，检查主题一致性
        if history and len(history) >= 2:
            recent_topics = self._extract_recent_topics(history[-5:])
            for topic_domain, confidence in recent_topics:
                candidates.append((f"context_{topic_domain}", IntentResult(
                    intent=self._get_intent_for_domain(topic_domain),
                    confidence=confidence * 0.9,
                    target_domain=topic_domain if topic_domain in self._registered_domains else None,
                    reasoning=f"context_continuity:{topic_domain}"
                )))
        
        if not candidates:
            return IntentResult(
                intent=IntentCategory.CHAT,
                confidence=0.5,
                target_domain=None,
                needs_clarification=True,
                clarification_question="我不太确定您需要什么帮助，能否详细描述一下您的需求？",
                reasoning="no_match_fallback"
            )
        
        # 选择最佳候选
        candidates.sort(key=lambda x: x[1].confidence, reverse=True)
        best_source, best_result = candidates[0]
        
        # 如果最佳结果的置信度仍然较低，标记为需要澄清
        if best_result.confidence < 0.6:
            best_result.needs_clarification = True
            best_result.clarification_question = self._generate_clarification(best_result, text)
            best_result.ambiguity_score = 1 - best_result.confidence
        
        return best_result
    
    def _extract_slots_by_rules(self, text: str) -> Dict[str, Any]:
        """基于正则的槽位提取"""
        slots = {}
        
        for slot_name, slot_def in self.SLOT_DEFINITIONS.items():
            for pattern in slot_def.extraction_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    slots[slot_name] = match.group(0)
                    break
        
        # 提取数字参数
        numbers = re.findall(r'\d+', text)
        if numbers:
            slots["numbers"] = [int(n) for n in numbers]
        
        return slots
    
    def _extract_recent_topics(self, recent_messages: List[Dict]) -> List[Tuple[str, float]]:
        """从历史消息中提取最近的领域话题"""
        topic_scores = {}
        
        for msg in recent_messages:
            content = msg.get("content", "")
            for domain, keywords in self.DOMAIN_KEYWORDS.items():
                count = sum(1 for kw in keywords["primary"] if kw.lower() in content.lower())
                if count > 0:
                    topic_scores[domain] = topic_scores.get(domain, 0) + count * 2
                
                count_sec = sum(1 for kw in keywords["secondary"] if kw.lower() in content.lower())
                if count_sec > 0:
                    topic_scores[domain] = topic_scores.get(domain, 0) + count_sec
        
        sorted_topics = sorted(topic_scores.items(), key=lambda x: x[1], reverse=True)
        return [(d, min(s / 10, 0.9)) for d, s in sorted_topics[:3]]
    
    def _get_intent_for_domain(self, domain: str) -> IntentCategory:
        mapping = {
            "ecommerce": IntentCategory.ECOMMERCE,
            "design": IntentCategory.DESIGN,
            "finance": IntentCategory.FINANCE,
            "development": IntentCategory.DEVELOPMENT,
            "content": IntentCategory.CONTENT_CREATION,
            "customer_service": IntentCategory.CUSTOMER_SERVICE
        }
        return mapping.get(domain, IntentCategory.TASK_EXECUTION)
    
    def _generate_clarification(self, result: IntentResult, original_text: str) -> str:
        """生成澄清问题"""
        templates = {
            IntentCategory.ECOMMERCE: "关于您的电商操作需求，请问是哪个平台（如亚马逊/1688）？什么类目的产品？",
            IntentCategory.DESIGN: "关于设计任务，能详细描述一下您的设计需求和风格偏好吗？",
            IntentCategory.FINANCE: "关于财务操作，请明确具体要处理的时间范围和业务类型？",
            IntentCategory.DEVELOPMENT: "关于开发任务，请说明使用的技术栈和具体功能需求？",
            IntentCategory.CONTENT_CREATION: "关于内容创作，请确认目标平台、受众和内容类型？",
            IntentCategory.CUSTOMER_SERVICE: "关于客服相关的问题，请提供订单号或更详细的信息？"
        }
        
        default = f"我注意到您想处理'{original_text[:30]}...'相关的任务，能否提供更多细节？"
        
        return templates.get(result.intent, default)
    
    async def validate_input(self, task: Dict[str, Any]) -> Tuple[bool, List[str]]:
        errors = []
        if "text" not in task or not task.get("text"):
            errors.append("Missing required parameter: 'text'")
        return (len(errors) == 0, errors)
    
    async def health_check(self) -> AgentHealthCheckResult:
        stats = await self.get_statistics()
        status = AgentHealthStatus.HEALTHY
        if stats["success_rate"] < 0.9:
            status = AgentHealthStatus.DEGRADED
        
        return AgentHealthCheckResult(
            status=status,
            agent_id=self.agent_id,
            uptime_seconds=stats["uptime_seconds"],
            tasks_completed=sum(1 for r in self._execution_history if r["success"]),
            tasks_failed=sum(1 for r in self._execution_history if not r["success"]),
            average_latency_ms=stats["avg_latency_ms"],
            details={
                "registered_domains_count": len(self._registered_domains),
                "supported_domains": self._registered_domains,
                **stats
            }
        )


__all__ = ["IntentSubAgent", "IntentResult", "IntentCategory", "SlotDefinition"]
