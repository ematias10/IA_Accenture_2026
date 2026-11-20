"""
BLOQUE 26: RECUPERACIÓN SEMÁNTICA Y PROMPT DINÁMICO CON FUENTE CITADA
---------------------------------------------------------------------
Objetivos de aprendizaje:
  1. Conexión limpia a Chroma persistido en disco (sin reindexar).
  2. Implementación de 'formatear_contexto' con numeración correlativa ([1], [2]).
  3. Mapeo estricto de metadatos de fuente y sección en un diccionario de citas.
  4. Diseño de prompt dinámico defensivo con reglas de citación y abstención explícita.
  5. Ejecución del flujo RAG con LangChain (LCEL) y trazabilidad verificable.
"""

import os
from dotenv import load_dotenv

from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import Chroma

import os
import shutil
from dotenv import load_dotenv, find_dotenv

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma

load_dotenv(find_dotenv())


# ============================================================================
# PASO 1: PLANTILLA DE PROMPT DINÁMICO DEFENSIVO
# ============================================================================

PLANTILLA_RAG_DEFENSIVA = """Responde la siguiente pregunta utilizando ÚNICAMENTE la información provista en el contexto.

Reglas obligatorias:
1. Cita la fuente de cada afirmación usando su número entre corchetes, por ejemplo [1] o [2].
2. Si el contexto provisto no contiene la información suficiente para responder con certeza, declara explícitamente:
   "El contexto disponible no contiene suficiente información para responder a esta consulta."
3. No intentes inventar, asumir ni extrapolar datos fuera de los textos provistos.

Contexto provisto:
{contexto}

Pregunta: {pregunta}

Respuesta fundamentada:"""

PROMPT_RAG = PromptTemplate(
    template=PLANTILLA_RAG_DEFENSIVA,
    input_variables=["contexto", "pregunta"]
)


# ============================================================================
# PASO 2: FORMATEO DE CONTEXTO NUMERADO Y DICCIONARIO DE CITAS
# ============================================================================

def formatear_contexto(chunks_recuperados: list[Document]) -> tuple[str, dict[int, str]]:
    """
    Toma los documentos devueltos por el retriever de Chroma y produce:
      1. Un string con bloques numerados correlativamente: [1] ..., [2] ...
      2. Un diccionario que asocia cada índice [i] con la metadata del archivo original.

    Esto garantiza que el modelo use citas verificables y que el sistema pueda
    auditar de qué archivo exacto provino cada respuesta.
    """
    lineas = []
    citas = {}

    for i, doc in enumerate(chunks_recuperados, start=1):
        fuente = doc.metadata.get("fuente", "fuente_desconocida")
        seccion = doc.metadata.get("seccion", "general")

        lineas.append(f"[{i}] {doc.page_content.strip()}")
        citas[i] = f"{fuente} (sección: {seccion})"

    contexto_formateado = "\n\n".join(lineas)
    return contexto_formateado, citas


# ============================================================================
# PASO 3: CONEXIÓN AL VECTOR STORE (SIN REINDEXAR)
# ============================================================================

def cargar_vectorstore_existente(ruta_persistencia: str = "vectorstore_demo") -> Chroma:
    """
    Conecta al índice local persistido en disco.
    REGLA DE ORO DEL BLOQUE 26:
      Nunca llamar a Chroma.from_documents() aquí; eso recalcularía embeddings
      innecesarios, aumentando la latencia y consumiendo cuota de API.
    """
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    return Chroma(
        persist_directory=ruta_persistencia,
        embedding_function=embeddings
    )


# ============================================================================
# PASO 4: FUNCIÓN DE RECUPERACIÓN Y GENERACIÓN FUNDAMENTADA
# ============================================================================

def responder_consulta_rag(
    pregunta: str,
    vectorstore: Chroma,
    llm: ChatGoogleGenerativeAI,
    k: int = 2
) -> dict:
    """
    Ejecuta el flujo RAG completo:
      1. Recupera los k fragmentos más afines semánticamente.
      2. Formatea el contexto y construye el mapa de trazabilidad.
      3. Ejecuta la cadena con el prompt dinámico defensivo.
      4. Retorna la respuesta generada, el prompt exacto y el mapa de citas.
    """
    retriever = vectorstore.as_retriever(search_kwargs={"k": k})
    chunks_recuperados = retriever.invoke(pregunta)

    contexto, citas = formatear_contexto(chunks_recuperados)

    # Cadena LCEL para la generación
    cadena = PROMPT_RAG | llm | StrOutputParser()

    respuesta_texto = cadena.invoke({
        "contexto": contexto,
        "pregunta": pregunta
    })

    return {
        "pregunta": pregunta,
        "contexto_formateado": contexto,
        "citas": citas,
        "chunks_recuperados": chunks_recuperados,
        "respuesta": respuesta_texto
    }


# ============================================================================
# DEMOSTRACIÓN EN VIVO
# ============================================================================

if __name__ == "__main__":
    carpeta_bd = "./Modulo_2/Bloque26/vectorstore"

    # Verificar que el índice del Bloque 24/25 exista
    if not os.path.exists(carpeta_bd):
        print(f"Aviso: La carpeta '{carpeta_bd}' no existe. Creando un vectorstore temporal para la demo...")
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        docs_ejemplo = [
            Document(
                page_content="Política de Reembolsos: Los clientes tienen derecho a solicitar reembolso dentro de los 30 días posteriores a la compra con comprobante válido.",
                metadata={"fuente": "politicas_reembolso.md", "seccion": "general"}
            ),
            Document(
                page_content="Resiliencia de API: El cliente ejecuta backoff exponencial ante respuestas HTTP 429 con un límite de hasta 3 reintentos antes de fallar.",
                metadata={"fuente": "manual_api.md", "seccion": "resiliencia"}
            )
        ]
        splitter = RecursiveCharacterTextSplitter(chunk_size=150, chunk_overlap=20)
        chunks = splitter.split_documents(docs_ejemplo)
        embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
        vectorstore = Chroma.from_documents(documents=chunks, embedding=embeddings, persist_directory=carpeta_bd)
    else:
        vectorstore = cargar_vectorstore_existente(carpeta_bd)

    modelo_llm = ChatGoogleGenerativeAI(model="gemini-3.8-flash", temperature=0.0)

    print("==================================================================")
    print("DEMOSTRACIÓN 1: Pregunta cubierta (con citación verificable)")
    print("==================================================================")
    q1 = "¿Cuántos reintentos realiza el sistema cuando se produce un error 429?"
    res1 = responder_consulta_rag(q1, vectorstore, modelo_llm, k=2)

    print(f"\nPregunta: {res1['pregunta']}")
    print("\nCitas asociadas:")
    for num, fuente in res1["citas"].items():
        print(f"  [{num}] -> {fuente}")
    print(f"\nRespuesta del LLM:\n{res1['respuesta']}")

    print("\n==================================================================")
    print("DEMOSTRACIÓN 2: Pregunta NO cubierta (Abstención controlada)")
    print("==================================================================")
    q2 = "¿Cuál es el menú del casino de la empresa los días viernes?"
    res2 = responder_consulta_rag(q2, vectorstore, modelo_llm, k=2)

    print(f"\nPregunta: {res2['pregunta']}")
    print(f"\nRespuesta del LLM:\n{res2['respuesta']}")
