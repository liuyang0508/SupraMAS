"""
Wukong AI Platform - Supervisor Core Implementation
中央调度器五层职责模型的完整实现
"""

from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
import time
import uuid
import asyncio
import logging
from datetime import datetime

from langgraph.graph import StateGraph, END

from .state import SupervisorState, TaskStatus, RoutingDecision, OptimizedQuery, SubTask, TaskPlan, SecurityDecision
from .layers.input_router import InputRouter
from .layers.query_optimizer import QueryOptimizer
from .layers.task_planner import TaskPlanner
from .layers.execution_dispatcher import ExecutionDispatcher
from .layers.security_guard import SecurityGuard

logger = logging.getLogger(__name__)


class TraceIDGenerator:
    """Trace ID生成器"""
    def __init__(self):
        self.counter = 0
    
    def generate(self) -> str:
        self.counter += 1
        timestamp = int(time.time() * 1000)
        return f"trace_{timestamp}_{self.counter:04d}"


@dataclass
class UserInput:
    """用户输入"""
    user_id: str
    content: str
    input_type: str = "text"
    attachments: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConversationContext:
    """对话上下文"""
    session_id: str = ""
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    active_skills: List[str] = field(default_factory=list)
    last_intent: Optional[str] = None


@dataclass
class SupervisorResponse:
    """Supervisor响应"""
    success: bool = True
    content: Optional[str] = None
    response_type: str = "text"
    metadata: Dict[str, Any] = field(default_factory=dict)
    trace_id: str = ""
    execution_time: float = 0.0
    state: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    @classmethod
    def error(cls, error: str, trace_id: str = "", execution_time: float = 0.0) -> 'SupervisorResponse':
        return cls(success=False, error=error, trace_id=trace_id, execution_time=execution_time)


