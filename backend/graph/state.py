"""Shared state passed between nodes in the research graph."""

from typing import TypedDict


class ResearchState(TypedDict):
    ticker: str
    market_data: dict
    news_sentiment: dict
    fundamentals: dict
    critique: str
    report: str
    iteration: int
    status: str
    critique_result: dict 
    rag_context:list[str]