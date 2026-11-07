
from unittest.mock import MagicMock
from langchain_core.runnables import RunnableLambda
from enrutamiento import (
    construir_cadena_queja_segura,
    procesar_mensaje_seguro
)

def test_fallback_local_se_activa():
    # 1. Creamos una cadena que siempre lanza error
    cadena_rota = RunnableLambda(lambda x: (_ for _ in ()).throw(ConnectionError("Error red")))
    
    # 2. La protegemos con el fallback
    cadena_protegida = construir_cadena_queja_segura(cadena_rota)
    
    # 3. Invocamos pasando el diccionario requerido
    resultado = cadena_protegida.invoke({"mensaje": "Mi servicio no funciona"})
    
    # 4. Validamos que retorne el fallback y no la excepción
    assert "atención preferente" in resultado.lower() or "atención prioritaria" in resultado.lower()

def test_red_seguridad_global_captura_error():
    # 1. Mockeamos la cadena para que su método .invoke() lance excepción
    cadena_simulada = MagicMock()
    cadena_simulada.invoke.side_effect = TimeoutError("Timeout en pasarela")
    
    # 2. Ejecutamos la función segura
    resultado = procesar_mensaje_seguro(cadena_simulada, "Hola")
    
    # 3. Validamos que devuelva el mensaje de contingencia
    assert "inconveniente técnico" in resultado.lower()
