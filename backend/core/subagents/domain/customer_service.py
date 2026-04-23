"""
Customer Service Domain Agent - 智能客服专家

领域能力：
- 工单智能分类与路由
- 自动回复生成
- FAQ智能匹配
- 情感分析
- 客户满意度预测
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from .base import BaseDomainAgent, DomainCapability, DomainWorkflow, SkillBinding, AgentExecutionContext, AgentHealthCheckResult

logger = logging.getLogger(__name__)


class CustomerServiceDomainAgent(BaseDomainAgent):
    """
    智能客服专家型DomainAgent
    
    核心价值：
    - 将客户咨询转化为结构化工单处理流程
    - 整合知识库、情感分析、优先级评估
    - 输出专业、有温度的客服回复
    
    典型场景：
    - "处理这个退货请求"
    - "回答用户关于XXX的咨询"
    - "分析最近一周的客户反馈"
    """
    
    def __init__(self):
        capability = DomainCapability(
            domain_name="customer_service",
            display_name="智能客服专家",
            version="1.0.0",
            expertise_areas=["工单管理", "FAQ匹配", "情感分析", "SLA保障", "话术优化", "客户画像", "满意度提升", "投诉处理", "售后支持"],
            typical_tasks=["工单处理", "自动回复", "FAQ检索", "情感分析", "客户回访"],
            supported_intents=["customer_service", "support", "ticket"],
            required_infra_agents=["rag", "skill", "file"],
            estimated_latency_ms=3000,
            category="service", tags=["客服", "工单", "售后", "支持"], rating=4.7, install_count=5600
        )
        
        super().__init__("domain-customer-service", capability)
        
        self._setup_skills()
        self._setup_workflows()
    
    def _setup_skills(self):
        skills = [
            SkillBinding(skill_id="skill.ticket_classifier.v1", alias="classifier", is_required=True, priority=10),
            SkillBinding(skill_id="skill.reply_generator.v2", alias="reply_writer", is_required=True, priority=10),
            SkillBinding(skill_id="skill.sentiment_analyzer.v1", alias="sentiment_reader", is_required=False, priority=8),
            SkillBinding(skill_id="skill.faq_matcher.v1", alias="faq_finder", is_required=True, priority=9),
            SkillBinding(skill_id="skill.priority_estimator.v1", alias="priority_calc", is_required=False, priority=7)
        ]
        for s in skills:
            self.bind_skill(s)
    
    def _setup_workflows(self):
        ticket_wf = DomainWorkflow(
            workflow_id="cs_ticket_resolution",
            name="工单智能处理",
            steps=[
                {"step_id": "classify_ticket", "skill_alias": "classifier", "action": "categorize_and_prioritize", "params_mapping": {"ticket_content": "$input.customer_message"}, "depends_on": []},
                {"step_id": "analyze_sentiment", "skill_alias": "sentiment_reader", "action": "detect_emotion_and_urgency", "params_mapping": {"message": "$input.customer_message"}, "depends_on": []},
                {"step_id": "search_faq", "skill_alias": "faq_finder", "action": "find_relevant_answers", "params_mapping": {"query": "$input.customer_message", "category": "$step_classify_ticket.data.category"}, "depends_on": ["classify_ticket"]},
                {"step_id": "generate_reply", "skill_alias": "reply_writer", "action": "craft_response", "params_mapping": {"faq_context": "$step_search_faq.data", "sentiment": "$step_analyze_sentiment.data", "tone": "$input.tone_policy"}, "depends_on": ["classify_ticket", "sentiment_analysis", "search_faq"]},
                {"step_id": "estimate_satisfaction", "skill_alias": "priority_calc", "action": "predict_csat", "params_mapping": {"reply": "$step_generate_reply.data", "history": "$input.customer_history"}, "depends_on": ["generate_reply"]}
            ],
            execution_strategy="adaptive", estimated_duration_sec=30.0
        )
        self.register_workflow(ticket_wf)
        
        analysis_wf = DomainWorkflow(
            workflow_id="cs_feedback_analysis",
            name="客户反馈批量分析",
            steps=[
                {"step_id": "collect_feedback", "skill_alias": "sentiment_reader", "action": "batch_analyze_sentiment", "params_mapping": {"feedback_list": "$input.feedback_batch"}, "depends_on": []},
                {"step_id": "generate_report", "skill_alias": "reply_writer", "action": "create_insight_report", "params_mapping": {"analysis": "$step_collect_feedback.data", "period": "$input.analysis_period"}, "depends_on": ["collect_feedback"]}
            ],
            execution_strategy="sequential", estimated_duration_sec=45.0
        )
        self.register_workflow(analysis_wf)
    
    async def plan_workflow(self, task: Dict, context: AgentExecutionContext) -> Optional[DomainWorkflow]:
        task_type = task.get("task_type") or ("analysis" if "分析" in str(task) or "反馈" in str(task) else "ticket")
        wf_map = {"ticket": "cs_ticket_resolution", "analysis": "cs_feedback_analysis"}
        return self._workflows.get(wf_map.get(task_type, "ticket"))
    
    async def synthesize_result(self, workflow, step_results, original_task):
        predicted_csat = step_results.get("step_estimate_satisfaction", {}).get("data", {}).get("predicted_csat", 85)
        
        return {
            "report_type": f"{workflow.name} 结果",
            "suggested_reply": step_results.get("step_generate_reply", {}).get("data", {}).get("reply_text", ""),
            "category": step_results.get("step_classify_ticket", {}).get("data", {}).get("category", "general"),
            "priority": step_results.get("step_classify_ticket", {}).get("data", {}).get("priority", "normal"),
            "sentiment": step_results.get("step_analyze_sentiment", {}).get("data", {}).get("overall_sentiment", "neutral"),
            "predicted_satisfaction": f"{predicted_csat}%",
            "next_steps": ["发送回复 → 跟进确认 → 记录结果"]
        }
    
    async def _generate_business_insights(self, result, task):
        sentiment = result.get("sentiment", "")
        if sentiment == "negative":
            return [
                "🔴 建议立即人工介入，避免客户流失风险",
                "💡 可提供优惠券或补偿方案挽回客户"
            ]
        elif sentiment == "positive":
            return [
                "✅ 这是转介绍的好机会，建议引导分享"
            ]
        else:
            return [
                "📊 建议在24小时内进行跟进回访"
            ]
    
    async def _suggest_next_actions(self, result, task):
        return [
            "📤 发送回复并标记工单状态",
            "🔄 设置3天后自动跟进提醒",
            "📈 将该案例加入知识库供后续参考",
            "🎯 针对同类问题创建自动化规则"
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


__all__ = ["CustomerServiceDomainAgent"]
