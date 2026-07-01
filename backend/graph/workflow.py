"""LangGraph workflow that coordinates the stock research process."""

from typing import Literal
import json
import logging 

from crewai import Crew,Process
from langgraph.graph import END, START, StateGraph

from agents.crew_manager import get_research_crew
from agents.CriticAgent import criticAgent,build_critic_task
from .state import ResearchState
from rag.vector_store import embed_report,retrieve_similar
from .report import report_node

MAX_ITERATIONS = 2
APPROVED = "approved"

_FALLBACK_CRITIQUE = {
    "approved": True,
    "critique": "Critic evaluation failed; proceeding to report.",
    "missing": [],
}

logger=logging.getLogger(__name__)  

def _parse_critique_json(raw: str) -> dict:
    """Extract and parse the JSON critique result from LLM output."""
    text = raw.strip()
    if "```json" in text:
        try:
            text = text.split("```json", 1)[1].split("```", 1)[0].strip()
        except IndexError:
            pass
    elif "```" in text:
        try:
            text = text.split("```", 1)[1].split("```", 1)[0].strip()
        except IndexError:
            pass
    try:
        result = json.loads(text)
        # Validate required keys
        if "approved" in result and "critique" in result and "missing" in result:
            return result
    except json.JSONDecodeError as exc:
        logging.warning("Failed to parse critique JSON: %s", exc)
    return _FALLBACK_CRITIQUE

def researcher_node(state: ResearchState) -> dict:
    """Populate research data for the requested ticker using CrewAI agents."""
    ticker = state["ticker"].upper()
    iteration = state.get("iteration", 0) + 1
    rag_context=state.get("rag_context",[])

    crew = get_research_crew()
    crew_output = crew.run_research(ticker,rag_context=rag_context)

    return {
        "ticker": ticker,
        "market_data": crew_output.market_data,
        "news_sentiment": crew_output.news_sentiment,
        "fundamentals": crew_output.fundamentals,
        "iteration": iteration,
        "status": "research_complete",
    }


def critic_node(state: ResearchState) -> dict[str, str]:
    """Run the critic agent to evaluate research quality"""
    ticker =state["ticker"]
    iteration=state["iteration"]

    rag_context=state.get("rag_context",[])
    if iteration>1 and not rag_context:
        query=f"Contradictions and issues in {ticker} stock analysis"
        rag_context=retrieve_similar(ticker=ticker,query=query,k=2)

    critic_task=build_critic_task(
        ticker=ticker,
        market_data=state.get("market_data",{}),
        news_sentiment=state.get("news_sentiment",{}),
        fundamentals=state.get("fundamentals",{}),
        iteration=iteration,
        rag_context=rag_context
        )
    crew=Crew(
        agents=[criticAgent],
        tasks=[critic_task],
        process=Process.sequential,
        verbose=False,
        memory=False
    )
    try:
        crew.kickoff()
        raw_output=critic_task.output.raw if critic_task.output else ""
        critique_result=_parse_critique_json(raw_output)
    except Exception as exec:
        logging.error('CriticAgent failed for %s:%s',ticker,exec)
        critique_result=_FALLBACK_CRITIQUE
    status="critique_approved" if critique_result["approved"] else "critique_retry"
    return {
        "critique":critique_result["critique"],
        "critique_result":critique_result,    
        "status":status
    }

   



def route_after_critique(state: ResearchState) -> Literal["report", "retry"]:
    """Send approved research to reporting, otherwise retry up to the limit."""
    critique_result=state.get("critique_result",{})
    approved=critique_result.get("approved",True)
    if approved or state.get("iteration", 0) >= MAX_ITERATIONS:
        return "report"
    return "retry"


def rag_context_node(state: ResearchState) -> dict:
    """Query ChromaDB for prior analyses and inject them into ResearchState."""
    ticker = state["ticker"]
    query = f"Stock research analyses for {ticker}"
    try:
        prior_analyses = retrieve_similar(ticker=ticker, query=query, k=3)
    except Exception:
        logger.exception("[RAG] rag_context_node failed for %s — falling back to empty context", ticker)
        prior_analyses = []
    return {"rag_context": prior_analyses}

def persist_report_node(state: ResearchState) -> dict:
    """Store the completed report in ChromaDB for future RAG retrieval."""
    ticker = state["ticker"]
    report = state.get("report", "")
    if report:
        try:
            embed_report(report=report, ticker=ticker)
        except Exception as exc:
            logger.exception(
                "[RAG] persist_report_node FAILED for %s — full traceback:", ticker
            )
    return {}
    
def build_research_graph():
    """Build and compile the research workflow."""
    workflow = StateGraph(ResearchState)
    workflow.add_node("rag_context", rag_context_node)
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("critic", critic_node)
    workflow.add_node("report", report_node)
    workflow.add_node("persist_report", persist_report_node)


    workflow.add_edge(START, "rag_context")
    workflow.add_edge("rag_context","researcher")
    workflow.add_edge("researcher", "critic")
    workflow.add_conditional_edges(
        "critic",
        route_after_critique,
        {
            "report": "report",
            "retry": "researcher",
        },
    )
    workflow.add_edge("report","persist_report")
    workflow.add_edge("persist_report",END)

    return workflow.compile()


graph = build_research_graph()
