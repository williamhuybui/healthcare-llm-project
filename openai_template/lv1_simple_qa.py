from openai import OpenAI
import os 

openai_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_key)

response = client.responses.create(
    model="gpt-5",
    input="What did I just ask?"
)

print(response.output_text)
