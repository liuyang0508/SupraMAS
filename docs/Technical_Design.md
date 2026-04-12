# Wukong AI - 技术方案文档 (Technical Design Document)

## 文档信息

| 项目 | 内容 |
|------|------|
| 版本 | v1.0.0 |
| 日期 | 2026-04-12 |
| 架构模式 | Supervisor + SubAgent Multi-Agent System |
| 状态 | 设计完成 |

---

## 1. 技术选型与决策理由

### 1.1 核心技术栈

#### 🎯 后端核心层

| 组件 | 选型 | 版本 | 决策理由 | 替代方案(未选用) |
|-----|------|------|---------|-----------------|
| **语言** | **Python** | 3.11+ | AI生态最丰富、异步性能强、开发效率高 | Go(生态不足)、Node.js(AI库少) |
| **Web框架** | **FastAPI** | 0.109+ | 原生异步、自动OpenAPI文档、Pydantic校验、Starlette性能 | Flask(同步)、Django(重) |
| **任务队列** | **Celery** | 5.3+ | 成熟稳定、支持Redis/RabbitMQ、定时任务、监控完善 | Dramatiq(轻量但功能少) |
| **ASGI服务器** | **Uvicorn** | 0.27+ | 高性能异步、热重载、WebSocket原生支持 | Gunicorn(需额外配置) |

#### 🧠 AI/LLM 层

| 组件 | 选型 | 版本 | 决策理由 | 特性说明 |
|-----|------|------|---------|---------|
| **LLM编排框架** | **LangChain** | 0.1+ | 工具链完整、社区活跃、Agent支持好 | 抽象层过厚时可用原生API |
| **工作流引擎** | **LangGraph** | 0.0.20+ | 图状态机、条件分支、循环、检查点恢复 | 比LangChain Agent更可控 |
| **模型推理服务** | **vLLM** | 0.4+ | PagedAttention、高吞吐、连续批处理 | Ollama(简单但性能一般) |
| **Embedding模型** | **BAAI/bge-large-zh-v1.5** | - | 中文语义理解SOTA级、1024维向量 | OpenAI embedding(成本高、延迟大) |
| **Reranker模型** | **cross-encoder/ms-marco-MiniLM-L-6-v2** | - | 轻量高效、适合中文场景 | Cohere Rerank(API调用) |
| **多模型网关** | **LiteLLM** | 1.0+ | 统一接口、100+模型支持、负载均衡、Fallback | 自建适配器(维护成本高) |

#### 💾 数据存储层

| 组件 | 选型 | 用途 | 规模预估 | 选型理由 |
|-----|------|------|---------|---------|
| **PostgreSQL 15+** | 主数据库 | 用户、技能、任务、会话等结构化数据 | 初始100GB | ACID事务、JSONB支持、全文检索、成熟稳定 |
| **Milvus 2.3+** | 向量数据库 | 文档向量、记忆向量、技能向量 | 初始100万条 | 专为向量设计、IVF_FLAT/PQ索引、分布式支持 |
| **Redis 7+** | 缓存/会话 | 会话状态、Token缓存、Rate Limiting、Pub/Sub | 8GB内存 | 亚毫秒延迟、数据结构丰富、持久化选项 |
| **MinIO** | 对象存储 | 文件快照、技能包、用户上传文件 | 初始1TB | S3兼容、高性能、自托管、无厂商锁定 |

#### 🔌 集成与通信层

| 组件 | 选型 | 用途 | 选型理由 |
|-----|------|------|---------|
| **MCP协议** | 官方SDK | 外部系统集成 | 标准化协议、生态丰富、类型安全 |
| **消息队列** | **RabbitMQ 3.12+** | Agent间异步通信 | 可靠投递、消息确认、死信队列、管理UI友好 |
| **gRPC** | 内部服务通信 | Supervisor↔SubAgent高性能调用 | Protobuf高效序列化、流式传输、强类型 |
| **WebSocket** | 前端实时通信 | 流式输出、任务进度推送 | 全双工、浏览器原生支持 |

#### 🛡️ 安全层

| 组件 | 选型 | 用途 | 选型理由 |
|-----|------|------|---------|
| **OAuth 2.0 + OIDC** | 认证授权 | 企业SSO集成、JWT Token | 行业标准、企业友好、可对接钉钉/飞书 |
| **Docker** | 技能沙箱 | 技能隔离执行 | 资源限制、网络隔离、镜像标准化 |
| **Python-restrict** | 代码安全扫描 | 技能代码静态分析 | 检测危险操作(import os, subprocess等) |
| **Vault** | 密钥管理 | API Key、数据库密码等敏感信息 | 动态密钥、审计日志、自动轮换 |

#### 🖥️ 前端层

| 组件 | 选型 | 版本 | 用途 | 选型理由 |
|-----|------|------|------|---------|
| **React 18** | UI框架 | 18.2 | 组件化、虚拟DOM、生态庞大 | Vue3(也优秀但团队更熟悉React) |
| **TypeScript** | 类型系统 | 5.3+ | 类型安全、IDE支持、重构友好 | JavaScript(类型缺失) |
| **Vite** | 构建工具 | 5.x | 极速HMR、ESBuild、开箱即用 | Webpack(慢) |
| **Tailwind CSS** | 样式方案 | 3.4+ | 原子化CSS、快速原型、体积小 | Styled Components(运行时开销) |
| **Zustand** | 状态管理 | 4.4+ | 轻量、简洁、TypeScript友好 | Redux(样板代码多) |
| **React Query** | 服务端状态 | 5.x | 缓存、自动刷新、乐观更新 | SWR(功能类似) |
| **shadcn/ui** | 组件库 | latest | 可定制、基于Radix、无样式锁定 | Ant Design(定制困难) |

---

### 1.2 架构决策记录 (ADR)

#### ADR-001: 选择Supervisor+SubAgent而非平等协作

**背景**：需要选择Multi-Agent系统的协作模式

**决策**：采用 **Supervisor (中央调度) + SubAgent (专业执行)** 的层级架构

**理由**：

```mermaid
graph TB
    A[用户输入] --> B[Supervisor]
    B --> C[意图路由]
    C --> D[任务分解]
    D --> E[调度分发]
    E --> F[SubAgent A]
    E --> G[SubAgent B]
    E --> H[SubAgent C]
    F --> I[结果聚合]
    G --> I
    H --> I
    I --> J[最终输出]
    
    style B fill:#f9f,stroke:#333,stroke-width:4px
```

