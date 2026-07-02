from __future__ import annotations
from datetime import datetime
from typing import Any, Literal

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
    job_id: str
    ticker: str
    status: str
    report: str | None = None
    error: str | None = None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None
    signal: str | None = None
    confidence: float | None = None

class ResearchReportItem(BaseModel):
    job_id:str
    ticker:str
    status:str
    report:str
    created_at:datetime
    updated_at:datetime


class StockPriceToolResponse(BaseModel):
    ticker: str = Field(..., description="The stock ticker symbol.")
    current_price: float = Field(..., description="The current price of the stock.")
    percentage_change: float = Field(..., description="The percentage change in the stock price.")
    currency: str = Field(..., description="The currency of the stock price.")
    fifty_two_week_high:float|None=Field(...,description="The 52 week high of the stock.")
    fifty_two_week_low:float|None=Field(...,description="The 52 week low of the stock.")
    

class OHLCVRecord(BaseModel):
    date: datetime = Field(..., description="The date of the record.")
    open: float = Field(..., description="The opening price of the stock.")
    high: float = Field(..., description="The highest price of the stock.")
    low: float = Field(..., description="The lowest price of the stock.")
    close: float = Field(..., description="The closing price of the stock.")
    volume: int = Field(..., description="The trading volume of the stock.")

class OHLCVToolResponse(BaseModel):
    ticker: str = Field(..., description="The stock ticker symbol.")
    period: str = Field(..., description="The period for which the OHLCV data is provided (e.g., '1d', '1wk', '1mo').")
    data: list[OHLCVRecord] = Field(..., description="A list of OHLCV records for the stock.")

class CompanyInfoToolResponse(BaseModel):
    ticker: str = Field(..., description="The stock ticker symbol.")
    name: str | None = Field(None, description="The name of the company.")
    sector: str | None = Field(None, description="The sector in which the company operates.")
    industry: str | None = Field(None, description="The industry in which the company operates.")
    market_cap: float | None = Field(None, description="The market capitalization of the company.")
    description: str | None = Field(None, description="A brief description of the company.")


class IncomeStatementSummary(BaseModel):
    total_revenue: float | None = None
    gross_profit: float | None = None
    operating_income: float | None = None
    net_income: float | None = None
    diluted_eps: float | None = None


class BalanceSheetSummary(BaseModel):
    total_assets: float | None = None
    total_liabilities: float | None = None
    total_equity: float | None = None
    cash_and_cash_equivalents: float | None = None
    total_debt: float | None = None


class FinancialsToolResponse(BaseModel):
    ticker: str
    currency: str | None = None
    fiscal_year: int | None = None
    income_statement: IncomeStatementSummary | None = None
    balance_sheet: BalanceSheetSummary | None = None


class NewsArticle(BaseModel):
    title: str | None = None
    source: str | None = None
    url: str | None = None
    published_at: datetime | None = None
    description: str | None = None


class NewsToolResponse(BaseModel):
    ticker: str
    days: int
    articles: list[NewsArticle] = Field(default_factory=list)


class SentimentToolResponse(BaseModel):
    ticker: str
    label: Literal["positive", "negative", "neutral"]
    score: float
    positive_headlines: int | None = None
    negative_headlines: int | None = None
    neutral_headlines: int | None = None


class ReportHistoryItem(BaseModel):
    """Row returned by GET /reports — DB-backed, paginated."""
    id: int
    job_id: str
    ticker: str
    created_at: datetime
    signal: str
    confidence: float

    model_config = {"from_attributes": True}  # allows ORM -> Pydantic conversion
