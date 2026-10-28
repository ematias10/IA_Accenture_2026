import requests
import json
from dotenv import load_dotenv
import os

# Cargar variables de entorno desde el archivo .env
load_dotenv()

url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent"

payload = json.dumps(
    {
        "contents": [
            {"parts": [{"text": "Explicame como funciona la NBA en 20 palabras"}]}
        ]
    }
)
headers = {
    "x-goog-api-key": os.getenv("AI_API_KEY"),
    "Content-Type": "application/json",
}

try:
    response = requests.request("POST", url, headers=headers, data=payload)

    print(response.text)

except Exception as e:
    print("Error:", e)

print("API request completed.")
