import os
import requests
from dotenv import load_dotenv
from cprint import cprint
import re
import json

load_dotenv()


def calcular_costo_peticion(
    datos: dict, precio_entrada: float, precio_salida: float
) -> float:
    tokens_entrada = datos["usageMetadata"]["promptTokenCount"]
    tokens_salida = datos["usageMetadata"]["candidatesTokenCount"]
    costo_entrada = tokens_entrada * precio_entrada
    costo_salida = tokens_salida * precio_salida
    costo_total = costo_entrada + costo_salida
    return costo_total


def armar_peticion(
    pregunta: str, system_instruction: str, response_schema: dict = None
) -> tuple[str, dict]:
    if type(pregunta) != str:
        raise ValueError("La pregunta debe ser una cadena de texto.")
    api_key = os.getenv("AI_API_KEY")
    modelo = "gemini-3.5-flash-lite"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={api_key}"
    body = {
        "systemInstruction": {"parts": [{"text": system_instruction}]},
        "contents": [{"parts": [{"text": pregunta}]}],
    }
    if response_schema:
        body["generationConfig"] = {
            "responseMimeType": "application/json",
            "responseSchema": response_schema,
        }
    return url, body


def enviar_peticion(url: str, body: dict) -> dict:
    try:
        respuesta = requests.post(url, json=body, timeout=10)
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
        raise TimeoutError(f"Error de conexión o tiempo de espera: {e}")

    if respuesta.status_code in (401, 403):
        raise ValueError("Error de autenticación. Verifica tu API key.")
    if respuesta.status_code == 429:
        if "Retry-After" in respuesta.headers:
            tiempo_espera = int(respuesta.headers["Retry-After"])
            raise TimeoutError(
                f"Se ha alcanzado el límite de peticiones. Intenta más tarde en {tiempo_espera} segundos."
            )
        else:
            raise TimeoutError(
                "Se ha alcanzado el límite de peticiones. Intenta más tarde."
            )
    return respuesta.json()


def extraer_texto(datos: dict) -> str:
    cprint.ok("Tokens prompt:", datos["usageMetadata"]["promptTokenCount"])
    cprint.ok("Tokens candidates:", datos["usageMetadata"]["candidatesTokenCount"])
    cprint.ok("Tokens total:", datos["usageMetadata"]["totalTokenCount"])
    return datos["candidates"][0]["content"]["parts"][0]["text"]


def parsear_respuesta_json(texto):
    texto_limpio = texto.strip()  # Elimina espacios en blanco al inicio y al final
    texto_limpio = re.sub(
        r"^```(?:json)?\s*", "", texto_limpio
    )  # Elimina el bloque de código inicial si es md
    texto_limpio = re.sub(
        r"\s*```$", "", texto_limpio
    )  # Elimina el bloque de código final si es md
    try:
        datos = json.loads(
            texto_limpio
        )  # Intenta convertir el texto limpio a un diccionario de Python
    except json.JSONDecodeError:
        raise ValueError(
            "La respuesta del modelo no es JSON válido."
        )  # Si no es válido, lanza un error
    if "rta" not in datos or "fuente" not in datos:
        raise ValueError(
            "La respuesta no tiene la estructura esperada."
        )  # Si no tiene las claves esperadas, lanza un error
    return datos  # Devuelve el diccionario con las claves "rta" y "fuente"


def obtener_dato_de_prueba(
    pregunta: str, system_instruction: str, response_schema: dict = None
) -> str | None:
    try:
        url, body = armar_peticion(pregunta, system_instruction, response_schema)
        datos = enviar_peticion(url, body)
        costo = calcular_costo_peticion(datos, 0.0000003, 0.0000025)
        cprint.info(f"Costo estimado de la petición: {costo}")
        texto = extraer_texto(datos)
        if response_schema:
            datos_json = parsear_respuesta_json(texto)
            return datos_json
        else:
            return texto
    except KeyError as e:
        cprint.fatal(f"Error al extraer el dato de prueba: {e}")
        return None
    except ValueError as e:
        cprint.fatal(f"Error de valor: {e}")
        return
    except Exception as e:
        cprint.fatal(f"Error inesperado: {e}")
        return None


# Ejemplo de uso
if __name__ == "__main__":
    print("Prueba local")
    cprint.err(
        obtener_dato_de_prueba(
            "¿Cuál es la capital legislativa de Sudafrica?",
            "Da respuestas de una sola palabra",
            None,
        )
    )
