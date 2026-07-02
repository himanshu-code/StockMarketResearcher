from crewai import Agent
from crewai.tools import tool
# from .GPTLLM import llm
from .llm import llm

from mcp_servers.news_server import get_news, get_sentiment_score

newsSentimentAgent = Agent(
    role="Financial News Analyst",
    goal=(
        "Gauge market sentiment from recent news for {ticker}. "
        "Retrieve the latest news articles and compute an overall sentiment score, "
        "categorising headlines as positive, negative, or neutral."
    ),
    backstory=(
        "You are a sharp Financial News Analyst with deep expertise in parsing "
        "financial press, earnings call commentary, and market headlines. "
        "You cut through noise to surface the sentiment signals that move markets, "
        "delivering concise, structured sentiment summaries that traders can act on."
    ),
    verbose=True,
    allow_delegation=False,
    tools=[tool(get_news), tool(get_sentiment_score)],
    llm=llm,
    memory=False,
)