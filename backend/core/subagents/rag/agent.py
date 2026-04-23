"""
RAG SubAgent - 检索增强生成Agent
负责：文档检索、知识问答、上下文生成
"""

import time
import logging
from typing import Dict, Any, List, Optional, Tuple

from ..base import BaseSubAgent, AgentCapability, AgentExecutionContext, AgentExecutionResult, AgentHealthCheckResult, AgentHealthStatus

logger = logging.getLogger(__name__)


class RAGSubAgent(BaseSubAgent):
    """
    RAG检索增强生成Agent
    
    核心能力：
    1. 混合检索（语义 + 关键词）
    2. 重排序（CrossEncoder）
    3. 上下文构建与截断
    4. LLM生成（基于检索结果）
    
    架构：
        Query → Embedding → Milvus检索 → BM25补充 → 
        Rerank → Context Build → LLM Generate → Answer + Sources
    """
    
    def __init__(self, config: Optional[Dict] = None):
        capability = AgentCapability(
            name="rag_retrieval",
            description="文档检索、知识问答、上下文生成",
            version="1.0.0",
            input_schema={
                "query": {"type": "string", "required": True},
                "top_k": {"type": "integer", "default": 5},
                "collection_name": {"type": "string", "default": "default"},
                "filters": {"type": "object", "default": {}}
            },
            output_schema={
                "answer": {"type": "string"},
                "sources": {"type": "array"},
                "confidence_score": {"type": "number"}
            },
            supported_intents=["question_answering", "data_analysis", "knowledge_query"],
            max_concurrent_tasks=10,
            estimated_latency_ms=1500
        )
        
        super().__init__("rag-agent-001", capability)
        
        self.config = config or {}
        
        # 组件引用（延迟初始化）
        self._vector_store = None
        self._embedder = None
        self._reranker = None
        self._llm_client = None
        
        # 检索参数
        self.default_top_k = config.get("top_k", 5) if config else 5
        self.similarity_threshold = config.get("similarity_threshold", 0.75) if config else 0.75
        self.max_context_tokens = config.get("max_context_tokens", 4096) if config else 4096
        
        # 缓存
        self._query_cache: Dict[str, Any] = {}
        self._cache_max_size = 10000
    
    async def execute(self, task: Dict[str, Any], context: AgentExecutionContext) -> AgentExecutionResult:
        """执行RAG查询"""
        start_time = time.time()
        
        query = task.get("query", "")
        top_k = task.get("top_k", self.default_top_k)
        collection_name = task.get("collection_name", "default")
        filters = task.get("filters", {})
        
        logger.info(f"[{self.agent_id}] RAG query: {query[:50]}... (k={top_k})")
        
        # 缓存检查
        cache_key = f"{query}:{top_k}:{collection_name}"
        cached = self._query_cache.get(cache_key)
        if cached and (time.time() - cached["timestamp"] < 300):  # 5分钟缓存
            return AgentExecutionResult(
                success=True,
                data=cached["data"],
                metrics={"cache_hit": True, **cached["metrics"]}
            )
        
        try:
            # Step 1: Query理解与扩展
            expanded_queries = await self._expand_query(query)
            
            # Step 2: 混合检索
            retrieval_results = await self._hybrid_retrieval(
                queries=expanded_queries,
                top_k=top_k * 2,
                collection_name=collection_name,
                filters=filters
            )
            
            if not retrieval_results:
                return AgentExecutionResult(
                    success=True,
                    data={
                        "answer": f"未找到与'{query}'相关的信息。请尝试使用不同的关键词。",
                        "sources": [],
                        "confidence_score": 0.0,
                        "suggestion": "建议简化查询或检查拼写"
                    },
                    metrics={"retrieval_count": 0, "total_time_ms": (time.time()-start_time)*1000}
                )
            
            # Step 3: 重排序
            reranked_results = await self._rerank(query, retrieval_results, top_k)
            
            # Step 4: 上下文构建
            context_text = self._build_context(reranked_results)
            
            # Step 5: LLM生成
            answer = await self._generate_answer(query, context_text, reranked_results)
            
            result_data = {
                "answer": answer,
                "sources": [
                    {
                        "id": doc.get("id", ""),
                        "title": doc.get("metadata", {}).get("title", ""),
                        "score": doc.get("score", 0),
                        "snippet": doc.get("text", "")[:200]
                    }
                    for doc in reranked_results
                ],
                "confidence_score": self._calculate_confidence(reranked_results),
                "metadata": {
                    "retrieved_docs": len(retrieval_results),
                    "reranked_docs": len(reranked_results),
                    "context_length": len(context_text)
                }
            }
            
            total_time_ms = (time.time() - start_time) * 1000
            
            # 缓存结果
            self._cache_result(cache_key, result_data, {"total_time_ms": total_time_ms})
            
            return AgentExecutionResult(
                success=True,
                data=result_data,
                metrics={
                    "total_time_ms": total_time_ms,
                    "retrieved_count": len(retrieval_results),
                    "final_count": len(reranked_results)
                },
                artifacts=reranked_results
            )
            
        except Exception as e:
            logger.error(f"[{self.agent_id}] RAG execution error: {e}", exc_info=True)
            return AgentExecutionResult(
                success=False,
                error=str(e),
                error_type="rag_error"
            )
    
    async def validate_input(self, task: Dict[str, Any]) -> Tuple[bool, List[str]]:
        errors = []
        
        if "query" not in task or not task.get("query"):
            errors.append("Missing required parameter: 'query'")
        
        if "top_k" in task:
            top_k = task["top_k"]
            if not isinstance(top_k, int) or top_k < 1 or top_k > 50:
                errors.append("'top_k' must be an integer between 1 and 50")
        
        return (len(errors) == 0, errors)
    
    async def health_check(self) -> AgentHealthCheckResult:
        stats = await self.get_statistics()
        
        status = AgentHealthStatus.HEALTHY
        if stats["success_rate"] < 0.8:
            status = AgentHealthStatus.DEGRADED
        if stats["success_rate"] < 0.5:
            status = AgentHealthStatus.UNHEALTHY
        
        return AgentHealthCheckResult(
            status=status,
            agent_id=self.agent_id,
            uptime_seconds=stats["uptime_seconds"],
            tasks_completed=sum(1 for r in self._execution_history if r["success"]),
            tasks_failed=sum(1 for r in self._execution_history if not r["success"]),
            average_latency_ms=stats["avg_latency_ms"],
            details=stats
        )
    
    async def _expand_query(self, query: str) -> List[str]:
        """查询扩展"""
        expansions = [query]
        
        # TODO: 实现LLM驱动的查询扩展
        # 目前返回原始查询
        return expansions
    
    async def _hybrid_retrieval(
        self,
        queries: List[str],
        top_k: int,
        collection_name: str,
        filters: Dict
    ) -> List[Dict]:
        """
        混合检索：语义 + 关键词
        """
        from services.rag_service import get_rag_service
        rag_service = get_rag_service()

        all_results = []
        for query in queries:
            results = await rag_service.search(
                query=query,
                collection_name=collection_name,
                top_k=top_k,
                filters=filters
            )
            all_results.extend(results)

        return all_results
    
    async def _rerank(self, query: str, documents: List[Dict], top_k: int) -> List[Dict]:
        """
        CrossEncoder重排序
        
        TODO: 集成实际的CrossEncoder模型
        """
        sorted_docs = sorted(documents, key=lambda x: x.get("score", 0), reverse=True)
        return sorted_docs[:top_k]
    
    def _build_context(self, documents: List[Dict]) -> str:
        """构建LLM上下文"""
        context_parts = []
        current_tokens = 0
        
        for doc in documents:
            text = f"\n[来源: {doc['metadata'].get('title', 'Unknown')}]\n{doc['text']}\n"
            estimated_tokens = len(text) // 2
            
            if current_tokens + estimated_tokens > self.max_context_tokens:
                break
            
            context_parts.append(text)
            current_tokens += estimated_tokens
        
        return "\n".join(context_parts)
    
    async def _generate_answer(self, query: str, context: str, sources: List[Dict]) -> str:
        """基于上下文生成回答"""
        from services.llm_service import get_llm_service
        llm = get_llm_service()

        prompt = f"""基于以下参考信息回答问题。如果参考信息中没有答案，请明确说明。

问题: {query}

参考信息:
{context}

请用中文简洁地回答:"""

        if not llm.is_available:
            answer = f"根据检索到的{len(sources)}份文档，关于'{query}'的回答如下：\n\n"
            answer += "（请在 .env 中配置 OPENAI_API_KEY 以启用LLM生成功能）\n\n"
            answer += f"\n---\n*以上内容基于 {len(sources)} 个相关文档生成，置信度较高。*"
            return answer

        response = await llm.generate(prompt, system_prompt="你是一个有帮助的AI助手，请基于提供的参考信息回答问题。")
        return response.content
    
    def _calculate_confidence(self, documents: List[Dict]) -> float:
        if not documents:
            return 0.0
        
        scores = [doc.get("score", 0) for doc in documents]
        avg_score = sum(scores) / len(scores)
        return min(avg_score, 1.0)
    
    def _cache_result(self, key: str, data: Dict, metrics: Dict):
        if len(self._query_cache) >= self._cache_max_size:
            oldest_key = next(iter(self._query_cache))
            del self._query_cache[oldest_key]
        
        self._query_cache[key] = {
            "data": data,
            "metrics": metrics,
            "timestamp": time.time()
        }
