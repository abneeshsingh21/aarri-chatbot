# test_groq.py
import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Groq client
client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

try:
    print("📡 Querying Groq: What is the capital of France?")
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",  # ✅ Fast & reliable
        messages=[
            {"role": "user", "content": "What is the capital of France?"}
        ],
        temperature=0.7,
        max_tokens=64
    )
    print("✅ Success!")
    print("Answer:", response.choices[0].message.content)

except Exception as e:
    print("❌ Error:", str(e))