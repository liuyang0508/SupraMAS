"""
Domain Agent - 业务领域专家型子代理基类

核心理念：
- DomainAgent 是真正的"业务专家"，代表一个垂直领域的专业能力
- 每个 DomainAgent 由一组 Skill 组成，Skill 定义了该领域的专业工作流
- DomainAgent 可以调用 Infrastructure Agents (RAG/File/MCP) 来完成基础操作
- DomainAgent 的能力边界由其 Skill 生态决定，可动态扩展

架构关系：
    Supervisor
        ↓
   ┌────┴────┐
   │ Domain   │ ← 业务决策层（电商/设计/财税/开发...）
   │ Agents  │
   └────┬────┘
        ↓ 调用
   ┌────┴────┐
   │ Infra    │ ← 基础能力层（RAG/File/MCP/Intent...）
   │ Agents  │
   └─────────┘
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple, Type
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import logging
import time

from ..base import (
    BaseSubAgent, 
    AgentCapability, 
    AgentExecutionContext, 
    AgentExecutionResult,
    AgentHealthCheckResult,
    AgentHealthStatus
)

logger = logging.getLogger(__name__)


@dataclass
class DomainCapability:
    """
    领域能力声明 - 比通用AgentCapability更丰富

    包含业务语义信息，不仅仅是技术参数
    """
    domain_name: str                    # 领域名称: "ecommerce", "design", "finance"
    display_name: str                   # 显示名称: "电商运营专家"
    version: str = "1.0.0"

    # 领域专长描述
    expertise_areas: List[str] = field(default_factory=list)  # ["选品分析", "价格策略", "Listing优化"]
    typical_tasks: List[str] = field(default_factory=list)     # ["市场调研", "竞品分析", "营销文案"]

    # 技术规格
    supported_intents: List[str] = field(default_factory=list)
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)

    # 性能特征
    max_concurrent_tasks: int = 5
    estimated_latency_ms: int = 2000      # DomainAgent通常比InfraAgent慢(涉及多步骤)
    required_infra_agents: List[str] = field(default_factory=list)  # ["rag", "file", "mcp"]

    # 元数据
    author: str = "Wukong Team"
    category: str = "general"
    tags: List[str] = field(default_factory=list)
    rating: float = 0.0
    install_count: int = 0

    # Agent name for compatibility with BaseSubAgent
    name: str = ""

    def __post_init__(self):
        """Auto-populate name from display_name if not set"""
        if not self.name:
            self.name = self.display_name


@dataclass
class SkillBinding:
    """技能绑定 - DomainAgent如何使用某个Skill"""
    skill_id: str
    alias: str                          # 在Domain内的别名: "price_analyzer"
    trigger_conditions: List[Dict] = field(default_factory=list)  # 触发条件
    default_params: Dict[str, Any] = field(default_factory=dict)  # 默认参数模板
    is_required: bool = False           # 是否是该Domain的核心Skill
    priority: int = 5                  # 优先级(1-10)


@dataclass
class DomainWorkflow:
    """
    领域工作流定义

    DomainAgent的核心是工作流编排能力，
    它知道如何将复杂任务分解为Skill调用序列
    """
    workflow_id: str
    name: str                           # "amazon_product_research"
    description: str = ""               # "完整的亚马逊产品研究流程"

    # 工作流步骤 (DAG)
    steps: List[Dict[str, Any]] = field(default_factory=list)
    # [
    #   {
    #     "step_id": "step_1",
    #     "skill_alias": "market_researcher",
    #     "action": "analyze_trends",
    #     "params_mapping": {"query": "$input.category"},
    #     "depends_on": [],
    #     "timeout": 30
    #   },
    #   ...
    # ]
    
    # 输入/输出映射
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)
    
    # 执行策略
    execution_strategy: str = "auto"   # auto, sequential, parallel, adaptive
    estimated_duration_sec: float = 60.0
    
    # 版本与状态
    version: str = "1.0"
    status: str = "active"


@dataclass
class DomainExecutionResult(AgentExecutionResult):
    """DomainAgent执行结果 - 包含更多业务上下文"""
    domain: str = ""
    workflow_used: Optional[str] = None
    skills_invoked: List[str] = field(default_factory=list)
    intermediate_results: Dict[str, Any] = field(default_factory=dict)
    business_insights: List[str] = field(default_factory=list)
    next_suggested_actions: List[str] = field(default_factory=list)


class BaseDomainAgent(BaseSubAgent, ABC):
    """
    业务领域专家型子代理基类
    
    与Infrastructure Agent的区别：
    1. **业务导向**：理解业务语义，而非仅仅执行技术操作
    2. **工作流驱动**：内置领域最佳实践的工作流
    3. **Skill编排**：组合多个Skill完成复杂任务
    4. **Infra代理用**：通过调用RAG/File等基础Agent获取数据
    5. **可扩展**：通过安装新Skill来扩展能力
    
    设计模式：Strategy + Template Method
    - 子类定义领域知识和工作流
    - 基类提供通用的Skill调度和结果聚合逻辑
    """
    
    def __init__(self, agent_id: str, capability: DomainCapability):
        super().__init__(agent_id, capability)
        
        self.domain_capability = capability
        
        # Skill注册表 {alias: SkillBinding}
        self._skill_bindings: Dict[str, SkillBinding] = {}
        
        # 工作流注册表 {workflow_id: DomainWorkflow}
        self._workflows: Dict[str, DomainWorkflow] = {}
        
        # 基础设施Agent引用 (由Supervisor注入)
        self._infra_agents: Dict[str, BaseSubAgent] = {}
        
        # 领域知识库引用
        self._knowledge_base_id: Optional[str] = None
        
        logger.info(f"[{agent_id}] DomainAgent initialized for domain: {capability.domain_name}")
    
    def bind_skill(self, binding: SkillBinding):
        """绑定一个Skill到这个Domain"""
        self._skill_bindings[binding.alias] = binding
        logger.debug(f"[{self.agent_id}] Bound skill: {binding.skill_id} as '{binding.alias}'")
    
    def register_workflow(self, workflow: DomainWorkflow):
        """注册一个领域工作流"""
        self._workflows[workflow.workflow_id] = workflow
        logger.info(f"[{self.agent_id}] Registered workflow: {workflow.name}")
    
    def set_infra_agents(self, agents: Dict[str, BaseSubAgent]):
        """设置基础设施Agent引用（由Supervisor在初始化时注入）"""
        self._infra_agents = agents
        required = set(self.domain_capability.required_infra_agents)
        available = set(agents.keys())
        missing = required - available
        if missing:
            logger.warning(f"[{self.agent_id}] Missing required infra agents: {missing}")
    
    @abstractmethod
    async def plan_workflow(
        self, 
        task: Dict[str, Any], 
        context: AgentExecutionContext
    ) -> Optional[DomainWorkflow]:
        """
        根据任务选择或生成合适的工作流
        
        这是DomainAgent的"智能"所在 - 它知道如何将模糊的业务需求
        映射到具体的工作流步骤
        """
        pass
    
    @abstractmethod
    async def synthesize_result(
        self,
        workflow: DomainWorkflow,
        step_results: Dict[str, Any],
        original_task: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        综合各步骤结果，生成领域专业的最终输出
        
        这里可以加入领域知识、行业best practice等
        """
        pass
    
    async def execute(self, task: Dict[str, Any], context: AgentExecutionContext) -> DomainExecutionResult:
        """
        DomainAgent的主执行方法
        
        流程：
        1. 理解任务意图 → 选择工作流
        2. 分解为Skill调用步骤
        3. 依次/并行执行各步骤（可能调用Infra Agent）
        4. 综合结果并添加业务洞察
        5. 返回结构化的领域结果
        """
        start_time = time.time()
        
        domain = self.domain_capability.domain_name
        logger.info(f"[{self.agent_id}][{domain}] Executing task: {str(task)[:80]}...")
        
        try:
            # Step 1: 选择工作流
            workflow = await self.plan_workflow(task, context)
            
            if not workflow:
                return DomainExecutionResult(
                    success=False,
                    error=f"No suitable workflow found for task in domain '{domain}'",
                    error_type="workflow_not_found",
                    should_retry=False,
                    domain=domain
                )
            
            logger.info(f"[{self.agent_id}] Using workflow: {workflow.name} ({len(workflow.steps)} steps)")
            
            # Step 2 & 3: 执行工作流步骤
            step_results = await self._execute_workflow_steps(workflow, task, context)
            
            # Step 4: 综合结果
            final_output = await self.synthesize_result(workflow, step_results, task)
            
            # Step 5: 生成业务洞察和建议
            insights = await self._generate_business_insights(final_output, task)
            suggestions = await self._suggest_next_actions(final_output, task)
            
            execution_time = time.time() - start_time
            
            return DomainExecutionResult(
                success=True,
                data=final_output,
                domain=domain,
                workflow_used=workflow.workflow_id,
                skills_invoked=self._extract_invoked_skills(step_results),
                intermediate_results=step_results,
                business_insights=insights,
                next_suggested_actions=suggestions,
                metrics={
                    "total_time_sec": execution_time,
                    "steps_executed": len(step_results),
                    "workflow": workflow.name,
                    **self._calculate_step_metrics(step_results)
                }
            )
            
        except Exception as e:
            logger.error(f"[{self.agent_id}] Execution error: {e}", exc_info=True)
            return DomainExecutionResult(
                success=False,
                error=str(e),
                error_type="domain_execution_error",
                should_retry=self._should_retry_domain_error(str(e)),
                retry_delay=2.0,
                domain=domain,
                metrics={"total_time_sec": time.time() - start_time}
            )
    
    async def _execute_workflow_steps(
        self,
        workflow: DomainWorkflow,
        task: Dict[str, Any],
        context: AgentExecutionContext
    ) -> Dict[str, Any]:
        """执行工作流的所有步骤"""
        results = {}
        
        if workflow.execution_strategy == "parallel":
            results = await self._execute_parallel(workflow, task, context)
        elif workflow.execution_strategy == "sequential":
            results = await self._execute_sequential(workflow, task, context)
        else:
            results = await self._execute_adaptive(workflow, task, context)
        
        return results
    
    async def _execute_sequential(
        self, workflow: DomainWorkflow, task: Dict, context: AgentExecutionContext
    ) -> Dict:
        """串行执行步骤"""
        results = {}
        
        for step in workflow.steps:
            step_id = step["step_id"]
            
            # 检查依赖是否满足
            deps = step.get("depends_on", [])
            if not all(dep in results for dep in deps):
                results[step_id] = {"error": f"Dependency not met: {deps}", "status": "skipped"}
                continue
            
            try:
                step_result = await self._execute_single_step(step, task, results, context)
                results[step_id] = {"data": step_result, "status": "success"}
                
            except Exception as e:
                results[step_id] = {"error": str(e), "status": "failed"}
                if step.get("required", True):
                    break  # 关键步骤失败，终止工作流
        
        return results
    
    async def _execute_parallel(
        self, workflow: DomainWorkflow, task: Dict, context: AgentExecutionContext
    ) -> Dict:
        """并行执行无依赖关系的步骤"""
        import asyncio
        
        results = {}
        
        # 找出所有无依赖的步骤（第一层）
        ready_steps = [s for s in workflow.steps if not s.get("depends_on")]
        
        tasks = [
            self._execute_single_step(s, task, {}, context)
            for s in ready_steps
        ]
        
        parallel_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for step, result in zip(ready_steps, parallel_results):
            if isinstance(result, Exception):
                results[step["step_id"]] = {"error": str(result), "status": "failed"}
            else:
                results[step["step_id"]] = {"data": result, "status": "success"}
        
        return results
    
    async def _execute_adaptive(
        self, workflow: DomainWorkflow, task: Dict, context: AgentExecutionContext
    ) -> Dict:
        """自适应执行：根据中间结果动态调整"""
        # 先尝试并行执行无依赖步骤
        results = await self._execute_parallel(workflow, task, context)
        
        # 然后串行处理有依赖的步骤
        remaining_steps = [s for s in workflow.steps if s["step_id"] not in results]
        
        for step in remaining_steps:
            if all(dep in results and results[dep].get("status") == "success" 
                   for dep in step.get("depends_on", [])):
                try:
                    result = await self._execute_single_step(step, task, results, context)
                    results[step["step_id"]] = {"data": result, "status": "success"}
                except Exception as e:
                    results[step["step_id"]] = {"error": str(e), "status": "failed"}
        
        return results
    
    async def _execute_single_step(
        self, step: Dict, original_task: Dict, previous_results: Dict, context: AgentExecutionContext
    ) -> Any:
        """执行单个工作流步骤"""
        skill_alias = step.get("skill_alias")
        action = step.get("action")
        
        # 解析参数（支持从输入和前序结果中提取）
        params = self._resolve_params(step.get("params_mapping", {}), original_task, previous_results)
        
        # 合并默认参数
        if skill_alias and skill_alias in self._skill_bindings:
            params = {**self._skill_bindings[skill_alias].default_params, **params}
        
        # 调用Skill（通过Skill Agent）或直接调用Infra Agent
        if skill_alias and skill_alias in self._skill_bindings:
            skill_binding = self._skill_bindings[skill_alias]
            result = await self._invoke_skill(skill_binding, action, params, context)
        else:
            # 可能是直接调用Infra Agent
            result = await self._invoke_infra_agent(action, params, context)
        
        return result
    
    async def _invoke_skill(
        self, 
        binding: SkillBinding, 
        action: str, 
        params: Dict, 
        context: AgentExecutionContext
    ) -> Any:
        """调用绑定的Skill"""
        skill_agent = self._infra_agents.get("skill")
        if not skill_agent:
            raise RuntimeError(f"Skill agent not available for invoking {binding.skill_id}")
        
        skill_task = {
            "skill_name": binding.skill_id,
            "action": action,
            "params": params
        }
        
        result = await skill_agent.safe_execute(skill_task, context)
        
        if not result.success:
            raise RuntimeError(f"Skill {binding.skill_id}.{action} failed: {result.error}")
        
        return result.data
    
    async def _invoke_infra_agent(
        self, 
        agent_type: str, 
        params: Dict, 
        context: AgentExecutionContext
    ) -> Any:
        """调用基础设施Agent"""
        agent = self._infra_agents.get(agent_type)
        if not agent:
            raise RuntimeError(f"Infra agent '{agent_type}' not available")
        
        result = await agent.safe_execute(params, context)
        
        if not result.success:
            raise RuntimeError(f"Infra agent {agent_type} failed: {result.error}")
        
        return result.data
    
    def _resolve_params(
        self, 
        mapping: Dict, 
        original_task: Dict, 
        previous_results: Dict
    ) -> Dict:
        """解析参数映射（支持变量替换）"""
        resolved = {}
        
        for key, value_template in mapping.items():
            if isinstance(value_template, str):
                # 支持变量引用: $input.xxx, $step_xxx.yyy
                if value_template.startswith("$input."):
                    field = value_template[7:]
                    resolved[key] = original_task.get(field, value_template)
                elif value_template.startswith("$step_"):
                    parts = value_template.split(".")
                    step_ref = parts[0]
                    field = ".".join(parts[1:]) if len(parts) > 1 else "data"
                    
                    if step_ref in previous_results:
                        step_data = previous_results[step_ref]
                        if isinstance(step_data, dict) and "data" in step_data:
                            resolved[key] = step_data["data"].get(field, value_template)
                        else:
                            resolved[key] = value_template
                    else:
                        resolved[key] = value_template
                else:
                    resolved[key] = value_template
            else:
                resolved[key] = value_template
        
        return resolved
    
    async def _generate_business_insights(self, result: Dict, task: Dict) -> List[str]:
        """基于结果生成业务洞察（可被子类重写以提供领域专业知识）"""
        return []
    
    async def _suggest_next_actions(self, result: Dict, task: Dict) -> List[str]:
        """建议下一步行动"""
        return []
    
    def _extract_invoked_skills(self, step_results: Dict) -> List[str]:
        """提取使用的Skill列表"""
        invoked = set()
        for step_data in step_results.values():
            if isinstance(step_data, dict):
                invoked.add(step_data.get("skill_used", "unknown"))
        return list(invoked)
    
    def _calculate_step_metrics(self, step_results: Dict) -> Dict:
        """计算步骤级指标"""
        total = len(step_results)
        success = sum(1 for r in step_results.values() if isinstance(r, dict) and r.get("status") == "success")
        
        return {
            "success_rate": success / max(total, 1),
            "failed_steps": total - success
        }
    
    def _should_retry_domain_error(self, error_type: str) -> bool:
        non_retryable = ["workflow_not_found", "validation_error", "permission_denied"]
        return error_type.lower() not in non_retryable