✅ **优势**：
1. **集中管控**：权限、审计、监控统一在Supervisor层
2. **高效协调**：避免Agent间的协商开销，直接指令式调度
3. **故障隔离**：单个SubAgent失败不影响整体，Supervisor可降级处理
4. **企业适配**：符合企业"集中管控"的治理理念
5. **可观测性**：全链路Trace集中在Supervisor，易于调试

❌ **劣势及缓解**：
- 单点瓶颈 → Supervisor无状态化 + 水平扩展
- 扩展性受限 → SubAgent可独立扩展，Skill动态注册

**替代方案对比**：

| 方案 | 协调效率 | 故障隔离 | 企业适配 | 复杂度 |
|-----|---------|---------|---------|-------|
| **★ Supervisor+SubAgent** | ★★★★★ | ★★★★☆ | ★★★★★ | ★★★☆☆ |
| 平等协商(Peer-to-Peer) | ★★☆☆☆ | ★★★★★ | ★★☆☆☆ | ★★★★★ |
| 黑板模式(Blackboard) | ★★★☆☆ | ★★★☆☆ | ★★☆☆☆ | ★★★★☆ |
| 层级主从(Hierarchy) | ★★★★☆ | ★★★☆☆ | ★★★★☆ | ★★★☆☆ |

---

#### ADR-002: 选择LangGraph而非纯LangChain Agent

**背景**：选择任务编排和工作流引擎

**决策**：采用 **LangGraph** 作为核心工作流引擎

**理由**：

```python
# LangGraph 示例：Supervisor的状态机定义
from langgraph.graph import StateGraph, END

workflow = StateGraph(SupervisorState)

# 定义节点
workflow.add_node("input_router", input_router_node)
workflow.add_node("query_optimizer", query_optimizer_node)
workflow.add_node("task_planner", task_planner_node)
workflow.add_node("security_check", security_guard_node)
workflow.add_node("dispatcher", execution_dispatcher_node)
workflow.add_node("result_aggregator", result_aggregator_node)

# 定义边（包含条件分支）
workflow.set_entry_point("input_router")
workflow.add_edge("input_router", "query_optimizer")
workflow.add_conditional_edges(
    "query_optimizer",
    route_after_optimization,
    {
        "needs_clarification": "result_aggregator",  # 需要澄清→直接返回问题
        "proceed": "task_planner"                     # 继续→任务规划
    }
)
workflow.add_edge("task_planner", "security_check")
workflow.add_conditional_edges(
    "security_check",
    security_decision,
    {
        "approved": "dispatcher",
        "denied": "result_aggregator"
    }
)
workflow.add_edge("dispatcher", "result_aggregator")
workflow.add_edge("result_aggregator", END)

app = workflow.compile()
```

✅ **优势**：
1. **显式状态机**：流程可视化、调试容易
2. **循环支持**：支持重试、回退、重新规划
3. **检查点机制**：断点续传、长时间任务恢复
4. **人机协同**：可在任意节点暂停等待人工输入
5. **类型安全**：TypedDict定义状态结构

---

#### ADR-003: 选择Milvus而非Pinecone/Qdrant

**背景**：选择向量数据库用于RAG和记忆系统

**决策**：采用 **Milvus** 开源版本（可升级至云服务Zilliz）

**理由**：

| 维度 | Milvus | Pinecone | Qdrant | Weaviate |
|-----|--------|----------|--------|----------|
| **部署方式** | ✅ 自托管/云 | ❌ 仅云 | ✅ 自托管/云 | ✅ 自托管/云 |
| **成本控制** | ✅ 完全可控 | 💰 按用量付费 | ✅ 可控 | ✅ 可控 |
| **中文优化** | ✅ 原生支持 | ⚠️ 一般 | ⚠️ 一般 | ⚠️ 一般 |
| **规模能力** | 十亿级向量 | 十亿级 | 百万级优化 | 千万级 |
| **索引类型** | IVF_FLAT/PQ/HNSW/... | HNSW | HNSW | HNSW |
| **社区活跃度** | ★★★★★ | ★★★★☆ | ★★★★☆ | ★★★☆☆ |
| **企业案例** | 阿里、腾讯、平安 | OpenAI、Notion | ... | ... |

**关键特性**：
- Collection分区（按租户隔离）
- 多向量字段（Dense+Sparse混合检索）
- TTL自动过期（会话向量清理）
- 数据一致性级别可配置

---

## 2. 系统架构设计

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              用户层 (User Layer)                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Web App    │  │   Mobile PWA │  │   API Client │  │   IM Bot     │     │
│  │  (React)     │  │              │  │  (REST/gRPC) │  │ (钉钉/飞书)  │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
└─────────┼─────────────────┼─────────────────┼─────────────────┼─────────────┘
          │                 │                 │                 │
          ▼                 ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            接入层 (Gateway Layer)                            │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                    Kong API Gateway / Nginx                          │   │
