"""LangGraph workflow that coordinates the stock research process."""

from typing import Literal

from langgraph.graph import END, START, StateGraph

from .state import ResearchState

MAX_ITERATIONS = 3
APPROVED = "approved"


def researcher_node(state: ResearchState) -> dict:
    """Populate placeholder research data for the requested ticker."""
    ticker = state["ticker"].upper()
    iteration = state.get("iteration", 0) + 1

    return {
        "ticker": ticker,
        "market_data": {
            "ticker": ticker,
            "price": 100.0,
            "currency": "USD",
            "source": "mock",
        },
        "news_sentiment": {
            "label": "neutral",
            "score": 0.0,
            "source": "mock",
        },
        "fundamentals": {
            "summary": f"Placeholder fundamentals for {ticker}.",
            "source": "mock",
        },
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
