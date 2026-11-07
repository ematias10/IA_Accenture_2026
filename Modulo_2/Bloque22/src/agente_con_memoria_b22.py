"""
BLOQUE 22: MEMORIA CONVERSACIONAL Y PERSISTENCIA POR SESIÓN
-----------------------------------------------------------
Objetivos de aprendizaje:
  1. Superar el estado 'stateless' de los modelos reinyectando historial.
  2. Agregar MessagesPlaceholder('historial') al prompt del agente.
  3. Administrar almacenes de mensajes independientes por session_id.
  4. Envolver la ejecución con RunnableWithMessageHistory.
"""

import os
from dotenv import load_dotenv, find_dotenv

from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.runnables import RunnableLambda
from langchain_google_genai import ChatGoogleGenerativeAI

try:
    from langchain.agents import AgentExecutor, create_tool_calling_agent
except ImportError:
    # Soporte para versiones modernas de LangChain (>=1.0.0 / langchain-classic)
    from langchain_classic.agents import AgentExecutor, create_tool_calling_agent

load_dotenv(find_dotenv())


# ============================================================================
# PASO 1: HERRAMIENTAS BÁSICAS
# ============================================================================

@tool
def consultar_catalogo(categoria: str) -> str:
    """Busca productos dentro de una categoría específica (ej: computacion, audio)."""
    catalogo = {
        "computacion": "MacBook Pro ($1800), Monitor 4K ($400)",
        "audio": "Audífonos Noise Cancelling ($250), Micrófono USB ($100)"
    }
    return catalogo.get(categoria.strip().lower(), "Categoría sin productos disponibles.")

herramientas = [consultar_catalogo]


# ============================================================================
# PASO 2: PROMPT CON HISTORIAL + SCRATCHPAD
# ============================================================================

def construir_prompt_con_memoria():
    """
    DIFERENCIA FUNDAMENTAL ENTRE LOS DOS PLACEHOLDERS:
      - 'historial': Turnos previos completos (Usuario y Asistente de sesiones pasadas).
      - 'agent_scratchpad': Acciones intermedias del agente en el turno ACTUAL.
    """
    return ChatPromptTemplate.from_messages([
        (
            "system",
            "Eres un asesor de ventas con memoria. Recuerda los nombres, preferencias "
            "y datos compartidos por el cliente en turnos anteriores para responder con continuidad."
        ),
        MessagesPlaceholder("historial"),         # Reinyección de contexto pasado
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),  # Razonamiento del turno presente
    ])


# ============================================================================
# PASO 3: GESTIÓN DEL ALMACÉN DE SESIONES (IN-MEMORY)
# ============================================================================

almacen_historiales = {}

def obtener_historial_por_sesion(session_id: str) -> InMemoryChatMessageHistory:
    """
    Garantiza aislamiento: Cada usuario/sesión tiene su propia libreta de notas.
    Si la sesión no existe, se inicializa vacía.
    """
    if session_id not in almacen_historiales:
        almacen_historiales[session_id] = InMemoryChatMessageHistory()
    return almacen_historiales[session_id]


# ============================================================================
# PASO 4: CONSTRUCCIÓN DEL SISTEMA CON RunnableWithMessageHistory
# ============================================================================

def normalizar_salida_agente(resultado: dict) -> dict:
    """
    Garantiza que el valor de 'output' sea siempre un string limpio.
    En versiones recientes de Google GenAI, el modelo puede devolver bloques de
    contenido estructurados (list[dict]) en lugar de texto plano. Esto rompería
    RunnableWithMessageHistory al reinyectar el historial en los siguientes turnos.
    """
    salida = resultado.get("output", "")
    if isinstance(salida, list):
        texto = "".join(b.get("text", "") if isinstance(b, dict) else str(b) for b in salida)
        resultado["output"] = texto
    return resultado


def construir_agente_con_memoria(modelo, herramientas):
    """
    Envuelve el AgentExecutor con la capa de persistencia conversacional.
    """
    prompt = construir_prompt_con_memoria()
    agente = create_tool_calling_agent(modelo, herramientas, prompt)
    ejecutor = AgentExecutor(agent=agente, tools=herramientas, verbose=False)
    ejecutor_normalizado = ejecutor | RunnableLambda(normalizar_salida_agente)

    return RunnableWithMessageHistory(
        ejecutor_normalizado,
        obtener_historial_por_sesion,
        input_messages_key="input",
        history_messages_key="historial"
    )


if __name__ == "__main__":
    modelo_nombre = os.getenv("AI_MODEL") or "gemini-3.5-flash"
    llm = ChatGoogleGenerativeAI(model=modelo_nombre, temperature=0.1)
    asistente_memoria = construir_agente_con_memoria(llm, herramientas)

    config_sesion_1 = {"configurable": {"session_id": "cliente_carlos"}}
    config_sesion_2 = {"configurable": {"session_id": "cliente_ana"}}

    print("--- TURNO 1: Carlos se presenta ---")
    r1 = asistente_memoria.invoke(
        {"input": "Hola, mi nombre es Carlos y me interesa renovar mi equipo de computación."},
        config=config_sesion_1
    )
    print("Carlos:", r1["output"])

    print("\n--- TURNO 2: Carlos pregunta por su nombre sin repetirlo ---")
    r2 = asistente_memoria.invoke(
        {"input": "¿Recuerdas cómo me llamo y qué categoría de producto busco?"},
        config=config_sesion_1
    )
    print("Carlos:", r2["output"])

    print("\n--- TURNO 3: Ana entra en otra sesión (Verificación de aislamiento) ---")
    r3 = asistente_memoria.invoke(
        {"input": "¿Sabes cuál es mi nombre?"},
        config=config_sesion_2
    )
    print("Ana:", r3["output"])
