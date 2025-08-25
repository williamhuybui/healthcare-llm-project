"""LangGraph Conversational Agent with Tools

A conversational AI agent with multiple tools:
- Calculator for mathematical expressions
- Time retrieval
- Public IP address lookup
- City location by IP
- Web search via Tavily
"""

import os
import math
import re
import time
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_tavily import TavilySearch
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

# Load environment variables
load_dotenv('../.env')

# Environment variables
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
TAVILY_API_KEY = os.getenv('TAVILY_API_KEY')

# ===== TOOL DEFINITIONS =====

@tool
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

@tool
def get_time() -> str:
    """Returns the current date and time."""
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

@tool
def get_public_ip(_: str = "") -> str:
    """Returns the public IP address using an external service."""
    try:
        import requests
        ip = requests.get('https://api.ipify.org', timeout=5).text
        return f"Public IP: {ip}"
    except Exception as e:
        return f"Error: {str(e)}"
@tool
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

# ===== AGENT SETUP =====
memory = MemorySaver()
model = init_chat_model("openai:gpt-4")
search = TavilySearch(max_results=2, api_key=TAVILY_API_KEY)
tools = [search, calculator, get_time, get_public_ip, get_city_by_ip]
agent_executor = create_react_agent(model, tools, checkpointer=memory)

def main():
    """Main conversation loop."""
    config = {"configurable": {"thread_id": "conversation_1"}}
    
    print("🤖 AI Agent ready! Available tools: calculator, time, IP lookup, search")
    print("💬 Type 'exit' to quit\n")
    
    while True:
        try:
            user_input = input("👤 You: ").strip()
            
            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("👋 Goodbye!")
                break
            
            if not user_input:
                continue
            
            input_message = {
                "messages": [{
                    "role": "user",
                    "content": user_input
                }]
            }
            
            response = agent_executor.invoke(input_message, config=config)
            
            # Display all messages (user, tool calls, and AI responses)
            for message in response["messages"]:
                message.pretty_print()
                    
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    main()
