"""
Supervisor State Definitions - 状态类型定义
"""

from typing import TypedDict, List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class SupervisorState(TypedDict):
    """
    Supervisor全局状态 - 在LangGraph各节点间传递
    
    这是整个系统的"真相来源"(Single Source of Truth)，
    每个Layer读取前序状态并写入自己的输出。
    """
    
    user_id: str
    session_id: str
    original_input: str
    input_type: str
    
    intent: Optional[str]
    intent_confidence: float
    extracted_slots: Dict[str, Any]
    routing_decision: Optional[Dict[str, Any]]
    needs_clarification: bool
    clarification_question: Optional[str]
    
    optimized_query: Optional[str]
    query_rewrite_history: List[Dict[str, str]]
    expanded_entities: List[str]
    
    task_plan: Optional[Dict[str, Any]]
    subtasks: List[Dict[str, Any]]
    task_dag: Optional[Dict[str, List[str]]]
    estimated_duration_seconds: float
    resource_requirements: Dict[str, Any]
    
    current_batch: int
    total_batches: int
    completed_subtasks: List[Dict[str, Any]]
    failed_subtasks: List[Dict[str, Any]]
    subtask_results: Dict[str, Dict[str, Any]]
    execution_metrics: Dict[str, float]
    
    security_decisions: Dict[str, bool]
    audit_log_entries: List[Dict[str, Any]]
    sanitized_data: bool
    
    final_response: Optional[str]
    response_type: str
    metadata: Dict[str, Any]
    
    trace_id: str
    timestamp_start: float
    timestamp_end: Optional[float]
    conversation_context: Optional[Dict[str, Any]]


@dataclass
class RoutingDecision:
    """Layer 1 输出：路由决策"""
    intent: str
    confidence: float
    target_agent: str
    slots: Dict[str, Any] = field(default_factory=dict)
    alternative_agents: List[str] = field(default_factory=list)
    reasoning: str = ""
    needs_clarification: bool = False
    clarification_question: Optional[str] = None


@dataclass
class OptimizedQuery:
    """Layer 2 输出：优化后的查询"""
    rewritten_query: str
    original_query: str
    applied_transformations: List[str] = field(default_factory=list)
    context_used: List[str] = field(default_factory=list)
    expansion_terms: List[str] = field(default_factory=list)


@dataclass
class SubTaskDef:
    """子任务定义"""
    task_id: str
    agent_type: str
    action: str
    params: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[str] = field(default_factory=list)
    priority: int = 5
    timeout_seconds: float = 30.0
    retry_count: int = 0
    max_retries: int = 3
    status: TaskStatus = TaskStatus.PENDING


@dataclass
class TaskPlan:
    """Layer 3 输出：任务计划"""
    plan_id: str
    subtasks: List[SubTaskDef]
    dag_adjacency: Dict[str, List[str]]
    execution_strategy: str
    estimated_total_time: float
    required_capabilities: List[str]


@dataclass
class SecurityDecision:
    """Layer 5 输出：安全决策"""
    allowed: bool
    reason: str = ""
    risk_level: str = "low"
    required_approval: bool = False
    sanitized_action: Optional[Dict[str, Any]] = None
    audit_entry: Optional[Dict[str, Any]] = None
