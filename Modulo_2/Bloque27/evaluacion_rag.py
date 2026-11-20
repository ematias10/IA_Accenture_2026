"""
BLOQUE 27: EVALUACIÓN DE LA RECUPERACIÓN RAG (PRECISIÓN Y RECALL)
-----------------------------------------------------------------
Objetivos de aprendizaje:
  1. Superar la evaluación 'a simple vista' mediante métricas formales de Recuperación de Información.
  2. Implementar funciones matemáticas determinísticas para Precision@k y Recall@k.
  3. Estructurar un conjunto de prueba etiquetado a mano (Ground Truth) con identificadores únicos.
  4. Ejecutar la evaluación comparativa variando k (trade-off entre cobertura y ruido).
"""

import os
from typing import List, Set, Dict, Tuple
from dotenv import load_dotenv

from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings

load_dotenv()


# ============================================================================
# PASO 1: FUNCIONES MATEMÁTICAS FORMALES DE EVALUACIÓN
# ============================================================================

def calcular_precision_at_k(recuperados_ids: List[str], relevantes_ids: Set[str], k: int) -> float:
    """
    Calcula la Precisión en los primeros k resultados (Precision@k).
    
    Fórmula:
      Precision@k = |Recuperados_k ∩ Relevantes| / k
      
    Interpretación pedagógica:
      De los k fragmentos que el retriever devolvió en la red, ¿cuántos eran
      verdaderamente útiles y cuántos eran 'basura o ruido'?
    """
    if k <= 0:
        return 0.0
    
    # Tomamos solo la ventana de los primeros k recuperados
    recuperados_k = set(recuperados_ids[:k])
    coincidencias = len(recuperados_k.intersection(relevantes_ids))
    return coincidencias / k


def calcular_recall_at_k(recuperados_ids: List[str], relevantes_ids: Set[str], k: int) -> float:
    """
    Calcula la Exhaustividad o Cobertura en los primeros k resultados (Recall@k).
    
    Fórmula:
      Recall@k = |Recuperados_k ∩ Relevantes| / |Relevantes|
      
    Interpretación pedagógica:
      De todos los fragmentos clave que existían en el corpus para responder la duda,
      ¿qué porcentaje logró atrapar el retriever? (Si Recall es 0, el modelo alucina).
    """
    if not relevantes_ids:
        return 0.0
    
    recuperados_k = set(recuperados_ids[:k])
    coincidencias = len(recuperados_k.intersection(relevantes_ids))
    return coincidencias / len(relevantes_ids)


# ============================================================================
# PASO 2: CONJUNTO DE EVALUACIÓN ETIQUETADO (GROUND TRUTH)
# ============================================================================

def obtener_conjunto_evaluacion() -> List[Dict]:
    """
    Devuelve un banco de preguntas representativas vinculadas a los IDs únicos
    de los documentos relevantes que contienen la verdad factual.
    
    REGLA DE ORO DEL BLOQUE 27:
      Nunca evaluar comparando texto contra texto. Se evalúa comparando IDs
      únicos ('id_doc') para garantizar pruebas 100% determinísticas.
    """
    return [
        {
            "pregunta": "¿Cuál es el plazo máximo para solicitar la devolución del dinero y qué se exige?",
            "ids_relevantes": {"doc1"}
        },
        {
            "pregunta": "¿Cuáles son los tiempos de entrega en la Región Metropolitana y en zonas rurales?",
            "ids_relevantes": {"doc2"}
        },
        {
            "pregunta": "¿Cómo mitiga el cliente API los errores de tasa HTTP 429 y cuántos reintentos hace?",
            "ids_relevantes": {"doc3"}
        },
        {
            "pregunta": "¿Qué cobertura ofrece la garantía legal y ante qué situaciones no aplica?",
            "ids_relevantes": {"doc4"}
        },
        {
            "pregunta": "¿A qué correo o teléfono debe notificarse un incidente crítico de servidores?",
            "ids_relevantes": {"doc5"}
        }
    ]


