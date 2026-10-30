"""
Pipeline de procesamiento básico de texto (NLP inicial).
Proporciona funciones para limpieza con expresiones regulares y tokenización.
"""

import re

def limpiar_texto(texto: str) -> str:
    """Convierte a minúsculas y remueve caracteres especiales y puntuación."""
    texto_bajo = texto.lower()
    # Elimina todo lo que no sea letra, número o espacio en blanco
    texto_limpio = re.sub(r"[^\w\s]", "", texto_bajo)
    return texto_limpio.strip()

def tokenizar(texto_limpio: str) -> list[str]:
    """Divide el texto limpio en una lista de palabras (tokens)."""
    if not texto_limpio:
        return []
    return texto_limpio.split()

def procesar_texto(texto_crudo: str) -> list[str]:
    """Pipeline que une la limpieza y la tokenización."""
    limpio = limpiar_texto(texto_crudo)
    return tokenizar(limpio)

if __name__ == "__main__":
    ejemplo = "¡Alerta en Producción! Error 500 al conectar con la base de datos."
    print("Texto original:", ejemplo)
    print("Tokens limpios:", procesar_texto(ejemplo))
