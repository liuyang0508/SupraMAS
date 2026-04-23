"""
Ecommerce Domain Agent - 电商运营专家

领域能力：
- 市场调研与选品分析
- 竞品分析与价格策略
- Listing优化与文案生成
- 供应链管理
- 数据驱动决策

工作流：
1. 产品研究流程 (product_research)
2. 选品决策流程 (sourcing_decision)
3. Listing生成流程 (listing_generation)
4. 全链路运营流程 (full_operation)
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from .base import (
    BaseDomainAgent,
    DomainCapability,
    DomainWorkflow,
    DomainExecutionResult,
    SkillBinding,
    AgentExecutionContext,
    AgentHealthCheckResult
)

logger = logging.getLogger(__name__)


class EcommerceDomainAgent(BaseDomainAgent):
    """
    电商运营专家型DomainAgent
    
    核心价值：
    - 将"帮我做亚马逊选品"这样的模糊需求，转化为结构化的专业操作序列
    - 整合市场数据、供应商信息、平台规则等多维度信息
    - 输出可执行的选品建议和营销方案
    
    典型场景：
    - "帮我分析上周户外运动类目热销产品"
    - "在1688找同款供应商，对比价格"
    - "生成5个产品Listing和营销文案"
    """
    
    def __init__(self):
        capability = DomainCapability(
            domain_name="ecommerce",
            display_name="电商运营专家",
            version="1.0.0",
            
            expertise_areas=[
                "市场趋势分析",
                "竞品深度调研", 
                "选品策略制定",
                "价格优化",
                "Listing SEO优化",
                "A+内容策划",
                "PPC广告策略",
                "库存管理",
                "供应链协调",
                "数据报表分析"
            ],
            
            typical_tasks=[
                "热销产品挖掘",
                "蓝海市场发现",
                "竞品监控追踪",
                "利润计算器",
                "关键词研究",
                "主图视频策划",
                "Review分析",
                "Q&A优化"
            ],
            
            supported_intents=[
                "ecommerce_operation",
                "market_research",
                "product_sourcing",
                "listing_optimization",
                "price_analysis",
                "competitor_analysis"
            ],
            
            input_schema={
                "task_type": {"type": "string", "enum": ["research", "sourcing", "listing", "analysis"]},
                "platform": {"type": "string", "default": "amazon"},
                "category": {"type": "string"},
                "keywords": {"type": "array", "items": {"type": "string"}},
                "time_range": {"type": "string", "default": "last_30d"},
                "target_marketplace": {"type": "string", "default": "US"}
            },
            
            output_schema={
                "research_report": {"type": "object"},
                "product_recommendations": {"type": "array"},
                "supplier_options": {"type": "array"},
                "listing_content": {"type": "object"},
                "pricing_strategy": {"type": "object"}
            },
            
            required_infra_agents=["rag", "skill", "file", "mcp"],
            estimated_latency_ms=5000,
            
            category="business",
            tags=["ecommerce", "amazon", "1688", "跨境", "选品"],
            rating=4.8,
            install_count=12500
        )
        
        super().__init__("domain-ecommerce", capability)
        
        # 绑定核心Skill
        self._setup_skill_bindings()
        
        # 注册标准工作流
        self._setup_workflows()
    
    def _setup_skill_bindings(self):
        """配置电商领域的Skill绑定"""
        
        skills = [
            SkillBinding(
                skill_id="skill.amazon_trend_analyzer.v1",
                alias="trend_analyzer",
                trigger_conditions=[{"field": "task_type", "value": "research"}],
                default_params={"platform": "amazon", "depth": "deep"},
                is_required=True,
                priority=10
            ),
            SkillBinding(
                skill_id="skill.competitor_scraper.v1",
                alias="competitor_scanner",
                trigger_conditions=[{"field": "task_type", "in": ["research", "analysis"]}],
                default_params={"include_reviews": True, "include_ppc": False},
                is_required=True,
                priority=9
            ),
            SkillBinding(
                skill_id="skill.supplier_matcher.v1",
                alias="supplier_finder",
                trigger_conditions=[{"field": "task_type", "value": "sourcing"}],
                default_params={"source_platform": "1688", "min_order_qty": 50},
                is_required=True,
                priority=10
            ),
            SkillBinding(
                skill_id="skill.listing_generator.v2",
                alias="listing_writer",
                trigger_conditions=[{"field": "task_type", "value": "listing"}],
                default_params={"language": "en", "style": "professional"},
                is_required=True,
                priority=9
            ),
            SkillBinding(
                skill_id="skill.price_optimizer.v1",
                alias="price_calculator",
                trigger_conditions=[{"field": "task_type", "in": ["sourcing", "analysis"]}],
                default_params={"margin_target": 0.3, "currency": "USD"},
                is_required=False,
                priority=7
            ),
            SkillBinding(
                skill_id="skill.keyword_researcher.v1",
                alias="keyword_tool",
                trigger_conditions=[{"field": "task_type", "in": ["listing", "research"]}],
                default_params={"tool": "helium10", "max_keywords": 100},
                is_required=False,
                priority=6
            )
        ]
        
        for skill in skills:
            self.bind_skill(skill)
    
    def _setup_workflows(self):
        """注册电商领域的标准工作流"""
        
        # 工作流1: 完整的产品研究流程
        research_workflow = DomainWorkflow(
            workflow_id="ecommerce_product_research",
            name="全链路产品研究",
            description="从市场趋势到竞品分析的完整研究流程，输出选品建议报告",
            steps=[
                {
                    "step_id": "step_1_trend",
                    "skill_alias": "trend_analyzer",
                    "action": "analyze_category_trends",
                    "params_mapping": {
                        "category": "$input.category",
                        "time_range": "$input.time_range",
                        "marketplace": "$input.target_marketplace"
                    },
                    "depends_on": [],
                    "timeout": 45,
                    "required": True
                },
                {
                    "step_id": "step_2_competitor",
                    "skill_alias": "competitor_scanner",
                    "action": "deep_scan_top_products",
                    "params_mapping": {
                        "category": "$input.category",
                        "top_n": 20,
                        "include_data": ["sales_rank", "reviews", "price", "listing_quality"]
                    },
                    "depends_on": [],
                    "timeout": 60,
                    "required": True
                },
                {
                    "step_id": "step_3_keyword",
                    "skill_alias": "keyword_tool",
                    "action": "discover_opportunities",
                    "params_mapping": {
                        "seed_keywords": "$input.keywords",
                        "competition_level": "medium"
                    },
                    "depends_on": ["step_1_trend"],
                    "timeout": 30,
                    "required": False
                },
                {
                    "step_id": "step_4_synthesis",
                    "skill_alias": "trend_analyzer",
                    "action": "synthesize_findings",
                    "params_mapping": {
                        "trend_data": "$step_1_trend.data",
                        "competitor_data": "$step_2_competitor.data",
                        "keyword_data": "$step_3_keyword.data"
                    },
                    "depends_on": ["step_1_trend", "step_2_competitor"],
                    "timeout": 20,
                    "required": True
                }
            ],
            input_schema={
                "category": {"type": "string", "required": True},
                "platform": {"type": "string"},
                "time_range": {"type": "string"}
            },
            output_schema={
                "report": {"type": "object"},
                "recommendations": {"type": "array"},
                "opportunity_score": {"type": "number"}
            },
            execution_strategy="adaptive",
            estimated_duration_sec=180.0
        )
        self.register_workflow(research_workflow)
        
        # 工作流2: 采购决策流程
        sourcing_workflow = DomainWorkflow(
            workflow_id="ecommerce_sourcing_decision",
            name="智能采购决策",
            description="从产品选择到供应商匹配的完整采购决策流程",
            steps=[
                {
                    "step_id": "step_1_product_select",
                    "skill_alias": "trend_analyzer",
                    "action": "validate_product_potential",
                    "params_mapping": {
                        "product_query": "$input.product_description",
                        "criteria": "$input.selection_criteria"
                    },
                    "depends_on": [],
                    "timeout": 30
                },
                {
                    "step_id": "step_2_supplier_search",
                    "skill_alias": "supplier_finder",
                    "action": "find_matching_suppliers",
                    "params_mapping": {
                        "product_spec": "$step_1_product_select.product_spec",
                        "price_range": "$input.budget_range",
                        "min_moq": "$input.min_order_quantity"
                    },
                    "depends_on": ["step_1_product_select"],
                    "timeout": 60
                },
                {
                    "step_id": "step_3_price_analysis",
                    "skill_alias": "price_calculator",
                    "action": "calculate_profitability",
                    "params_mapping": {
                        "supplier_quotes": "$step_2_supplier_search.quotes",
                        "platform_fees": "$input.platform_fee_rate",
                        "shipping_cost": "$input.shipping_estimate"
                    },
                    "depends_on": ["step_2_supplier_search"],
                    "timeout": 15
                }
            ],
            input_schema={
                "product_description": {"type": "string"},
                "selection_criteria": {"type": "object"},
                "budget_range": {"type": "object"}
            },
            output_schema={
                "recommended_products": {"type": "array"},
                "supplier_comparison": {"type": "object"},
                "profit_analysis": {"type": "array"}
            },
            execution_strategy="sequential",
            estimated_duration_sec=120.0
        )
        self.register_workflow(sourcing_workflow)
        
        # 工作流3: Listing生成流程
        listing_workflow = DomainWorkflow(
            workflow_id="ecommerce_listing_generation",
            name="专业Listing生成",
            description="基于产品信息和市场洞察，生成SEO优化的Amazon Listing",
            steps=[
                {
                    "step_id": "step_1_market_context",
                    "skill_alias": "trend_analyzer",
                    "action": "get_category_insights",
                    "params_mapping": {
                        "category": "$input.category",
                        "focus": "seo_keywords"
                    },
                    "depends_on": []
                },
                {
                    "step_id": "step_2_keyword_research",
                    "skill_alias": "keyword_tool",
                    "action": "generate_backend_keywords",
                    "params_mapping": {
                        "product": "$input.product_info",
                        "market_context": "$step_1_market_context.data"
                    },
                    "depends_on": ["step_1_market_context"]
                },
                {
                    "step_id": "step_3_listing_create",
                    "skill_alias": "listing_writer",
                    "action": "create_full_listing",
                    "params_mapping": {
                        "product_info": "$input.product_info",
                        "keywords": "$step_2_keyword_research.keywords",
                        "brand_guidelines": "$input.brand_voice",
                        "competitor_benchmarks": "$input.competitor_references"
                    },
                    "depends_on": ["step_2_keyword_research"]
                }
            ],
            execution_strategy="sequential",
            estimated_duration_sec=90.0
        )
        self.register_workflow(listing_workflow)
    
    async def plan_workflow(
        self, 
        task: Dict[str, Any], 
        context: AgentExecutionContext
    ) -> Optional[DomainWorkflow]:
        """根据任务选择最合适的工作流"""
        task_type = task.get("task_type")
        
        if not task_type:
            # 自动推断任务类型
            query = str(task.get("query", "") or task.get("product_description", ""))
            if any(kw in query.lower() for kw in ["选品", "研究", "分析", "趋势", "research"]):
                task_type = "research"
            elif any(kw in query.lower() for kw in ["采购", "供应商", "1688", "货源", "sourcing"]):
                task_type = "sourcing"
            elif any(kw in query.lower() for kw in ["listing", "文案", "标题", "bullet", "description"]):
                task_type = "listing"
            else:
                task_type = "research"  # 默认
        
        workflow_map = {
            "research": "ecommerce_product_research",
            "sourcing": "ecommerce_sourcing_decision",
            "listing": "ecommerce_listing_generation"
        }
        
        workflow_id = workflow_map.get(task_type)
        if workflow_id and workflow_id in self._workflows:
            return self._workflows[workflow_id]
        
        return None
    
    async def synthesize_result(
        self,
        workflow: DomainWorkflow,
        step_results: Dict[str, Any],
        original_task: Dict[str, Any]
    ) -> Dict[str, Any]:
        """综合各步骤结果，生成专业的电商分析报告"""
        
        final_output = {
            "report_type": workflow.name,
            "generated_at": datetime.utcnow().isoformat(),
            "domain": "ecommerce",
            "summary": "",
            "details": {},
            "actionable_items": [],
            "risk_alerts": []
        }
        
        # 提取各步骤的关键结果
        if "step_4_synthesis" in step_results:
            synthesis_data = step_results["step_4_synthesis"].get("data", {})
            final_output["summary"] = synthesis_data.get("executive_summary", "")
            final_output["details"]["recommendations"] = synthesis_data.get("recommendations", [])
            final_output["actionable_items"] = synthesis_data.get("next_steps", [])
        
        elif "step_3_price_analysis" in step_results:
            price_data = step_results["step_3_price_analysis"].get("data", {})
            final_output["summary"] = f"完成{len(price_data.get('products', []))}个产品的盈利性分析"
            final_output["details"]["profit_analysis"] = price_data
            final_output["actionable_items"] = [
                f"优先考虑 {p.get('name', 'Product')}: 预估毛利率 {p.get('margin', 0):.1%}"
                for p in price_data.get("products", [])[:5]
                if p.get("margin", 0) > 0.25
            ]
        
        elif "step_3_listing_create" in step_results:
            listing_data = step_results["step_3_listing_create"].get("data", {})
            final_output["summary"] = f"成功生成 {listing_data.get('title', 'N/A')} 的完整Listing"
            final_output["details"]["listing_content"] = listing_data
            final_output["actionable_items"] = [
                "审核并优化Title（确保包含核心关键词）",
                "检查Bullet Points的卖点排序",
                "准备主图和A+内容素材"
            ]
        
        else:
            # 聚合所有步骤的数据
            for step_id, result in step_results.items():
                if isinstance(result, dict) and result.get("status") == "success":
                    final_output["details"][step_id] = result.get("data", {})
            
            final_output["summary"] = f"完成工作流 '{workflow.name}' 的执行，共{len(step_results)}个步骤"
        
        return final_output
    
    async def _generate_business_insights(self, result: Dict, task: Dict) -> List[str]:
        """生成电商业务洞察"""
        insights = []
        
        domain = self.domain_capability.domain_name
        
        if "profit_analysis" in result.get("details", {}):
            avg_margin = 0
            products = result["details"]["profit_analysis"].get("products", [])
            if products:
                margins = [p.get("margin", 0) for p in products]
                avg_margin = sum(margins) / len(margins)
            
            if avg_margin > 0.35:
                insights.append(f"💰 高利润机会：平均预估毛利率达 {avg_margin:.1%}，建议优先推进")
            elif avg_margin < 0.15:
                insights.append(f"⚠️ 利润预警：当前选品毛利率偏低({avg_margin:.1%})，建议重新评估成本或寻找替代品")
        
        if "recommendations" in result.get("details", {}):
            rec_count = len(result["details"]["recommendations"])
            if rec_count > 5:
                insights.append(f"📊 市场机会丰富：发现 {rec_count} 个潜在高潜力产品方向")
        
        insights.append(f"🎯 下一步建议：使用 '/ecommerce listing' 流程为选定产品生成Listing")
        
        return insights
    
    async def _suggest_next_actions(self, result: Dict, task: Dict) -> List[str]:
        """建议下一步行动"""
        suggestions = [
            "📝 运行 'listing_generation' 工作流生成产品详情页",
            "💰 执行 'sourcing_decision' 寻找优质供应商",
            "📈 设置定期竞品监控（每周自动更新）",
            "🔍 深入分析Top 3推荐产品的Review情感"
        ]
        
        current_task_type = task.get("task_type", "")
        if current_task_type == "research":
            suggestions.insert(0, "🛒 立即对推荐产品执行采购决策分析")
        elif current_task_type == "sourcing":
            suggestions.insert(0, "✍️ 为选定的供应商产品创建Listing")

        return suggestions

    async def validate_input(self, task: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """验证输入参数"""
        errors = []
        if not task:
            errors.append("Task cannot be empty")
        return (len(errors) == 0, errors)

    async def health_check(self) -> AgentHealthCheckResult:
        """健康检查"""
        from ..base import AgentHealthStatus, AgentHealthCheckResult
        stats = await self.get_statistics()
        status = AgentHealthStatus.HEALTHY if stats["success_rate"] > 0.8 else AgentHealthStatus.DEGRADED
        return AgentHealthCheckResult(
            status=status,
            agent_id=self.agent_id,
            uptime_seconds=stats["uptime_seconds"],
            tasks_completed=stats["total_executions"],
            average_latency_ms=stats["avg_latency_ms"]
        )


__all__ = ["EcommerceDomainAgent"]
