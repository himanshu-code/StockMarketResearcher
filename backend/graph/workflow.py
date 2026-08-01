"""LangGraph workflow that coordinates the stock research process."""

from typing import Literal
import json
import logging 

from crewai import Process
from langgraph.graph import END, START, StateGraph

from agents.crew_manager import _make_crew, get_research_crew
from agents.CriticAgent import get_critic_agent, build_critic_task
from .state import ResearchState
from rag.vector_store import embed_report,retrieve_similar
from .report import report_node
from langfuse import propagate_attributes
from observability.langfuse_client import get_langfuse_client

MAX_ITERATIONS = 2
APPROVED = "approved"

_FALLBACK_CRITIQUE = {
    "approved": True,
    "critique": "Critic evaluation failed; proceeding to report.",
    "missing": [],
}

logger=logging.getLogger(__name__)  

def _get_trace_id(config:dict)->str|None:
    return (config or {}).get("metadata",{}).get("langfuse_trace_id")

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

def researcher_node(state: ResearchState,config:dict=None) -> dict:
    """Populate research data for the requested ticker using CrewAI agents."""
    ticker = state["ticker"].upper()
    iteration = state.get("iteration", 0) + 1
    rag_context=state.get("rag_context",[])
    trace_id = _get_trace_id(config)
    lf = get_langfuse_client()
    span = lf.start_observation(
        as_type="span",
        trace_context={"trace_id": trace_id} if trace_id else None,
        name=f"research/{ticker}/iter-{iteration}",
        input={"ticker": ticker, "iteration": iteration},
        metadata={"node": "researcher"}
    )
    crew = get_research_crew()
    try:
        crew_output = crew.run_research(ticker,rag_context=rag_context,trace_id=trace_id)
        span.update(output={"status":"research_complete"})
        span.end()
    except Exception as exc:
        logger.error("researcher_node failed for %s: %s",ticker,exc)
        span.update(output={"status":"research_failed"})
        span.end()
        raise


    return {
        "ticker": ticker,
        "market_data": crew_output.market_data,
        "news_sentiment": crew_output.news_sentiment,
        "fundamentals": crew_output.fundamentals,
        "iteration": iteration,
        "status": "research_complete",
    }


def critic_node(state: ResearchState,config:dict=None) -> dict[str, str]:
    """Run the critic agent to evaluate research quality"""
    ticker =state["ticker"]
    iteration=state["iteration"]
    trace_id=_get_trace_id(config)

    lf = get_langfuse_client()
    span = lf.start_observation(
        as_type="span",
        trace_context={"trace_id": trace_id} if trace_id else None,
        name=f"critic/{ticker}/iter-{iteration}",
        input={"ticker": ticker, "iteration": iteration, "market_data_keys": list(state.get("market_data", {}).keys())},
        metadata={"node": "critic"}
    )

    rag_context=state.get("rag_context",[])

    # 1. Fetch Critic prompt from Langfuse
    critic_prompt = lf.get_prompt("critic-agent-prompt", label="production")

    # 2. Dynamic Agent Instantiation
    critic_agent = get_critic_agent(
        ticker=ticker,
        goal=critic_prompt.compile(ticker=ticker),
        backstory=critic_prompt.config.get("backstory")
    )

    critic_task = build_critic_task(
        ticker=ticker,
        agent=critic_agent,
        market_data=state.get("market_data",{}),
        news_sentiment=state.get("news_sentiment",{}),
        fundamentals=state.get("fundamentals",{}),
        iteration=iteration,
        rag_context=rag_context
    )

    crew = _make_crew(
        agents=[critic_agent],
        tasks=[critic_task],
        process=Process.sequential,
        verbose=False,
        memory=False,
    )
    try:
        with propagate_attributes(prompt=critic_prompt):
            crew.kickoff()
        raw_output=critic_task.output.raw if critic_task.output else ""
        critique_result=_parse_critique_json(raw_output)
    except Exception as exec:
        logging.error('CriticAgent failed for %s:%s',ticker,exec)
        critique_result=_FALLBACK_CRITIQUE
    status="critique_approved" if critique_result["approved"] else "critique_retry"
    span.update(output={"approved":critique_result["approved"],"status":status,})
    span.end()
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
    """Query ChromaDB for prior analyses and inject them into ResearchState. (RAG DISABLED)"""
    # ticker = state["ticker"]
    # query = f"Stock research analyses for {ticker}"
    # try:
    #     prior_analyses = retrieve_similar(ticker=ticker, query=query, k=3)
    # except Exception:
    #     logger.exception("[RAG] rag_context_node failed for %s — falling back to empty context", ticker)
    #     prior_analyses = []
    return {"rag_context": []}

def persist_report_node(state: ResearchState) -> dict:
    """Store the completed report in ChromaDB for future RAG retrieval. (RAG DISABLED)"""
    # ticker = state["ticker"]
    # report = state.get("report", "")
    # if report:
    #     try:
    #         embed_report(report=report, ticker=ticker)
    #     except Exception as exc:
    #         logger.exception(
    #             "[RAG] persist_report_node FAILED for %s — full traceback:", ticker
    #         )
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
