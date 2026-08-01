from crewai import Agent
from crewai.tools import tool
# from .GPTLLM import llm
from .llm import llm

from mcp_servers.yahoo_finance_server import get_company_info, get_financials

def get_fundamentals_agent(ticker: str, goal: str, backstory: str) -> Agent:
    return Agent(
        role="Fundamental Research Analyst",
        goal=goal,
        backstory=backstory,
        verbose=True,
        allow_delegation=False,
        tools=[tool(get_company_info), tool(get_financials)],
        llm=llm,
        memory=False,
    )

