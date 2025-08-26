"""LangGraph ReAct Agent with Tools

A ReAct (Reason + Act) conversational AI agent with multiple tools:
- Calculator for mathematical expressions
- Time retrieval
- Public IP address lookup
- City location by IP
- Web search via Tavily

ReAct combines reasoning and acting in language models by having the model
generate both reasoning traces and task-specific actions in an interleaved manner.
"""

import os
import uuid
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_tavily import TavilySearch
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from tools.test_tools import *
# Load environment variables
load_dotenv('.env')

# Environment variables
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
TAVILY_API_KEY = os.getenv('TAVILY_API_KEY')

# ===== REACT AGENT SETUP =====
memory = MemorySaver()
model = init_chat_model("openai:gpt-4", api_key=OPENAI_API_KEY, temperature=0)
search = TavilySearch(max_results=2, api_key=TAVILY_API_KEY)  # Web search tool
tools = [search, calculator, get_time, get_public_ip, get_city_by_ip]

SYSTEM_PROMPT = (
    "You are a helpful assistant that follows the ReAct pattern with tools. "
    "Decide when and which tools to call; you may chain multiple tools if useful. "
    "Prefer tools over guessing. Do not reveal hidden reasoning; only show tool calls and your final answer."
)

# --- AGENT ---
memory = MemorySaver()
agent = create_react_agent(model=model, tools=tools, checkpointer=memory)

# --- MAIN ---
def main():
    print("ReAct Agent ready. Tools: calculator, time, IP, city-by-IP, Tavily search")
    print("Type 'exit' to quit.\n")

    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    while True:
        user_text = input("You: ").strip()
        if user_text.lower() in {"exit", "quit", "bye"}:
            print("Goodbye!")
            break
        if not user_text:
            continue

        response = agent.invoke(
            {"messages": [("system", SYSTEM_PROMPT), ("user", user_text)]},
            config=config
        )

        print("\n=== FULL CONVERSATION TRACE ===")
        for message in response["messages"]:
            message.pretty_print()
        print("================================\n")

if __name__ == "__main__":
    main()