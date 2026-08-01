# pyrefly: ignore [missing-import]
from crewai import Agent,Task
# from .GPTLLM import llm
from .llm import llm
def get_critic_agent(ticker: str, goal: str, backstory: str) -> Agent:
    return Agent(
        role="Research Quality Auditor",
        goal=goal,
        backstory=backstory,
        verbose=True,
        allow_delegation=False,
        tools=[],
        llm=llm,
        memory=False,
    )





def build_critic_task(ticker:str,agent:Agent,market_data:dict,news_sentiment:dict,fundamentals:dict,iteration:int,rag_context:list[str]|None =None)->Task:
    rag_block=""
    if rag_context:
        joined="\n\n--\n\n".join(rag_context)
        rag_block=f"\n\n Previous analysis context (look for contradictions):\n{joined}"
    return Task(
        name="Critic_evalutation",
        description=(
            f"Evaluate the following research data for '{ticker}'"
            f"(iteration {iteration})."
            f"Market data: \n{market_data}"
            f"News sentiment: \n{news_sentiment}"
            f"Fundamentals: \n{fundamentals}"
            +rag_block+
            "\ncheck for:\n "
            "  1. Missing or null critical fields (market_cap, revenue, net_income, current_price).\n"
            "  2. Conflicting signals (e.g., bullish trend but very negative sentiment score < -0.5).\n"
            "  3. Absence of top headlines (empty list).\n"
            "  4. Source fields set to 'error'.\n\n"
            "Return ONLY a valid JSON object with exactly these keys:\n"
            "  'approved' (bool): true if research quality is acceptable.\n"
            "  'critique' (str): concise human-readable summary of issues found.\n"
            "  'missing' (list[str]): list of missing or problematic field names.\n"
            "If no issues are found, return: "
            '{"approved": true, "critique": "Research is complete and consistent.", "missing": []}'
        ),
        expected_output=('A JSON object {"approved":bool,"critique":str,"missing":list[str]}'
        ),
        agent=agent,
    )
