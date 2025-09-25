#!/usr/bin/env python3
"""
Local runner for LangGraph agents without langgraph dev server
This bypasses the langgraph-cli dependency issues
"""

import uuid
from custom_tool import graph

def main():
    print("🚀 LangGraph Agent Running Locally")
    print("Type 'exit' to quit.\n")
    
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    while True:
        try:
            user_text = input("You: ").strip()
            if user_text.lower() in {"exit", "quit", "bye"}:
                print("Goodbye!")
                break
            if not user_text:
                continue
            
            print("🤖 Processing...")
            response = graph.invoke(
                {"messages": [("user", user_text)]},
                config=config
            )
            
            # Just show the final assistant message
            last_message = response["messages"][-1]
            print(f"Assistant: {last_message.content}\n")
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}\n")

if __name__ == "__main__":
    main()