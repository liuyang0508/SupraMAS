"""
Layer 2: Query Optimizer - 查询改写与优化
负责：指代消解、省略补全、语义规范化、查询扩展
"""

import re
import logging
from typing import Dict, Any, List, Optional

from ..supervisor.state import OptimizedQuery

logger = logging.getLogger(__name__)


class QueryOptimizer:
    """
    Layer 2: 查询优化器
    
    职责：
    1. 指代消解 (Coreference Resolution) - "它" → "上个产品"
    2. 省略补全 (Ellipsis Completion) - "那国内的呢？" → 补全条件
    3. 语义规范化 (Semantic Normalization) - 口语 → 标准术语
    4. 查询扩展 (Query Expansion) - 增加相关概念提升召回
    
    改写策略优先级：
    - 规则改写（快速、确定性）
    - 上下文融合（利用对话历史）
    - LLM增强（复杂语义理解）
    """
    
    COREFERENCE_MAP = {
        "它": ["上一个查询的主体", "最近讨论的对象"],
        "这个": ["当前主题", "刚刚提到的"],
        "那个": ["之前提到的", "另一个选项"],
        "它们": ["多个对象"],
        "前者": ["第一个对象"],
        "后者": ["第二个对象"]
    }
    
    NORMALIZATION_RULES = [
        (r"帮我瞅瞅|帮我看看|看看|查查|找找", "检索/分析"),
        (r"卖得火的|热销的|卖得好", "销量Top/热门"),
        (r"便宜点|价格低|性价比高", "价格优势"),
        (r"咋样|怎么样|如何", "评估/分析"),
        (r"搞个|弄个|做个|生成|创建", "生成/创建"),
        (r"给我整理|汇总一下|总结", "总结/聚合")
    ]
    
    EXPANSION_DICTIONARY = {
        "手机": ["智能手机", "移动电话", "mobile phone", "手机"],
        "电脑": ["计算机", "笔记本电脑", "PC", "computer"],
        "亚马逊": ["Amazon", "amazon.com", "美亚"],
        "1688": ["阿里巴巴批发", "alibaba 1688"],
        "电商": ["电子商务", "e-commerce", "在线零售"]
    }
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.context_window_size = config.get("context_window_size", 20)
        self.enable_expansion = config.get("enable_query_expansion", True)
        
        self._rewrite_cache: Dict[str, OptimizedQuery] = {}
    
    async def optimize(
        self,
        original_query: str,
        intent: Optional[str] = None,
        slots: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> OptimizedQuery:
        """
        执行查询优化
        
        Args:
            original_query: 原始查询
            intent: 已识别的意图
            slots: 已提取的槽位
            conversation_history: 对话历史
            
        Returns:
            OptimizedQuery: 优化后的查询
        """
        cache_key = f"{original_query}_{intent}"
        if cache_key in self._rewrite_cache:
            logger.debug(f"[QueryOptimizer] Cache hit for: {original_query[:30]}...")
            return self._rewrite_cache[cache_key]
        
        transformations = []
        query = original_query
        
        # Step 1: 指代消解
        query, coref_applied = self._resolve_coreferences(query, conversation_history)
        if coref_applied:
            transformations.append("coreference_resolution")
        
        # Step 2: 省略补全
        query, ellipsis_applied = self._complete_ellipsis(query, conversation_history)
        if ellipsis_applied:
            transformations.append("ellipsis_completion")
        
        # Step 3: 语义规范化
        query, norm_applied = self._normalize_semantics(query)
        if norm_applied:
            transformations.append("semantic_normalization")
        
        # Step 4: 槽位注入（将提取的结构化信息融入查询）
        if slots and intent:
            query = self._inject_slots(query, slots, intent)
            transformations.append("slot_injection")
        
        # Step 5: 查询扩展
        expansion_terms = []
        if self.enable_expansion:
            query, expansion_terms = self._expand_query(query)
            if expansion_terms:
                transformations.append("query_expansion")
        
        optimized = OptimizedQuery(
            rewritten_query=query,
            original_query=original_query,
            applied_transformations=transformations,
            context_used=self._get_context_summary(conversation_history),
            expansion_terms=expansion_terms
        )
        
        # 缓存结果
        self._rewrite_cache[cache_key] = optimized
        
        logger.info(f"[QueryOptimizer] '{original_query[:40]}...' → '{query[:40]}...' [{', '.join(transformations)}]")
        
        return optimized
    
    def _resolve_coreferences(self, query: str, history: Optional[List[Dict]]) -> Tuple[str, bool]:
        """指代消解"""
        modified = False
        
        if not history or len(history) < 2:
            return query, False
        
        last_user_msg = ""
        for msg in reversed(history):
            if msg.get("role") == "user":
                last_user_msg = msg.get("content", "")
                break
        
        for pronoun, resolution_options in self.COREFERENCE_MAP.items():
            pattern = rf"\b{pronoun}\b"
            if re.search(pattern, query, re.IGNORECASE):
                replacement = resolution_options[0]
                query = re.sub(pattern, f"[{replacement}]", query, flags=re.IGNORECASE)
                modified = True
        
        return query, modified
    
    def _complete_ellipsis(self, query: str, history: Optional[List[Dict]]) -> Tuple[str, bool]:
        """省略补全"""
        modified = False
        
        if not history or len(history) < 2:
            return query, False
        
        # 检测省略模式："那X呢？" / "X呢？"
        ellipsis_pattern = r"^那?(.+?)呢?[\?？！!]*$"
        match = re.match(ellipsis_pattern, query.strip())
        
        if match:
            topic = match.group(1).strip()
            
            # 从历史中查找上下文
            context_info = self._extract_context_for_ellipsis(history, topic)
            
            if context_info:
                query = f"{context_info} 关于{topic}的信息"
                modified = True
        
        return query, modified
    
    def _extract_context_for_ellipsis(self, history: List[Dict], topic: str) -> Optional[str]:
        """为省略补全提取上下文"""
        recent_contexts = []
        
        for msg in history[-self.context_window_size:]:
            content = msg.get("content", "")
            if topic.lower() in content.lower():
                recent_contexts.append(content[:100])
        
        return recent_contexts[-1] if recent_contexts else None
    
    def _normalize_semantics(self, query: str) -> Tuple[str, bool]:
        """语义规范化"""
        modified = False
        
        for pattern, replacement in self.NORMALIZATION_RULES:
            if re.search(pattern, query, re.IGNORECASE):
                query = re.sub(pattern, replacement, query, flags=re.IGNORECASE)
                modified = True
        
        return query, modified
    
    def _inject_slots(self, query: str, slots: Dict[str, Any], intent: str) -> str:
        """将结构化槽位信息注入查询"""
        slot_texts = []
        
        important_slots = ["platform", "category", "time_range", "file_type"]
        for slot_name in important_slots:
            if slot_name in slots:
                slot_texts.append(f"{slot_name}={slots[slot_name]}")
        
        if slot_texts:
            query = f"[{', '.join(slot_texts)}] {query}"
        
        return query
    
    def _expand_query(self, query: str) -> Tuple[str, List[str]]:
        """查询扩展"""
        expansion_terms = []
        
        for term, expansions in self.EXPANSION_DICTIONARY.items():
            if term in query:
                for exp in expansions[1:]:  # 排除原始词
                    if exp not in query:
                        expansion_terms.append(exp)
        
        return query, expansion_terms
    
    def _get_context_summary(self, history: Optional[List[Dict]]) -> List[str]:
        """获取上下文摘要用于记录"""
        if not history:
            return []
        
        summaries = []
        for msg in history[-5:]:  # 最近5轮
            role = msg.get("role", "unknown")
            content_preview = msg.get("content", "")[:50]
            summaries.append(f"[{role}] {content_preview}")
        
        return summaries
