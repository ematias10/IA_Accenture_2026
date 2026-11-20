"""
BLOQUE 28: LATENCIA Y COSTO DEL FLUJO RAG COMPLETO (CIERRE U2.5)
----------------------------------------------------------------
Objetivos de aprendizaje:
  1. Desglosar la latencia de una consulta RAG etapa por etapa:
     - embed_y_busqueda: Generación de embeddings de la consulta y búsqueda en Chroma.
     - generacion: Llamada al modelo generativo (LLM) con el contexto inyectado.
  2. Implementar un context manager 'medir()' con time.perf_counter().
  3. Contabilizar tokens reales (prompt vs output) y calcular el costo exacto en USD.
  4. Demostrar la paradoja de los tokens: inyectar contexto infla los tokens de entrada,
     pero el costo de salida sigue dominando la factura.
  5. Registrar cada interacción en 'registros_latencia_costo.jsonl' (UTF-8).
"""

import os
import json
import time
from datetime import datetime
from contextlib import contextmanager
from typing import Dict, Any, Tuple, Optional
from dotenv import load_dotenv

# Importaciones de LangChain con soporte defensivo
try:
    from langchain_core.documents import Document
    from langchain_core.prompts import PromptTemplate
    from langchain_core.output_parsers import StrOutputParser
    from langchain_community.vectorstores import Chroma
    from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
except ImportError:
    # Definición de respaldo para pruebas sin dependencias de red externas
    class Document:  # type: ignore
        def __init__(self, page_content: str = "", metadata: Optional[dict] = None):
            self.page_content = page_content
            self.metadata = metadata or {}
    Chroma = Any  # type: ignore
    ChatGoogleGenerativeAI = Any  # type: ignore

load_dotenv()

# ============================================================================
# TARIFARIO OFICIAL DE REFERENCIA (Ejemplo: Gemini 1.5 Flash por 1M de tokens)
# ============================================================================
PRECIO_POR_MILLON_INPUT_USD = 0.075    # $0.075 USD por cada 1,000,000 tokens de entrada
PRECIO_POR_MILLON_OUTPUT_USD = 0.300   # $0.300 USD por cada 1,000,000 tokens de salida


# ============================================================================
# 1. INSTRUMENTACIÓN CON CONTEXT MANAGER (time.perf_counter)
# ============================================================================

@contextmanager
def medir(etapa: str, metricas_tiempo: Dict[str, float]):
    """
    Context manager de alta resolución para medir la latencia de una etapa en milisegundos.
    
    Uso:
      tiempos = {}
      with medir("generacion", tiempos):
          llm.invoke(...)
      # tiempos["generacion"] tendrá los milisegundos transcurridos
    """
    inicio = time.perf_counter()
    try:
        yield
    finally:
        fin = time.perf_counter()
        duracion_ms = round((fin - inicio) * 1000, 2)
        metricas_tiempo[etapa] = duracion_ms


# ============================================================================
# 2. CÁLCULO DE COSTO BASADO EN TOKENS REALES
# ============================================================================

def calcular_costo_usd(input_tokens: int, output_tokens: int) -> float:
    """
    Calcula el costo total de la llamada a la API en dólares estadounidenses (USD).
    """
    costo_input = (input_tokens / 1_000_000) * PRECIO_POR_MILLON_INPUT_USD
    costo_output = (output_tokens / 1_000_000) * PRECIO_POR_MILLON_OUTPUT_USD
    return round(costo_input + costo_output, 7)


# ============================================================================
# 3. REGISTRADOR DE TRAZAS EN FORMATO JSON LINES (JSONL)
# ============================================================================

def registrar_evento_jsonl(evento: Dict[str, Any], archivo: str = "registros_latencia_costo.jsonl"):
    """
    Escribe un evento estructurado en un archivo JSON Lines (UTF-8).
    Garantiza persistencia auditable para monitoreo en producción.
    """
    with open(archivo, "a", encoding="utf-8") as f:
        f.write(json.dumps(evento, ensure_ascii=False) + "\n")


# ============================================================================
# 4. PIPELINE RAG INSTRUMENTADO ETAPA POR ETAPA
# ============================================================================

PLANTILLA_RAG = (
    "Responde la pregunta basándote estrictamente en el siguiente contexto.\n"
    "Cita la fuente usando [1], [2], etc. Si el contexto no es suficiente, dilo.\n\n"
    "Contexto:\n{contexto}\n\n"
    "Pregunta: {pregunta}\n\n"
    "Respuesta fundamentada:"
)

