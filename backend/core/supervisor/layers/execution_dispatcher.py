"""
Layer 4: Execution Dispatcher - 执行调度器
负责：智能调度、并行/串行执行、进度监控、错误处理、动态重规划
"""

import asyncio
import time
import logging
from typing import Dict, Any, List, Optional
from collections import deque

logger = logging.getLogger(__name__)


class ExecutionDispatcher:
    """
    Layer 4: 执行调度器
    
    职责：
    1. 智能调度 (Intelligent Scheduling) - 基于能力匹配和负载均衡
    2. 并行/串行执行 (Parallel/Serial Execution)
    3. 进度监控 (Progress Monitoring)
    4. 错误处理与重试 (Error Handling & Retry)
    5. 动态重规划 (Dynamic Replanning)
    
    调度策略：
    - round_robin: 轮询分配
    - load_balanced: 负载感知分配
    - intelligent: 综合评分（能力匹配+负载+历史表现）
    """
    
    def __init__(self, config: Dict[str, Any], agent_pool: Dict[str, Any]):
        self.config = config
        self.agent_pool = agent_pool
        
        self.scheduling_strategy = config.get("scheduling_strategy", "intelligent")
        self.enable_parallel = config.get("enable_parallel_execution", True)
        self.max_parallel = config.get("max_parallel_subtasks", 5)
        self.max_retries = config.get("retry_max_attempts", 3)
        self.retry_backoff_base = config.get("retry_backoff_base", 1.0)
        
        # 熔断器状态
        self._circuit_breaker_state: Dict[str, str] = {}  # agent_id -> closed/open/half_open
        self._circuit_breaker_failures: Dict[str, int] = {}
    
    async def dispatch(
        self,
        subtasks: List[Dict[str, Any]],
        task_dag: Optional[Dict[str, List[str]]] = None,
        trace_id: str = "",
        user_id: str = "",
        session_id: str = "",
        security_token: str = ""
    ) -> List[Dict[str, Any]]:
        """
        调度和执行子任务
        
        Args:
            subtasks: 子任务列表
            task_dag: DAG邻接表
            trace_id: 追踪ID
            user_id: 用户ID
            session_id: 会话ID
            security_token: 安全令牌
            
        Returns:
            List[Dict]: 每个子任务的执行结果
        """
        if not subtasks:
            return []
        
        logger.info(f"[Dispatcher][{trace_id}] Dispatching {len(subtasks)} subtasks...")
        
        start_time = time.time()
        
        # 构建执行计划（考虑DAG依赖）
        execution_batches = self._build_execution_batches(subtasks, task_dag)
        
        all_results = []
        
        for batch_idx, batch in enumerate(execution_batches):
            logger.debug(f"[Dispatcher][{trace_id}] Executing batch {batch_idx + 1}/{len(execution_batches)} ({len(batch)} tasks)")
            
            batch_results = await self._execute_batch(
                batch=batch,
                trace_id=trace_id,
                user_id=user_id,
                session_id=session_id,
                security_token=security_token
            )
            
            all_results.extend(batch_results)
            
            # 检查是否需要重规划（关键任务失败）
            failed_critical = [r for r in batch_results if not r.get("success") and r.get("is_critical")]
            if failed_critical and self.config.get("enable_dynamic_replanning", False):
                logger.warning(f"[Dispatcher][{trace_id}] Critical tasks failed, attempting replan")
                replanned_results = await self._attempt_replan(failed_critical, trace_id)
                all_results.extend(replanned_results)
        
        total_time = time.time() - start_time
        logger.info(f"[Dispatcher][{trace_id}] All batches completed in {total_time:.2f}s ({len(all_results)} results)")
        
        return all_results
    
    def _build_execution_batches(self, subtasks: List[Dict], dag: Optional[Dict]) -> List[List[Dict]]:
        """根据DAG构建执行批次"""
        if not dag or self.scheduling_strategy == "round_robin":
            return [subtasks]
        
        # 计算每个任务的入度
        in_degree = {st["task_id"]: 0 for st in subtasks}
        for task_id, dependencies in dag.items():
            for dep in dependencies:
                if dep in in_degree:
                    pass  # dep is a prerequisite
        
        # 拓扑排序构建批次
        completed = set()
        batches = []
        remaining = [st.copy() for st in subtasks]
        
        while remaining:
            batch = []
            still_remaining = []
            
            for task in remaining:
                deps = task.get("depends_on", [])
                can_execute = all(dep in completed for dep in deps)
                
                if can_execute:
                    batch.append(task)
                else:
                    still_remaining.append(task)
            
            if not batch and still_remaining:
                logger.warning("Circular dependency detected, forcing execution")
                batch = still_remaining[:self.max_parallel]
                still_remaining = still_remaining[self.max_parallel:]
            
            batches.append(batch)
            completed.update(st["task_id"] for st in batch)
            remaining = still_remaining
            
            if len(batches) > 20:
                logger.error("Too many batches, possible infinite loop")
                break
        
        return batches
    
    async def _execute_batch(
        self,
        batch: List[Dict],
        trace_id: str,
        user_id: str,
        session_id: str,
        security_token: str
    ) -> List[Dict[str, Any]]:
        """执行一批任务"""
        if len(batch) == 1 or not self.enable_parallel:
            results = []
            for task in batch:
                result = await self._execute_single_task(task, trace_id, user_id, session_id, security_token)
                results.append(result)
            return results
        
        # 并行执行
        tasks = [
            self._execute_single_task(task, trace_id, user_id, session_id, security_token)
            for task in batch[:self.max_parallel]
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "task_id": batch[i]["task_id"],
                    "success": False,
                    "error": str(result),
                    "error_type": "execution_error"
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def _execute_single_task(
        self,
        task: Dict[str, Any],
        trace_id: str,
        user_id: str,
        session_id: str,
        security_token: str
    ) -> Dict[str, Any]:
        """执行单个子任务"""
        task_id = task["task_id"]
        agent_type = task["agent_type"]
        action = task["action"]
        params = task.get("params", {})
        
        start_time = time.time()
        
        logger.info(f"[Dispatcher][{trace_id}] Executing {task_id} on {agent_type}.{action}")
        
        # 检查熔断器
        if self._is_circuit_open(agent_type):
            return {
                "task_id": task_id,
                "success": False,
                "error": f"Circuit breaker open for {agent_type}",
                "error_type": "circuit_breaker",
                "duration_ms": 0
            }
        
        # 获取Agent实例
        agent = self.agent_pool.get(agent_type)
        if not agent:
            error_msg = f"Agent type '{agent_type}' not found in pool"
            logger.error(f"[Dispatcher][{trace_id}] {error_msg}")
            self._record_failure(agent_type)
            return {
                "task_id": task_id,
                "success": False,
                "error": error_msg,
                "error_type": "agent_not_found",
                "duration_ms": (time.time() - start_time) * 1000
            }
        
        # 构建执行上下文
        from ..supervisor.state import AgentExecutionContext
        context = AgentExecutionContext(
            supervisor_id="wukong-supervisor-1",
            session_id=session_id,
            trace_id=trace_id,
            task_id=task_id,
            security_token=security_token,
            timeout_seconds=task.get("timeout_seconds", 30.0),
            priority=task.get("priority", 5)
        )
        
        # 执行任务（带重试）
        result = None
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                if hasattr(agent, 'safe_execute'):
                    result = await agent.safe_execute(params, context)
                elif hasattr(agent, 'execute'):
                    result = await agent.execute(params, context)
                else:
                    raise NotImplementedError(f"Agent {agent_type} has no execute method")
                
                if result.success:
                    self._record_success(agent_type)
                    break
                else:
                    last_error = result.error
                    if result.should_retry and attempt < self.max_retries:
                        delay = result.retry_delay * (attempt + 1)
                        await asyncio.sleep(delay)
                        continue
                    
            except Exception as e:
                last_error = str(e)
                if attempt < self.max_retries:
                    delay = self.retry_backoff_base * (2 ** attempt)
                    await asyncio.sleep(delay)
                    continue
        
        duration_ms = (time.time() - start_time) * 1000
        
        if result and result.success:
            return {
                "task_id": task_id,
                "success": True,
                "data": result.data,
                "metrics": result.metrics,
                "artifacts": result.artifacts,
                "duration_ms": duration_ms,
                "attempts": attempt + 1
            }
        else:
            self._record_failure(agent_type)
            return {
                "task_id": task_id,
                "success": False,
                "error": last_error or "Unknown error",
                "error_type": "execution_failed",
                "duration_ms": duration_ms,
                "attempts": attempt + 1
            }
    
    def _is_circuit_open(self, agent_type: str) -> bool:
        """检查熔断器是否开启"""
        state = self._circuit_breaker_state.get(agent_type, "closed")
        return state == "open"
    
    def _record_success(self, agent_type: str):
        """记录成功，可能关闭熔断器"""
        if agent_type in self._circuit_breaker_failures:
            del self._circuit_breaker_failures[agent_type]
        self._circuit_breaker_state[agent_type] = "closed"
    
    def _record_failure(self, agent_type: str):
        """记录失败，可能开启熔断器"""
        self._circuit_breaker_failures[agent_type] = self._circuit_breaker_failures.get(agent_type, 0) + 1
        
        threshold = self.config.get("circuit_breaker_threshold", 5)
        if self._circuit_breaker_failures[agent_type] >= threshold:
            self._circuit_breaker_state[agent_type] = "open"
            logger.warning(f"[Dispatcher] Circuit breaker OPENED for {agent_type} after {threshold} failures")
    
    async def _attempt_replan(self, failed_tasks: List[Dict], trace_id: str) -> List[Dict]:
        """尝试重新规划失败的任务"""
        # TODO: 实现智能重规划逻辑
        logger.info(f"[Dispatcher][{trace_id}] Replan attempted for {len(failed_tasks)} tasks")
        return []
