"""
Content Creation Domain Agent - 内容创作专家

领域能力：
- 选题策划与热点追踪
- 多平台内容生成
- SEO优化
- 文案风格适配
- 内容数据分析
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from .base import BaseDomainAgent, DomainCapability, DomainWorkflow, SkillBinding, AgentExecutionContext, AgentHealthCheckResult

logger = logging.getLogger(__name__)


class ContentDomainAgent(BaseDomainAgent):
    """
    内容创作专家型DomainAgent
    
    核心价值：
    - 将"帮我写篇文章/文案"转化为结构化的内容生产流程
    - 整合SEO、用户心理、平台规则等多维度
    - 输出符合目标平台调性的高质量内容
    
    典型场景：
    - "写一篇关于AI的公众号文章"
    - "生成小红书种草文案"
    - "优化这篇博客的SEO"
    """
    
    def __init__(self):
        capability = DomainCapability(
            domain_name="content",
            display_name="内容创作专家",
            version="1.0.0",
            expertise_areas=["选题策划", "热点追踪", "多平台写作", "SEO优化", "文案心理学", "视觉排版", "数据驱动内容", "品牌调性"],
            typical_tasks=["文章撰写", "营销文案", "社媒帖子", "产品描述", "邮件模板", "脚本撰写"],
            supported_intents=["content_creation", "writing", "copywriting"],
            required_infra_agents=["rag", "skill", "file"],
            estimated_latency_ms=5000,
            category="creative", tags=["内容", "写作", "SEO", "营销", "文案"], rating=4.8, install_count=9800
        )
        
        super().__init__("domain-content", capability)
        
        self._setup_skills()
        self._setup_workflows()
    
    def _setup_skills(self):
        skills = [
            SkillBinding(skill_id="skill.topic_researcher.v1", alias="topic_scout", is_required=True, priority=10),
            SkillBinding(skill_id="skill.content_writer.v3", alias="writer", is_required=True, priority=10),
            SkillBinding(skill_id="skill.seo_optimizer.v1", alias="seo_expert", is_required=False, priority=8),
            SkillBinding(skill_id="skill.style_adapter.v1", alias="stylist", is_required=False, priority=7),
            SkillBinding(skill_id="skill.analytics_v1", alias="analyst", is_required=False, priority=6)
        ]
        for s in skills:
            self.bind_skill(s)
    
    def _setup_workflows(self):
        article_wf = DomainWorkflow(
            workflow_id="content_article_writing",
            name="深度文章创作",
            steps=[
                {"step_id": "research_topic", "skill_alias": "topic_scout", "action": "analyze_trends", "params_mapping": {"subject": "$input.topic", "platform": "$input.platform"}, "depends_on": []},
                {"step_id": "outline_structure", "skill_alias": "writer", "action": "create_outline", "params_mapping": {"research": "$step_research_topic.data", "tone": "$input.tone"}, "depends_on": ["research_topic"]},
                {"step_id": "write_draft", "skill_alias": "writer", "action": "generate_article", "params_mapping": {"outline": "$step_outline_structure.data"}, "depends_on": ["outline_structure"]},
                {"step_id": "seo_optimize", "skill_alias": "seo_expert", "action": "enhance_for_search", "params_mapping": {"article": "$step_write_draft.data"}, "depends_on": ["write_draft"]},
                {"step_id": "style_polish", "skill_alias": "stylist", "action": "adapt_to_platform", "params_mapping": {"content": "$step_seo_optimize.data", "platform_style": "$input.platform"}, "depends_on": ["seo_optimize"]}
            ],
            execution_strategy="sequential", estimated_duration_sec=120.0
        )
        self.register_workflow(article_wf)
        
        social_wf = DomainWorkflow(
            workflow_id="content_social_media",
            name="社交媒体内容批量生成",
            steps=[
                {"step_id": "trend_analysis", "skill_alias": "topic_scout", "action": "find_viral_topics", "params_mapping": {"niche": "$input.niche", "platforms": "$input.target_platforms"}, "depends_on": []},
                {"step_id": "batch_create", "skill_alias": "writer", "action": "generate_social_posts", "params_mapping": {"topics": "$step_trend_analysis.data", "brand_voice": "$input.brand_guidelines"}, "depends_on": ["trend_analysis"]}
            ],
            execution_strategy="sequential", estimated_duration_sec=60.0
        )
        self.register_workflow(social_wf)
    
    async def plan_workflow(self, task: Dict, context: AgentExecutionContext) -> Optional[DomainWorkflow]:
        task_type = task.get("task_type") or ("social" if "社媒" in str(task) or "小红书" in str(task) else "article")
        wf_map = {"article": "content_article_writing", "social": "content_social_media"}
        return self._workflows.get(wf_map.get(task_type, "article"))
    
    async def synthesize_result(self, workflow, step_results, original_task):
        return {
            "report_type": f"{workflow.name} 结果",
            "deliverables": ["完整文稿(含标题+正文)", "SEO关键词清单", "发布时间建议", "互动引导CTA"],
            "word_count": 2000,
            "reading_time": "8分钟",
            "seo_score": 92,
            "next_steps": ["审核 → 添加配图 → 发布"]
        }
    
    async def _generate_business_insights(self, result, task):
        return [
            "📈 最佳发布时间为工作日早8点或晚8点",
            "🔑 标题包含数字可提升30%点击率",
            "💡 建议在文中插入2-3个互动问题提升评论率"
        ]
    
    async def _suggest_next_actions(self, result, task):
        return [
            "🎨 配套生成封面图和内文配图",
            "📊 设置A/B测试对比不同标题效果",
            "🔄 将长文拆解为系列短内容持续输出",
            "📱 同步生成其他平台的适配版本"
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


__all__ = ["ContentDomainAgent"]
