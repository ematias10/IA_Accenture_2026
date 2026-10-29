import re
from collections import Counter

def limpiar_texto(texto: str) -> str:
    """Normaliza el texto: minúsculas y sin puntuación."""
    #convertir todo el text a minusculas
    texto = texto.lower() 
    print(texto)
    #eliminar cualquier signo de puntuacion o elemento que no sea letra, numero o espacio en blanco
    texto = re.sub(r"[^\w\s]", "", texto) 
    print(texto)
    ##r"\s+" convierte todo espacio multiple consecutivo, en un solo espacio en blanco
    ##strip elimina los espacios antes y despues
    texto = re.sub(r"\s+", " ", texto).strip() 
    print(texto)

    
    return texto

def tokenizar(texto_limpio: str) -> list[str]:
    """Convierte texto limpio en una lista de tokens."""
    return texto_limpio.split()

# lista[] -> se puede modificar, agregar, quitar.
# tupla() -> es inmutable

def vectorizar(tokens: list[str]) -> Counter:
    """Cuenta cuantas veces se repite un token"""
    return Counter(tokens)

texto = "El gaTo y   el PerrO . El perro va a ladrar y el gato va a maullar."
texto_limpio = limpiar_texto(texto)

texto_tokenizado = tokenizar(texto_limpio)
print(f"El texto tokenizado es: {texto_tokenizado}")

counter_vectores = vectorizar(texto_tokenizado)
print(f"Counters: {counter_vectores}")



