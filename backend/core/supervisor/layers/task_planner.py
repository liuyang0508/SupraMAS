"""
Layer 3: Task Planner - 任务分解与规划
负责：任务分解、依赖分析、DAG构建、资源预估
"""

import uuid
import logging
from typing import Dict, Any, List, Optional
from collections import defaultdict

from ..state import TaskPlan, SubTaskDef, RoutingDecision

logger = logging.getLogger(__name__)


class TaskPlanner:
    """
    Layer 3: 任务规划器
    
    职责：
    1. 任务分解 (Task Decomposition) - 将复杂任务拆解为子任务
    2. 依赖分析 (Dependency Analysis) - 确定子任务间的依赖关系
    3. DAG构建 (DAG Construction) - 构建有向无环图表示执行顺序
    4. 资源预估 (Resource Estimation) - 预估所需资源和时间
    
    分解策略：
    - 基于意图的模板分解（快速、确定性）
    - LLM驱动的智能分解（灵活、可适应新场景）
    """
    
    TASK_TEMPLATES = {
        "chat": {
            "subtasks": [],
            "strategy": "none"
        },
        "skill_execution": {
            "subtasks": [
                {"agent_type": "skill", "action": "execute_skill", "params_source": "query"}
            ],
            "strategy": "serial"
        },
        "question_answering": {
            "subtasks": [
                {"agent_type": "rag", "action": "retrieve", "params_source": "query"},
                {"agent_type": "rag", "action": "generate_answer", "params_source": "query", "depends_on": [0]}
            ],
            "strategy": "serial"
        },
        "ecommerce_operation": {
            "subtasks": [
                {"agent_type": "rag", "action": "market_research", "params_source": "query", "depends_on": []},
                {"agent_type": "rag", "action": "synthesize_answer", "params_source": "query", "depends_on": [0]}
            ],
            "strategy": "serial"
        },
        "file_operation": {
            "subtasks": [
                {"agent_type": "file", "action": "read_file", "params_source": "slots"},
                {"agent_type": "file", "action": "modify_content", "depends_on": [0]},
                {"agent_type": "file", "action": "create_snapshot", "depends_on": [1]}
            ],
            "strategy": "serial"
        },
        "data_analysis": {
            "subtasks": [
                {"agent_type": "rag", "action": "retrieve_data", "params_source": "query"},
                {"agent_type": "mcp", "action": "query_database", "params_source": "slots"},
                {"agent_type": "skill", "action": "analyze_data", "depends_on": [0, 1]},
                {"agent_type": "file", "action": "generate_report", "depends_on": [2]},
                {"agent_type": "skill", "action": "generate_charts", "depends_on": [2]}
            ],
            "strategy": "mixed"
        },
        "design_work": {
            "subtasks": [
                {"agent_type": "intent", "action": "extract_requirements", "params_source": "input"},
                {"agent_type": "rag", "action": "retrieve_design_references", "depends_on": [0]},
                {"agent_type": "skill", "action": "analyze_requirements", "depends_on": [0]},
                {"agent_type": "skill", "action": "generate_design_drafts", "depends_on": [0, 1, 2], "count": 3},
                {"agent_type": "file", "action": "save_design_files", "depends_on": [3]}
            ],
            "strategy": "mixed"
        }
    }
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.max_task_depth = config.get("max_task_depth", 3)
    
    async def plan(
        self,
        query: str,
        intent: Optional[str] = None,
        slots: Optional[Dict[str, Any]] = None,
        routing_decision: Optional[Dict[str, Any]] = None
    ) -> TaskPlan:
        """
        执行任务规划
        
        Args:
            query: 优化后的查询
            intent: 意图
            slots: 槽位信息
            routing_decision: 路由决策
            
        Returns:
            TaskPlan: 任务计划（含DAG）
        """
        plan_id = f"plan_{uuid.uuid4().hex[:8]}"
        
        if intent and intent in self.TASK_TEMPLATES:
            task_plan = self._plan_from_template(intent, query, slots)
        else:
            task_plan = await self._plan_with_llm(query, intent, slots)
        
        task_plan.plan_id = plan_id
        
        logger.info(f"[TaskPlanner] Created plan {plan_id} with {len(task_plan.subtasks)} subtasks")
        
        return task_plan
    
    def _plan_from_template(self, intent: str, query: str, slots: Optional[Dict]) -> TaskPlan:
        """基于模板的任务规划"""
        template = self.TASK_TEMPLATES[intent]
        
        subtasks = []
        for idx, task_def in enumerate(template["subtasks"]):
            params = self._resolve_params(task_def.get("params_source"), query, slots)
            
            subtask = SubTaskDef(
                task_id=f"st_{idx+1:03d}",
                agent_type=task_def["agent_type"],
                action=task_def["action"],
                params=params,
                depends_on=[
                    f"st_{dep+1:03d}" 
                    for dep in task_def.get("depends_on", [])
                ],
                status="pending"
            )
            
            # 如果有count参数，生成多个实例
            count = task_def.get("count", 1)
            if count > 1:
                base_task = subtask
                subtasks.append(base_task)
                for i in range(1, count):
                    variant = SubTaskDef(
                        task_id=f"st_{idx+1:03d}_v{i}",
                        agent_type=base_task.agent_type,
                        action=base_task.action,
                        params={**base_task.params, "variant": i + 1},
                        depends_on=base_task.depends_on.copy(),
                        status="pending"
                    )
                    subtasks.append(variant)
            else:
                subtasks.append(subtask)
        
        dag_adjacency = self._build_dag_from_subtasks(subtasks)
        
        return TaskPlan(
            plan_id=plan_id,
            subtasks=subtasks,
            dag_adjacency=dag_adjacency,
            execution_strategy=template["strategy"],
            estimated_total_time=self._estimate_time(subtasks),
            required_capabilities=list(set(st.agent_type for st in subtasks))
        )
    
    async def _plan_with_llm(self, query: str, intent: Optional[str], slots: Optional[Dict]) -> TaskPlan:
        """基于LLM的智能任务规划"""
        # TODO: 集成LLM调用进行动态任务分解
        # 目前回退到通用模板
        logger.warning("[TaskPlanner] LLM-based planning not yet implemented, using generic template")
        
        generic_subtasks = [
            SubTaskDef(
                task_id="st_001",
                agent_type="rag",
                action="general_query",
                params={"query": query}
            ),
            SubTaskDef(
                task_id="st_002",
                agent_type="rag",
                action="synthesize_answer",
                params={},
                depends_on=["st_001"]
            )
        ]
        
        return TaskPlan(
            plan_id=plan_id,
            subtasks=generic_subtasks,
            dag_adjacency={"st_002": ["st_001"]},
            execution_strategy="serial",
            estimated_total_time=5.0,
            required_capabilities=["rag"]
        )
    
    def _resolve_params(self, source: Optional[str], query: str, slots: Optional[Dict]) -> Dict[str, Any]:
        """解析任务参数来源"""
        params = {}
        
        if source == "query":
            params["query"] = query
        elif source == "slots":
            params.update(slots or {})
        elif source == "input":
            params["input"] = query
        else:
            params["query"] = query
        
        return params
    
    def _build_dag_from_subtasks(self, subtasks: List[SubTaskDef]) -> Dict[str, List[str]]:
        """从子任务列表构建DAG邻接表"""
        dag = defaultdict(list)
        
        for subtask in subtasks:
            for dep_id in subtask.depends_on:
                dag[dep_id].append(subtask.task_id)
        
        return dict(dag)
    
    def _estimate_time(self, subtasks: List[SubTaskDef]) -> float:
        """预估总执行时间（秒）"""
        time_estimates = {
            ("rag", "retrieve"): 1.0,
            ("rag", "generate_answer"): 2.0,
            ("mcp", "search_supplier"): 3.0,
            ("file", "read_file"): 0.5,
            ("file", "modify_content"): 1.0,
            ("file", "create_snapshot"): 0.3,
            ("skill", "generate_listing"): 5.0,
            ("skill", "generate_marketing_copy"): 3.0,
            ("intent", "extract_requirements"): 1.0,
        }
        
        total_time = sum(
            time_estimates.get((st.agent_type, st.action), 2.0)
            for st in subtasks
        )
        
        return total_time


# 模块级变量，供其他模块引用
plan_id = ""
