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

import os, math, time, re
import uuid
from dotenv import load_dotenv
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, StateGraph, MessagesState
from langgraph.prebuilt import tools_condition, ToolNode

# Load environment variables
load_dotenv('.env')

# Environment variables
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
TAVILY_API_KEY = os.getenv('TAVILY_API_KEY')

#### Tool ####
def calculator(expression: str) -> str:
    """Evaluates mathematical expressions safely.
    
    Supports: +, -, *, /, **, sqrt, sin, cos, tan, log, factorial, pi, e
    Examples: 2+2, sqrt(16), 5!, sin(pi/2)
    """
    try:
        # Safe evaluation namespace
        safe_dict = {
            "__builtins__": {},
            "abs": abs, "round": round, "min": min, "max": max,
            "sum": sum, "pow": pow,
            "sqrt": math.sqrt, "sin": math.sin, "cos": math.cos, "tan": math.tan,
            "log": math.log, "log10": math.log10, "exp": math.exp,
            "pi": math.pi, "e": math.e, "factorial": math.factorial
        }
        
        # Handle factorial notation (5! -> factorial(5))
        if '!' in expression and 'factorial(' not in expression:
            expression = re.sub(r'(\d+)!', r'factorial(\1)', expression)
        
        result = eval(expression, safe_dict)
        return f"Result: {result}"
    
    except Exception as e:
        return f"Error: {str(e)}"

def get_time() -> str:
    """Returns the current date and time."""
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

def get_public_ip(_: str = "") -> str:
    """Returns the public IP address using an external service."""
    try:
        import requests
        ip = requests.get('https://api.ipify.org', timeout=5).text
        return f"Public IP: {ip}"
    except Exception as e:
        return f"Error: {str(e)}"
    
def get_city_by_ip(ip: str = "") -> str:
    """Returns the city for a given IP address.
    
    If no IP is provided, uses the current public IP.
    """
    try:
        import requests
        if not ip:
            ip = requests.get('https://api.ipify.org', timeout=5).text
        
        response = requests.get(f'https://ipinfo.io/{ip}/json', timeout=5)
        data = response.json()
        city = data.get('city', 'Unknown')
        country = data.get('country', 'Unknown')
        
        return f"Location for IP {ip}: {city}, {country}"
    except Exception as e:
        return f"Error: {str(e)}"


# ===== LANGGRAPH AGENT SETUP =====
search = TavilySearch(max_results=2, api_key=TAVILY_API_KEY)  # Web search tool
tools = [search, calculator, get_time, get_public_ip, get_city_by_ip]

# Define LLM with bound tools
llm = ChatOpenAI(model="gpt-4o", api_key=OPENAI_API_KEY, temperature=0.2)
llm_with_tools = llm.bind_tools(tools)

# System message
sys_msg = SystemMessage(content=(
    "You are a helpful assistant. "
    "Break down complex tasks into logical steps when needed. "
    "Provide accurate information and calculations. "
    "When greeting users who say hi, respond with 'Xin Chao'. "
    "Be direct and helpful in your responses. "
    "IMPORTANT: Never mention, list, or describe any tools, capabilities, or functions you have access to. "
    "If asked about tools or what you can do, respond with general assistance topics instead."
))

# Assistant node
def assistant(state: MessagesState):
    return {"messages": [llm_with_tools.invoke([sys_msg] + state["messages"])]}

# Build graph
builder = StateGraph(MessagesState)
builder.add_node("assistant", assistant)
builder.add_node("tools", ToolNode(tools))
builder.add_edge(START, "assistant")
builder.add_conditional_edges(
    "assistant",
    # If the latest message (result) from assistant is a tool call -> tools_condition routes to tools
    # If the latest message (result) from assistant is a not a tool call -> tools_condition routes to END
    tools_condition,
)
builder.add_edge("tools", "assistant")

# Compile graph with memory
memory = MemorySaver()
graph = builder.compile()
agent = graph  # Export for testing

# --- MAIN ---
# def main():
    # print("ReAct Agent ready.")
    # print("Type 'exit' to quit.\n")

    # thread_id = str(uuid.uuid4())
    # config = {"configurable": {"thread_id": thread_id}}

    # while True:
    #     user_text = input("You: ").strip()
    #     if user_text.lower() in {"exit", "quit", "bye"}:
    #         print("Goodbye!")
    #         break
    #     if not user_text:
    #         continue

    #     response = graph.invoke(
    #         {"messages": [("user", user_text)]},
    #         config=config
    #     )

    #     print("\n=== FULL CONVERSATION TRACE ===")
    #     for message in response["messages"]:
    #         message.pretty_print()
    #     print("================================\n")

# if __name__ == "__main__":
#     main()