# SupraMAS 系统架构

## 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        React Frontend (5173)                     │
│              ChatInterface │ Sidebar │ SkillMarket               │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP POST /api/v1/chat/completions
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                        FastAPI Backend (8000)                     │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              WukongSupervisor (LangGraph)                  │  │
│  │                                                           │  │
│  │  L1 InputRouter ──▶ L2 QueryOptimizer ──▶ L3 TaskPlanner │  │
│  │        │                                   │               │  │
│  │        ▼                                   ▼               │  │
│  │  L5 SecurityGuard ◀──── L4 ExecutionDispatcher             │  │
│  │                                                           │  │
│  └──────────────────────────────────────────────────────────┘  │
│                             │                                   │
│  ┌──────────────────────────▼───────────────────────────────┐  │
│  │                    Agent Pool (10 Agents)                   │  │
│  │                                                            │  │
│  │  Infrastructure Layer           Domain Expert Layer        │  │
│  │  ├─ RAGSubAgent (检索)          ├─ EcommerceDomainAgent    │  │
│  │  ├─ SkillSubAgent (技能执行)    ├─ DesignDomainAgent       │  │
│  │  ├─ FileSubAgent (文件操作)     ├─ FinanceDomainAgent     │  │
│  │  └─ IntentSubAgent (意图识别)    ├─ DeveloperDomainAgent   │  │
│  │                                  ├─ ContentDomainAgent     │  │
│  │                                  └─ CustomerServiceAgent   │  │
│  └──────────────────────────┬───────────────────────────────┘  │
│                             │                                    │
│  ┌──────────────────────────▼───────────────────────────────┐  │
│  │              MCP Client (外部系统集成)                     │  │
│  │         Search Server (2 tools)                            │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
          │                                    │
          ▼                                    ▼
     MiniMax M2                         PostgreSQL / Redis
     (LLM推理)                          (数据存储)
```

---

## 完整链路流程（以"全网比价iPhone17Promax"为例）

```
用户输入: "全网比价iPhone17Promax"
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ L1: InputRouter (意图识别 & 路由)                            │
│                                                             │
│  Rule-based匹配 → "全网比价"命中 skill_execution 意图 (0.7)  │
│  confidence_threshold=0.60, 通过                             │
│                                                             │
│  输出: intent=skill_execution, target_agent=skill           │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ L2: QueryOptimizer (查询改写)                                │
│                                                             │
│  原始: "全网比价iPhone17Promax"                              │
│  优化: "全网比价查询 iPhone17Promax 各平台最低价"            │
│  transformations: [entity_expansion]                        │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ L3: TaskPlanner (任务分解)                                  │
│                                                             │
│  模板: skill_execution → [st_001: skill.execute_skill]      │
│  DAG: st_001 (无依赖)                                        │
│                                                             │
│  输出: subtasks=[{task_id:st_001, agent_type:skill,          │
│                   action:execute_skill, params:{query:...}}] │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ L5: SecurityGuard (安全审计)                                │
│                                                             │
│  pre_check(subtask) → {allowed: true}                       │
│  audit_log: [{agent_type:skill, action:execute_skill}]      │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ L4: ExecutionDispatcher (执行调度)                          │
│                                                             │
│  识别 agent_type=skill → 使用技能特殊处理路径:               │
│    1. 从 query 中解析 "全网比价" → skill_id=price_compare    │
│    2. 提取参数: {product_name: "iPhone17Promax"}            │
│    3. 调用 SkillSubAgent.execute({                          │
│         skill_name: "price_compare",                        │
│         params: {product_name: "iPhone17Promax"}            │
│       })                                                    │
│                                                             │
│  SkillSubAgent 内部:                                        │
│    - _load_skill("price_compare") → 加载 skill_manifest.json │
│    - _validate_skill_params() → 通过                        │
│    - _execute_in_process(main.py) → 返回比价报告           │
│                                                             │
│  输出: {task_id:st_001, success:true, data:{report:...}}    │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ ResultAggregator (结果聚合)                                 │
│                                                             │
│  skill返回 data.report → 作为 final_response                │
│  metadata: {intent, execution_chain, subtasks_count}       │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
   HTTP Response → Frontend