│  │  • Rate Limiting  • SSL Termination  • JWT Validation               │   │
│  │  • Request Routing  • Load Balancing   • API Versioning             │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           服务层 (Service Layer)                             │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      FastAPI Application                            │   │
│  │  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐        │   │
│  │  │ Chat API  │  │ Task API  │  │ Skill API │  │ File API  │        │   │
│  │  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘        │   │
│  │        └───────────────┴───────────────┴───────────────┘            │   │
│  │                              │                                      │   │
│  │  ┌───────────────────────────────────────────────────────────────┐  │   │
│  │  │                  WebSocket Handler (流式输出)                  │  │   │
│  │  └───────────────────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        核心引擎层 (Core Engine Layer)                        │
│                                                                             │
│  ╔═════════════════════════════════════════════════════════════════════╗   │
║  ║                        SUPERVISOR (中央调度器)                       ║   │
║  ║  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐      ║   │
║  ║  │Layer 1: │ │Layer 2: │ │Layer 3: │ │Layer 4: │ │Layer 5: │      ║   │
║  ║  │Input    │ │Query    │ │Task     │ │Exec     │ │Security │      ║   │
║  ║  │Router   │ │Optimizer│ │Planner  │ │Dispatch │ │Guard    │      ║   │
║  ║  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘      ║   │
║  ║       └───────────┴───────────┴───────────┴───────────┘           ║   │
║  ╚═════════════════════════════════════════════════════════════════════╝   │
│                                    │                                        │
│         ┌──────────────────────────┼──────────────────────────┐           │
│         │                          │                          │           │
│         ▼                          ▼                          ▼           │
│  ┌─────────────┐           ┌─────────────┐           ┌─────────────┐      │
│  │ Intent Agent│           │  RAG Agent  │           │ Skill Agent │      │
│  │ (意图识别)   │           │ (检索增强)   │           │ (技能执行)   │      │
│  └─────────────┘           └─────────────┘           └─────────────┘      │
│  ┌─────────────┐           ┌─────────────┐           ┌─────────────┐      │
│  │  File Agent │           │  MCP Agent  │           │Memory Agent │      │
│  │ (文件处理)   │           │ (外部集成)   │           │ (长期记忆)   │      │
│  └─────────────┘           └─────────────┘           └─────────────┘      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         基础设施层 (Infrastructure Layer)                    │
│                                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │ PostgreSQL  │  │   Milvus    │  │    Redis    │  │    MinIO    │       │
│  │ (主数据库)   │  │ (向量数据库) │  │ (缓存/会话)  │  │ (对象存储)   │       │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘       │
│                                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │  RabbitMQ   │  │   Docker    │  │   vLLM      │  │  Prometheus │       │
│  │ (消息队列)   │  │ (技能沙箱)  │  │ (模型推理)   │  │  +Grafana  │       │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Supervisor 五层职责模型详解

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Supervisor Internal Architecture                   │
│                                                                     │
│  User Input                                                         │
│      │                                                              │
│      ▼                                                              │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  LAYER 1: Input Router (意图路由层)                          │   │
│  │  ├─ Intent Classification (意图分类)                        │   │
│  │  ├─ Slot Extraction (槽位提取)                              │   │
│  │  ├─ Ambiguity Detection (歧义检测)                          │   │
│  │  └─ Output: RoutingDecision {target_agent, confidence}       │   │
│  └─────────────────────────────────────────────────────────────┘   │
│      │                                                              │
│      ▼                                                              │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  LAYER 2: Query Optimizer (查询优化层)                       │   │
│  │  ├─ Coreference Resolution (指代消解)                       │   │
│  │  ├─ Ellipsis Completion (省略补全)                          │   │
│  │  ├─ Semantic Normalization (语义规范化)                     │   │
│  │  ├─ Query Expansion (查询扩展)                              │   │
│  │  └─ Output: OptimizedQuery {rewritten, context_enriched}     │   │
│  └─────────────────────────────────────────────────────────────┘   │
│      │                                                              │
│      ▼                                                              │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  LAYER 3: Task Planner (任务规划层)                          │   │
│  │  ├─ Task Decomposition (任务分解 - LLM驱动)                  │   │
│  │  ├─ Dependency Analysis (依赖分析)                           │   │
│  │  ├─ DAG Construction (构建有向无环图)                        │   │
│  │  ├─ Resource Estimation (资源预估)                           │   │
│  │  └─ Output: TaskPlan {subtasks[], dag, resources}            │   │
│  └─────────────────────────────────────────────────────────────┘   │
│      │                                                              │
│      ▼                                                              │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  LAYER 4: Execution Dispatcher (执行调度层)                   │   │
│  │  ├─ Intelligent Scheduling (智能调度)                        │   │
│  │  │   ├─ Capability Match Scoring (能力匹配评分)              │   │
│  │  │   ├─ Load Balancing (负载均衡)                           │   │
│  │  │   └─ Priority Queuing (优先级队列)                       │   │
│  │  ├─ Parallel/Serial Execution (并行/串行执行)                │   │
│  │  ├─ Progress Monitoring (进度监控)                           │   │
│  │  ├─ Error Handling & Retry (错误处理与重试)                  │   │
│  │  └─ Dynamic Replanning (动态重规划)                          │   │
│  └─────────────────────────────────────────────────────────────┘   │
│      │                                                              │
│      ▼                                                              │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  LAYER 5: Security Guard (安全审计层)                         │   │
│  │  ├─ Permission Intersection Check (权限交集检查)              │   │
│  │  ├─ Data Sanitization (敏感数据脱敏)                         │   │
│  │  ├─ Operation Audit Logging (操作审计日志)                   │   │
│  │  ├─ Threat Detection (威胁检测)                              │   │
│  │  └─ Output: SecurityDecision {allowed/denied, reason}        │   │
│  └─────────────────────────────────────────────────────────────┘   │
│      │                                                              │
│      ▼                                                              │
│  Final Response to User                                             │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.3 数据流架构

```mermaid
sequenceDiagram
    participant U as User
    participant GW as API Gateway
    participant SV as Supervisor
    participant IR as Input Router
    participant QO as Query Optimizer
    participant TP as Task Planner
    participant SG as Security Guard
    participant ED as Dispatcher
    participant SA as SubAgents
    participant RA as Result Aggregator
    
    U->>GW: POST /api/v1/chat (user message)
    GW->>SV: Authenticated Request
    SV->>IR: Layer 1: Route Input
    IR-->>SV: RoutingDecision
    
    SV->>QO: Layer 2: Optimize Query
    QO-->>SV: OptimizedQuery
    
    SV->>TP: Layer 3: Plan Tasks
    TP-->>SV: TaskPlan (DAG)
    
    loop For each task batch
        SV->>SG: Layer 5: Security Check
        SG-->>SV: SecurityDecision
        
        alt Security Approved
            SV->>ED: Layer 4: Dispatch Tasks
            ED->>SA: Execute SubTasks (parallel/serial)
            SA-->>ED: SubTask Results
            ED-->>SV: Batch Results
        else Security Denied
            SV-->>SV: Log & Skip Task
        end
    end
    
    SV->>RA: Aggregate Results
    RA-->>SV: FinalResponse
    SV-->>GW: Response (streaming or complete)
    GW-->>U: HTTP/SSE Response
```

---

## 3. 详细模块设计

### 3.1 Supervisor 核心模块

#### 3.1.1 状态定义 (State TypedDict)

