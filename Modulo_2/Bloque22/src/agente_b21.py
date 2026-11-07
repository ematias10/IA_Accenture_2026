"""
BLOQUE 21: PRIMER AGENTE CON HERRAMIENTAS Y AUDITORÍA DE TRAZA
--------------------------------------------------------------
Objetivos de aprendizaje:
  1. Definición formal de herramientas con @tool y docstrings semánticos.
  2. Construcción de un agente autónomo con create_tool_calling_agent.
  3. Ejecución del bucle ReAct con AgentExecutor.
  4. Inspección de la traza de decisión mediante intermediate_steps.
"""

import os
from dotenv import load_dotenv, find_dotenv

from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI

try:
    from langchain.agents import AgentExecutor, create_tool_calling_agent
except ImportError:
    # Soporte para versiones modernas de LangChain (>=1.0.0 / langchain-classic)
    from langchain_classic.agents import AgentExecutor, create_tool_calling_agent

# Cargar variables de entorno buscando recursivamente el archivo .env
load_dotenv(find_dotenv())


# ============================================================================
# PASO 1: DEFINICIÓN DE HERRAMIENTAS CON EL DECORADOR @tool
# ============================================================================

@tool
def consultar_stock_producto(nombre_producto: str) -> str:
    """
    IMPORTANCIA CRÍTICA DEL DOCSTRING:
    El modelo LLM lee esta descripción para decidir si invoca la herramienta.
    Debe describir con precisión qué hace la función, qué argumento recibe
    y qué información retorna.
    
    Consulta el inventario y precio de catálogo para un producto dado.
    """
    inventario = {
        "laptop": "5 unidades en bodega | Precio: $800 USD",
        "teclado": "20 unidades en bodega | Precio: $50 USD",
        "monitor": "0 unidades (Agotado) | Precio: $250 USD"
    }
    clave = nombre_producto.strip().lower()
    return inventario.get(clave, f"El producto '{nombre_producto}' no existe en el catálogo.")


@tool
def calcular_descuento_promocional(precio: float, porcentaje: float) -> str:
    """
    Calcula el precio final tras aplicar un porcentaje de descuento a un monto base.
    Argumentos:
      precio: El precio original en número flotante.
      porcentaje: El descuento entre 0 y 100.
    """
    descuento = precio * (porcentaje / 100)
    total = precio - descuento
    return f"Precio base: ${precio:.2f} | Descuento: {porcentaje}% | Precio final: ${total:.2f} USD"


herramientas_agente = [consultar_stock_producto, calcular_descuento_promocional]


# ============================================================================
# PASO 2: CONSTRUCCIÓN DEL PROMPT CON AGENT_SCRATCHPAD
# ============================================================================

def construir_prompt_agente():
    """
    El prompt de un agente requiere obligatoriamente:
      1. Instrucciones de sistema (rol y directrices).
      2. Variable de entrada del usuario ({input}).
      3. MessagesPlaceholder('agent_scratchpad'): Es el 'borrador mental'
         donde LangChain inyecta las llamadas a tools y las observaciones
         intermedias antes de que el modelo decida la respuesta final.
    """
    return ChatPromptTemplate.from_messages([
        (
            "system",
            "Eres un asistente de ventas técnico y riguroso. "
            "Usa siempre tus herramientas para consultar inventario o calcular precios. "
            "Si la consulta no requiere herramientas, responde cortésmente de forma directa."
        ),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),
    ])


# ============================================================================
# PASO 3: ENSAMBLAJE DEL AGENTE Y EJECUTOR
# ============================================================================

def construir_ejecutor_agente(modelo, herramientas):
    """
    create_tool_calling_agent enlaza el LLM con las definiciones JSON Schema
    de las tools. Luego, AgentExecutor gestiona el ciclo iterativo de pensamiento,
    ejecución de herramientas y respuesta final.
    """
    prompt = construir_prompt_agente()
    agente = create_tool_calling_agent(modelo, herramientas, prompt)
    
    return AgentExecutor(
        agent=agente,
        tools=herramientas,
        verbose=True,
        return_intermediate_steps=True
    )


def formatear_respuesta(salida):
    """Extrae el contenido de texto en caso de que el LLM retorne bloques estructurados."""
    if isinstance(salida, list):
        return "".join(b.get("text", "") if isinstance(b, dict) else str(b) for b in salida)
    return str(salida)


if __name__ == "__main__":
    modelo_nombre = os.getenv("AI_MODEL") or "gemini-3.5-flash"
    llm = ChatGoogleGenerativeAI(model=modelo_nombre, temperature=0.1)
    ejecutor = construir_ejecutor_agente(llm, herramientas_agente)

    print("\n--- CONSULTA QUE REQUIERE HERRAMIENTA ---")
    consulta = "¿Tienes stock de teclado y cuánto cuesta?"
    respuesta = ejecutor.invoke({"input": consulta})

    texto_final = formatear_respuesta(respuesta["output"])
    print("\nRespuesta del Agente:\n", texto_final)

    pasos = respuesta.get("intermediate_steps", [])
    if pasos:
        accion_ejecutada, observacion = pasos[0]
        print(f"\n[AUDITORÍA DE TRAZA]:")
        print(f" -> Herramienta elegida: {accion_ejecutada.tool}")
        print(f" -> Argumentos enviados: {accion_ejecutada.tool_input}")
        print(f" -> Resultado obtenido : {observacion}")
