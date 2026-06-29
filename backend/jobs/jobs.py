from __future__ import annotations

import asyncio
from datetime import datetime,timezone
from typing import Any
from uuid import uuid4
from graph.workflow import graph

TERMINAL_STATUSES=["completed","failed"]

_jobs:dict[str,dict[str,Any]]={}
_jobs_lock=asyncio.Lock()

def _now()->datetime:
    return datetime.now(timezone.utc)

def _initial_job(ticker:str,job_id:str)->dict[str,Any]:
    now=_now()
    return {
        "job_id":job_id,
        "ticker":ticker.upper().strip(),
        "status":"queued",
        "report":None,
        "error":None,
        "created_at":now,
        "updated_at":now,
        "completed_at":None,
        "seq":0,
        "events":[],
        "queue":asyncio.Queue()

    }

async def create_job(ticker:str)->dict[str,Any]:
    job_id=str(uuid4())
    job=_initial_job(ticker,job_id)
    async with _jobs_lock:
        _jobs[job_id]=job
    return job

async def get_job(job_id:str)->dict[str,Any]|None:
    async with _jobs_lock:
        return _jobs.get(job_id)

async def list_reports()->list[dict[str,Any]]:
    async with _jobs_lock:
        completed=[
            job 
            for job in _jobs.values()
            if job["status"] =="completed" and job["report"] 
        ]
    return sorted(completed,key=lambda item:item["completed_at"],reverse=True)


async def _append_event(job_id:str,event:str,data:dict[str,Any]):
    async with _jobs_lock:
        job=_jobs[job_id]
        job["seq"]+=1
        record={
            "seq":job["seq"],
            "event":event,
            "data":data,
            "created_at":_now()
        }
        job["events"].append(record)
        job["updated_at"]=record["created_at"]
        queue=job["queue"]
    await queue.put(record)


async def _update_job(job_id:str,**fields:Any):
    async with _jobs_lock:
        job=_jobs[job_id]
        job.update(fields)
        job["updated_at"]=_now()

async def run_research_job(job_id: str):
    job=await get_job(job_id)
    if not job:
        return
    await _update_job(job_id,status="running")
    await _append_event(job_id,"agent_started",{"job_id":job_id,"ticker":job["ticker"]})
    initial_state = {
        "ticker": job["ticker"],
        "market_data": {},
        "news_sentiment": {},
        "fundamentals": {},
        "critique": "",
        "critique_result": {},
        "report": "",
        "iteration": 0,
        "status": "queued",
    }
    try:
        accumulated=dict(initial_state)
       
        async for chunk in graph.astream(initial_state):
            for node_name, node_output in chunk.items():
                accumulated.update(node_output)
                if node_name == "critic":
                    critique_result = node_output.get("critique_result", {})
                    await _append_event(
                        job_id,
                        "critique",
                        {
                            "job_id": job_id,
                            "iteration": accumulated.get("iteration", 1),
                            "approved": critique_result.get("approved"),
                            "critique": critique_result.get("critique", ""),
                            "missing": critique_result.get("missing", []),
                        },
                    )
                else:
                    await _append_event(
                        job_id,
                        node_name,
                        {
                            "job_id": job_id,
                            "iteration": accumulated.get("iteration", 1),
                            **node_output,
                        },
                    )
            

        # result =await graph.ainvoke({
        #     "ticker": job["ticker"],
        #     "market_data":{},
        #     "news_sentiment":{},
        #     "fundamentals":{},
        #     "critique":"",
        #     "report":"",
        #     "iteration":0,
        #     "status":"queued"
        # })

        report =accumulated.get("report","")
        await _update_job(job_id,status="completed",report=report,completed_at=_now())
        await _append_event(job_id,"agent_done",{"job_id":job_id,"ticker":job["ticker"]})
        await _append_event(job_id,"report_ready",{"job_id":job_id,"ticker":job["ticker"],"report":report})
    except Exception as e:
        error_text=str(e)
        await _update_job(job_id,status="failed",error=error_text,completed_at=_now())
        await _append_event(job_id,"agent_failed",{"job_id":job_id,"error":error_text})
