from crewai import Agent
from crewai.tools import tool
from .llm import llm as _default_llm

from mcp_servers.news_server import get_news, get_sentiment_score

def get_news_sentiment_agent(ticker: str, goal: str, backstory: str, llm=None) -> Agent:
    return Agent(
        role="Financial News Analyst",
        goal=goal,
        backstory=backstory,
        verbose=True,
        allow_delegation=False,
        tools=[tool(get_news), tool(get_sentiment_score)],
        llm=llm or _default_llm,
        memory=False,
    )
