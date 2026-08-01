# API Endpoints Documentation

This document describes the API endpoints exposed by the backend FastAPI application for the Stock Market Researcher.

---

## Base URL
* **Development**: `http://127.0.0.1:8000`
* **Production**: (Vercel/Docker environment host)

All request/response bodies are in JSON format unless stated otherwise.

---

## Endpoints Reference

### 1. Health Check
* **Endpoint**: `GET /health`
* **Description**: Verifies if the backend server is running correctly.
* **Response**:
  ```json
  {
    "status": "ok"
  }
  ```

---

### 2. Start Research Job
* **Endpoint**: `POST /research`
* **Description**: Initiates a background research process for a given stock ticker. This spins up the agentic workflow (LangGraph + CrewAI) and returns immediately with a unique job ID.
* **Request Body**:
  ```json
  {
    "ticker": "AAPL"
  }
  ```
* **Response** (`ResearchSubmitResponse`):
  ```json
  {
    "job_id": "6a997ee6-b534-4ef7-9a07-d44cb411fc83",
    "message": "Research for AAPL started."
  }
  ```

---

### 3. Get Research Job Status
* **Endpoint**: `GET /research/{job_id}`
* **Description**: Retrieves the current status, metadata, and generated report (if complete) of a research job.
* **Response** (`ResearchJobResponse`):
  ```json
  {
    "job_id": "6a997ee6-b534-4ef7-9a07-d44cb411fc83",
    "ticker": "AAPL",
    "status": "completed", // "queued" | "running" | "completed" | "failed"
    "report": "# AAPL Research Report...\n\n## Executive Summary...",
    "error": null,
    "created_at": "2026-08-01T23:28:07Z",
    "updated_at": "2026-08-01T23:30:12Z",
    "completed_at": "2026-08-01T23:30:12Z",
    "signal": "Bullish", // "Bullish" | "Neutral" | "Bearish" | null
    "confidence": 0.87, // float between 0.0 and 1.0 or null
    "langfuse_trace_id": "1da7741308dd4a6fbbb626fd60fb2228"
  }
  ```

---

### 4. Stream Research Real-Time Events (SSE)
* **Endpoint**: `GET /research/{job_id}/stream`
* **Description**: Connects to a Server-Sent Events (SSE) stream to receive live log updates from the agent workspace (e.g., node transitions, researcher logs, critic feedback, report completion).
* **Headers**:
  * `Accept: text/event-stream`
* **SSE Message Format**:
  ```text
  event: <event_type>
  data: <json_string>
  ```
* **Common Event Types & Payloads**:
  * `trace_created`:
    ```json
    { "job_id": "...", "langfuse_trace_id": "..." }
    ```
  * `agent_started`:
    ```json
    { "job_id": "...", "ticker": "AAPL" }
    ```
  * `critic` (feedback from Critic agent):
    ```json
    { "job_id": "...", "approved": false, "critique": "Missing valuation parameters...", "missing": ["gross_margins"] }
    ```
  * `report_ready` (final completion):
    ```json
    { "job_id": "...", "report": "...", "signal": "...", "confidence": 0.85 }
    ```

---

### 5. Export Report to PDF
* **Endpoint**: `POST /research/{job_id}/export`
* **Description**: Fetches the completed research report, compiles the markdown content to a PDF document, and streams it back to the client as an attachment.
* **Response Content Type**: `application/pdf`
* **Response Headers**:
  * `Content-Disposition: attachment; filename="AAPL_report.pdf"`

---

### 6. List Saved Reports (History)
* **Endpoint**: `GET /reports`
* **Description**: Returns a paginated list of all completed research reports stored in the database.
* **Query Parameters**:
  * `page` (default: `1`): The page number to fetch.
  * `per_page` (default: `10`): Number of items per page.
* **Response** (`list[ReportHistoryItem]`):
  ```json
  [
    {
      "id": 1,
      "job_id": "6a997ee6-b534-4ef7-9a07-d44cb411fc83",
      "ticker": "AAPL",
      "created_at": "2026-08-01T23:30:12Z",
      "signal": "Bullish",
      "confidence": 0.87
    }
  ]
  ```

---

### 7. Fetch Stock OHLCV History
* **Endpoint**: `GET /stock/{ticker}/ohlcv`
* **Description**: Retrieves historical Open, High, Low, Close, Volume (OHLCV) records for a stock. Used on the frontend to draw historical price sparklines and charts.
* **Query Parameters**:
  * `period` (default: `"1mo"`): The timeframe window (e.g., `"1d"`, `"1wk"`, `"1mo"`, `"1y"`).
* **Response** (`OHLCVToolResponse`):
  ```json
  {
    "ticker": "TSLA",
    "period": "1mo",
    "data": [
      {
        "date": "2026-07-01T00:00:00Z",
        "open": 180.50,
        "high": 185.00,
        "low": 179.20,
        "close": 184.10,
        "volume": 84200000
      }
    ]
  }
  ```