```python
from typing import TypedDict, List, Dict, Any, Optional
from enum import Enum

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"

class SupervisorState(TypedDict):
    """Supervisor的全局状态 - 在LangGraph各节点间传递"""
    
    # 输入相关
    user_id: str
    session_id: str
    original_input: str
    input_type: str  # text, voice, file_upload
    
    # Layer 1: Input Router 输出
    intent: Optional[str]
    intent_confidence: float
    extracted_slots: Dict[str, Any]
    routing_decision: Optional[Dict[str, Any]]
    needs_clarification: bool
    clarification_question: Optional[str]
    
    # Layer 2: Query Optimizer 输出
    optimized_query: Optional[str]
    query_rewrite_history: List[Dict[str, str]]
    expanded_entities: List[str]
    
    # Layer 3: Task Planner 输出
    task_plan: Optional[Dict[str, Any]]
    subtasks: List[Dict[str, Any]]
    task_dag: Optional[Dict[str, Any]]  # DAG adjacency list
    estimated_duration_seconds: float
    resource_requirements: Dict[str, Any]
    
    # Layer 4: Dispatcher 状态
    current_batch: int
    total_batches: int
    completed_subtasks: List[Dict[str, Any]]
    failed_subtasks: List[Dict[str, Any]]
    subtask_results: Dict[str, Any]
    execution_metrics: Dict[str, float]
    
    # Layer 5: Security Guard 输出
    security_decisions: Dict[str, bool]
    audit_log_entries: List[Dict[str, Any]]
    sanitized_data: bool
    
    # 最终输出
    final_response: Optional[str]
    response_type: str  # text, structured_data, file_ref, action_required
    metadata: Dict[str, Any]
    trace_id: str
    timestamp_start: float
    timestamp_end: Optional[float]
```

#### 3.1.2 核心类实现骨架

```python
# backend/core/supervisor/__init__.py
from typing import Dict, Any, Optional, List
import asyncio
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum

@dataclass
class RoutingDecision:
    """Layer 1 输出"""
    target_agent_type: str
    confidence: float
    alternative_agents: List[str] = field(default_factory=list)
    reasoning: str = ""

@dataclass
class OptimizedQuery:
    """Layer 2 输出"""
    rewritten_query: str
    original_query: str
    applied_transformations: List[str] = field(default_factory=list)
    context_used: List[str] = field(default_factory=list)
    expansion_terms: List[str] = field(default_factory=list)

@dataclass
class SubTask:
    """子任务定义"""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    agent_type: str = ""
    action: str = ""
    params: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[str] = field(default_factory=list)
    priority: int = 5  # 1-10, 10最高
    timeout_seconds: float = 30.0
    retry_count: int = 0
    max_retries: int = 3
    status: str = "pending"

@dataclass
class TaskPlan:
    """Layer 3 输出"""
    plan_id: str = field(default_factory=lambda: f"plan_{uuid.uuid4().hex[:8]}")
    subtasks: List[SubTask] = field(default_factory=list)
    dag_adjacency: Dict[str, List[str]] = field(default_factory=dict)
    execution_strategy: str = "auto"  # auto, parallel, serial, mixed
    estimated_total_time: float = 0.0
    required_capabilities: List[str] = field(default_factory=list)

@dataclass
class SecurityDecision:
    """Layer 5 输出"""
    allowed: bool
    reason: str = ""
    risk_level: str = "low"  # low, medium, high, critical
    required_approval: bool = False
    sanitized_action: Optional[Dict[str, Any]] = None
    audit_entry: Optional[Dict[str, Any]] = None


class WukongSupervisor:
    """
    悟空Supervisor - 中央调度器
    
    采用五层职责模型：
    Layer 1: Input Router - 意图识别与路由
    Layer 2: Query Optimizer - 查询改写与优化
    Layer 3: Task Planner - 任务分解与规划
    Layer 4: Execution Dispatcher - 执行调度与监控
    Layer 5: Security Guard - 权限管控与审计
    """
    
    def __init__(self, config: SupervisorConfig):
        self.config = config
        self.trace_id_generator = TraceIDGenerator()
        
        # 各层组件（延迟初始化）
        self._input_router: Optional[InputRouter] = None
        self._query_optimizer: Optional[QueryOptimizer] = None
        self._task_planner: Optional[TaskPlanner] = None
        self._execution_dispatcher: Optional[ExecutionDispatcher] = None
        self._security_guard: Optional[SecurityGuard] = None
        
        # SubAgent池
        self.agent_pool: Dict[str, BaseSubAgent] = {}
        
        # LangGraph工作流
        self.workflow = None
        self.compiled_app = None
    
    async def initialize(self):
        """初始化所有组件"""
        # 初始化各层组件
        self._input_router = InputRouter(self.config.input_router)
        self._query_optimizer = QueryOptimizer(self.config.query_optimizer)
        self._task_planner = TaskPlanner(self.config.task_planner)
        self._execution_dispatcher = ExecutionDispatcher(
            self.config.dispatcher,
            agent_pool=self.agent_pool
        )
        self._security_guard = SecurityGuard(self.config.security)
        
        # 注册SubAgents
        await self._register_subagents()
        
        # 编译LangGraph工作流
        self._build_workflow()
        self.compiled_app = self.workflow.compile()
    
    async def process_user_input(
        self, 
        user_input: UserInput,
        context: Optional[ConversationContext] = None
    ) -> SupervisorResponse:
        """
        处理用户输入的主入口
        
        Args:
            user_input: 用户输入（文本/语音/文件）
            context: 对话上下文
            
        Returns:
            SupervisorResponse: 包含响应内容、元数据、执行轨迹
        """
        trace_id = self.trace_id_generator.generate()
        start_time = time.time()
        
        # 构建初始状态
        initial_state: SupervisorState = {
            "user_id": user_input.user_id,
            "session_id": context.session_id if context else self._new_session(),
            "original_input": user_input.content,
            "input_type": user_input.type,
            
            # 待填充的状态字段
            "intent": None,
            "intent_confidence": 0.0,
            "extracted_slots": {},
            "routing_decision": None,
            "needs_clarification": False,
            "clarification_question": None,
            
            "optimized_query": None,
            "query_rewrite_history": [],
            "expanded_entities": [],
            
            "task_plan": None,
            "subtasks": [],
            "task_dag": None,
            "estimated_duration_seconds": 0.0,
            "resource_requirements": {},
            
            "current_batch": 0,
            "total_batches": 0,
            "completed_subtasks": [],
            "failed_subtasks": [],
            "subtask_results": {},
            "execution_metrics": {},
            
            "security_decisions": {},
            "audit_log_entries": [],
            "sanitized_data": False,
            
            "final_response": None,
            "response_type": "text",
            "metadata": {},
            "trace_id": trace_id,
            "timestamp_start": start_time,
            "timestamp_end": None
        }
        
        # 注入上下文到各层
        if context:
            self._query_optimizer.set_context(context)
            self._security_guard.set_user_context(user_input.user_id, context)
        
        try:
            # 通过LangGraph执行工作流
            final_state = await self.compiled_app.ainvoke(initial_state)
            
            # 构建响应
            return SupervisorResponse(
                content=final_state["final_response"],
                response_type=final_state["response_type"],
                metadata=final_state["metadata"],
                trace_id=trace_id,
                execution_time=time.time() - start_time,
                state=final_state
            )
            
        except Exception as e:
            return SupervisorResponse.error(
                error=str(e),
                trace_id=trace_id,
                execution_time=time.time() - start_time
            )
```