def ejecutar_flujo_rag_instrumentado(
    pregunta: str,
    vectorstore: Any,
    llm: Any,
    k: int = 3,
    archivo_logs: str = "registros_latencia_costo.jsonl"
) -> Dict[str, Any]:
    """
    Ejecuta el ciclo RAG completo midiendo por separado cada etapa de procesamiento:
      1. embed_y_busqueda (incluye embedding de la consulta y recuperación en Chroma).
      2. formateo_contexto.
      3. generacion (llamada al LLM y generación token a token).
    """
    tiempos: Dict[str, float] = {}
    inicio_total = time.perf_counter()

    # --- ETAPA 1 Y 2: Embedding de la consulta y búsqueda vectorial ---
    with medir("embed_y_busqueda", tiempos):
        retriever = vectorstore.as_retriever(search_kwargs={"k": k})
        docs_recuperados = retriever.invoke(pregunta)

    # Formateo de fragmentos numerados
    lineas_contexto = []
    for i, doc in enumerate(docs_recuperados, start=1):
        fuente = doc.metadata.get("fuente", "sin_fuente")
        lineas_contexto.append(f"[{i}] ({fuente}): {doc.page_content.strip()}")
    contexto_str = "\n\n".join(lineas_contexto)

    prompt = PLANTILLA_RAG.format(contexto=contexto_str, pregunta=pregunta)

    # --- ETAPA 3: Inferencia del Modelo Generativo ---
    with medir("generacion", tiempos):
        respuesta_msg = llm.invoke(prompt)
        contenido_respuesta = (
            respuesta_msg.content if hasattr(respuesta_msg, "content") else str(respuesta_msg)
        )

    fin_total = time.perf_counter()
    tiempos["tiempo_total_ms"] = round((fin_total - inicio_total) * 1000, 2)

    # Extracción de tokens reales desde usage_metadata del mensaje devuelto
    usage = getattr(respuesta_msg, "usage_metadata", None) or {}
    input_tokens = usage.get("input_tokens", len(prompt.split()) * 2)
    output_tokens = usage.get("output_tokens", len(contenido_respuesta.split()) * 2)
    total_tokens = input_tokens + output_tokens

    costo_usd = calcular_costo_usd(input_tokens, output_tokens)

    # Estructura del evento completo
    evento = {
        "timestamp": datetime.now().isoformat(),
        "pregunta": pregunta,
        "k": k,
        "tiempos_ms": {
            "embed_y_busqueda": tiempos.get("embed_y_busqueda", 0.0),
            "generacion": tiempos.get("generacion", 0.0)
        },
        "tiempo_total_ms": tiempos["tiempo_total_ms"],
        "tokens": {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens
        },
        "costo_usd": costo_usd,
        "respuesta": contenido_respuesta
    }

    # Registro en archivo JSONL para trazabilidad
    registrar_evento_jsonl(evento, archivo=archivo_logs)

    return evento


# ============================================================================
# DEMOSTRACIÓN EN CLASE (EJECUCIÓN REAL)
# ============================================================================

if __name__ == "__main__":
    carpeta_bd = "./Modulo_2/Bloque26/vectorstore"

    if not os.path.exists(carpeta_bd):
        print(f"Aviso: Directorio '{carpeta_bd}' no encontrado.")
        print("Ejecuta primero el script de indexación de los Bloques 24/25 o 26.")
    else:
        print("Iniciando conexión a Chroma y Gemini...")
        embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
        vectorstore = Chroma(
            persist_directory=carpeta_bd,
            embedding_function=embeddings
        )
        llm = ChatGoogleGenerativeAI(model="gemini-3.8-flash", temperature=0.1)

        consultas_demo = [
            "¿Qué hace el cliente si una llamada tarda demasiado tiempo y da error 429?",
            "¿Cuál es el plazo máximo para pedir devolución y qué documento se pide?",
            "¿A qué dirección de correo se notifica una caída de servidores?"
        ]

        print(f"\nEjecutando {len(consultas_demo)} consultas instrumentadas...\n")
        for q in consultas_demo:
            resultado = ejecutar_flujo_rag_instrumentado(
                pregunta=q,
                vectorstore=vectorstore,
                llm=llm,
                k=3,
                archivo_logs="registros_latencia_costo.jsonl"
            )
            print(f"Pregunta: '{q}'")
            print(f"  • Embed & Búsqueda: {resultado['tiempos_ms']['embed_y_busqueda']} ms")
            print(f"  • Generación LLM:  {resultado['tiempos_ms']['generacion']} ms")
            print(f"  • Tiempo Total:    {resultado['tiempo_total_ms']} ms")
            print(f"  • Tokens: In={resultado['tokens']['input_tokens']} | Out={resultado['tokens']['output_tokens']}")
            print(f"  • Costo: ${resultado['costo_usd']:.6f} USD")
            print("------------------------------------------------------------------")
