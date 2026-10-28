from peticiones import make_request
import os
from dotenv import load_dotenv

load_dotenv()

result = make_request(
    url="https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent",
    api_key=os.getenv("AI_API_KEY"),
    prompt="Explicame como funciona la UEFA en 20 palabras",
)

print(result)