---

### 3.2 SubAgent 基类体系

```python
# backend/core/subagents/base.py
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import time
import logging

logger = logging.getLogger(__name__)

class AgentHealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

@dataclass
class AgentCapability:
    """Agent能力声明"""
    name: str
    description: str
    version: str = "1.0.0"
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)
    supported_intents: List[str] = field(default_factory=list)
    max_concurrent_tasks: int = 5
    estimated_latency_ms: int = 1000
    required_resources: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AgentExecutionContext:
    """SubAgent执行上下文 - 由Supervisor注入"""
    supervisor_id: str
    session_id: str
    trace_id: str
    task_id: str
    security_token: str
    timeout_seconds: float
    priority: int = 5
    memory_bank: Optional['MemoryBank'] = None
    communication_channel: Optional['AgentChannel'] = None
    metrics_collector: Optional['MetricsCollector'] = None

@dataclass
class AgentExecutionResult:
    """SubAgent执行结果"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    error_type: Optional[str] = None  # timeout, permission_denied, invalid_input, etc.
    metrics: Dict[str, Any] = field(default_factory=dict)
    artifacts: List[Any] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    should_retry: bool = False
    retry_delay: float = 0.0

@dataclass
class AgentHealthCheckResult:
    """健康检查结果"""
    status: AgentHealthStatus
    agent_id: str
    uptime_seconds: float
    tasks_completed: int
    tasks_failed: int
    average_latency_ms: float
    queue_size: int
    resource_usage: Dict[str, float]
    last_error: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)


class BaseSubAgent(ABC):
    """
    SubAgent基类 - 所有专业Agent必须继承
    
    强制实现标准化接口，确保与Supervisor的无缝协作。
    
    设计原则：
    1. 单一职责：每个Agent专注一个领域
    2. 接口标准化：统一的execute/health_check/validate接口
    3. 可观测性：内置指标收集和日志
    4. 弹性设计：支持超时、重试、降级
    """
    
    def __init__(self, agent_id: str, capability: AgentCapability):
        self.agent_id = agent_id
        self.capability = capability
        self.state = "idle"
        self.task_queue: asyncio.Queue = asyncio.Queue(maxsize=capability.max_concurrent_tasks * 2)
        self._start_time = time.time()
        self._execution_history: List[Dict[str, Any]] = []
        self._lock = asyncio.Lock()
        
        logger.info(f"[{agent_id}] Initialized with capability: {capability.name}")
    
    @abstractmethod
    async def execute(
        self, 
        task: Dict[str, Any], 
        context: AgentExecutionContext
    ) -> AgentExecutionResult:
        """
        执行任务的核心方法 - 必须由子类实现
        
        Args:
            task: 任务参数字典
            context: 执行上下文（含认证、超时、监控等）
            
        Returns:
            AgentExecutionResult: 执行结果
        """
        pass
    
    @abstractmethod
    async def validate_input(self, task: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        验证输入参数的有效性
        
        Returns:
            (is_valid, error_messages)
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> AgentHealthCheckResult:
        """返回Agent的健康状态"""
        pass
    
    def get_supported_intents(self) -> List[str]:
        """返回支持的意图列表"""
        return self.capability.supported_intents
    
    def get_capability(self) -> AgentCapability:
        """返回Agent的能力声明"""
        return self.capability
    
    async def safe_execute(
        self, 
        task: Dict[str, Any], 
        context: AgentExecutionContext
    ) -> AgentExecutionResult:
        """
        安全执行包装器 - 提供超时、日志、错误处理
        
        这是Supervisor调用的入口方法，不建议直接调用execute()
        """
        start_time = time.time()
        exec_id = f"{context.trace_id}_{context.task_id}"
        
        logger.info(f"[{self.agent_id}] Starting task {exec_id}")
        
        try:
            # Step 1: 输入验证
            is_valid, errors = await self.validate_input(task)
            if not is_valid:
                return AgentExecutionResult(
                    success=False,
                    error=f"Validation failed: {'; '.join(errors)}",
                    error_type="invalid_input",
                    metrics={"validation_time_ms": (time.time() - start_time) * 1000}
                )
            
            # Step 2: 带超时的执行
            result = await asyncio.wait_for(
                self.execute(task, context),
                timeout=context.timeout_seconds
            )
            
            # Step 3: 记录成功指标
            duration_ms = (time.time() - start_time) * 1000
            self._record_execution(True, duration_ms)
            
            result.metrics.update({
                "total_time_ms": duration_ms,
                "exec_id": exec_id
            })
            
            # 上报指标到收集器
            if context.metrics_collector:
                await context.metrics_collector.record(
                    agent_id=self.agent_id,
                    metric_name="execution_time",
                    value=duration_ms,
                    tags={"success": "true"}
                )
            
            logger.info(f"[{self.agent_id}] Task {exec_id} completed in {duration_ms:.0f}ms")
            return result
            
        except asyncio.TimeoutError:
            duration_ms = (time.time() - start_time) * 1000
            self._record_execution(False, duration_ms, "timeout")
            
            logger.warning(f"[{self.agent_id}] Task {exec_id} timed out after {context.timeout_seconds}s")
            return AgentExecutionResult(
                success=False,
                error=f"Execution timed out after {context.timeout_seconds:.1f}s",
                error_type="timeout",
                should_retry=True,
                retry_delay=1.0,
                metrics={"total_time_ms": duration_ms}
            )
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            error_msg = str(e)
            error_type = type(e).__name__
            
            self._record_execution(False, duration_ms, error_msg)
            
            logger.error(f"[{self.agent_id}] Task {exec_id} failed: {error_msg}", exc_info=True)
            return AgentExecutionResult(
                success=False,
                error=error_msg,
                error_type=error_type,
                should_retry=self._should_retry(error_type),
                retry_delay=self._get_retry_delay(error_type),
                metrics={"total_time_ms": duration_ms}
            )
    
    def _record_execution(self, success: bool, duration_ms: float, error: str = ""):
        """记录执行历史（保留最近1000条）"""
        record = {
            "timestamp": time.time(),
            "success": success,
            "duration_ms": duration_ms,
            "error": error
        }
        self._execution_history.append(record)
        
        # 保持历史记录大小
        if len(self._execution_history) > 1000:
            self._execution_history = self._execution_history[-1000:]
    
    def _should_retry(self, error_type: str) -> bool:
        """判断是否应该重试"""
        retryable_errors = {"timeout", "connection_error", "rate_limit", "temporary_failure"}
        return error_type.lower() in retryable_errors
    
    def _get_retry_delay(self, error_type: str) -> float:
        """获取重试延迟（指数退避）"""
        base_delays = {
            "timeout": 2.0,
            "rate_limit": 5.0,
            "connection_error": 1.0,
            "temporary_failure": 1.0
        }
        return base_delays.get(error_type.lower(), 2.0)
    
    async def get_statistics(self) -> Dict[str, Any]:
        """获取Agent统计信息"""
        if not self._execution_history:
            return {
                "total_executions": 0,
                "success_rate": 0,
                "avg_latency_ms": 0,
                "error_distribution": {}
            }
        
        total = len(self._execution_history)
        successful = sum(1 for r in self._execution_history if r["success"])
        avg_latency = sum(r["duration_ms"] for r in self._execution_history) / total
        
        error_dist: Dict[str, int] = {}
        for r in self._execution_history:
            if not r["success"]:
                err = r.get("error", "unknown")[:50]
                error_dist[err] = error_dist.get(err, 0) + 1
        
        return {
            "total_executions": total,
            "success_rate": successful / total,
            "avg_latency_ms": avg_latency,
            "error_distribution": error_dist,
            "uptime_seconds": time.time() - self._start_time
        }
```

