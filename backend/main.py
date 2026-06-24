from __future__ import annotations

import json
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from config.settings import get_settings
from graph.workflow import graph  # Imported to keep the app wired to the workflow package.
from jobs.jobs import create_job, get_job, list_reports, run_research_job
from schema.schemas import (
    ResearchJobResponse,
    ResearchReportItem,
    ResearchRequest,
    ResearchSubmitResponse,
)
import asyncio

settings = get_settings()

app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173","http://localhost"],
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


@app.get("/reports", response_model=list[ResearchReportItem])
async def get_reports() -> list[ResearchReportItem]:
    reports = await list_reports()
    return [
        ResearchReportItem(
            job_id=report["job_id"],
            ticker=report["ticker"],
            status=report["status"],
            report=report["report"],
            created_at=report["created_at"],
            updated_at=report["updated_at"],
        )
        for report in reports
    ]
