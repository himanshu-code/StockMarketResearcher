from __future__ import annotations

from datetime import datetime,timezone
from sqlalchemy import DateTime,Float,String,Text,JSON
from sqlalchemy.orm import Mapped,mapped_column
from db.database import Base

def _utcnow()->datetime:
    return datetime.now(timezone.utc)

class Report(Base):
    __tablename__ = "reports"
    id:Mapped[int]=mapped_column(primary_key=True,autoincrement=True)
    job_id:Mapped[str]=mapped_column(String(64),unique=True,index=True,nullable=False)
    ticker:Mapped[str]=mapped_column(String(16),index=True,nullable=False)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=_utcnow,nullable=False)
    markdown:Mapped[str]=mapped_column(Text,nullable=False)
    signal:Mapped[str]=mapped_column(String(16),nullable=False)
    confidence:Mapped[float]=mapped_column(Float,nullable=False)
    
class Job(Base):
    __tablename__="jobs"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    job_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    ticker: Mapped[str] = mapped_column(String(16), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="queued", nullable=False)
    report: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    signal: Mapped[str | None] = mapped_column(String(16), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    events: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)