---

## 4. 接口设计 (API Specification)

### 4.1 RESTful API

#### 核心对话接口

```
POST /api/v1/chat/completions
Content-Type: application/json
Authorization: Bearer <jwt_token>

{
  "messages": [
    {"role": "system", "content": "You are Wukong AI assistant..."},
    {"role": "user", "content": "帮我分析上周的销售数据"}
  ],
  "stream": true,
  "temperature": 0.7,
  "max_tokens": 4096,
  "options": {
    "use_rag": true,
    "skill_ids": ["skill.sales_analysis.v1"],
    "force_agent": null,
    "conversation_id": "conv_abc123"
  }
}

Response (stream=true):
HTTP/1.1 200 OK
Content-Type: text/event-stream

data: {"type":"thinking","content":"正在分析销售数据..."}

data: {"type":"task_started","task_id":"task_001","description":"检索销售数据库"}

data: {"delta":{"role":"assistant","content":"根据上周的数据分析..."}}

data: {"type":"citation","sources":[{"id":"doc_001","title":"周报2026-W15"}]}

data: [DONE]
```

#### 任务管理接口

```
# 创建任务
POST /api/v1/tasks
{
  "name": "月度财务报告生成",
  "description": "自动整理发票、生成报表",
  "trigger": "schedule",  # manual / schedule / webhook
  "schedule_cron": "0 9 1 * *",  # 每月1号9点
  "task_plan": {...},  # 预定义的任务计划
  "skills_required": ["invoice_ocr", "report_gen"]
}

# 查询任务列表
GET /api/v1/tasks?status=running&page=1&size=20

# 获取任务详情（含子任务状态）
GET /api/v1/tasks/{task_id}/detail

# 取消任务
DELETE /api/v1/tasks/{task_id}
```

#### 技能市场接口

```
# 浏览技能市场
GET /api/v1/skills/market?category=ecommerce&q=amazon&sort=rating&page=1

# 安装技能
POST /api/v1/skills/{skill_id}/install
{
  "version": "latest",
  "config": {
    "api_key": "sk_xxx"
  }
}

# 查看已安装技能
GET /api/v1/skills/installed

# 自定义技能注册
POST /api/v1/skills/custom/register
{
  "manifest": {...skill_manifest.json...},
  "code": "base64_encoded_code...",
  "resources": ["icon.png", "README.md"]
}
```

### 4.2 内部gRPC接口 (Supervisor ↔ SubAgent)

```protobuf
// proto/subagent.proto
syntax = "proto3";
package wukong.subagent;

service SubAgentService {
    // 执行任务
    rpc ExecuteTask (ExecuteTaskRequest) returns (stream TaskProgress);
    
    // 健康检查
    rpc HealthCheck (HealthCheckRequest) returns (HealthCheckResponse);
    
    // 获取能力声明
    rpc GetCapability (CapabilityRequest) returns (CapabilityResponse);
}

message ExecuteTaskRequest {
    string task_id = 1;
    string agent_type = 2;
    map<string, Value> params = 3;
    ExecutionContext context = 4;
    float timeout_seconds = 5;
}

message TaskProgress {
    oneof update {
        TaskStarted started = 1;
        TaskProgressUpdate progress = 2;
        TaskCompleted completed = 3;
        TaskFailed failed = 4;
    }
}

message ExecutionContext {
    string supervisor_id = 1;
    string session_id = 2;
    string trace_id = 3;
    string security_token = 4;
}
```

---

## 5. 数据库Schema设计

### 5.1 PostgreSQL核心表

