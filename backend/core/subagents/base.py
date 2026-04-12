"""
Base SubAgent - 所有专业子代理的基类
强制实现标准化接口，确保与Supervisor的无缝协作
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, Type
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import time
import logging

logger = logging.getLogger(__name__)


class AgentHealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class AgentCapability:
    """Agent能力声明"""
    name: str
    description: str
    version: str = "1.0.0"
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)
    supported_intents: List[str] = field(default_factory=list)
    max_concurrent_tasks: int = 5
    estimated_latency_ms: int = 1000
    required_resources: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentExecutionContext:
    """SubAgent执行上下文 - 由Supervisor注入"""
    supervisor_id: str = ""
    session_id: str = ""
    trace_id: str = ""
    task_id: str = ""
    security_token: str = ""
    timeout_seconds: float = 30.0
    priority: int = 5


@dataclass
class AgentExecutionResult:
    """SubAgent执行结果"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    error_type: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    artifacts: List[Any] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    should_retry: bool = False
    retry_delay: float = 0.0


@dataclass
class AgentHealthCheckResult:
    """健康检查结果"""
    status: AgentHealthStatus
    agent_id: str
    uptime_seconds: float = 0
    tasks_completed: int = 0
    tasks_failed: int = 0
    average_latency_ms: float = 0
    queue_size: int = 0
    resource_usage: Dict[str, float] = field(default_factory=dict)
    last_error: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)


class BaseSubAgent(ABC):
    """
    SubAgent基类 - 所有专业Agent必须继承
    
    设计原则：
    1. 单一职责：每个Agent专注一个领域
    2. 接口标准化：统一的execute/health_check/validate接口
    3. 可观测性：内置指标收集和日志
    4. 弹性设计：支持超时、重试、降级
    
    使用示例：
        class MyAgent(BaseSubAgent):
            async def execute(self, task, context):
                # 实现业务逻辑
                return AgentExecutionResult(success=True, data=result)
            
            async def validate_input(self, task):
                return True, []
            
            async def health_check(self):
                return AgentHealthCheckResult(status=AgentHealthStatus.HEALTHY, ...)
    """
    
    def __init__(self, agent_id: str, capability: AgentCapability):
        self.agent_id = agent_id
        self.capability = capability
        self.state = "idle"
        self._start_time = time.time()
        self._execution_history: List[Dict[str, Any]] = []
        self._lock = asyncio.Lock()
        
        logger.info(f"[{agent_id}] Initialized - {capability.name} v{capability.version}")
    
    @abstractmethod
    async def execute(
        self,
        task: Dict[str, Any],
        context: AgentExecutionContext
    ) -> AgentExecutionResult:
        """
        执行任务的核心方法 - 必须由子类实现
        
        Args:
            task: 任务参数字典
            context: 执行上下文（含认证、超时、监控等）
            
        Returns:
            AgentExecutionResult: 执行结果
        """
        pass
    
    @abstractmethod
    async def validate_input(self, task: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        验证输入参数的有效性
        
        Returns:
            (is_valid, error_messages)
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> AgentHealthCheckResult:
        """返回Agent的健康状态"""
        pass
    
    def get_supported_intents(self) -> List[str]:
        return self.capability.supported_intents
    
    def get_capability(self) -> AgentCapability:
        return self.capability
    
    async def safe_execute(
        self,
        task: Dict[str, Any],
        context: AgentExecutionContext
    ) -> AgentExecutionResult:
        """
        安全执行包装器 - 提供超时、日志、错误处理
        
        这是Supervisor调用的入口方法。
        """
        start_time = time.time()
        exec_id = f"{context.trace_id}_{context.task_id}"
        
        logger.info(f"[{self.agent_id}] Starting execution {exec_id}")
        
        try:
            is_valid, errors = await self.validate_input(task)
            if not is_valid:
                return AgentExecutionResult(
                    success=False,
                    error=f"Validation failed: {'; '.join(errors)}",
                    error_type="invalid_input",
                    metrics={"validation_time_ms": (time.time() - start_time) * 1000}
                )
            
            result = await asyncio.wait_for(
                self.execute(task, context),
                timeout=context.timeout_seconds
            )
            
            duration_ms = (time.time() - start_time) * 1000
            self._record_execution(True, duration_ms)
            
            result.metrics.update({
                "total_time_ms": duration_ms,
                "exec_id": exec_id
            })
            
            logger.info(f"[{self.agent_id}] Execution {exec_id} completed in {duration_ms:.0f}ms")
            return result
            
        except asyncio.TimeoutError:
            duration_ms = (time.time() - start_time) * 1000
            self._record_execution(False, duration_ms, "timeout")
            
            logger.warning(f"[{self.agent_id}] Execution {exec_id} timed out after {context.timeout_seconds}s")
            return AgentExecutionResult(
                success=False,
                error=f"Timeout after {context.timeout_seconds:.1f}s",
                error_type="timeout",
                should_retry=True,
                retry_delay=1.0,
                metrics={"total_time_ms": duration_ms}
            )
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            error_msg = str(e)
            error_type = type(e).__name__
            
            self._record_execution(False, duration_ms, error_msg)
            
            logger.error(f"[{self.agent_id}] Execution {exec_id} failed: {error_msg}", exc_info=True)
            return AgentExecutionResult(
                success=False,
                error=error_msg,
                error_type=error_type,
                should_retry=self._should_retry(error_type),
                retry_delay=self._get_retry_delay(error_type),
                metrics={"total_time_ms": duration_ms}
            )
    
    def _record_execution(self, success: bool, duration_ms: float, error: str = ""):
        record = {
            "timestamp": time.time(),
            "success": success,
            "duration_ms": duration_ms,
            "error": error[:200]
        }
        self._execution_history.append(record)
        
        if len(self._execution_history) > 1000:
            self._execution_history = self._execution_history[-1000:]
    
    def _should_retry(self, error_type: str) -> bool:
        retryable = {"timeout", "connection_error", "rate_limit", "temporary_failure"}
        return error_type.lower() in retryable
    
    def _get_retry_delay(self, error_type: str) -> float:
        delays = {
            "timeout": 2.0,
            "rate_limit": 5.0,
            "connection_error": 1.0,
            "temporary_failure": 1.0
        }
        return delays.get(error_type.lower(), 2.0)
    
    async def get_statistics(self) -> Dict[str, Any]:
        if not self._execution_history:
            return {
                "total_executions": 0,
                "success_rate": 0,
                "avg_latency_ms": 0,
                "error_distribution": {}
            }
        
        total = len(self._execution_history)
        successful = sum(1 for r in self._execution_history if r["success"])
        avg_latency = sum(r["duration_ms"] for r in self._execution_history) / total
        
        error_dist: Dict[str, int] = {}
        for r in self._execution_history:
            if not r["success"]:
                err = r.get("error", "unknown")[:50]
                error_dist[err] = error_dist.get(err, 0) + 1
        
        return {
            "agent_id": self.agent_id,
            "total_executions": total,
            "success_rate": successful / total,
            "avg_latency_ms": avg_latency,
            "error_distribution": error_dist,
            "uptime_seconds": time.time() - self._start_time
        }