# ============================================================================
# PASO 3: MOTOR DE EVALUACIÓN AUTOMATIZADO
# ============================================================================

def evaluar_recuperacion(retriever, casos: List[Dict], k: int) -> Tuple[float, float, List[Dict]]:
    """
    Ejecuta cada pregunta del conjunto de prueba contra el retriever, extrae
    los metadatos de los chunks devueltos y calcula las métricas individuales y globales.
    """
    reporte_detallado = []
    suma_precision = 0.0
    suma_recall = 0.0

    print(f"\n=======================================================")
    print(f" INICIANDO EVALUACIÓN DE RECUPERACIÓN CON k = {k}")
    print(f"=======================================================")

    for idx, caso in enumerate(casos, start=1):
        pregunta = caso["pregunta"]
        esperados = caso["ids_relevantes"]

        # 1. Invocación al retriever de LangChain
        docs_obtenidos = retriever.invoke(pregunta)

        # 2. Extracción de IDs normalizados desde metadata
        ids_recuperados = [
            str(doc.metadata.get("id_doc", "sin_id")).strip()
            for doc in docs_obtenidos[:k]
        ]

        # 3. Cálculo de métricas para este caso puntual
        p_at_k = calcular_precision_at_k(ids_recuperados, esperados, k)
        r_at_k = calcular_recall_at_k(ids_recuperados, esperados, k)

        suma_precision += p_at_k
        suma_recall += r_at_k

        registro = {
            "caso_id": idx,
            "pregunta": pregunta,
            "esperados": list(esperados),
            "recuperados": ids_recuperados,
            "precision": p_at_k,
            "recall": r_at_k
        }
        reporte_detallado.append(registro)

        print(f"[{idx}] P@{k}: {p_at_k:.2f} | R@{k}: {r_at_k:.2f} | Pregunta: '{pregunta[:50]}...'")
        print(f"    -> Esperados: {esperados} | Recuperados: {ids_recuperados}")

    promedio_precision = suma_precision / len(casos) if casos else 0.0
    promedio_recall = suma_recall / len(casos) if casos else 0.0

    print(f"-------------------------------------------------------")
    print(f" RESULTADOS GLOBALES (k={k}):")
    print(f"   • Precision@{k} Promedio: {promedio_precision:.3f}")
    print(f"   • Recall@{k}    Promedio: {promedio_recall:.3f}")
    print(f"=======================================================\n")

    return promedio_precision, promedio_recall, reporte_detallado


# ============================================================================
# DEMOSTRACIÓN DE TRADE-OFF EN CLASE (k=2 vs k=4)
# ============================================================================

if __name__ == "__main__":
    carpeta_vectorstore = "./Modulo_2/Bloque26/vectorstore"

    if not os.path.exists(carpeta_vectorstore):
        print(f"Aviso: No se encontró la carpeta '{carpeta_vectorstore}'.")
        print("Asegúrate de haber corrido previamente el script del Bloque 24/25 o 26.")
    else:
        embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
        vectorstore = Chroma(
            persist_directory=carpeta_vectorstore,
            embedding_function=embeddings
        )

        casos = obtener_conjunto_evaluacion()

        # Evaluación con k=2
        retriever_k2 = vectorstore.as_retriever(search_kwargs={"k": 2})
        p2, r2, _ = evaluar_recuperacion(retriever_k2, casos, k=2)

        # Evaluación con k=4
        retriever_k4 = vectorstore.as_retriever(search_kwargs={"k": 4})
        p4, r4, _ = evaluar_recuperacion(retriever_k4, casos, k=4)

        # Análisis pedagógico del trade-off
        print("\n--- RESUMEN DEL TRADE-OFF (k=2 vs k=4) ---")
        print(f"k=2 -> Precision: {p2:.3f} | Recall: {r2:.3f}")
        print(f"k=4 -> Precision: {p4:.3f} | Recall: {r4:.3f}")
        if r4 >= r2 and p4 <= p2:
            print("✓ Comportamiento esperado: Subir k aumentó/mantuvo el Recall pero redujo la Precisión (más ruido).")
