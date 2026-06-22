# Stock Market Researcher

Full-stack monorepo for the Stock Market Researcher application.

## Project structure

```text
StockMarketResearcher/
├── frontend/          # React + Vite
├── backend/           # FastAPI
│   ├── agents/
│   ├── graph/
│   ├── mcp_servers/
│   └── config/
├── notebooks/
├── .env.example
├── docker-compose.yml
└── README.md
```

## Prerequisites

- Python 3.12+
- Node.js 20+
- npm

## Environment setup

Copy the example environment file and fill in any keys needed for local development:

```bash
cp .env.example .env
```

The expected variables are:

- `OPENAI_API_KEY`
- `NEWSAPI_KEY`
- `DATABASE_URL`

## Backend setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

The backend starts at <http://127.0.0.1:8000>. Verify it with:

```bash
curl http://127.0.0.1:8000/health
```

Expected response:

```json
{"status":"ok"}
```

## Frontend setup

```bash
cd frontend
npm install
npm run dev
```

The Vite dev server starts at <http://localhost:5173>.

## Docker Compose

After creating `.env`, both services can be started with:

```bash
docker compose up --build
```
