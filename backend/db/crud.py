from __future__ import annotations 

import logging
from datetime import datetime,timezone
from sqlalchemy import select

from sqlalchemy.ext.asyncio import AsyncSession
from db.models import Report

logger=logging.getLogger(__name__)

async def save_report(
    db:AsyncSession,
    *,
    job_id:str,
    ticker:str,
    markdown:str,
    signal:str,
    confidence:float,
)-> Report:
    report=Report(
        job_id=job_id,
        ticker=ticker.upper(),
        signal=signal,
        confidence=confidence,
        markdown=markdown,
        created_at=datetime.now(timezone.utc)
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    logger.info(
        "[CRUD] Saved report | ticker=%s | job_id=%s | signal=%s | confidence=%.2f",
        ticker.upper(),job_id,signal,confidence
    )
    return report

async def get_report_by_job_id(db:AsyncSession,job_id:str)->Report| None:
    result=await db.execute(select(Report).where(Report.job_id==job_id))
    return result.scalar_one_or_none()

async def list_reports_paginated(db:AsyncSession,*,page:int=1,per_page:int=10)-> list[Report]:
    offset=(page-1)*per_page
    result=await db.execute(select(Report).order_by(Report.created_at.desc()).offset(offset).limit(per_page))
    return list(result.scalars().all())

