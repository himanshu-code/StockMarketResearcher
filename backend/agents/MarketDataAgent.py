from crewai import Agent
from crewai.tools import tool
# from .GPTLLM import llm
from .llm import llm

from mcp_servers.yahoo_finance_server import get_stock_price, get_ohlcv

def get_market_data_agent(ticker: str, goal: str, backstory: str) -> Agent:
    return Agent(
        role="Senior Market Analyst",
        goal=goal,
        backstory=backstory,
        verbose=True,
        allow_delegation=False,
        tools=[tool(get_stock_price), tool(get_ohlcv)],
        llm=llm,
        memory=False,
    )


