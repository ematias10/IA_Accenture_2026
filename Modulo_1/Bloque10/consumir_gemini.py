import os
import requests
from dotenv import load_dotenv
from cprint import cprint
import time
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
    inicio = time.time()
    respuesta = requests.post(url, json=body)
    duracion = time.time() - inicio
    cprint.info(f"Duración de la petición: {duracion} segundos")
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
    except Exception as e:
        cprint.fatal(f"Error inesperado: {e}")
        return None


def test_latencia(ciclos: int = 5):
    latencias = []
    for i in range(ciclos):
        url, body = armar_peticion("Cuanto es 2 + 2? Dame solo el resultado")
        inicio = time.time()
        datos = enviar_peticion(url, body)
        duracion = time.time() - inicio
        cprint.info(f"Duración de la petición {i + 1}: {duracion} segundos")
        latencias.append(duracion)
    latencia_promedio = sum(latencias) / len(latencias)
    cprint.info(
        f"Latencia promedio después de {ciclos} ciclos: {latencia_promedio} segundos"
    )


# Ejemplo de uso
if __name__ == "__main__":
    cprint.ok(
        obtener_dato_de_prueba(
            "¿Cuál es la capital legislativa de Sudafrica?",
            "Da respuestas de una sola palabra",
            None,
        )
    )
    cprint.ok(
        obtener_dato_de_prueba(
            "¿Cuál es la capital legislativa de Sudafrica?", "", None
        )
    )
    cprint.ok(
        obtener_dato_de_prueba(
            "¿Cuál es la capital legislativa de Sudafrica?",
            "Utiliza solo formato JSON sin markdown, claves: rta:str y fuente:str",
            None,
        )
    )
    cprint.err(
        obtener_dato_de_prueba(
            "¿Cuál es la capital legislativa de Sudafrica?",
            "Da respuestas de una sola palabra",
            {
                "type": "OBJECT",
                "properties": {"rta": {"type": "STRING"}, "fuente": {"type": "STRING"}},
                "required": ["rta", "fuente"],
            },
        )
    )
