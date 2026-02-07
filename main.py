import json
import os
import asyncio

from langchain_community.agent_toolkits import SQLDatabase
from dotenv import load_dotenv
from openai import OpenAI

load.dotenv()
AI_TOKEN = os.getenv("AI_TOKEN")

SYSTEM_PROMPT = """

"""

client = OpenAI(
    base_url = "https://openrouter.ai/api/v1",
    api_key=AI_TOKEN,
    max_retries=0
)