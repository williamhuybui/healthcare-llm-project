#!/usr/bin/env python3
"""Test script for the LangGraph ReAct Agent"""

import uuid
from custom_tool import agent

def test_agent():
    """Test the agent with a simple calculation"""
    print("Testing LangGraph ReAct Agent...")
    
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    # Test calculation
    test_message = "What is 2+2?"
    print(f"Testing: {test_message}")
    
    try:
        response = agent.invoke(
            {"messages": [("user", test_message)]},
            config=config
        )
        
        print("✅ Agent successfully invoked!")
        print("Last message:")
        last_message = response["messages"][-1]
        print(f"Content: {last_message.content}")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_agent()
    print(f"\nTest {'PASSED' if success else 'FAILED'}")