```

---

## 五层职责模型

```
┌─────────────────────────────────────────────┐
│  Layer 5: Security Guard (安全审计)         │
│  - 权限交集检查 (Permission Intersection)    │
│  - 数据脱敏 (Data Sanitization)            │
│  - 审计日志 (Audit Logging)                 │
├─────────────────────────────────────────────┤
│  Layer 4: Execution Dispatcher (执行调度)    │
│  - 智能调度 (Intelligent Scheduling)         │
│  - 并行/串行执行 (Parallel/Serial)          │
│  - 熔断器 (Circuit Breaker)                 │
│  - 动态重规划 (Dynamic Replanning)          │
├─────────────────────────────────────────────┤
│  Layer 3: Task Planner (任务规划)           │
│  - 任务分解 (Task Decomposition)            │
│  - 依赖分析 (Dependency Analysis)           │
│  - DAG构建 (DAG Construction)               │
│  - 资源预估 (Resource Estimation)          │
├─────────────────────────────────────────────┤
│  Layer 2: Query Optimizer (查询优化)        │
│  - 指代消解 (Coreference Resolution)       │
│  - 查询改写 (Query Rewriting)               │
│  - 同义扩展 (Synonym Expansion)            │
├─────────────────────────────────────────────┤
│  Layer 1: Input Router (意图路由)           │
│  - 意图分类 (Intent Classification)         │
│  - 槽位提取 (Slot Extraction)              │
│  - 歧义检测 (Ambiguity Detection)          │
└─────────────────────────────────────────────┘
```

---

## Agent Pool 架构

```
Infrastructure Layer (基础设施层)
│
├── RAGSubAgent
│   └── 混合检索: 向量检索 + BM25 → CrossEncoder重排 → LLM生成
│
├── SkillSubAgent
│   └── 技能执行: 注册表 → 安全扫描 → Docker沙箱/进程内执行
│
├── FileSubAgent
│   └── 文件操作: 原子读/写/修改/快照
│
└── IntentSubAgent
    └── 三层识别: 规则 → 语义 → LLM

Domain Expert Layer (领域专家层)
│
├── EcommerceDomainAgent (电商运营专家)
├── DesignDomainAgent (设计创意专家)
├── FinanceDomainAgent (财税管理专家)
├── DeveloperDomainAgent (软件开发专家)
├── ContentDomainAgent (内容创作专家)
└── CustomerServiceDomainAgent (智能客服专家)
```

---

## 技能市场执行链路

```
用户点击技能卡片
       │
       ▼
SkillMarket.onUseSkill(skillId) → 切换到chat view
       │
       ▼
handleSendMessage(预设提示词)
       │
       ▼
POST /api/v1/chat/completions
       │
       ├── L1: intent=skill_execution (命中技能关键词)
       ├── L2: rewrite query
       ├── L3: 生成 skill agent 子任务
       ├── L5: security pre-check
       ├── L4: ExecutionDispatcher
       │        │
       │        ├── skill_map["全网比价"] → "price_compare"
       │        ├── resolved_params: {product_name: "..."}
       │        └── agent.execute({skill_name, params})
       │              │
       │              ▼
       │         SkillSubAgent._load_skill()
       │         SkillSubAgent._execute_in_process()
       │         skill/main.py → main({product_name}) → report
       │
       ▼
Aggregator 取 data.report → final_response
```

---

## 技术栈

| 层级 | 技术 |
|------|------|
| **Frontend** | React 18, TypeScript, Vite, TailwindCSS |
| **Backend** | FastAPI, Python 3.11, LangGraph, Pydantic |
| **LLM** | MiniMax M2 / OpenAI GPT-4 / Anthropic Claude |
| **Database** | PostgreSQL, Redis, Milvus (Vector DB) |
| **Container** | Docker, Docker Compose |
| **Protocol** | MCP (Model Context Protocol) |

---

## 关键文件路径

| 文件 | 作用 |
|------|------|
| `backend/main.py` | FastAPI入口，注册Supervisor和所有Agent |
| `core/supervisor/__init__.py` | Supervisor主体，LangGraph状态机编排 |
| `core/supervisor/layers/input_router.py` | 三层意图识别（规则→语义→LLM） |
| `core/supervisor/layers/task_planner.py` | 意图模板→子任务DAG映射 |
| `core/supervisor/layers/execution_dispatcher.py` | 调度Agent执行，skill类型特殊处理 |
| `core/subagents/skill/agent.py` | 技能生命周期管理（加载→校验→执行） |
| `services/llm_service.py` | MiniMax/OpenAI/Anthropic统一调用 |