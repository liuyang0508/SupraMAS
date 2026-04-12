<p align="center">
  <h1 align="center">SupraMAS</h1>
  <p align="center">
    <strong>Supervisor Multi-Agent System</strong>
  </p>
  <p align="center">
    Enterprise-grade AI Native Workspace Platform | 企业级AI原生工作平台
  </p>

  <p align="center">
    <img src="https://img.shields.io/badge/Python-3.11-blue.svg" alt="Python Version" />
    <img src="https://img.shields.io/badge/FastAPI-0.109-green.svg" alt="Framework" />
    <img src="https://img.shields.io/badge/LangGraph-0.1-orange.svg" alt="Orchestration" />
    <img src="https://img.shields.io/badge/React-18-61DAFB.svg" alt="Frontend" />
    <img src="https://img.shields.io/badge/Docker-Ready-2496ED.svg" alt="Docker" />
    <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License" />
    <a href="https://github.com/liuyang0508/SupraMAS/stargazers"><img src="https://img.shields.io/github/stars/liuyang0508/SupraMAS.svg?style=social" alt="Stars" /></a>
    <a href="https://github.com/liuyang0508/SupraMAS/network/members"><img src="https://img.shields.io/github/forks/liuyang0508/SupraMAS.svg?style=social" alt="Forks" /></a>
  </p>
</p>

---

## 📖 Table of Contents

