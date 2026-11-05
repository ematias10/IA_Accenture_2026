from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate

from langchain_core.output_parsers import StrOutputParser

from cprint import cprint
import os
from dotenv import load_dotenv

load_dotenv()  # Esto busca el archivo .env y carga las variables
modelo = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite")

plantilla_extraccion = PromptTemplate.from_template(
    "Lee el siguiente texto y devuelve solo sus 3 puntos "
    "clave, uno por línea, sin desarrollarlos:\n\n{texto}"
)

paso_extraccion = plantilla_extraccion | modelo | StrOutputParser()

plantilla_simplificacion = PromptTemplate.from_template(
    "Reescribe estos puntos en lenguaje simple, sin jerga "
    "técnica, para alguien sin conocimientos previos:\n\n{puntos}"
)

paso_simplificacion = (
    plantilla_simplificacion | modelo | StrOutputParser()
)

plantilla_formato = PromptTemplate.from_template(
    "Convierte este texto en una lista de viñetas markdown, "
    "de máximo 3 líneas, sin introducción:\n\n{texto_simple}"
)

paso_formato = plantilla_formato | modelo | StrOutputParser()


texto_prueba = (
    "Los modelos de lenguaje grandes generan texto "
    "prediciendo un token a la vez, basándose en el "
    "texto que ya generaron antes. Cada token puede "
    "ser una palabra completa, parte de una palabra, "
    "o un signo de puntuación. Antes de que el modelo "
    "genere una respuesta, el texto de entrada se "
    "divide en tokens, un proceso llamado tokenización."
)

# Parte 1 
puntos_clave = paso_extraccion.invoke({"texto": texto_prueba})
cprint.err(type(puntos_clave))
cprint.info(puntos_clave)

# Parte 2
texto_simple = paso_simplificacion.invoke({"puntos": puntos_clave})
cprint.err(type(texto_simple))
cprint.info(texto_simple)

# Parte 3
texto_formateado = paso_formato.invoke({"texto_simple": texto_simple})
cprint.err(type(texto_formateado))
cprint.info(texto_formateado)

# Proceso completo en una sola cadena

cadena_simplificada=(
    plantilla_extraccion
    | modelo
    | StrOutputParser()
    | (lambda puntos: {"puntos": puntos}) # Para pasar la salida del paso anterior como entrada del siguiente dict
    | plantilla_simplificacion
    | modelo
    | StrOutputParser()
    | (lambda texto_simple: {"texto_simple": texto_simple}) # Para pasar la salida del paso anterior como entrada del siguiente dict
    | plantilla_formato
    | modelo
    | StrOutputParser()
)

cprint.err(type(cadena_simplificada))
cprint.info(cadena_simplificada.invoke({"texto": texto_prueba}))   