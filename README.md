# Stock Market Researcher

A production-grade, full-stack monorepo for automated stock market research, analysis, and report generation. The application uses a multi-agent system (CrewAI) orchestrated by a state graph workflow (LangGraph) to gather, criticize, and summarize stock research into comprehensive PDF reports.

---

## 🛠️ Technology Stack

### Backend
* **Python**: 3.12
* **Framework**: FastAPI (Asynchronous background tasks & SSE streaming)
* **Orchestration**: LangGraph (Handles stateful research transitions & loops)
* **Agentic Framework**: CrewAI (Configured with specialized research, fundamentals, and critic agents)
* **LLM Engine**: LiteLLM & Google GenAI SDK (Dynamic routing across Gemini, OpenAI, and Mistral)
* **Database**: SQLite (Development) / PostgreSQL (Production) using SQLAlchemy and aiosqlite/asyncpg
* **Vector Search / RAG**: ChromaDB (Stores historical reports for context injection)
* **Observability**: Langfuse (Complete tracing, prompt version management, and LLM-as-a-Judge custom evaluations)
* **Caching**: Redis (For stock query and ticker OHLCV caching)

### Frontend
* **Next.js**: 15 (App Router, TypeScript)
* **State & Rendering**: React 19, React Markdown, Recharts (Stock performance charts)
* **Styling**: Tailwind CSS & Material UI (MUI)

### Protocol / Integrations
* **Model Context Protocol (MCP)**: Native tools exposed via custom local servers (`news_server`, `yahoo_finance_server`) to retrieve news, sentiment, fundamentals, and financials.

---

## 📂 Project Structure

```text
StockMarketResearcher/
├── docs/                     # Detailed architectural & API documentation
│   ├── api_endpoints.md      # API Reference for routes, models, and SSE events
│   └── langfuse_integration.md # Langfuse integration details & evaluation configs
├── frontend/                 # React + Next.js web application
│   ├── src/
│   │   ├── api/             # API client & SSE hooks (useSSE)
│   │   ├── app/             # Next.js App Router (Pages, layout, reports dashboard)
│   │   └── components/      # UI components (Sparklines, charts, markdown reports)
│   ├── tailwind.config.js
│   └── tsconfig.json
├── backend/                  # FastAPI web server & agent workflow
│   ├── agents/               # CrewAI agents (CriticAgent, FundamentalsAgent, etc.)
│   ├── graph/                # LangGraph definition (workflow, nodes, report compiler)
│   ├── mcp_servers/          # Custom MCP servers (News & Yahoo Finance integrations)
│   ├── db/                   # Database models, schemas, and CRUD utilities
│   ├── config/               # Settings & system credentials manager
│   ├── observability/        # Langfuse client, trace initializers, and patches
│   ├── rag/                  # ChromaDB vector store wrapper & embeddings logic
│   ├── schema/               # Pydantic schemas (Request/Response models)
│   ├── requirements.txt
│   └── main.py               # FastAPI application entrypoint
├── notebooks/                # Jupyter Notebooks for agent prototyping
├── docker-compose.yml        # Docker composition for easy database/caching deployment
└── README.md                 # Main workspace documentation
```

---

## 📖 Documentation

* [Langfuse Integration Guide](file:///d:/Code/StockResearcher/StockMarketResearcher/docs/langfuse_integration.md) - Deep dive into tracing, prompt registry management, and LLM-as-a-Judge evaluations.
* [API Endpoints Guide](file:///d:/Code/StockResearcher/StockMarketResearcher/docs/api_endpoints.md) - Details on FastAPI endpoints, payload schemas, and SSE stream data shapes.

---

## 🚀 Getting Started

### 1. Prerequisites
* Python 3.12+
* Node.js 20+
* npm or Yarn

### 2. Environment Setup
Copy the example environment file in the project root:
```bash
cp .env.example .env
```

Ensure your `.env` contains the required keys:
```ini
OPENAI_API_KEY="your_openai_key"       # Or GEMINI_API_KEY / MISTRAL_API_KEY
NEWSAPI_KEY="your_news_api_key"        # For news search agent tools
DATABASE_URL="sqlite+aiosqlite:///./data/stock_market.db" # Default SQLite DB

# Langfuse Credentials (Required for Observability & Judge Evals)
LANGFUSE_PUBLIC_KEY="pk-lf-..."
LANGFUSE_SECRET_KEY="sk-lf-..."
LANGFUSE_HOST="https://cloud.langfuse.com"
```

### 3. Running the Backend
```bash
cd backend
python -m venv .venv
# On Windows: .venv\Scripts\activate
# On macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```
The backend server runs at <http://127.0.0.1:8000>.

### 4. Running the Frontend
```bash
cd frontend
npm install
npm run dev
```
The Next.js client dev server runs at <http://localhost:3000>.

---

## 🐳 Docker Deployment

To spin up the Postgres database, Redis cache, and both backend/frontend services in a production-like environment:

```bash
docker compose up --build
```
This binds:
* Frontend: `http://localhost:3000`
* Backend: `http://localhost:8000`
