"""
BLOQUE 23: LÍMITES DE AUTONOMÍA, SUPERVISIÓN HUMANA Y TRAZABILIDAD
-----------------------------------------------------------------
Objetivos de aprendizaje:
  1. Clasificación de herramientas por nivel de riesgo (Bajo vs Alto).
  2. Implementación del patrón Human-in-the-Loop (Supervisión Humana).
  3. Esquemas estrictos de entrada en tools con Pydantic.
  4. Registro y auditoría de trazas de decisión en trazas_agente.jsonl.
"""

import os
import json
from datetime import datetime
from dotenv import load_dotenv

from pydantic import BaseModel, Field
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, create_tool_calling_agent

load_dotenv()

# ============================================================================
# PASO 1: ESTRUCTURA DE REGISTRO DE AUDITORÍA Y REGISTRO DE TRAZAS
# ============================================================================

# Memoria de auditoría de aprobaciones humanas en tiempo de ejecución
registro_aprobaciones = []

def registrar_aprobacion(herramienta: str, argumentos: dict, aprobado: bool):
    """Guarda en memoria la decisión del supervisor humano."""
    registro_aprobaciones.append({
        "herramienta": herramienta,
        "argumentos": argumentos,
        "aprobado": aprobado,
        "momento": datetime.now().isoformat()
    })

def esperar_aprobacion(mensaje_solicitud: str) -> bool:
    """
    Intercepción para supervisión humana (Human-in-the-Loop).
    Pausa la ejecución para solicitar confirmación explícita en consola.
    """
    print(f"\n⚠️  [ALERTA DE SEGURIDAD - ACCIÓN DE ALTO RIESGO]")
    print(f"    Solicitud: {mensaje_solicitud}")
    confirmacion = input("    ¿Autoriza la ejecución de esta operación irreversible? (s/n): ")
    return confirmacion.strip().lower() == 's'

def registrar_traza_jsonl(entrada: str, pasos_intermedios: list, respuesta_final: str, archivo="trazas_agente.jsonl"):
    """
    Guarda la traza completa del turno en formato JSON Lines (UTF-8).
    Permite auditar el razonamiento, las herramientas elegidas y las observaciones.
    """
    acciones_registradas = []
    for accion, observacion in pasos_intermedios:
        acciones_registradas.append({
            "herramienta": accion.tool,
            "argumentos": accion.tool_input,
            "observacion": observacion
        })
    
    registro = {
        "timestamp": datetime.now().isoformat(),
        "entrada": entrada,
        "acciones": acciones_registradas,
        "respuesta_final": respuesta_final
    }
    
    with open(archivo, "a", encoding="utf-8") as f:
        f.write(json.dumps(registro, ensure_ascii=False) + "\n")


# ============================================================================
# PASO 2: DEFINICIÓN DE HERRAMIENTAS CLASIFICADAS POR RIESGO
# ============================================================================

# --- HERRAMIENTA 1: BAJO RIESGO (Solo lectura, autonomía total) ---
@tool
def consultar_estado_pedido(numero_pedido: str) -> str:
    """
    [RIESGO BAJO] Consulta el estado de despacho de un pedido en la base de datos.
    No realiza modificaciones ni transacciones. Autonomía completa del agente.
    """
    # Base de datos simulada
    pedidos = {
        "P-100": "El pedido P-100 está en preparación en bodega centro.",
        "P-200": "El pedido P-200 fue entregado con éxito ayer a las 15:30.",
        "P-9988": "El pedido P-9988 se encuentra retenido en aduana."
    }
    clave = numero_pedido.strip().upper()
    return pedidos.get(clave, f"El pedido '{numero_pedido}' no se encuentra en el sistema.")


# --- HERRAMIENTA 2: ALTO RIESGO (Escritura irreversible / Devolución de Dinero) ---
class EsquemaReembolso(BaseModel):
    """Esquema de validación estricta con Pydantic para la herramienta de reembolso."""
    numero_pedido: str = Field(description="Código alfanumérico del pedido a reembolsar (ej. P-9988).")
    monto: float = Field(description="Monto exacto en USD a devolver al cliente.")
    motivo: str = Field(description="Justificación detallada de la devolución.")


@tool(args_schema=EsquemaReembolso)
def generar_reembolso(numero_pedido: str, monto: float, motivo: str) -> str:
    """
    [RIESGO ALTO] Procesa una devolución de dinero a la tarjeta del cliente.
    REQUIERE APROBACIÓN HUMANA PREVIA OBLIGATORIA (Human-in-the-Loop).
    """
    solicitud = f"Reembolsar ${monto:.2f} USD para el pedido {numero_pedido} (Motivo: {motivo})"
    
    # Intercepción de supervisión humana
    aprobado = esperar_aprobacion(solicitud)
    
    # Registro de auditoría
    registrar_aprobacion("generar_reembolso", {"pedido": numero_pedido, "monto": monto, "motivo": motivo}, aprobado)
    
    if aprobado:
        return f"ÉXITO: Reembolso de ${monto:.2f} USD emitido correctamente para el pedido {numero_pedido}."
    else:
        return f"RECHAZADO: El supervisor denegó el reembolso de ${monto:.2f} USD para el pedido {numero_pedido}."


# ============================================================================
# PASO 3: CONSTRUCCIÓN Y ENSAMBLAJE DEL AGENTE
# ============================================================================

def construir_agente_con_gobernanza(modelo, herramientas):
    """Ensambla el agente asociando el prompt con agent_scratchpad y el ejecutor auditado."""
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "Eres un agente de soporte al cliente con gobernanza de seguridad. "
            "Para consultas informativas, usa herramientas directas. "
            "Para solicitudes de dinero o reembolso, usa las herramientas correspondientes "
            "respetando los protocolos de confirmación."
        ),
        ("human", "{entrada}"),
        MessagesPlaceholder("agent_scratchpad")
    ])

    agente = create_tool_calling_agent(modelo, herramientas, prompt)
    
    return AgentExecutor(
        agent=agente,
        tools=herramientas,
        verbose=True,
        return_intermediate_steps=True  # Indispensable para auditar trazas
    )


# ============================================================================
# DEMOSTRACIÓN EN CLASE
# ============================================================================

if __name__ == "__main__":
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.1)
    herramientas_agente = [consultar_estado_pedido, generar_reembolso]
    ejecutor = construir_agente_con_gobernanza(llm, herramientas_agente)

    print("\n--- CASO 1: Consulta de bajo riesgo ---")
    res1 = ejecutor.invoke({"entrada": "¿En qué estado se encuentra mi pedido P-100?"})
    registrar_traza_jsonl(res1["input"], res1.get("intermediate_steps", []), res1["output"])
    print("Respuesta:", res1["output"])

    print("\n--- CASO 2: Operación de alto riesgo (Supervisada) ---")
    res2 = ejecutor.invoke({
        "entrada": "Solicito reembolso de $150 USD por mi pedido P-9988 que venía roto."
    })
    registrar_traza_jsonl(res2["input"], res2.get("intermediate_steps", []), res2["output"])
    print("Respuesta final:", res2["output"])