class DomainAgentFactory:
    """
    DomainAgent工厂 - 动态创建和管理领域Agent
    
    核心功能：
    1. 从Skill包自动生成DomainAgent
    2. 管理DomainAgent生命周期
    3. 提供DomainAgent发现机制
    """
    
    def __init__(self, supervisor_reference=None):
        self.supervisor = supervisor_reference
        self._domain_agents: Dict[str, BaseDomainAgent] = {}
        self._domain_registry: Dict[str, DomainCapability] = {}  # 所有可用领域
    
    def create_from_skills(
        self, 
        domain_name: str,
        skills: List[Dict],
        workflows: List[Dict]
    ) -> BaseDomainAgent:
        """
        从Skill列表动态创建DomainAgent
        
        Args:
            domain_name: 领域名称
            skills: Skill元数据列表
            workflows: 工作流定义列表
            
        Returns:
            配置好的DomainAgent实例
        """
        # 创建领域能力声明
        capability = DomainCapability(
            domain_name=domain_name,
            display_name=f"{domain_name.title()} Expert",
            expertise_areas=[s.get("category", "") for s in skills],
            supported_intents=[f"{domain_name}_operation"],
            required_infra_agents=["skill", "rag", "file"]  # 大多数Domain需要这些
        )
        
        # 动态创建DomainAgent类
        DynamicDomainAgent = type(
            f"{domain_name.capitalize()}Agent",
            (BaseDomainAgent,),
            {
                "__module__": self.__class__.__module__,
                "_domain_workflows": workflows,
                "_domain_skills": skills
            }
        )
        
        agent = DynamicDomainAgent(
            agent_id=f"domain-{domain_name}",
            capability=capability
        )
        
        # 注册Skill绑定
        for skill in skills:
            binding = SkillBinding(
                skill_id=skill["id"],
                alias=skill.get("alias", skill["id"]),
                is_required=skill.get("required", False)
            )
            agent.bind_skill(binding)
        
        # 注册工作流
        for wf_def in workflows:
            workflow = DomainWorkflow(**wf_def)
            agent.register_workflow(workflow)
        
        return agent
    
    def register_domain(self, agent: BaseDomainAgent):
        """注册DomainAgent到工厂"""
        domain = agent.domain_capability.domain_name
        self._domain_agents[domain] = agent
        self._domain_registry[domain] = agent.domain_capability
        logger.info(f"[DomainFactory] Registered domain: {domain}")
    
    def get_domain(self, domain_name: str) -> Optional[BaseDomainAgent]:
        """获取指定领域的Agent"""
        return self._domain_agents.get(domain_name)
    
    def discover_domains(self, intent: str, slots: Dict) -> List[str]:
        """
        根据意图和槽位推荐合适的Domain
        
        Returns:
            匹配的域名列表（按匹配度排序）
        """
        candidates = []
        
        for domain, cap in self._domain_registry.items():
            score = 0
            
            # 检查支持的意图
            if intent in cap.supported_intents:
                score += 3
            
            # 检查标签匹配
            for tag in cap.tags:
                if tag.lower() in intent.lower() or tag.lower() in str(slots).lower():
                    score += 1
            
            if score > 0:
                candidates.append((domain, score))
        
        candidates.sort(key=lambda x: x[1], reverse=True)
        return [d for d, s in candidates]
    
    def list_available_domains(self) -> List[Dict]:
        """列出所有可用的领域"""
        return [
            {
                "domain": domain,
                "display_name": cap.display_name,
                "expertise": cap.expertise_areas[:3],
                "skills_count": len(self._domain_agents[domain]._skill_bindings) if domain in self._domain_agents else 0,
                "rating": cap.rating
            }
            for domain, cap in self._domain_registry.items()
        ]
