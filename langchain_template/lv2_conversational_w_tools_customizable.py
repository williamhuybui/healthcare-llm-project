"""LangGraph Conversational Agent with Tools

A conversational AI agent with multiple tools:
- Calculator for mathematical expressions
- Time retrieval
- Public IP address lookup
- City location by IP
- Web search via Tavily
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

# ===== AGENT SETUP =====
memory = MemorySaver()
model = init_chat_model("openai:gpt-4", api_key=OPENAI_API_KEY)
search = TavilySearch(max_results=2, api_key=TAVILY_API_KEY) # Web search tool
tools = [search, calculator, get_time, get_public_ip, get_city_by_ip]
agent_executor = create_react_agent(model, tools, checkpointer=memory) #Orchestrator

def main():
    """Main conversation loop."""
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    
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