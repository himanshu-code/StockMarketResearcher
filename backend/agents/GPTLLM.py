from crewai import LLM
from dotenv import load_dotenv
import os




llm = LLM(
    model = 'openai/gpt-4.1-mini',
    api_base = os.getenv("OPENAI_BASE_URL"),
    api_key = os.getenv("OPENAI_API_KEY"),
    temperature = 0
)