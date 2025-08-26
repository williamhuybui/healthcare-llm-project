# Import relevant functionality
import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model

# Load environment variables
load_dotenv('../.env')
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

# Create the agent
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
TEST_API_KEY = os.getenv('TEST_API_KEY')


memory = MemorySaver()
model = init_chat_model("openai:gpt-4", api_key=TEST_API_KEY)
agent_executor = create_react_agent(model, checkpointer=memory, tools = [])

config = {"configurable": {"thread_id": "abc123"}}

# input_message = {
#     "messages": [
#         {
#             "role": "user", 
#             "content": "Hi, I'm Bob and I live in SF."
#         }
#     ]
# }

# response = agent_executor.invoke(input_message, config=config)
# for message in response["messages"]:
#     message.pretty_print()

#Loop, continuous
while True:
    user_input = input("You: ")
    if user_input.lower() == "exit":
        break

    input_message = {
        "messages": [
            {
                "role": "user",
                "content": user_input
            }
        ]
    }

    response = agent_executor.invoke(input_message, config=config)
    for message in response["messages"]:
        message.pretty_print()
