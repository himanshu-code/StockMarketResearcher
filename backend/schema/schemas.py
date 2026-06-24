from __future__ import annotations
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

class ResearchRequest(BaseModel):
    ticker: str = Field(..., description="The stock ticker symbol to research.")

class ResearchSubmitResponse(BaseModel):
    job_id: str = Field(..., description="The unique identifier for the research job.")
    message: str = Field(..., description="A message indicating the status of the research request.")

class ResearchEvent(BaseModel):
    seq:int
    event:str
    data:dict[str, Any]
    created_at:datetime 

class ResearchJobResponse(BaseModel):
    job_id:str 
    ticker:str
    status:str
    report:str | None = None
    error:str | None = None
    created_at:datetime
    updated_at:datetime
    completed_at:datetime | None = None

class ResearchReportItem(BaseModel):
    job_id:str
    ticker:str
    status:str
    report:str
    created_at:datetime
    updated_at:datetime