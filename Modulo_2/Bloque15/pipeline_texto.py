from collections import Counter
import re


def limpiar_texto(texto: str) -> str:
    """Normaliza el texto: minúsculas y sin puntuación."""
    if not isinstance(texto, str):
        raise ValueError("El argumento debe ser una cadena de texto.")
    texto = texto.lower()
    texto = re.sub(r"[^\w\s]", "", texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto

def tokenizar(texto_limpio: str) -> list[str]:
    """Convierte texto limpio en una lista de tokens."""
    return texto_limpio.split()

def vectorizar(tokens: list[str]) -> Counter:
    """Cuenta cuántas veces aparece cada token."""
    return Counter(tokens)


def procesar_texto(texto: str) -> list[str]:
    texto_limpio = limpiar_texto(texto)
    return tokenizar(texto_limpio)

if __name__ == "__main__":
    texto = "El gato y el perro"
    texto_limpio = limpiar_texto(texto)
    print(texto_limpio)
    tokens = tokenizar(texto_limpio)
    print(tokens)
    vectores = vectorizar(tokens)
    print(vectores)


    # Comparacion de dos textos
    referencia = "Es San Juan de Pasto"
    respuesta = "Es SAN Juan Pasto de Juan  "

    tokens_referencia = referencia.split()
    tokens_respuesta = respuesta.split()

    set_referencia = set(tokens_referencia)
    set_respuesta = set(tokens_respuesta)

    comunes = set(tokens_referencia) & set(tokens_respuesta)

    if tokens_referencia:
        proporcion = len(comunes) / len(set_referencia)
    else:
        proporcion = 0.0

    print(f"Proporción de coincidencias: {proporcion:.2f}")

    # Procesar textos
    tokens_referencia = procesar_texto(referencia)
    tokens_respuesta = procesar_texto(respuesta)

    print(f"Tokens referencia: {tokens_referencia}")
    print(f"Tokens respuesta: {tokens_respuesta}")

    # Comparar tokens
    set_referencia = set(tokens_referencia)
    set_respuesta = set(tokens_respuesta)

    comunes = set_referencia & set_respuesta

    if tokens_referencia:
        proporcion = len(comunes) / len(set_referencia)
    else:
        proporcion = 0.0

    print(f"Proporción de coincidencias: {proporcion:.2f}")