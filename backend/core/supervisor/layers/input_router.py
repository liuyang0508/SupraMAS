"""
Layer 1: Input Router - 意图识别与路由
负责：意图分类、槽位提取、歧义检测、路由决策
"""

import re
import json
import logging
from typing import Dict, Any, List, Optional, Tuple

from ..state import RoutingDecision

logger = logging.getLogger(__name__)


class InputRouter:
    """
    Layer 1: 输入路由器

    职责：
    1. 意图分类 (Intent Classification)
    2. 槽位提取 (Slot Extraction / Entity Recognition)
    3. 歧义检测 (Ambiguity Detection)
    4. 路由决策 (Routing Decision)

    支持三种模式：
    - rule_based: 基于规则的关键词匹配（快速、可解释）
    - llm_based: 基于LLM的语义理解（准确但较慢）
    - hybrid: 规则优先 + LLM兜底（推荐）
    """

    INTENT_RULES = {
        "chat": {
            "patterns": [r"^(你好|hi|hello|嗨|在吗)", r"^(谢谢|感谢|好的|OK)"],
            "keywords": ["聊天", "闲聊", "说说", "聊聊"],
            "default_agent": "chat"
        },
        "question_answering": {
            "patterns": [r"(什么是|怎么|如何|为什么|哪|谁|多少|解释|说明)"],
            "keywords": ["问题", "查询", "搜索", "了解", "告诉我"],
            "default_agent": "rag"
        },
        "task_execution": {
            "patterns": [r"(帮我|请|帮我做|执行|完成|处理|生成|创建|分析)"],
            "keywords": ["任务", "工作", "处理", "执行"],
            "default_agent": "skill"
        },
        "ecommerce_operation": {
            "patterns": [r"(亚马逊|amazon|1688|淘宝|天猫|电商|选品|产品|商品|listing)"],
            "keywords": ["选品", "上架", "价格", "供应商", "库存"],
            "default_agent": "skill"
        },
        "file_operation": {
            "patterns": [r"(文件|文档|读取|写入|修改|删除|保存|打开|创建.*文件)"],
            "keywords": ["文件", "文档", "read", "write", "edit", "save"],
            "default_agent": "file"
        },
        "skill_management": {
            "patterns": [r"(技能|skill|安装|卸载|技能市场|skills?)"],
            "keywords": ["安装技能", "卸载", "技能商店", "marketplace"],
            "default_agent": "skill"
        },
        "data_analysis": {
            "patterns": [r"(分析|统计|报表|数据|图表|可视化|dashboard)"],
            "keywords": ["数据分析", "报表", "图表", "趋势", "统计"],
            "default_agent": "rag"
        },
        "design_work": {
            "patterns": [r"(设计|logo|海报|UI|界面|原型|方案|初稿)"],
            "keywords": ["设计", "logo", "海报", "UI设计", "原型"],
            "default_agent": "skill"
        },
        "finance_management": {
            "patterns": [r"(财务|发票|报销|账目|报表|税务|预算)"],
            "keywords": ["发票", "财务", "报销", "账单", "税务"],
            "default_agent": "skill"
        },
        "software_development": {
            "patterns": [r"(代码|编程|开发|bug|部署|API|接口|测试)"],
            "keywords": ["代码", "编程", "bug", "deploy", "API"],
            "default_agent": "skill"
        }
    }

    # Intent definitions for LLM
    INTENT_DESCRIPTIONS = {
        "chat": "General conversation, greetings, casual chat",
        "question_answering": "Question answering, information retrieval, knowledge lookup",
        "task_execution": "Task execution, workflow automation, complex operations",
        "ecommerce_operation": "E-commerce operations, product research, supplier sourcing, listing optimization",
        "file_operation": "File operations: read, write, edit, delete files or documents",
        "skill_management": "Skill installation, uninstallation, skill marketplace",
        "data_analysis": "Data analysis, statistics, reporting, visualization",
        "design_work": "Design work, logo creation, UI design, marketing materials",
        "finance_management": "Finance, invoicing, expense tracking, tax, budgeting",
        "software_development": "Software development, coding, debugging, deployment, API"
    }

    SLOT_PATTERNS = {
        "platform": [
            (r"亚马逊|amazon|Amazon", "amazon"),
            (r"1688|阿里巴巴|alibaba", "1688"),
            (r"淘宝|taobao", "taobao"),
            (r"京东|JD|jd", "jd")
        ],
        "time_range": [
            (r"上周|last week", "last_week"),
            (r"本月|这个月|this month", "this_month"),
            (r"昨天|yesterday", "yesterday"),
            (r"最近\d+天|最近\d+周", "recent_period"),
            (r"\d{4}年?\d{1,2}月?", "specific_date")
        ],
        "category": [
            (r"户外运动|outdoor sports?|户外", "outdoor_sports"),
            (r"电子产品|electronics|电子", "electronics"),
            (r"服装|clothing|服饰|衣服", "clothing"),
            (r"家居|home.*garden|家具", "home_garden")
        ],
        "file_type": [
            (r"\.md$|markdown|MD", "markdown"),
            (r"\.pdf$|PDF", "pdf"),
            (r"\.(docx?|word)$|Word", "word"),
            (r"\.(xlsx?|excel)$|Excel", "excel"),
            (r"\.(json|JSON)$", "json"),
            (r"\.(py|python)$", "python")
        ]
    }

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.mode = config.get("mode", "hybrid")  # rule_based, llm_based, hybrid
        self.confidence_threshold = config.get("confidence_threshold", 0.75)
        self._llm_client = None
        self._init_llm_client()

        logger.info(f"[InputRouter] Initialized with mode={self.mode}")

    def _init_llm_client(self):
        """Initialize LLM client for intent classification"""
        from services.llm_service import get_llm_service
        self._llm_client = get_llm_service()
        if self._llm_client and self._llm_client.is_available:
            logger.info("[InputRouter] LLM client initialized")
        else:
            logger.info("[InputRouter] No LLM provider configured or API key missing, LLM routing disabled")
    
    async def route(
        self,
        text: str,
        input_type: str = "text",
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> RoutingDecision:
        """
        执行路由决策
        
        Args:
            text: 用户输入文本
            input_type: 输入类型
            conversation_history: 对话历史
            
        Returns:
            RoutingDecision: 路由决策结果
        """
        text_clean = text.strip()
        
        if not text_clean:
            return RoutingDecision(
                intent="chat",
                confidence=0.5,
                target_agent="chat",
                reasoning="Empty input, default to chat"
            )
        
        if self.mode == "rule_based":
            return await self._route_by_rules(text_clean)
        elif self.mode == "llm_based":
            return await self._route_by_llm(text_clean, conversation_history)
        else:
            return await self._route_hybrid(text_clean, conversation_history)
    
    async def _route_by_rules(self, text: str) -> RoutingDecision:
        """基于规则的路由（快速路径）"""
        text_lower = text.lower()
        
        best_intent = None
        best_confidence = 0.0
        best_match_reasoning = ""
        
        for intent, rules in self.INTENT_RULES.items():
            score = 0.0
            matched_patterns = []
            
            for pattern in rules.get("patterns", []):
                if re.search(pattern, text_lower):
                    score += 0.4
                    matched_patterns.append(pattern[:30])
            
            for keyword in rules.get("keywords", []):
                if keyword.lower() in text_lower:
                    score += 0.3
            
            if score > best_confidence:
                best_confidence = min(score, 1.0)
                best_intent = intent
                best_match_reasoning = f"Matched patterns: {matched_patterns}"
        
        slots = self._extract_slots(text_lower)
        needs_clarification = best_confidence < self.confidence_threshold
        
        clarification_question = None
        if needs_clarification and best_intent:
            clarification_question = self._generate_clarification(best_intent, slots, text)
        
        return RoutingDecision(
            intent=best_intent or "chat",
            confidence=best_confidence,
            target_agent=self.INTENT_RULES.get(best_intent, {}).get("default_agent", "chat"),
            slots=slots,
            reasoning=f"Rule-based match: {best_match_reasoning}",
            needs_clarification=needs_clarification,
            clarification_question=clarification_question
        )
    
    async def _route_by_llm(self, text: str, history: Optional[List[Dict]] = None) -> RoutingDecision:
        """基于LLM的路由（准确路径）"""
        if not self._llm_client or not self._llm_client.is_available:
            logger.warning("[InputRouter] LLM client not available, falling back to rules")
            return await self._route_by_rules(text)

        try:
            intent_options = "\n".join([
                f"- {intent}: {desc}"
                for intent, desc in self.INTENT_DESCRIPTIONS.items()
            ])

            history_context = ""
            if history:
                recent = history[-5:] if len(history) > 5 else history
                history_context = "\n\nConversation history:\n" + "\n".join([
                    f"{'User' if msg.get('role') == 'user' else 'Assistant'}: {msg.get('content', '')[:100]}"
                    for msg in recent
                ])

            prompt = f"""You are an intent classification system for an AI assistant called Wukong.

Classify the user's input into one of these intents:
{intent_options}

User's input: "{text}"
{history_context}

Respond with ONLY a JSON object in this format (no markdown, no explanation):
{{"intent": "the_matched_intent", "confidence": 0.0-1.0, "reasoning": "brief explanation"}}

Choose the intent that best matches the user's input. confidence should reflect how certain you are."""

            response = await self._llm_client.generate(prompt)
            response_text = response.content

            import json
            try:
                json_str = response_text.strip()
                if json_str.startswith("```"):
                    json_str = json_str.split("```")[1]
                    if json_str.startswith("json"):
                        json_str = json_str[4:]
                result = json.loads(json_str)

                intent = result.get("intent", "chat")
                confidence = float(result.get("confidence", 0.5))
                reasoning = result.get("reasoning", "")

                if intent not in self.INTENT_RULES:
                    logger.warning(f"[InputRouter] LLM returned unknown intent '{intent}', using 'chat'")
                    intent = "chat"

                return RoutingDecision(
                    intent=intent,
                    confidence=min(max(confidence, 0.0), 1.0),
                    target_agent=self.INTENT_RULES.get(intent, {}).get("default_agent", "chat"),
                    slots=self._extract_slots(text),
                    reasoning=f"LLM-based: {reasoning}",
                    needs_clarification=confidence < self.confidence_threshold
                )
            except json.JSONDecodeError as e:
                logger.warning(f"[InputRouter] Failed to parse LLM response as JSON: {e}, falling back to rules")
                return await self._route_by_rules(text)

        except Exception as e:
            logger.error(f"[InputRouter] LLM routing failed: {e}", exc_info=True)
            return await self._route_by_rules(text)
    
    async def _route_hybrid(self, text: str, history: Optional[List[Dict]] = None) -> RoutingDecision:
        """混合模式：规则优先 + LLM兜底"""
        rule_result = await self._route_by_rules(text)
        
        if rule_result.confidence >= self.confidence_threshold:
            return rule_result
        
        # 置信度不足时，尝试LLM增强
        llm_result = await self._route_by_llm(text, history)
        
        # 取置信度更高的结果
        if llm_result.confidence > rule_result.confidence:
            logger.info(f"[InputRouter] LLM override: {rule_result.intent}({rule_result.confidence:.2f}) → {llm_result.intent}({llm_result.confidence:.2f})")
            return llm_result
        
        return rule_result
    
    def _extract_slots(self, text: str) -> Dict[str, Any]:
        """从文本中提取槽位信息"""
        slots = {}
        
        for slot_name, patterns in self.SLOT_PATTERNS.items():
            for pattern, value in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    slots[slot_name] = value
                    break
        
        # 提取数字参数
        numbers = re.findall(r'\d+', text)
        if numbers:
            slots["numbers"] = [int(n) for n in numbers]
        
        # 提取文件路径
        file_paths = re.findall(r'[a-zA-Z0-9_/\-\.]+\.(md|txt|pdf|docx|xlsx|json|py)', text)
        if file_paths:
            slots["file_paths"] = file_paths
        
        return slots
    
    def _generate_clarification(self, intent: str, slots: Dict, original_text: str) -> Optional[str]:
        """生成澄清问题"""
        clarification_templates = {
            "task_execution": "我注意到您想执行一个任务，能否提供更多细节？比如具体要做什么？",
            "ecommerce_operation": "关于您的电商操作需求，请问是哪个平台（如亚马逊/1688）？什么类目的产品？",
            "file_operation": "关于文件操作，请确认您想操作哪个文件？需要做什么操作？",
            "data_analysis": "关于数据分析，请明确分析的数据范围和时间周期？",
            "design_work": "关于设计任务，能详细描述一下您的设计需求和风格偏好吗？"
        }
        
        return clarification_templates.get(intent)