```sql
-- 用户表
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(100),
    avatar_url TEXT,
    role VARCHAR(20) DEFAULT 'user', -- admin, user, viewer
    organization_id UUID REFERENCES organizations(id),
    permissions JSONB DEFAULT '[]',
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_login_at TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT true
);

-- 会话表
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    title VARCHAR(255),
    summary TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    is_archived BOOLEAN DEFAULT false
);

-- 消息表（对话历史）
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id),
    role VARCHAR(20) NOT NULL, -- user, assistant, system, tool
    content TEXT NOT NULL,
    content_type VARCHAR(20) DEFAULT 'text',
    metadata JSONB DEFAULT '{}',
    token_count INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 技能注册表
CREATE TABLE skills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    skill_id VARCHAR(200) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    version VARCHAR(20) NOT NULL,
    author_id UUID REFERENCES users(id),
    category VARCHAR(100),
    manifest JSONB NOT NULL,
    code_storage_path TEXT,
    status VARCHAR(20) DEFAULT 'draft', -- draft, published, deprecated
    rating DECIMAL(2,1) DEFAULT 0,
    install_count INTEGER DEFAULT 0,
    is_builtin BOOLEAN DEFAULT false,
    auto_improve BOOLEAN DEFAULT false,
    security_scan_result JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 已安装技能表（用户维度）
CREATE TABLE installed_skills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    skill_id UUID NOT NULL REFERENCES skills(id),
    config JSONB DEFAULT '{}',
    install_status VARCHAR(20) DEFAULT 'installed',
    installed_at TIMESTAMPTZ DEFAULT NOW(),
    last_used_at TIMESTAMPTZ,
    UNIQUE(user_id, skill_id)
);

-- 任务表
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    session_id UUID REFERENCES sessions(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    trigger_type VARCHAR(20) DEFAULT 'manual',
    schedule_cron VARCHAR(100),
    task_plan JSONB,
    status VARCHAR(20) DEFAULT 'pending',
    priority INTEGER DEFAULT 5,
    progress_percent INTEGER DEFAULT 0,
    result_summary TEXT,
    result_data JSONB,
    error_message TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 子任务表
CREATE TABLE subtasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL REFERENCES tasks(id),
    parent_task_id UUID REFERENCES subtasks(id),
    agent_type VARCHAR(100) NOT NULL,
    action VARCHAR(200) NOT NULL,
    params JSONB DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'pending',
    retry_count INTEGER DEFAULT 0,
    result JSONB,
    error_message TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    duration_ms INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 操作审计表（WORM - Write Once Read Many）
CREATE TABLE audit_logs (
    id BIGSERIAL PRIMARY KEY,
    trace_id VARCHAR(64) NOT NULL,
    user_id UUID REFERENCES users(id),
    session_id UUID REFERENCES sessions(id),
    agent_id VARCHAR(100),
    action_type VARCHAR(100) NOT NULL,
    action_params JSONB,
    result_status VARCHAR(20),
    risk_level VARCHAR(20) DEFAULT 'low',
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    CONSTRAINT audit_immutable CHECK (created_at IS NOT NULL) -- 防止修改
);

-- 文件版本表（RealDoc风格）
CREATE TABLE file_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_id UUID NOT NULL,
    version_number INTEGER NOT NULL,
    storage_path TEXT NOT NULL,
    operation_type VARCHAR(50), -- create, modify, delete
    operation_detail JSONB,
    checksum VARCHAR(128),
    size_bytes BIGINT,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(file_id, version_number)
);

-- 向量集合表（Milvus映射）
CREATE TABLE vector_collections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    collection_name VARCHAR(200) UNIQUE NOT NULL,
    owner_type VARCHAR(50), -- user, org, system, skill
    owner_id UUID,
    dimension INTEGER NOT NULL,
    index_type VARCHAR(50) DEFAULT 'IVF_FLAT',
    metric_type VARCHAR(20) DEFAULT 'COSINE',
    document_count INTEGER DEFAULT 0,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 创建索引
CREATE INDEX idx_sessions_user ON sessions(user_id);
CREATE INDEX idx_messages_session ON messages(session_id, created_at);
CREATE INDEX idx_tasks_user_status ON tasks(user_id, status);
CREATE INDEX idx_subtasks_task ON subtasks(task_id, status);
CREATE INDEX idx_audit_logs_trace ON audit_logs(trace_id);
CREATE INDEX idx_audit_logs_user_time ON audit_logs(user_id, created_at);
CREATE INDEX idx_file_versions_file ON file_versions(file_id, version_number DESC);
```

---

## 6. 部署架构

### 6.1 Docker Compose (开发环境)

```yaml
# docker/docker-compose.dev.yml
version: '3.8'

services:
  wukong-api:
    build:
      context: ../backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://wukong:wukong@postgres:5432/wukong
      - REDIS_URL=redis://redis:6379/0
      - MILVUS_HOST=milvus
      - MINIO_ENDPOINT=minio:9000
      - RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
      - VLLM_URL=http://vllm:8000/v1
    volumes:
      - ../backend:/app
      - ./volumes/skills:/app/data/skills
    depends_on:
      - postgres
      - redis
      - milvus
      - minio
      - rabbitmq
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: wukong
      POSTGRES_PASSWORD: wukong
      POSTGRES_DB: wukong
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-db.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"

  milvus:
    image: milvusdb/milvus:v2.3-latest
    environment:
      ETCD_ENDPOINTS: etcd:2379
      MINIO_ADDRESS: minio:9000
    volumes:
      - milvus_data:/var/lib/milvus
    ports:
      - "19530:19530"
      - "9091:9091"
    depends_on:
      - etcd
      - minio

  etcd:
    image: quay.io/coreos/etcd:v3.5.5
    environment:
      - ETCD_AUTO_COMPACTION_MODE=revision
      - ETCD_AUTO_COMPACTION_RETENTION=1000
      - ETCD_QUOTA_BACKEND_BYTES=4294967296
    volumes:
      - etcd_data:/etcd
    command: >
      etcd
      -advertise-client-urls=http://0.0.0.0:2379
      -listen-client-urls http://0.0.0.0:2379
      --data-dir /etcd

  minio:
    image: minio/minio:latest
    environment:
      MINIO_ROOT_USER: wukongadmin
      MINIO_ROOT_PASSWORD: wukongadmin123
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - minio_data:/data
    command: server /data --console-address ":9001"

  rabbitmq:
    image: rabbitmq:3.12-management-alpine
    environment:
      RABBITMQ_DEFAULT_USER: guest
      RABBITMQ_DEFAULT_PASS: guest
    ports:
      - "5672:5672"
      - "15672:15672"
    volumes:
      - rabbitmq_data:/var/lib/rabbitmq

  vllm:
    image: vllm/vllm-openai:latest
    environment:
      - MODEL=BAAI/bge-large-zh-v1.5
    volumes:
      - model_cache:/root/.cache/huggingface/
    ports:
      - "8000:8000"
    deploy:
      resources:
        reservations:
          devices:
            - capabilities: [gpu]

volumes:
  postgres_data:
  redis_data:
  milvus_data:
  etcd_data:
  minio_data:
  rabbitmq_data:
  model_cache:
```

