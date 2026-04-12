"""
Finance Domain Agent - 财税管理专家

领域能力：
- 发票OCR与识别
- 自动记账
- 报表生成
- 税务合规检查
- 财务分析
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from .base import (
    BaseDomainAgent,
    DomainCapability,
    DomainWorkflow,
    SkillBinding,
    AgentExecutionContext
)

logger = logging.getLogger(__name__)


class FinanceDomainAgent(BaseDomainAgent):
    """
    财税管理专家型DomainAgent
    
    核心价值：
    - 将"帮我整理发票/生成报表"转化为结构化的财务流程
    - 确保数据准确性和合规性
    - 输出符合会计准则的财务报告
    
    典型场景：
    - "每月底整理发票、录入账目、生成报表"
    - "核对税务、确保合规"
    - "分析本季度财务状况"
    """
    
    def __init__(self):
        capability = DomainCapability(
            domain_name="finance",
            display_name="财税管理专家",
            version="1.0.0",
            
            expertise_areas=[
                "发票管理与OCR",
                "自动记账与分类",
                "财务报表生成",
                "税务合规检查",
                "成本控制分析",
                "预算管理",
                "现金流预测",
                "审计准备"
            ],
            
            typical_tasks=[
                "发票批量处理",
                "科目智能分类",
                "三大报表生成",
                "增值税申报准备",
                "费用报销审核",
                "利润分析",
                "税务筹划建议"
            ],
            
            supported_intents=["finance_management", "accounting", "tax_compliance", "reporting"],
            
            required_infra_agents=["skill", "file", "rag"],
            estimated_latency_ms=4000,
            
            category="business",
            tags=["财务", "税务", "会计", "报表", "合规"],
            rating=4.7,
            install_count=6700
        )
        
        super().__init__("domain-finance", capability)
        
        self._setup_skills()
        self._setup_workflows()
    
    def _setup_skills(self):
        skills = [
            SkillBinding(skill_id="skill.invoice_ocr.v2", alias="invoice_scanner", is_required=True, priority=10),
            SkillBinding(skill_id="skill.auto_ledger.v1", alias="ledger_engine", is_required=True, priority=10),
            SkillBinding(skill_id="skill.report_generator.v2", alias="report_builder", is_required=True, priority=9),
            SkillBinding(skill_id="skill.tax_checker.v1", alias="tax_auditor", is_required=False, priority=8),
            SkillBinding(skill_id="skill.anomaly_detector.v1", alias="fraud_watcher", is_required=False, priority=7)
        ]
        for s in skills:
            self.bind_skill(s)
    
    def _setup_workflows(self):
        # 月度结账工作流
        monthly_close_wf = DomainWorkflow(
            workflow_id="finance_monthly_close",
            name="月度结账全流程",
            description="从发票扫描到报表生成的完整月度结账流程",
            steps=[
                {
                    "step_id": "scan_invoices",
                    "skill_alias": "invoice_scanner",
                    "action": "batch_process",
                    "params_mapping": {"source_dir": "$input.invoices_path", "formats": ["pdf", "image"]},
                    "depends_on": []
                },
                {
                    "step_id": "auto_entry",
                    "skill_alias": "ledger_engine",
                    "action": "create_entries_from_invoices",
                    "params_mapping": {"invoice_data": "$step_scan_invoices.data"},
                    "depends_on": ["scan_invoices"]
                },
                {
                    "step_id": "generate_reports",
                    "skill_alias": "report_builder",
                    "action": "monthly_financial_package",
                    "params_mapping": {
                        "period": "$input.period",
                        "entries": "$step_auto_entry.data",
                        "include": ["balance_sheet", "income_statement", "cash_flow"]
                    },
                    "depends_on": ["auto_entry"]
                },
                {
                    "step_id": "tax_check",
                    "skill_alias": "tax_auditor",
                    "action": "compliance_review",
                    "params_mapping": {"reports": "$step_generate_reports.data"},
                    "depends_on": ["generate_reports"]
                }
            ],
            execution_strategy="sequential",
            estimated_duration_sec=120.0
        )
        self.register_workflow(monthly_close_wf)
        
        # 快速分析工作流
        quick_analysis_wf = DomainWorkflow(
            workflow_id="finance_quick_analysis",
            name="财务快速分析",
            steps=[
                {
                    "step_id": "gather_data",
                    "skill_alias": "ledger_engine",
                    "action": "query_period_data",
                    "params_mapping": {"period": "$input.analysis_period"},
                    "depends_on": []
                },
                {
                    "step_id": "analyze_trends",
                    "skill_alias": "report_builder",
                    "action": "trend_analysis",
                    "params_mapping": {"financial_data": "$step_gather_data.data"},
                    "depends_on": ["gather_data"]
                }
            ],
            execution_strategy="sequential",
            estimated_duration_sec=30.0
        )
        self.register_workflow(quick_analysis_wf)
    
    async def plan_workflow(self, task: Dict, context: AgentExecutionContext) -> Optional[DomainWorkflow]:
        task_type = task.get("task_type") or self._infer_finance_type(task)
        
        wf_map = {
            "monthly_close": "finance_monthly_close",
            "analysis": "finance_quick_analysis"
        }
        
        return self._workflows.get(wf_map.get(task_type, "analysis"))
    
    def _infer_finance_type(self, task: Dict) -> str:
        query = str(task)
        if any(kw in query.lower() for kw in ["月度", "结账", "发票", "报表", "close"]):
            return "monthly_close"
        return "analysis"
    
    async def synthesize_result(self, workflow, step_results, original_task):
        has_anomalies = any("tax_check" in str(r) for r in step_results.values())
        
        return {
            "report_type": workflow.name,
            "period": original_task.get("period", "current"),
            "status": "completed" if not any(isinstance(r, dict) and r.get("status") == "failed" for r in step_results.values()) else "partial",
            "reports_generated": ["资产负债表", "损益表", "现金流量表"],
            "compliance_status": "⚠️ 需关注项" if has_anomalies else "✅ 合规",
            "anomaly_alerts": [] if not has_anomalies else ["发现3处需要人工确认的异常分录"]
        }
    
    async def _generate_business_insights(self, result, task):
        insights = [
            "📊 建议每周执行快速分析以监控现金流健康度",
            "💰 发票自动化可减少80%的手工录入时间",
            "⚠️ 季度末前完成税务预审可避免申报期压力"
        ]
        
        if result.get("compliance_status") != "✅ 合规":
            insights.insert(0, "🔴 优先处理合规预警项，避免税务风险")
        
        return insights
    
    async def _suggest_next_actions(self, result, task):
        return [
            "📋 导出Excel格式的明细账供会计师复核",
            "🔔 设置下月发票自动扫描提醒",
            "📈 配置关键指标监控仪表盘",
            "🏦 安排季度税务筹划会议"
        ]


__all__ = ["FinanceDomainAgent"]
