import os

from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
	raise ValueError("GEMINI_API_KEY not found in .env")

client = genai.Client(api_key=api_key)

response = client.models.generate_content(
	model="gemini-3.6-flash",
	contents="Explain what an action item in a meeting means in one simple sentence.",
)

print(response.text)
