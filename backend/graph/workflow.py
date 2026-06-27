"""LangGraph workflow that coordinates the stock research process."""

from typing import Any, Literal

from langgraph.graph import END, START, StateGraph

from mcp_servers.news_server import get_news, get_sentiment_score
from mcp_servers.yahoo_finance_server import (
    get_company_info,
    get_financials,
    get_stock_price,
)

from .state import ResearchState

MAX_ITERATIONS = 3
APPROVED = "approved"


def _safe_tool_call(tool_func: Any, *args: Any, **kwargs: Any) -> Any | None:
    try:
        return tool_func(*args, **kwargs)
    except Exception:
        return None


def researcher_node(state: ResearchState) -> dict:
    """Populate research data for the requested ticker using local MCP-backed tools."""
    ticker = state["ticker"].upper()
    iteration = state.get("iteration", 0) + 1

    market_data = {
        "ticker": ticker,
        "price": 100.0,
        "currency": "USD",
        "source": "placeholder",
    }
    news_sentiment = {
        "label": "neutral",
        "score": 0.0,
        "source": "placeholder",
    }
    fundamentals = {
        "summary": f"No fundamentals available for {ticker}.",
        "source": "placeholder",
    }

    stock_price = _safe_tool_call(get_stock_price, ticker)
    if stock_price is not None:
        market_data.update(
            {
                "price": stock_price.current_price,
                "currency": stock_price.currency,
                "percentage_change": stock_price.percentage_change,
                "source": "mcp",
            }
        )

    company_info = _safe_tool_call(get_company_info, ticker)
    if company_info is not None:
        fundamentals.update(
            {
                "company_name": company_info.name,
                "sector": company_info.sector,
                "industry": company_info.industry,
                "description": company_info.description,
                "source": "mcp",
            }
        )

    financials = _safe_tool_call(get_financials, ticker)
    if financials is not None:
        income_statement = financials.income_statement
        balance_sheet = financials.balance_sheet
        summary_parts = []
        if income_statement and income_statement.total_revenue is not None:
            summary_parts.append(
                f"Revenue: {income_statement.total_revenue:,.0f}"
            )
        if income_statement and income_statement.net_income is not None:
            summary_parts.append(
                f"Net income: {income_statement.net_income:,.0f}"
            )
        if balance_sheet and balance_sheet.total_assets is not None:
            summary_parts.append(
                f"Assets: {balance_sheet.total_assets:,.0f}"
            )

        fundamentals.update(
            {
                "summary": " | ".join(summary_parts) or fundamentals["summary"],
                "fiscal_year": financials.fiscal_year,
                "currency": financials.currency,
                "source": "mcp",
            }
        )

    news_result = _safe_tool_call(get_news, ticker, 7)
    if news_result is not None and getattr(news_result, "articles", None):
        headlines = [article.title for article in news_result.articles[:3] if article.title]
        fundamentals["news_headlines"] = headlines

    sentiment_result = _safe_tool_call(get_sentiment_score, ticker)
    if sentiment_result is not None:
        news_sentiment.update(
            {
                "label": sentiment_result.label,
                "score": sentiment_result.score,
                "source": "mcp",
                "positive_headlines": sentiment_result.positive_headlines,
                "negative_headlines": sentiment_result.negative_headlines,
                "neutral_headlines": sentiment_result.neutral_headlines,
            }
        )

    return {
        "ticker": ticker,
        "market_data": market_data,
        "news_sentiment": news_sentiment,
        "fundamentals": fundamentals,
        "iteration": iteration,
        "status": "research_complete",
    }


def critic_node(state: ResearchState) -> dict[str, str]:
    """Approve the placeholder research until a real critic is connected."""
    return {
        "critique": APPROVED,
        "status": "critique_approved",
    }


def report_node(state: ResearchState) -> dict[str, str]:
    """Format the collected research state as a Markdown report."""
    report = f"""# Research Report: {state["ticker"]}

## Market Data

- Price: {state["market_data"].get("price", "N/A")}
- Currency: {state["market_data"].get("currency", "N/A")}

## News Sentiment

- Label: {state["news_sentiment"].get("label", "N/A")}
- Score: {state["news_sentiment"].get("score", "N/A")}

## Fundamentals

{state["fundamentals"].get("summary", "No fundamentals available.")}

## Review

- Critique: {state["critique"]}
- Research iterations: {state["iteration"]}
"""
    return {
        "report": report,
        "status": "complete",
    }


def route_after_critique(state: ResearchState) -> Literal["report", "retry"]:
    """Send approved research to reporting, otherwise retry up to the limit."""
    critique = state.get("critique", "").strip().lower()
    if critique == APPROVED or state.get("iteration", 0) >= MAX_ITERATIONS:
        return "report"
    return "retry"


def build_research_graph():
    """Build and compile the research workflow."""
    workflow = StateGraph(ResearchState)
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("critic", critic_node)
    workflow.add_node("report", report_node)

    workflow.add_edge(START, "researcher")
    workflow.add_edge("researcher", "critic")
    workflow.add_conditional_edges(
        "critic",
        route_after_critique,
        {
            "report": "report",
            "retry": "researcher",
        },
    )
    workflow.add_edge("report", END)

    return workflow.compile()


graph = build_research_graph()
