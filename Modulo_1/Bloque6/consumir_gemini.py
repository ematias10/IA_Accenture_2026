import os
import requests
from dotenv import load_dotenv
from cprint import cprint

load_dotenv()


def armar_peticion(pregunta):
    api_key = os.getenv("AI_API_KEY")
    modelo = "gemini-3.5-flash-lite"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={api_key}"
    body = {"contents": [{"parts": [{"text": pregunta}]}]}
    return url, body


def enviar_peticion(url, body):
    respuesta = requests.post(url, json=body)
    return respuesta.json()


def extraer_texto(datos):
    return datos["candidates"][0]["content"]["parts"][0]["text"]


def obtener_dato_de_prueba(pregunta):
    url, body = armar_peticion(pregunta)
    datos = enviar_peticion(url, body)
    return extraer_texto(datos)


# Ejemplo de uso
if __name__ == "__main__":
    cprint.ok(obtener_dato_de_prueba("¿Cuál es la capital de Escocia?"))