class WukongSupervisor:
    """
    悟空Supervisor - 中央调度器
    
    五层职责模型：
    ┌─────────────────────────────────────────────┐
    │  Layer 5: Security Guard (安全审计)         │
    ├─────────────────────────────────────────────┤
    │  Layer 4: Execution Dispatcher (执行调度)   │
    ├─────────────────────────────────────────────┤
    │  Layer 3: Task Planner (任务规划)           │
    ├─────────────────────────────────────────────┤
    │  Layer 2: Query Optimizer (查询优化)         │
    ├─────────────────────────────────────────────┤
    │  Layer 1: Input Router (意图路由)           │
    └─────────────────────────────────────────────┘
    """
    
    def __init__(self, config_dict: Dict[str, Any]):
        self.config = config_dict
        self.trace_gen = TraceIDGenerator()
        
        # 延迟初始化各层组件
        self._input_router: Optional[InputRouter] = None
        self._query_optimizer: Optional[QueryOptimizer] = None
        self._task_planner: Optional[TaskPlanner] = None
        self._dispatcher: Optional[ExecutionDispatcher] = None
        self._security_guard: Optional[SecurityGuard] = None
        
        # SubAgent注册表
        self.agent_pool: Dict[str, Any] = {}
        
        # LangGraph工作流
        self.workflow = None
        self.compiled_app = None
        
        logger.info("[Supervisor] Initialized")
    
    async def initialize(self):
        """初始化所有组件和LangGraph工作流"""
        logger.info("[Supervisor] Initializing components...")
        
        # 初始化各层
        self._input_router = InputRouter(self.config.get('input_router', {}))
        self._query_optimizer = QueryOptimizer(self.config.get('query_optimizer', {}))
        self._task_planner = TaskPlanner(self.config.get('task_planner', {}))
        self._dispatcher = ExecutionDispatcher(
            self.config.get('dispatcher', {}),
            agent_pool=self.agent_pool
        )
        self._security_guard = SecurityGuard(self.config.get('security', {}))
        
        # 构建LangGraph工作流
        self._build_langgraph_workflow()
        
        logger.info("[Supervisor] All components initialized successfully")
    
    def register_subagent(self, agent_type: str, agent_instance: Any):
        """注册SubAgent到池中"""
        self.agent_pool[agent_type] = agent_instance
        logger.info(f"[Supervisor] Registered SubAgent: {agent_type}")
    
    def _build_langgraph_workflow(self):
        """构建LangGraph状态机工作流"""
        workflow = StateGraph(SupervisorState)
        
        # 添加节点（对应五个Layer）
        workflow.add_node("input_router", self._layer1_input_router_node)
        workflow.add_node("query_optimizer", self._layer2_query_optimizer_node)
        workflow.add_node("task_planner", self._layer3_task_planner_node)
        workflow.add_node("security_pre_check", self._layer5_security_pre_check_node)
        workflow.add_node("dispatcher", self._layer4_dispatcher_node)
        workflow.add_node("result_aggregator", self._result_aggregator_node)
        
        # 定义入口点
        workflow.set_entry_point("input_router")
        
        # 定义边
        workflow.add_edge("input_router", "query_optimizer")
        
        # 条件分支：需要澄清 vs 继续
        workflow.add_conditional_edges(
            "query_optimizer",
            self._route_after_optimization,
            {
                "needs_clarification": "result_aggregator",
                "proceed": "task_planner"
            }
        )
        
        workflow.add_edge("task_planner", "security_pre_check")
        
        # 条件分支：安全检查通过/拒绝
        workflow.add_conditional_edges(
            "security_pre_check",
            self._route_after_security,
            {
                "approved": "dispatcher",
                "denied": "result_aggregator"
            }
        )
        
        workflow.add_edge("dispatcher", "result_aggregator")
        workflow.add_edge("result_aggregator", END)
        
        self.workflow = workflow
        self.compiled_app = workflow.compile()
        
        logger.info("[Supervisor] LangGraph workflow built and compiled")
    
    async def process_user_input(
        self,
        user_input: UserInput,
        context: Optional[ConversationContext] = None
    ) -> SupervisorResponse:
        """
        处理用户输入的主入口
        
        Args:
            user_input: 用户输入对象
            context: 对话上下文
            
        Returns:
            SupervisorResponse: 包含响应内容、元数据、执行轨迹
        """
        trace_id = self.trace_gen.generate()
        start_time = time.time()
        
        if not self.compiled_app:
            await self.initialize()
        
        session_id = context.session_id if context else f"session_{uuid.uuid4().hex[:12]}"
        
        initial_state: SupervisorState = {
            "user_id": user_input.user_id,
            "session_id": session_id,
            "original_input": user_input.content,
            "input_type": user_input.input_type,
            
            # Layer 1 输出（待填充）
            "intent": None,
            "intent_confidence": 0.0,
            "extracted_slots": {},
            "routing_decision": None,
            "needs_clarification": False,
            "clarification_question": None,
            
            # Layer 2 输出（待填充）
            "optimized_query": None,
            "query_rewrite_history": [],
            "expanded_entities": [],
            
            # Layer 3 输出（待填充）
            "task_plan": None,
            "subtasks": [],
            "task_dag": None,
            "estimated_duration_seconds": 0.0,
            "resource_requirements": {},
            
            # Layer 4 状态（待填充）
            "current_batch": 0,
            "total_batches": 0,
            "completed_subtasks": [],
            "failed_subtasks": [],
            "subtask_results": {},
            "execution_metrics": {},
            
            # Layer 5 输出（待填充）
            "security_decisions": {},
            "audit_log_entries": [],
            "sanitized_data": False,
            
            # 最终输出（待填充）
            "final_response": None,
            "response_type": "text",
            "metadata": {},
            "trace_id": trace_id,
            "timestamp_start": start_time,
            "timestamp_end": None
        }
        
        try:
            if context:
                initial_state["conversation_context"] = {
                    "history": context.conversation_history[-20:],  # 最近20轮
                    "user_prefs": context.user_preferences,
                    "active_skills": context.active_skills
                }
            
            final_state = await self.compiled_app.ainvoke(initial_state)
            
            exec_time = time.time() - start_time
            
            return SupervisorResponse(
                success=True,
                content=final_state.get("final_response"),
                response_type=final_state.get("response_type", "text"),
                metadata={
                    **final_state.get("metadata", {}),
                    "intent": final_state.get("intent"),
                    "subtasks_count": len(final_state.get("subtasks", [])),
                    "trace_id": trace_id
                },
                trace_id=trace_id,
                execution_time=exec_time,
                state=final_state
            )
            
        except Exception as e:
            logger.error(f"[Supervisor][{trace_id}] Error processing input: {e}", exc_info=True)
            return SupervisorResponse.error(
                error=str(e),
                trace_id=trace_id,
                execution_time=time.time() - start_time
            )
    
    # ==================== LangGraph 节点函数 ====================
    
    async def _layer1_input_router_node(self, state: SupervisorState) -> dict:
        """Layer 1: Input Router - 意图识别与路由"""
        logger.info(f"[Layer1][{state['trace_id']}] Processing input: {state['original_input'][:50]}...")
        
        routing_decision = await self._input_router.route(
            text=state["original_input"],
            input_type=state["input_type"],
            conversation_history=state.get("conversation_context", {}).get("history", [])
        )
        
        return {
            "intent": routing_decision.intent,
            "intent_confidence": routing_decision.confidence,
            "extracted_slots": routing_decision.slots,
            "routing_decision": {
                "target_agent": routing_decision.target_agent,
                "confidence": routing_decision.confidence,
                "reasoning": routing_decision.reasoning
            },
            "needs_clarification": routing_decision.needs_clarification,
            "clarification_question": routing_decision.clarification_question
        }
    
    async def _layer2_query_optimizer_node(self, state: SupervisorState) -> dict:
        """Layer 2: Query Optimizer - 查询改写与优化"""
        logger.info(f"[Layer2][{state['trace_id']}] Optimizing query...")
        
        optimized = await self._query_optimizer.optimize(
            original_query=state["original_input"],
            intent=state["intent"],
            slots=state["extracted_slots"],
            conversation_history=state.get("conversation_context", {}).get("history", [])
        )
        
        return {
            "optimized_query": optimized.rewritten_query,
            "query_rewrite_history": [{
                "original": state["original_input"],
                "rewritten": optimized.rewritten_query,
                "transformations": optimized.applied_transformations
            }],
            "expanded_entities": optimized.expansion_terms
        }
    
    async def _layer3_task_planner_node(self, state: SupervisorState) -> dict:
        """Layer 3: Task Planner - 任务分解与规划"""
        logger.info(f"[Layer3][{state['trace_id']}] Planning tasks for intent: {state['intent']}")
        
        task_plan = await self._task_planner.plan(
            query=state["optimized_query"] or state["original_input"],
            intent=state["intent"],
            slots=state["extracted_slots"],
            routing_decision=state["routing_decision"]
        )
        
        subtask_list = []
        for st in task_plan.subtasks:
            subtask_list.append({
                "task_id": st.task_id,
                "agent_type": st.agent_type,
                "action": st.action,
                "params": st.params,
                "depends_on": st.depends_on,
                "priority": st.priority,
                "status": st.status
            })
        
        return {
            "task_plan": {
                "plan_id": task_plan.plan_id,
                "strategy": task_plan.execution_strategy
            },
            "subtasks": subtask_list,
            "task_dag": task_plan.dag_adjacency,
            "estimated_duration_seconds": task_plan.estimated_total_time,
            "resource_requirements": task_plan.required_capabilities
        }
    
    async def _layer5_security_pre_check_node(self, state: SupervisorState) -> dict:
        """Layer 5: Security Guard (Pre-execution check)"""
        logger.info(f"[Layer5][{state['trace_id']}] Running security pre-check...")
        
        security_decisions = {}
        audit_entries = []
        
        for subtask in state["subtasks"]:
            decision = await self._security_guard.pre_check(
                action={
                    "agent_type": subtask["agent_type"],
                    "action": subtask["action"],
                    "params": subtask["params"]
                },
                user_id=state["user_id"],
                session_id=state["session_id"],
                trace_id=state["trace_id"]
            )
            
            security_decisions[subtask["task_id"]] = decision.allowed
            audit_entries.append(decision.audit_entry or {})
        
        all_approved = all(security_decisions.values())
        
        return {
            "security_decisions": security_decisions,
            "audit_log_entries": audit_entries,
            "sanitized_data": True
        }
    
    async def _layer4_dispatcher_node(self, state: SupervisorState) -> dict:
        """Layer 4: Execution Dispatcher - 执行调度"""
        logger.info(f"[Layer4][{state['trace_id']}] Dispatching {len(state['subtasks'])} subtasks...")
        
        results = await self._dispatcher.dispatch(
            subtasks=state["subtasks"],
            task_dag=state["task_dag"],
            trace_id=state["trace_id"],
            user_id=state["user_id"],
            session_id=state["session_id"],
            security_token=f"token_{state['trace_id']}"
        )
        
        completed = [r for r in results if r.get("success")]
        failed = [r for r in results if not r.get("success")]
        
        return {
            "completed_subtasks": completed,
            "failed_subtasks": failed,
            "subtask_results": {r["task_id"]: r for r in results},
            "execution_metrics": {
                "total_subtasks": len(results),
                "success_count": len(completed),
                "fail_count": len(failed),
                "success_rate": len(completed) / max(len(results), 1)
            }
        }
    
    async def _result_aggregator_node(self, state: SupervisorState) -> dict:
        """结果聚合节点 - 整合所有层的输出生成最终响应"""
        logger.info(f"[Aggregator][{state['trace_id']}] Aggregating results...")
        
        if state.get("needs_clarification") and state.get("clarification_question"):
            return {
                "final_response": state["clarification_question"],
                "response_type": "clarification_request",
                "metadata": {"requires_user_input": True}
            }
        
        if not all(state.get("security_decisions", {}).values()):
            denied_tasks = [
                tid for tid, allowed in state["security_decisions"].items() 
                if not allowed
            ]
            return {
                "final_response": f"部分操作因安全策略被拒绝: {', '.join(denied_tasks)}",
                "response_type": "error",
                "metadata": {"denied_tasks": denied_tasks, "security_blocked": True}
            }
        
        if state.get("subtask_results"):
            final_response = self._aggregate_results(state)
        else:
            final_response = self._generate_simple_response(state)
        
        return {
            "final_response": final_response,
            "response_type": "text",
            "timestamp_end": time.time(),
            "metadata": {
                "total_execution_time": time.time() - state["timestamp_start"],
                "subtasks_completed": len(state.get("completed_subtasks", [])),
                "intent": state.get("intent")
            }
        }
    
    def _aggregate_results(self, state: SupervisorState) -> str:
        """聚合子任务结果为最终响应"""
        results = state["subtask_results"]
        
        aggregated_parts = []
        for task_id, result in results.items():
            if result.get("success"):
                data = result.get("data")
                if isinstance(data, str):
                    aggregated_parts.append(data)
                elif isinstance(data, dict):
                    summary = data.get("summary", str(data))
                    aggregated_parts.append(summary)
        
        if aggregated_parts:
            return "\n\n".join(aggregated_parts)
        else:
            failed_count = len(state.get("failed_subtasks", []))
            return f"任务执行完成，但{failed_count}个子任务失败。请查看详细日志。"
    
    def _generate_simple_response(self, state: SupervisorState) -> str:
        """生成简单响应（无子任务分解的情况）"""
        intent = state.get("intent", "chat")
        query = state.get("optimized_query") or state.get("original_input", "")
        
        response_templates = {
            "chat": f"收到您的消息: {query}",
            "question_answering": f"正在为您查询关于'{query}'的信息...",
            "file_operation": f"文件操作请求已接收，正在处理..."
        }
        
        return response_templates.get(intent, f"已处理您的请求: {query}")
    
    # ==================== 条件路由函数 ====================
    
    def _route_after_optimization(self, state: SupervisorState) -> str:
        """查询优化后的路由决策"""
        if state.get("needs_clarification"):
            return "needs_clarification"
        return "proceed"
    
    def _route_after_security(self, state: SupervisorState) -> str:
        """安全检查后的路由决策"""
        decisions = state.get("security_decisions", {})
        if not decisions:
            return "approved"
        if all(decisions.values()):
            return "approved"
        return "denied"
