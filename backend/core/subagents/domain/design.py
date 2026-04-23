"""
Design Domain Agent - 设计工作专家

领域能力：
- 需求分析与拆解
- 设计方案生成
- 品牌VI系统
- UI/UX设计
- 文案与视觉素材
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from .base import (
    BaseDomainAgent,
    DomainCapability,
    DomainWorkflow,
    SkillBinding,
    AgentExecutionContext,
    AgentHealthCheckResult
)

logger = logging.getLogger(__name__)


class DesignDomainAgent(BaseDomainAgent):
    """
    设计专家型DomainAgent
    
    核心价值：
    - 将模糊的"帮我做个Logo/海报/PPT"转化为结构化的专业设计流程
    - 整合品牌理论、设计规范、用户偏好等多维度
    - 输出可交付的设计方案和素材清单
    
    典型场景：
    - "这是客户的新品牌VI需求，出3版初稿"
    - "根据产品特点生成营销海报"
    - "制作向客户汇报的PPT大纲"
    """
    
    def __init__(self):
        capability = DomainCapability(
            domain_name="design",
            display_name="设计创意专家",
            version="1.0.0",
            
            expertise_areas=[
                "品牌策略与定位",
                "视觉识别系统(VI)",
                "UI/UX界面设计",
                "平面设计与排版",
                "动效与交互",
                "3D建模与渲染",
                "插画与图标",
                "文案与内容策划"
            ],
            
            typical_tasks=[
                "Logo设计",
                "品牌VI手册",
                "产品包装设计",
                "营销海报/Banner",
                "PPT/演示文稿",
                "App界面设计",
                "网站页面设计",
                "社交媒体素材"
            ],
            
            supported_intents=["design_work", "creative_task", "branding", "visual_content"],
            
            required_infra_agents=["skill", "file", "rag"],
            estimated_latency_ms=8000,
            
            category="creative",
            tags=["design", "UI", "UX", "品牌", "创意", "平面"],
            rating=4.9,
            install_count=8900
        )
        
        super().__init__("domain-design", capability)
        
        self._setup_skills()
        self._setup_workflows()
    
    def _setup_skills(self):
        skills = [
            SkillBinding(
                skill_id="skill.requirement_analyzer.v1",
                alias="req_analyzer",
                is_required=True, priority=10
            ),
            SkillBinding(
                skill_id="skill.design_generator.v2",
                alias="design_creator",
                is_required=True, priority=10
            ),
            SkillBinding(
                skill_id="skill.brand_kit.v1",
                alias="brand_builder",
                is_required=False, priority=8
            ),
            SkillBinding(
                skill_id="skill.asset_exporter.v1",
                alias="asset_manager",
                is_required=False, priority=6
            )
        ]
        for s in skills:
            self.bind_skill(s)
    
    def _setup_workflows(self):
        # 品牌设计方案生成
        branding_wf = DomainWorkflow(
            workflow_id="design_branding_solution",
            name="品牌全案设计",
            description="从需求分析到设计方案生成的完整品牌设计流程",
            steps=[
                {
                    "step_id": "analyze_requirements",
                    "skill_alias": "req_analyzer",
                    "action": "extract_design_brief",
                    "params_mapping": {"brief": "$input.client_brief"},
                    "depends_on": []
                },
                {
                    "step_id": "research_references",
                    "skill_alias": "req_analyzer",
                    "action": "gather_inspiration",
                    "params_mapping": {
                        "industry": "$step_analyze_requirements.industry",
                        "style_prefs": "$input.style_preferences"
                    },
                    "depends_on": ["analyze_requirements"]
                },
                {
                    "step_id": "generate_concepts",
                    "skill_alias": "design_creator",
                    "action": "create_brand_concepts",
                    "params_mapping": {
                        "requirements": "$step_analyze_requirements.data",
                        "inspiration": "$step_research_references.data",
                        "variations": 3
                    },
                    "depends_on": ["analyze_requirements", "research_references"]
                }
            ],
            execution_strategy="sequential",
            estimated_duration_sec=150.0
        )
        self.register_workflow(branding_wf)
        
        # 营销物料快速生成
        marketing_wf = DomainWorkflow(
            workflow_id="design_marketing_assets",
            name="营销物料批量生成",
            description="基于产品信息快速生成营销所需的各类物料素材",
            steps=[
                {
                    "step_id": "understand_product",
                    "skill_alias": "req_analyzer",
                    "action": "extract_product_usp",
                    "params_mapping": {"product_info": "$input.product_details"},
                    "depends_on": []
                },
                {
                    "step_id": "create_assets",
                    "skill_alias": "design_creator",
                    "action": "generate_marketing_assets",
                    "params_mapping": {
                        "usp": "$step_understand_product.usp",
                        "asset_types": "$input.required_assets",
                        "brand_guidelines": "$input.brand_guidelines"
                    },
                    "depends_on": ["understand_product"]
                }
            ],
            execution_strategy="sequential",
            estimated_duration_sec=60.0
        )
        self.register_workflow(marketing_wf)
    
    async def plan_workflow(self, task: Dict, context: AgentExecutionContext) -> Optional[DomainWorkflow]:
        task_type = task.get("task_type") or self._infer_design_type(task)
        
        wf_map = {
            "branding": "design_branding_solution",
            "marketing": "design_marketing_assets"
        }
        
        return self._workflows.get(wf_map.get(task_type, "branding"))
    
    def _infer_design_type(self, task: Dict) -> str:
        query = str(task)
        if any(kw in query.lower() for kw in ["品牌", "vi", "logo", "identity"]):
            return "branding"
        return "marketing"
    
    async def synthesize_result(self, workflow, step_results, original_task):
        return {
            "report_type": f"{workflow.name} 结果",
            "concepts_generated": len([r for r in step_results.values() if isinstance(r, dict) and r.get("status") == "success"]),
            "deliverables": ["设计初稿文件包", "设计说明文档", "修改建议清单"],
            "next_steps": ["客户审核 → 收集反馈 → 迭代优化"]
        }
    
    async def _generate_business_insights(self, result, task):
        return [
            "🎨 建议提供2-3个参考案例以提升设计精准度",
            "⏰ 初稿通常需要1-2轮迭代达到交付标准",
            "💡 明确目标受众可显著提升设计转化效果"
        ]
    
    async def _suggest_next_actions(self, result, task):
        return [
            "🔄 对选定方案进行细节优化",
            "📦 导出可编辑的设计源文件",
            "🎯 创建A/B测试版本对比效果"
        ]

    async def validate_input(self, task: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """验证输入参数"""
        errors = []
        if not task:
            errors.append("Task cannot be empty")
        return (len(errors) == 0, errors)

    async def health_check(self) -> AgentHealthCheckResult:
        """健康检查"""
        from ..base import AgentHealthStatus
        stats = await self.get_statistics()
        status = AgentHealthStatus.HEALTHY if stats["success_rate"] > 0.8 else AgentHealthStatus.DEGRADED
        return AgentHealthCheckResult(
            status=status,
            agent_id=self.agent_id,
            uptime_seconds=stats["uptime_seconds"],
            tasks_completed=stats["total_executions"],
            average_latency_ms=stats["avg_latency_ms"]
        )


__all__ = ["DesignDomainAgent"]
