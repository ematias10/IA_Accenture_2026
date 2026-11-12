import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

# Tomar la API key
api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=api_key)

print("Listando modelos disponibles para tu clave:")
for model in client.models.list():
    if "embed" in model.name:
        print(f"-> {model.name} (Métodos: {getattr(model, 'supported_generation_methods', [])})")