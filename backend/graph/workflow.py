"""LangGraph workflow that coordinates the stock research process."""

from typing import Literal

from langgraph.graph import END, START, StateGraph

from agents.crew_manager import get_research_crew
from .state import ResearchState

MAX_ITERATIONS = 3
APPROVED = "approved"


def researcher_node(state: ResearchState) -> dict:
    """Populate research data for the requested ticker using CrewAI agents."""
    ticker = state["ticker"].upper()
    iteration = state.get("iteration", 0) + 1

    crew = get_research_crew()
    crew_output = crew.run_research(ticker)

    return {
        "ticker": ticker,
        "market_data": crew_output.market_data,
        "news_sentiment": crew_output.news_sentiment,
        "fundamentals": crew_output.fundamentals,
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
    md = state.get("market_data", {})
    ns = state.get("news_sentiment", {})
    fu = state.get("fundamentals", {})

    top_headlines = ns.get("top_headlines") or []
    headlines_md = (
        "\n".join(f"  - {h}" for h in top_headlines)
        if top_headlines
        else "  - N/A"
    )

    report = f"""# Research Report: {state["ticker"]}

## Market Data

- Current Price: {md.get("current_price", "N/A")} {md.get("currency", "")}
- Day Change: {md.get("percentage_change", "N/A")}%
- Trend: {md.get("trend", "N/A")}
- 52-Week High: {md.get("high_52w", "N/A")}
- 52-Week Low: {md.get("low_52w", "N/A")}

## News Sentiment

- Overall: {ns.get("label", "N/A")} (score: {ns.get("score", "N/A")})
- Positive / Negative / Neutral Headlines: {ns.get("positive_headlines", 0)} / {ns.get("negative_headlines", 0)} / {ns.get("neutral_headlines", 0)}
- Top Headlines:
{headlines_md}

## Fundamentals

- Company: {fu.get("company_name", "N/A")}
- Sector / Industry: {fu.get("sector", "N/A")} / {fu.get("industry", "N/A")}
- Market Cap: {fu.get("market_cap", "N/A")}
- Revenue: {fu.get("revenue", "N/A")}
- Net Income: {fu.get("net_income", "N/A")}
- Total Assets: {fu.get("total_assets", "N/A")}
- Total Liabilities: {fu.get("total_liabilities", "N/A")}
- Total Equity: {fu.get("total_equity", "N/A")}
- Fiscal Year: {fu.get("fiscal_year", "N/A")} ({fu.get("currency", "N/A")})

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