- [✨ Features](#-features)
- [📸 Screenshots & Demo](#-screenshots--demo)
- [🏗️ Architecture](#-architecture)
- [🚀 Quick Start](#-quick-start)
- [📦 Installation](#-installation)
- [🔧 Configuration](#-configuration)
- [📚 Documentation](#-documentation)
- 🛠️ [Tech Stack](#️-tech-stack)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)

---

## ✨ Features

### 🎯 Core Capabilities

- **🧠 Supervisor + SubAgent Architecture**: Five-layer intelligent orchestration system
  - L1 Input Router (Intent Classification & Slot Extraction)
  - L2 Query Optimizer (Coreference Resolution & Query Rewriting)
  - L3 Task Planner (DAG-based Task Decomposition)
  - L4 Execution Dispatcher (Intelligent Scheduling with Circuit Breaker)
  - L5 Security Guard (Permission Intersection & Data Sanitization)

- **🤖 Dual-Layer Agent System**:
  - **Infrastructure Layer**: RAG, Skill (Docker Sandbox), File (RealDoc-style), Intent Recognition
  - **Domain Expert Layer**: 6 Business Domain Agents with Skill-driven workflows

- **🔌 MCP Integration**: Model Context Protocol for external system connectivity
  - FileSystem Server, Database Server, Search Server
  - Unified client management and cross-server tool invocation

- **🎨 Modern Frontend**: React 18 + TypeScript + Vite + TailwindCSS
  - Real-time chat interface with streaming support
  - Domain selector with 6 business areas
  - Responsive design with smooth animations

### 📊 Business Domains

| Domain Agent | Core Capabilities | Workflows |
|-------------|-------------------|-----------|
| 🛒 Ecommerce | Product Research, Sourcing Decision, Listing Generation | `product_research`, `sourcing_decision`, `listing_generation` |
| 🎨 Design | Brand Identity, Marketing Asset Creation | `branding_solution`, `marketing_assets` |
| 💰 Finance | Financial Analysis, Tax Management, Reporting | `monthly_close`, `quick_analysis` |
| 💻 Developer | Feature Development, Bug Fixing, Code Review, DevOps | `feature_development`, `bugfix_workflow` |
| ✍️ Content | Article Writing, SEO Optimization, Social Media Batch | `article_writing`, `social_media_batch` |
| 🎧 Customer Service | Ticket Resolution, Sentiment Analysis, FAQ Matching | `ticket_resolution`, `feedback_analysis` |

---

## 🏗️ Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      React Frontend (Vite)                       │
│         Chat Interface │ Sidebar │ Domain Selector              │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP/WebSocket / SSE
┌────────────────────────────▼────────────────────────────────────┐
│                   FastAPI Backend (main.py)                     │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              WukongSupervisor (LangGraph)                │   │
│  │                                                           │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐               │   │
│  │  │Input     │─▶│Query     │─▶│Task      │               │   │
│  │  │Router    │  │Optimizer │  │Planner   │               │   │
│  │  └──────────┘  └──────────┘  └─────┬────┘               │   │
│  │                                     │                     │   │
│  │                              ┌──────▼──────┐             │   │
│  │                              │Execution    │             │   │
│  │                              │Dispatcher   │             │   │
│  │                              └──────┬──────┘             │   │
│  │                                     │                     │   │
│  │                              ┌──────▼──────┐             │   │
│  │                              │Security     │             │   │
│  │                              │Guard        │             │   │
│  │                              └─────────────┘             │   │
│  └──────────────────────────────┬───────────────────────────┘   │
│                                 │                               │
│  ┌──────────────────────────────▼───────────────────────────┐   │
│  │                    Agent Pool (10 Agents)                  │   │
│  │                                                            │   │
│  │  ┌────────────────────────────────────────────────────┐   │   │
│  │  │ Infrastructure Layer (Tools/Capabilities)           │   │   │
│  │  │ • RAGSubAgent       (Hybrid Retrieval + Reranking) │   │   │
│  │  │ • SkillSubAgent     (Docker Sandbox Execution)     │   │   │
│  │  │ • FileSubAgent      (RealDoc Atomic Operations)    │   │   │
│  │  │ • IntentSubAgent    (3-Tier: Rules→Semantic→LLM)  │   │   │
│  │  └────────────────────────────────────────────────────┘   │   │
│  │                                                            │   │
│  │  ┌────────────────────────────────────────────────────┐   │   │
│  │  │ Domain Expert Layer (Business Intelligence)        │   │   │
│  │  │ • EcommerceDomainAgent                             │   │   │
│  │  │ • DesignDomainAgent                                │   │   │
│  │  │ • FinanceDomainAgent                               │   │   │
│  │  │ • DeveloperDomainAgent                             │   │   │
│  │  │ • ContentDomainAgent                               │   │   │
│  │  │ • CustomerServiceDomainAgent                       │   │   │
│  │  └────────────────────────────────────────────────────┘   │   │
│  └──────────────────────────────┬───────────────────────────┘   │
│                                 │                               │
│  ┌──────────────────────────────▼───────────────────────────┐   │
│  │              MCP Client (External Systems)                │   │
│  │  FileSystem │ Database (PostgreSQL) │ Search Engine       │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
          │                │                │              │
    PostgreSQL          Redis            Milvus          MinIO
   (Users/Sessions)   (Cache/Sessions)  (Vector Store)  (File Storage)
```

### Data Flow

```
User Input → L1 Router (Intent+Slots) → L2 Optimizer (Rewrite)
    ↓
L3 Planner (Task DAG) → L4 Dispatcher (Schedule to Agents)
    ↓
Domain Agent Execution (Skills + Infrastructure Agents + MCP)
    ↓
L5 Security Check (Permission∩Sanitization) → Response Aggregation
    ↓
Streaming Output → Frontend Display
```

---

## 🚀 Quick Start

### Prerequisites

- **Python**: 3.11+
- **Node.js**: 18+
- **Docker**: 20.10+ (for containerized deployment)
- **PostgreSQL**: 15+ (or use Docker)
- **Redis**: 7+ (or use Docker)

### Option 1: Docker Compose (Recommended)

```bash
# Clone the repository
git clone https://github.com/liuyang0508/SupraMAS.git
cd SupraMAS

# Start all services (11 containers)
cd docker
docker-compose -f docker-compose.dev.yml up -d

# Wait for services to be healthy (~30s)
docker-compose ps

# Access the application
open http://localhost:8000  # API Docs: http://localhost:8000/docs
open http://localhost:5173  # Frontend (if running separately)
```

### Option 2: Local Development

#### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the server
python main.py
# OR with hot-reload:
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

#### Frontend Setup

```bash
# Navigate to frontend directory (new terminal)
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Open browser
open http://localhost:5173
```

---

## 📦 Installation

### Backend Dependencies

```bash
pip install -r requirements.txt
```

**Key packages**:
- `fastapi` - High-performance web framework
- `langchain` + `langgraph` - AI/LLM orchestration
- `pydantic-settings` - Configuration management
- `sqlalchemy` + `asyncpg` - Async database ORM
- `milvus` + `pymilvus` - Vector database client
- `sentence-transformers` - Embedding models for RAG

### Frontend Dependencies

```bash
npm install
```

**Key packages**:
- `react` + `react-dom` - UI framework
- `@tanstack/react-query` - Data fetching & caching
- `zustand` - State management
- `tailwindcss` - Utility-first CSS
- `recharts` - Data visualization
- `lucide-react` - Icon library

---

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the `backend/` directory:

```env
# Application Settings
APP_NAME=SupraMAS
APP_VERSION=1.0.0
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

# Database (PostgreSQL)
DATABASE_URL=postgresql+asyncpg://supramas:supramas@localhost:5432/supramas

# Cache (Redis)
REDIS_URL=redis://localhost:6379/0

# Vector Database (Milvus)
MILVUS_HOST=localhost
MILVUS_PORT=19530

# Object Storage (MinIO)
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=supramasadmin
MINIO_SECRET_KEY=supramasadmin123

# Message Queue (RabbitMQ)
RABBITMQ_URL=amqp://guest:guest@localhost:5672/

# LLM Configuration
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4-turbo-preview

# Security
JWT_SECRET_KEY=change-this-in-production
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]
```

### Supervisor Configuration

Customize the 5-layer supervisor in [`backend/main.py`](backend/main.py):

```python
supervisor_config = {
    "input_router": {
        "mode": "hybrid",  # rule_based | llm_based | hybrid
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
        "circuit_breaker_threshold": 5
    },
    "security": {
        "enable_permission_intersection": True,
        "enable_data_sanitization": True,
        "enable_audit_logging": True
    }
}
```

---

## 📚 Documentation

- **[Product Requirements Document (PRD)](docs/PRD.md)** - Complete feature specifications
- **[Technical Design Document](docs/Technical_Design.md)** - Architecture decisions (ADRs), database schema, API specs
- **[API Reference](http://localhost:8000/docs)** - Interactive Swagger/OpenAPI documentation
- **[Contributing Guide](CONTRIBUTING.md)** - How to contribute to SupraMAS

### Key API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/chat/completions` | Main chat interface (OpenAI-compatible) |
| `GET` | `/health` | Health check |
| `GET` | `/health/ready` | Readiness check with component status |
| `GET` | `/api/v1/agents/status` | List all registered agents with stats |
| `GET` | `/api/v1/domains` | List available business domains (6 total) |
| `GET` | `/api/v1/domains/{name}/info` | Get domain details, workflows, skills |
| `GET` | `/api/v1/skills/installed` | List installed skills via Skill Agent |
| `GET` | `/api/v1/mcp/status` | MCP servers connection status |
| `GET` | `/api/v1/intent/domains` | Intent recognition domain registry |

---

## 🛠️ Tech Stack

### Backend

| Technology | Version | Purpose |
|------------|---------|---------|
| ![Python](https://img.shields.io/badge/Python-3.11-blue) | 3.11+ | Primary language |
| ![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green) | 0.109+ | Web framework |
| ![LangChain](https://img.shields.io/badge/LangChain-0.1-orange) | 0.1+ | LLM orchestration |
| ![LangGraph](https://img.shields.io/badge/LangGraph-0.1-orange) | 0.1+ | Workflow/state machine |
| ![Pydantic](https://img.shields.io/badge/Pydantic-v2-red) | v2 | Data validation |
| ![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-red) | 2.0+ | ORM (async) |
| ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue) | 15+ | Primary database |
| ![Redis](https://img.shields.io/badge/Redis-7-red) | 7+ | Cache/session store |
| ![Milvus](https://img.shields.io/badge/Milvus-2.3-blue) | 2.3+ | Vector database |

### Frontend

| Technology | Version | Purpose |
|------------|---------|---------|
| ![React](https://img.shields.io/badge/React-18-61DAFB) | 18.2+ | UI framework |
| ![TypeScript](https://img.shields.io/badge/TypeScript-5.3-blue) | 5.3+ | Type safety |
| ![Vite](https://img.shields.io/badge/Vite-5.0-purple) | 5.0+ | Build tool |
| ![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.4-38B2AC) | 3.4+ | Styling |
| ![Zustand](https://img.shields.io/badge/Zustand-4.4-orange) | 4.4+ | State mgmt |
| ![React Query](https://img.shields.io/badge/React_Query-5.17-red) | 5.17+ | Data fetching |
| ![Recharts](https://img.shields.io/badge/Recharts-2.10-green) | 2.10+ | Charts |

### DevOps

| Technology | Purpose |
|------------|---------|
| ![Docker](https://img.shields.io/badge/Docker-Ready-2496ED) | Containerization |
| ![Kubernetes](https://img.shields.io/badge/K8s-Supported-326CE5) | Orchestration |
| ![Prometheus](https://img.shields.io/badge/Prometheus-E6522A) | Metrics collection |
| ![Grafana](https://img.shields.io/badge/Grafana-F46800) | Visualization |
| ![RabbitMQ](https://img.shields.io/badge/RabbitMQ-FF6600) | Message queue |

---

## 📁 Project Structure

```
SupraMAS/
├── backend/                    # FastAPI Python Backend
│   ├── config/
│   │   └── settings.py         # Pydantic configuration
│   ├── core/
│   │   ├── supervisor/         # 5-Layer Supervisor System
│   │   │   ├── __init__.py     # WukongSupervisor (LangGraph)
│   │   │   ├── state.py        # TypedDict state definitions
│   │   │   └── layers/
│   │   │       ├── input_router.py
│   │   │       ├── query_optimizer.py
│   │   │       ├── task_planner.py
│   │   │       ├── execution_dispatcher.py
│   │   │       └── security_guard.py
│   │   ├── subagents/          # Agent Implementations
│   │   │   ├── base.py         # BaseSubAgent ABC
│   │   │   ├── intent/         # Intent Recognition Agent
│   │   │   ├── rag/            # RAG Agent
│   │   │   ├── skill/          # Skill Execution Agent
│   │   │   ├── file/           # File Processing Agent
│   │   │   └── domain/         # 6 Business Domain Agents
│   │   │       ├── base.py     # BaseDomainAgent
│   │   │       ├── ecommerce.py
│   │   │       ├── design.py
│   │   │       ├── finance.py
│   │   │       ├── developer.py
│   │   │       ├── content.py
│   │   │       └── customer_service.py
│   │   └── mcp/                # MCP Integration Layer
│   │       └── __init__.py     # Servers + Client
│   ├── main.py                 # Application entry point
│   └── requirements.txt        # Python dependencies
│
├── frontend/                   # React TypeScript Frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── chat/ChatInterface.tsx
│   │   │   └── Sidebar.tsx
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── styles/index.css
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── tsconfig.json
│
├── docker/                     # Container Configurations
│   ├── Dockerfile              # Multi-stage build
│   ├── docker-compose.dev.yml  # Dev environment (11 services)
│   ├── docker-compose.prod.yml # Production setup
│   └── init-db.sql             # Database initialization
│
├── k8s/                        # Kubernetes Manifests
│   └── deployment.yaml         # Deployment + HPA + Ingress
│
├── docs/                       # Documentation
│   ├── PRD.md                  # Product Requirements
│   └── Technical_Design.md     # Architecture & Design
│
├── README.md                   # This file
└── .gitignore                  # Git ignore rules
```

---

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. Open a **Pull Request**

### Development Guidelines

- Follow **PEP 8** for Python code
- Use **TypeScript strict mode** for frontend
- Write **tests** for new features (pytest for backend, Jest/Vitest for frontend)
- Update **documentation** for API changes
- Ensure **Docker builds** succeed before submitting PR

### Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment.

---

## 📊 Project Statistics

- **Total Lines of Code**: ~9,500+ (Backend: ~8,000 | Frontend: ~1,500)
- **Python Files**: 40+ modules
- **React Components**: 5 core components
- **API Endpoints**: 10+ RESTful endpoints
- **Domain Agents**: 6 business experts
- **Infrastructure Agents**: 4 capability providers
- **Docker Services**: 11 containerized services
- **Documentation Pages**: 1,650+ lines (PRD + Tech Design)

---

## 🙏 Acknowledgments

- Inspired by **Alibaba DingTalk Wukong** platform architecture
- Built on **LangChain/LangGraph** ecosystem
- Powered by **FastAPI** performance
- Enhanced by **React** modern UX patterns

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## 📮 Contact

- **GitHub Issues**: [Report bugs or request features](https://github.com/liuyang0508/SupraMAS/issues)
- **Discussions**: [Join community discussions](https://github.com/liuyang0508/SupraMAS/discussions)

---

<div align="center">

**⭐ If this project helped you, please give it a star! ⭐**

Made with ❤️ by the SupraMAS Team

</div>
