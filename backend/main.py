"""
Wukong AI Platform - Backend Main Entry Point
悟空AI工作平台 - 企业级AI原生工作平台

Architecture: Supervisor + SubAgent Multi-Agent System
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("wukong")

# 导入配置
from config.settings import config, get_config

# 导入核心组件
from core.supervisor import WukongSupervisor, UserInput, ConversationContext, SupervisorResponse
from core.subagents import RAGSubAgent, SkillSubAgent, FileSubAgent
from core.subagents.intent import IntentSubAgent
from core.subagents.domain import (
    EcommerceDomainAgent,
    DesignDomainAgent,
    FinanceDomainAgent,
    DeveloperDomainAgent,
    ContentDomainAgent,
    CustomerServiceDomainAgent,
    DomainAgentFactory
)
from core.mcp import create_default_mcp_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("=" * 60)
    logger.info("🐵 Wukong AI Platform Starting...")
    logger.info(f"   Version: {config.APP_VERSION}")
    logger.info(f"   Environment: {config.ENVIRONMENT}")
    logger.info("=" * 60)
    
    # 初始化Supervisor
    supervisor_config = {
        "input_router": {
            "mode": "hybrid",
            "confidence_threshold": 0.75
        },
        "query_optimizer": {
            "context_window_size": 20,
            "enable_query_expansion": True
        },
        "task_planner": {
            "max_task_depth": 3
        },
        "dispatcher": {
            "scheduling_strategy": "intelligent",
            "enable_parallel_execution": True,
            "max_parallel_subtasks": 5,
            "circuit_breaker_threshold": 5,
            "enable_dynamic_replanning": True
        },
        "security": {
            "enable_permission_intersection": False,
            "enable_data_sanitization": True,
            "enable_audit_logging": True
        }
    }
    
    app.state.supervisor = WukongSupervisor(supervisor_config)
    
    # 注册SubAgents
    app.state.supervisor.register_subagent("rag", RAGSubAgent({
        "top_k": 5,
        "similarity_threshold": 0.75,
        "max_context_tokens": 4096
    }))
    
    app.state.supervisor.register_subagent("skill", SkillSubAgent({
        "skill_storage_path": "./data/skills",
        "default_timeout": 300,
        "security_scan_on_upload": True
    }))
    
    app.state.supervisor.register_subagent("file", FileSubAgent({
        "base_storage_path": "./data/files"
    }))

    # 意图识别 Agent (三层识别: 规则→语义→LLM)
    app.state.supervisor.register_subagent("intent", IntentSubAgent({
        "mode": "hybrid",
        "confidence_threshold": 0.80
    }))

    # ========== 注册 Domain Agents (业务领域专家) =========
    # Domain Agent 是真正的业务智能体，由 Skill 驱动，可调用基础设施Agent
    domain_factory = DomainAgentFactory(app.state.supervisor)

    # 电商运营专家
    ecommerce_agent = EcommerceDomainAgent()
    app.state.supervisor.register_subagent("domain-ecommerce", ecommerce_agent)
    domain_factory.register_domain(ecommerce_agent)

    # 设计创意专家
    design_agent = DesignDomainAgent()
    app.state.supervisor.register_subagent("domain-design", design_agent)
    domain_factory.register_domain(design_agent)

    # 财税管理专家
    finance_agent = FinanceDomainAgent()
    app.state.supervisor.register_subagent("domain-finance", finance_agent)
    domain_factory.register_domain(finance_agent)

    # 开发者专家 (NEW)
    developer_agent = DeveloperDomainAgent()
    app.state.supervisor.register_subagent("domain-developer", developer_agent)
    domain_factory.register_domain(developer_agent)

    # 内容创作专家 (NEW)
    content_agent = ContentDomainAgent()
    app.state.supervisor.register_subagent("domain-content", content_agent)
    domain_factory.register_domain(content_agent)

    # 客服专家 (NEW)
    cs_agent = CustomerServiceDomainAgent()
    app.state.supervisor.register_subagent("domain-customer_service", cs_agent)
    domain_factory.register_domain(cs_agent)

    # ========== 初始化 MCP Client (外部系统集成) ==========
    mcp_client = await create_default_mcp_client()
    logger.info(f"🔌 MCP Client initialized with {len(mcp_client.servers)} servers")

    # 为所有 Domain Agent 注入基础设施 Agent 引用 + MCP Client
    all_domain_agents = [
        ecommerce_agent, design_agent, finance_agent,
        developer_agent, content_agent, cs_agent
    ]

    infra_agents = {
        "rag": RAGSubAgent({"top_k": 5, "similarity_threshold": 0.75}),
        "skill": SkillSubAgent({"skill_storage_path": "./data/skills"}),
        "file": FileSubAgent({"base_storage_path": "./data/files"}),
        "intent": IntentSubAgent({"mode": "hybrid"}),
        "mcp": mcp_client
    }

    for domain_agent in all_domain_agents:
        domain_agent.set_infra_agents(infra_agents)

    app.state.domain_factory = domain_factory
    app.state.mcp_client = mcp_client
    logger.info(f"📦 Registered {len(all_domain_agents)} Domain Agents: [ecommerce, design, finance, developer, content, customer_service]")
    
    # 初始化所有组件
    await app.state.supervisor.initialize()
    
    logger.info("✅ Wukong AI Platform Ready!")
    logger.info("=" * 60)
    
    yield
    
    logger.info("🛑 Wukong AI Platform Shutting Down...")


app = FastAPI(
    title="Wukong AI Platform API",
    description="企业级AI原生工作平台 - Supervisor+SubAgent多智能体架构",
    version=config.APP_VERSION,
    lifespan=lifespan
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "service": "wukong-api",
        "version": config.APP_VERSION,
        "timestamp": time.time()
    }


@app.get("/health/ready")
async def readiness_check():
    """就绪检查（包含组件状态）"""
    components = {}
    
    if hasattr(app.state, 'supervisor') and app.state.supervisor:
        components["supervisor"] = "ready"
        components["registered_agents"] = list(app.state.supervisor.agent_pool.keys())
    else:
        components["supervisor"] = "not_initialized"
    
    all_ready = all(v == "ready" for v in components.values())
    
    return JSONResponse(
        status_code=200 if all_ready else 503,
        content={
            "status": "ready" if all_ready else "not_ready",
            "components": components
        }
    )


@app.post("/api/v1/chat/completions")
async def chat_completion(request: dict):
    """
    核心对话接口 - 处理用户输入并通过Supervisor调度
    
    Request Body:
    {
        "messages": [{"role": "user", "content": "..."}],
        "stream": false,
        "options": {
            "use_rag": true,
            "skill_ids": []
        }
    }
    """
    try:
        messages = request.get("messages", [])
        if not messages:
            raise HTTPException(status_code=400, detail="messages is required")
        
        user_message = messages[-1]
        if user_message.get("role") != "user":
            raise HTTPException(status_code=400, detail="Last message must be from user")
        
        conversation_history = [
            {"role": msg.get("role"), "content": msg.get("content")}
            for msg in messages[:-1]
        ]
        
        user_input = UserInput(
            user_id=request.get("user_id", "anonymous"),
            content=user_message.get("content", ""),
            input_type="text"
        )
        
        context = ConversationContext(
            session_id=request.get("conversation_id"),
            conversation_history=conversation_history
        )
        
        response: SupervisorResponse = await app.state.supervisor.process_user_input(
            user_input=user_input,
            context=context
        )
        
        if not response.success:
            raise HTTPException(status_code=500, detail=response.error)
        
        return {
            "id": f"chatcmpl-{response.trace_id}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": "wukong-supervisor-v1",
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": response.content
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": len(user_message.get("content", "")),
                "completion_tokens": len(response.content or ""),
                "total_tokens": len(user_message.get("content", "")) + len(response.content or "")
            },
            "metadata": response.metadata
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat completion error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/agents/status")
async def get_agents_status():
    """获取所有注册的SubAgent状态"""
    if not hasattr(app.state, 'supervisor'):
        raise HTTPException(status_code=503, detail="Supervisor not initialized")
    
    agents_status = {}
    for agent_type, agent_instance in app.state.supervisor.agent_pool.items():
        try:
            health = await agent_instance.health_check()
            stats = await agent_instance.get_statistics()
            agents_status[agent_type] = {
                "health": health.status.value,
                "capability": agent_instance.capability.name,
                "uptime_seconds": health.uptime_seconds,
                "total_executions": stats["total_executions"],
                "success_rate": stats["success_rate"],
                "avg_latency_ms": stats["avg_latency_ms"]
            }
        except Exception as e:
            agents_status[agent_type] = {"error": str(e)}
    
    return {"agents": agents_status}


@app.get("/api/v1/skills/installed")
async def list_installed_skills():
    """列出已安装的技能（通过Skill Agent）"""
    skill_agent = app.state.supervisor.agent_pool.get("skill")
    if not skill_agent:
        return {"skills": [], "message": "Skill agent not available"}
    
    return {
        "skills": list(skill_agent._skill_registry.keys()),
        "count": len(skill_agent._skill_registry)
    }


@app.get("/api/v1/domains")
async def list_available_domains():
    """获取所有可用的业务领域(Domain)"""
    if not hasattr(app.state, 'domain_factory'):
        raise HTTPException(status_code=503, detail="Domain factory not initialized")
    
    return {
        "domains": app.state.domain_factory.list_available_domains(),
        "total": len(app.state.domain_factory._domain_registry)
    }


@app.get("/api/v1/domains/{domain_name}/info")
async def get_domain_info(domain_name: str):
    """获取指定领域的详细信息"""
    if not hasattr(app.state, 'domain_factory'):
        raise HTTPException(status_code=503, detail="Domain factory not initialized")

    domain_agent = app.state.domain_factory.get_domain(domain_name)
    if not domain_agent:
        raise HTTPException(status_code=404, detail=f"Domain '{domain_name}' not found")

    cap = domain_agent.domain_capability
    stats = await domain_agent.get_statistics()
    workflows = list(domain_agent._workflows.keys())
    skills = list(domain_agent._skill_bindings.keys())

    return {
        "domain_id": domain_agent.agent_id,
        "capability": {
            "domain": cap.domain_name,
            "display_name": cap.display_name,
            "version": cap.version,
            "expertise_areas": cap.expertise_areas,
            "typical_tasks": cap.typical_tasks[:10],
            "tags": cap.tags,
            "rating": cap.rating
        },
        "statistics": stats,
        "registered_workflows": workflows,
        "bound_skills": skills,
        "required_infra_agents": cap.required_infra_agents
    }


@app.get("/api/v1/mcp/status")
async def get_mcp_status():
    """获取MCP服务器连接状态"""
    if not hasattr(app.state, 'mcp_client'):
        return {"status": "not_initialized", "servers": []}

    mcp_client = app.state.mcp_client
    servers_info = []

    for server_name, server in mcp_client.servers.items():
        try:
            capability = server.get_capability()
            tools = await server.list_tools()
            servers_info.append({
                "name": server_name,
                "status": "connected",
                "capability": capability,
                "tool_count": len(tools),
                "tools": [t.name for t in tools]
            })
        except Exception as e:
            servers_info.append({
                "name": server_name,
                "status": "error",
                "error": str(e)
            })

    return {
        "status": "initialized",
        "total_servers": len(servers_info),
        "servers": servers_info
    }


@app.get("/api/v1/intent/domains")
async def list_intent_domains():
    """获取意图识别Agent已注册的领域列表"""
    intent_agent = app.state.supervisor.agent_pool.get("intent")
    if not intent_agent:
        return {"domains": [], "message": "Intent agent not available"}

    return {
        "registered_domains": intent_agent._registered_domains,
        "domain_keywords": intent_agent._domain_keywords,
        "total_domains": len(intent_agent._registered_domains)
    }


if __name__ == "__main__":
    import uvicorn
    
    print("""
    ╔════════════════════════════════════════════════╗
    ║           🐵 Wukong AI Platform                 ║
    ║     企业级AI原生工作平台 | Supervisor+SubAgent    ║
    ╠════════════════════════════════════════════════╣
    ║  API: http://localhost:8000                     ║
    ║  Docs: http://localhost:8000/docs               ║
    ║  Health: http://localhost:8000/health           ║
    ╚════════════════════════════════════════════════╝
    """)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=config.DEBUG,
        log_level=config.LOG_LEVEL.lower()
    )
