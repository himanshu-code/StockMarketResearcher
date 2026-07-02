from crewai import Agent
from crewai.tools import tool
# from .GPTLLM import llm
from .llm import llm

from mcp_servers.yahoo_finance_server import get_company_info, get_financials

fundamentalsAgent = Agent(
    role="Fundamental Research Analyst",
    goal=(
        "Assess the financial health of the company identified by {ticker}. "
        "Retrieve company profile and financial statements, then summarise "
        "key metrics such as revenue, net income, assets, liabilities, and equity."
    ),
    backstory=(
        "You are a rigorous Fundamental Research Analyst with expertise in "
        "dissecting balance sheets, income statements, and business models. "
        "You translate complex financial data into clear, structured summaries "
        "that help investors understand a company's true financial condition."
    ),
    verbose=True,
    allow_delegation=False,
    tools=[tool(get_company_info), tool(get_financials)],
    llm=llm,
    memory=False,
)