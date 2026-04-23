"""
Developer Domain Agent - 软件开发专家

领域能力：
- 需求分析与技术方案
- 代码生成与审查
- Bug诊断与修复
- DevOps自动化部署
- API设计与文档
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


class DeveloperDomainAgent(BaseDomainAgent):
    """
    软件开发专家型DomainAgent
    
    核心价值：
    - 将"帮我写个XXX功能"转化为完整的开发工作流
    - 整合代码规范、测试、部署的最佳实践
    - 输出可运行的代码和完整的技术文档
    
    典型场景：
    - "用FastAPI写一个用户认证API"
    - "帮我修复这个Bug"
    - "部署应用到生产环境"
    """
    
    def __init__(self):
        capability = DomainCapability(
            domain_name="development",
            display_name="软件开发专家",
            version="1.0.0",
            
            expertise_areas=[
                "需求分析与架构设计",
                "后端API开发",
                "前端界面开发",
                "数据库设计",
                "DevOps与CI/CD",
                "代码审查与重构",
                "性能优化",
                "安全加固",
                "测试驱动开发",
                "技术文档编写"
            ],
            
            typical_tasks=[
                "功能模块开发",
                "API接口设计",
                "Bug修复",
                "代码重构",
                "性能调优",
                "自动化部署",
                "数据库迁移",
                "单元测试编写"
            ],
            
            supported_intents=["software_development", "coding", "devops"],
            required_infra_agents=["skill", "file", "rag"],
            estimated_latency_ms=6000,
            
            category="technology",
            tags=["开发", "编程", "Python", "API", "DevOps", "全栈"],
            rating=4.9,
            install_count=15200
        )
        
        super().__init__("domain-development", capability)
        
        self._setup_skills()
        self._setup_workflows()
    
    def _setup_skills(self):
        skills = [
            SkillBinding(skill_id="skill.code_generator.v3", alias="code_writer", is_required=True, priority=10),
            SkillBinding(skill_id="skill.code_reviewer.v1", alias="code_reviewer", is_required=False, priority=8),
            SkillBinding(skill_id="skill.bug_fixer.v2", alias="bug_hunter", is_required=True, priority=9),
            SkillBinding(skill_id="skill.devops_deployer.v1", alias="deployer", is_required=False, priority=7),
            SkillBinding(skill_id="skill.test_generator.v1", alias="test_maker", is_required=False, priority=6),
            SkillBinding(skill_id="skill.api_designer.v1", alias="api_architect", is_required=False, priority=8)
        ]
        for s in skills:
            self.bind_skill(s)
    
    def _setup_workflows(self):
        # 功能开发工作流
        feature_wf = DomainWorkflow(
            workflow_id="dev_feature_development",
            name="功能模块开发",
            steps=[
                {"step_id": "analyze_requirements", "skill_alias": "api_architect", "action": "extract_specs", "params_mapping": {"requirement": "$input.requirement"}, "depends_on": []},
                {"step_id": "design_api", "skill_alias": "api_architect", "action": "design_endpoints", "params_mapping": {"specs": "$step_analyze_requirements.data"}, "depends_on": ["analyze_requirements"]},
                {"step_id": "write_code", "skill_alias": "code_writer", "action": "generate_implementation", "params_mapping": {"api_design": "$step_design_api.data", "tech_stack": "$input.tech_stack"}, "depends_on": ["design_api"]},
                {"step_id": "write_tests", "skill_alias": "test_maker", "action": "create_unit_tests", "params_mapping": {"implementation": "$step_write_code.data"}, "depends_on": ["write_code"]},
                {"step_id": "review_code", "skill_alias": "code_reviewer", "action": "quality_check", "params_mapping": {"code": "$step_write_code.data"}, "depends_on": ["write_code"]}
            ],
            execution_strategy="sequential",
            estimated_duration_sec=180.0
        )
        self.register_workflow(feature_wf)
        
        # Bug修复工作流
        bugfix_wf = DomainWorkflow(
            workflow_id="dev_bug_resolution",
            name="智能Bug修复",
            steps=[
                {"step_id": "analyze_error", "skill_alias": "bug_hunter", "action": "diagnose_issue", "params_mapping": {"error_info": "$input.error_details", "stack_trace": "$input.stack_trace"}, "depends_on": []},
                {"step_id": "locate_cause", "skill_alias": "bug_hunter", "action": "find_root_cause", "params_mapping": {"diagnosis": "$step_analyze_error.data"}, "depends_on": ["analyze_error"]},
                {"step_id": "apply_fix", "skill_alias": "code_writer", "action": "generate_fix", "params_mapping": {"root_cause": "$step_locate_cause.data", "file_path": "$input.affected_file"}, "depends_on": ["locate_cause"]},
                {"step_id": "verify_fix", "skill_alias": "test_maker", "action": "run_regression", "params_mapping": {"fixed_code": "$step_apply_fix.data"}, "depends_on": ["apply_fix"]}
            ],
            execution_strategy="sequential",
            estimated_duration_sec=60.0
        )
        self.register_workflow(bugfix_wf)
    
    async def plan_workflow(self, task: Dict, context: AgentExecutionContext) -> Optional[DomainWorkflow]:
        task_type = task.get("task_type") or self._infer_dev_type(task)
        wf_map = {"feature": "dev_feature_development", "bugfix": "dev_bug_resolution"}
        return self._workflows.get(wf_map.get(task_type, "feature"))
    
    def _infer_dev_type(self, task: Dict) -> str:
        query = str(task)
        if any(kw in query.lower() for kw in ["bug", "error", "修复", "报错", "异常"]):
            return "bugfix"
        return "feature"
    
    async def synthesize_result(self, workflow, step_results, original_task):
        has_tests = "write_tests" in step_results and step_results["write_tests"].get("status") == "success"
        review_status = step_results.get("review_code", {}).get("status")
        
        return {
            "report_type": f"{workflow.name} 结果",
            "deliverables": [
                "源代码文件 (已格式化)",
                "单元测试文件" if has_tests else "(可选)",
                "API文档 (OpenAPI/Swagger)",
                "README.md (使用说明)"
            ],
            "code_quality": "✅ 通过审查" if review_status == "success" else "⚠️ 需人工审核",
            "next_steps": ["运行测试套件 → 代码审查 → 合并PR"]
        }
    
    async def _generate_business_insights(self, result, task):
        return [
            "🔧 建议配置pre-commit hooks自动执行linting和测试",
            "📊 代码复杂度较高时考虑拆分或引入设计模式",
            "🚀 使用Feature Flag可以更安全地发布新功能"
        ]
    
    async def _suggest_next_actions(self, result, task):
        return [
            "🧪 运行完整测试套件验证功能正确性",
            "📝 补充API文档和使用示例",
            "🚀 配置CI/CD流水线实现自动化部署",
            "🔍 进行性能基准测试"
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


__all__ = ["DeveloperDomainAgent"]
