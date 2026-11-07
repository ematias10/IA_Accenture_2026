"""
PRUEBAS UNITARIAS: BLOQUE 22
----------------------------
Verifica determinísticamente:
  1. Que InMemoryChatMessageHistory almacene mensajes en orden.
  2. Que dos sesiones distintas mantengan sus historiales completamente aislados.
"""

from langchain_core.messages import HumanMessage, AIMessage
from src.agente_con_memoria_b22 import obtener_historial_por_sesion, almacen_historiales


def test_almacen_historial_guarda_mensajes_en_orden():
    almacen_historiales.clear()

    historial = obtener_historial_por_sesion("sesion_test_01")
    historial.add_message(HumanMessage(content="Mi presupuesto es $500"))
    historial.add_message(AIMessage(content="Entendido, registraré ese tope."))

    assert len(historial.messages) == 2
    assert historial.messages[0].content == "Mi presupuesto es $500"
    assert "tope" in historial.messages[1].content


def test_aislamiento_estricto_entre_sesiones():
    almacen_historiales.clear()

    hist_carlos = obtener_historial_por_sesion("carlos_id")
    hist_ana = obtener_historial_por_sesion("ana_id")

    hist_carlos.add_message(HumanMessage(content="Soy Carlos"))
    hist_ana.add_message(HumanMessage(content="Soy Ana"))

    assert len(hist_carlos.messages) == 1
    assert len(hist_ana.messages) == 1
    assert hist_carlos.messages[0].content == "Soy Carlos"
    assert hist_ana.messages[0].content == "Soy Ana"
    assert "Carlos" not in hist_ana.messages[0].content