### 6.2 Kubernetes生产部署（概要）

```yaml
# k8s/deployment.yaml (关键部分)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: wukong-supervisor
spec:
  replicas: 3
  selector:
    matchLabels:
      app: wukong-supervisor
  template:
    spec:
      containers:
      - name: supervisor
        image: wukong/supervisor:v1.0.0
        resources:
          requests:
            cpu: "500m"
            memory: "512Mi"
          limits:
            cpu: "2000m"
            memory: "2Gi"
        env:
        - name: REPLICAS
          valueFrom:
            fieldRef:
              fieldPath: spec.replicas
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: wukong-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: wukong-supervisor
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

---

## 7. 监控与观测

### 7.1 关键指标 (Key Metrics)

```python
# 监控指标定义
METRICS_REGISTRY = {
    # Supervisor指标
    "supervisor.request_total": "Counter: 总请求数",
    "supervisor.request_duration_seconds": "Histogram: 请求处理时间分布",
    "supervisor.intent_recognition_accuracy": "Gauge: 意图识别准确率",
    "supervisor.task_success_rate": "Gauge: 任务成功率",
    "supervisor.subtask_avg_duration": "Histogram: 子任务平均耗时",
    
    # SubAgent指标
    "agent.{agent_id}.execution_total": "Counter: 执行总次数",
    "agent.{agent_id}.execution_duration_seconds": "Histogram: 执行耗时分布",
    "agent.{agent_id}.error_total": "Counter: 错误次数（按类型）",
    "agent.{agent_id}.queue_length": "Gauge: 任务队列长度",
    "agent.{agent_id}.concurrent_executions": "Gauge: 当前并发数",
    
    # RAG专项指标
    "rag.retrieval_latency_seconds": "Histogram: 检索延迟",
    "rag.retrieval_recall_top_k": "Gauge: Top-K召回率",
    "rag.generation_tokens_per_second": "Gauge: 生成速度",
    "rag.hallucination_rate": "Gauge: 幻觉率",
    
    # 技能系统指标
    "skill.execution_total": "Counter: 技能执行次数",
    "skill.sandbox_creation_seconds": "Histogram: 沙箱启动时间",
    "skill.security_scan_findings": "Counter: 安全扫描发现的问题数",
    
    # 系统资源指标
    "system.cpu_usage_percent": "Gauge: CPU使用率",
    "system.memory_usage_bytes": "Gauge: 内存使用量",
    "system.disk_usage_percent": "Gauge: 磁盘使用率",
    "database.connection_pool_usage": "Gauge: 数据库连接池使用率",
    "vector_index_size_bytes": "Gauge: 向量索引大小",
    
    # 业务指标
    "business.daily_active_users": "Gauge: 日活用户数",
    "business.tasks_completed_total": "Counter: 完成任务总数",
    "business.skill_installations": "Counter: 技能安装次数",
    "business.user_satisfaction_score": "Gauge: 用户满意度(NPS)"
}
```

### 7.2 告警规则示例

```yaml
# Prometheus告警规则
groups:
- name: wukong-critical-alerts
  rules:
  - alert: HighErrorRate
    expr: rate(supervisor_request_total{status="error"}[5m]) > 0.1
    for: 2m
    labels:
      severity: critical
    annotations:
      summary: "错误率过高 (>10%)"
      
  - alert: SubAgentDown
    expr: up{job="subagents"} == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "SubAgent {{ $labels.instance }} 宕机"
      
  - alert: HighLatencyP99
    expr: histogram_quantile(0.99, supvisor_request_duration_seconds_bucket) > 5
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "P99延迟超过5秒"
      
  - alert: DatabaseConnectionPoolExhausted
    expr: database_connection_pool_usage > 0.9
    for: 2m
    labels:
      severity: critical
    annotations:
      summary: "数据库连接池即将耗尽 (>90%)"
```

---

## 8. 测试策略

### 8.1 测试金字塔

```
        /\
       /  \     E2E Tests (10%)
      /────\    - 完整用户流程测试
     /      \   - 集成测试（真实基础设施）
    /────────\  
   /  Integration  \  (20%)
  /     Tests      \ - API接口测试
 /                  \  - Agent交互测试
/────────────────────\
/    Unit Tests       \ (70%)
/                      \ - 单个函数/方法测试
/                        \ - Mock外部依赖
```

### 8.2 关键测试用例类别

| 类别 | 示例 | 工具 |
|-----|------|------|
| **单元测试** | Supervisor状态转换逻辑、Intent分类准确性 | pytest + pytest-asyncio |
| **集成测试** | Supervisor→SubAgent完整调用链、RAG端到端 | pytest + testcontainers |
| **契约测试** | gRPC接口兼容性、API Schema验证 | Pact + schemathesis |
| **性能测试** | 并发100用户下的响应时间、RAG检索延迟 | locust + k6 |
| **安全测试** | SQL/XSS注入、权限绕过、沙箱逃逸 | OWASP ZAP + 自定义扫描 |
| **混沌测试** | SubAgent宕机、网络延迟、磁盘满 | Chaos Mesh |
| **回归测试** | PR自动化CI流水线 | GitHub Actions |

---

## 9. 性能基准目标

| 场景 | P50延迟 | P99延迟 | 吞吐(QPS) | 资源需求 |
|-----|--------|--------|-----------|---------|
| **简单对话** (无RAG/技能) | <400ms | <800ms | 500+ | 1核2GB |
| **RAG问答** (单次检索) | <800ms | <2s | 200+ | 2核4GB |
| **复杂任务** (3个子任务串行) | <5s | <10s | 50+ | 4核8GB |
| **技能执行** (Docker沙箱) | <2s(启动)+执行 | <5s+执行 | 30+ | 4核8GB |
| **文件操作** (读取/修改) | <200ms | <500ms | 1000+ | 1核2GB |

---

**文档结束**

*最后更新：2026-04-12*
*作者：Wukong AI Architecture Team*
*审核状态：待技术委员会评审*
