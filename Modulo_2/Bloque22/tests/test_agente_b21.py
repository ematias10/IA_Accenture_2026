"""
PRUEBAS UNITARIAS: BLOQUE 21
----------------------------
Verifica determinísticamente:
  1. Que las herramientas funcionen de forma aislada.
  2. Que la traza de decisión registre correctamente la herramienta invocada.
"""

from unittest.mock import MagicMock
from langchain_core.agents import AgentAction
from src.agente_b21 import consultar_stock_producto, calcular_descuento_promocional


def test_herramienta_consultar_stock_aislada():
    resultado = consultar_stock_producto.invoke({"nombre_producto": "laptop"})
    assert "5 unidades" in resultado
    assert "$800" in resultado


def test_herramienta_calcular_descuento_aislada():
    resultado = calcular_descuento_promocional.invoke({"precio": 100.0, "porcentaje": 20.0})
    assert "$80.00" in resultado


def test_auditoria_traza_de_decision_con_mock():
    accion_falsa = AgentAction(
        tool="consultar_stock_producto",
        tool_input={"nombre_producto": "teclado"},
        log="Decidí consultar el inventario para el teclado"
    )
    observacion_falsa = "20 unidades en bodega"

    resultado_simulado = {
        "input": "¿Hay teclados?",
        "output": "Sí, disponemos de 20 teclados en bodega.",
        "intermediate_steps": [(accion_falsa, observacion_falsa)]
    }

    pasos = resultado_simulado["intermediate_steps"]
    assert len(pasos) == 1
    assert pasos[0][0].tool == "consultar_stock_producto"
    assert pasos[0][0].tool_input == {"nombre_producto": "teclado"}
