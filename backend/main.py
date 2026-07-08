from __future__ import annotations

import json
import logging
from contextlib import asynccontextmanager

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import get_settings
from db.database import get_db, init_db
from db import crud
from graph.workflow import graph  # Imported to keep the app wired to the workflow package.
from jobs.jobs import create_job, get_job, run_research_job
from schema.schemas import (
    ReportHistoryItem,
    ResearchJobResponse,
    ResearchRequest,
    ResearchSubmitResponse,
    OHLCVToolResponse,
)
from utils.pdf import markdown_to_pdf
from utils.cache import redis_cache
import asyncio


settings = get_settings()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialise DB tables on startup."""
    try:
        await init_db()
        logger.info("[DB] Tables created/verified successfully")
    except Exception:
        logger.exception(
            "[DB] init_db failed — DB features (GET /reports, PDF export) unavailable. "
            "Check DATABASE_URL in .env"
        )
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost",
        "https://stock-market-researcher.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _format_sse(event: dict) -> str:
    data = json.dumps(event["data"], default=str)
    return f"event: {event['event']}\ndata: {data}\n\n"


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

@app.post("/research", response_model=ResearchSubmitResponse)
async def start_research(
    request: ResearchRequest,
    background_tasks: BackgroundTasks,
) -> ResearchSubmitResponse:
    job = await create_job(request.ticker)
    background_tasks.add_task(run_research_job, job["job_id"])
    return ResearchSubmitResponse(
        job_id=job["job_id"],
        message=f"Research for {request.ticker} started.",
    )

@app.get("/research/{job_id}", response_model=ResearchJobResponse)
async def get_research(job_id: str) -> ResearchJobResponse:
    job = await get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return ResearchJobResponse(
        job_id=job["job_id"],
        ticker=job["ticker"],
        status=job["status"],
        report=job["report"],
        error=job["error"],
        created_at=job["created_at"],
        updated_at=job["updated_at"],
        completed_at=job["completed_at"],
        signal=job.get("signal"),
        confidence=job.get("confidence"),
    )

@app.get("/research/{job_id}/stream")
async def stream_research(job_id: str) -> StreamingResponse:
    job = await get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    async def event_generator():
        last_seq = 0
        snapshot = list(job["events"])

        for event in snapshot:
            last_seq = event["seq"]
            yield _format_sse(event)

        if job["status"] in {"completed", "failed"} and snapshot:
            return

        queue = job["queue"]
        while True:
            event = await queue.get()
            if event["seq"] <= last_seq:
                continue

            last_seq = event["seq"]
            yield _format_sse(event)

            if event["event"] in {"report_ready", "agent_failed"}:
                break

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/research/{job_id}/export")
async def export_report(
    job_id: str,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Convert the completed Markdown report to a PDF and stream it as a download."""
    report = await crud.get_report_by_job_id(db, job_id)
    if not report:
        raise HTTPException(
            status_code=404,
            detail="Report not found in database for the given job ID",
        )
    if not report.markdown:
        raise HTTPException(
            status_code=400,
            detail="Report markdown is empty or not available",
        )

    pdf_bytes = markdown_to_pdf(report.markdown)
    ticker = report.ticker or "report"

    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{ticker}_report.pdf"',
            "Content-Length": str(len(pdf_bytes)),
        },
    )


@app.get("/reports", response_model=list[ReportHistoryItem])
async def get_reports(
    page: int = 1,
    per_page: int = 10,
    db: AsyncSession = Depends(get_db),
) -> list[ReportHistoryItem]:
    """Return paginated report history from the database (persists across restarts)."""
    try:
        rows = await crud.list_reports_paginated(db, page=page, per_page=per_page)
        return [ReportHistoryItem.model_validate(r) for r in rows]
    except Exception:
        logger.exception("[GET /reports] DB query failed")
        raise HTTPException(
            status_code=503,
            detail="Report history unavailable — database connection failed. Check DATABASE_URL.",
        )


@redis_cache(ttl_seconds=300)
def _get_full_ohlcv(ticker: str, period: str) -> OHLCVToolResponse:
    from yfinance import Ticker
    from schema.schemas import OHLCVRecord
    normalized_ticker = ticker.strip().upper()
    tick = Ticker(normalized_ticker)
    ohlcv_data = tick.history(period=period, auto_adjust=False)
    
    records = []
    for timestamp, row in ohlcv_data.iterrows():
        records.append(
            OHLCVRecord(
                date=timestamp.to_pydatetime() if hasattr(timestamp, "to_pydatetime") else timestamp,
                open=float(row["Open"]),
                high=float(row["High"]),
                low=float(row["Low"]),
                close=float(row["Close"]),
                volume=int(row["Volume"]),
            )
        )
        
    return OHLCVToolResponse(ticker=normalized_ticker, period=period, data=records)


@app.get("/stock/{ticker}/ohlcv", response_model=OHLCVToolResponse)
async def get_stock_ohlcv(ticker: str, period: str = "1mo") -> OHLCVToolResponse:
    """Fetch 30-day historical OHLCV data for drawing stock price sparklines."""
    try:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _get_full_ohlcv, ticker, period)
    except Exception as e:
        logger.exception("[GET /stock/{ticker}/ohlcv] Failed to fetch OHLCV data")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch stock history: {str(e)}",
        )
