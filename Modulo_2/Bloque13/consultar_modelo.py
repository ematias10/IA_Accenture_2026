from consumir_gemini import armar_peticion, calcular_costo_peticion, extraer_texto,enviar_peticion
from reintento import con_reintento

response_schema = {
                "type": "OBJECT",
                "properties": {"rta": {"type": "STRING"}, "fuente": {"type": "STRING"}},
                "required": ["rta", "fuente"],
            }
def consultar_modelo(pregunta: str, system_instruction: str = "") -> str:
    url, body = armar_peticion(pregunta, system_instruction, None)
    try:
        respuesta = con_reintento(lambda: enviar_peticion(url, body), intentos=5, espera_base=5, espera_maxima=10)
    except TimeoutError:
        raise RuntimeError("El servicio no respondió tras varios intentos. Intenta más tarde.")
    
    costo = calcular_costo_peticion(respuesta,0.0001,0.0025)
    print(f"Costo de la petición: {costo}")
    return extraer_texto(respuesta)


if __name__ == "__main__":
    print("Prueba local")
    for i in range(100):
        print(f"Iteración {i+1}:")
        consultar_modelo(
            "¿Quíen ganó la carrera de Austin 2024?",
            "Escudería, piloto, y posiciones finales en lista",
        )
