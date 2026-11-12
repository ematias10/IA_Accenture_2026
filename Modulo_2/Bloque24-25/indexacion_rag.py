"""
BLOQUES 24 Y 25: FUNDAMENTOS DE RAG, CHUNKING Y PERSISTENCIA EN CHROMA
----------------------------------------------------------------------
Objetivos de aprendizaje:
  1. Comprensión del flujo RAG (Retrieval-Augmented Generation).
  2. Preparación de documentos estructurados con Document(page_content, metadata).
  3. Estrategia de segmentación con RecursiveCharacterTextSplitter (chunk_size y chunk_overlap).
  4. Generación de representaciones vectoriales con GoogleGenerativeAIEmbeddings.
  5. Ingesta, persistencia en disco y recuperación por similitud con Chroma.
"""

import os
import shutil
from dotenv import load_dotenv, find_dotenv

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma

load_dotenv(find_dotenv())



# ============================================================================
# PASO 1: PREPARACIÓN DEL CORPUS CON METADATOS ENRIQUECIDOS (Bloque 24)
# ============================================================================

def cargar_corpus_soporte() -> list[Document]:
    """
    Crea una colección mínima representativa de documentos de soporte (Bloque 24).
    Cada Document posee:
      - page_content: El contenido textual que será vectorizado.
      - metadata: Diccionario con origen, autor, fecha o categoría para trazabilidad.
    """
    return [
        Document(
            page_content=(
                "Política de Reembolsos y Devoluciones:\n"
                "Los clientes tienen derecho a solicitar la devolución total de su dinero "
                "dentro de los primeros 30 días posteriores a la compra. Es obligatorio "
                "presentar el número de pedido y la boleta o factura de compra válida."
            ),
            metadata={"fuente": "politicas_empresa.md", "seccion": "reembolsos", "id_doc": 1}
        ),
        Document(
            page_content=(
                "Tiempos y Zonas de Despacho:\n"
                "Para compras realizadas en la Región Metropolitana, el plazo de entrega "
                "es de 24 a 48 horas hábiles. En regiones extremas y zonas rurales, el plazo "
                "se extiende entre 3 y 5 días hábiles a través del operador logístico oficial."
            ),
            metadata={"fuente": "logistica_despachos.md", "seccion": "tiempos", "id_doc": 2}
        ),
        Document(
            page_content=(
                "Resiliencia de la API y Límites de Tasa:\n"
                "Nuestros servicios externos de IA aplican rate limits (HTTP 429). "
                "El cliente modular de consumo implementa backoff exponencial con jitter aleatorio "
                "y hasta 3 reintentos antes de elevar una excepción no recuperable."
            ),
            metadata={"fuente": "manual_arquitectura_api.md", "seccion": "resiliencia", "id_doc": 3}
        ),
        Document(
            page_content=(
                "Garantía Legal de Productos Electrónicos:\n"
                "Todo hardware y accesorio cuenta con 12 meses de garantía legal ante defectos "
                "de fabricación. No cubre daños por mal uso, derrames de líquidos o golpes."
            ),
            metadata={"fuente": "garantias_hardware.md", "seccion": "garantias", "id_doc": 4}
        ),
        Document(
            page_content=(
                "Canales de Soporte y Contacto de Emergencia:\n"
                "En caso de incidentes críticos de infraestructura, contactar inmediatamente "
                "a la mesa de guardia técnica vía correo a soporte-urgente@empresa.com o al anexo 9999."
            ),
            metadata={"fuente": "contacto_soporte.md", "seccion": "urgencias", "id_doc": 5}
        ),
    ]


# ============================================================================
# PASO 2: CHUNKING DEFENSIVO CON RECURSIVECHARACTERTEXTSPLITTER
# ============================================================================

def segmentar_documentos(documentos: list[Document], chunk_size: int = 180, chunk_overlap: int = 30) -> list[Document]:
    """
    Divide los documentos en unidades manejables (chunks).
    
    DETALLE TÉCNICO CRÍTICO (Bloque 24 y 25):
      - chunk_size: Tamaño máximo del fragmento.
      - chunk_overlap: Caracteres compartidos entre fragmentos contiguos para no
        romper oraciones a la mitad ni perder contexto contextual en las fronteras.
      - separators: Intenta cortar primero por saltos de párrafo ("\n\n"), luego por
        líneas ("\n"), luego por espacios (" ") antes de cortar palabras arbitrariamente.
    """
    divisor = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", " ", ""]
    )
    
    chunks = divisor.split_documents(documentos)
    
    # Verificación de integridad local (Bloque 25: Troubleshooting)
    assert len(chunks) > 0, "Error crítico: El proceso de chunking arrojó 0 fragmentos."
    for i, chk in enumerate(chunks):
        if not chk.page_content.strip():
            raise ValueError(f"El chunk #{i} se encuentra completamente vacío.")
            
    return chunks


# ============================================================================
# PASO 3 Y 4: EMBEDDINGS E INGESTA EN VECTOR STORE (CHROMA)
# ============================================================================

def construir_o_cargar_vectorstore(chunks: list[Document] = None, ruta_persistencia: str = "./Modulo_2/Bloque24-25/vectorstore") -> Chroma:
    """
    PASO 4 Y 5 DE LA RECETA DE INDEXACIÓN:
      - Inicializa GoogleGenerativeAIEmbeddings con gemini-embedding-001.
      - Si se proporcionan chunks nuevos, indexa y persiste en disco.
      - Si no se proporcionan chunks, carga la base existente desde disco.
    """
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001"
    )
    
    if chunks:
        print(f"-> Indexando {len(chunks)} fragmentos en '{ruta_persistencia}'...")
        vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=ruta_persistencia
        )
        return vectorstore
    else:
        print(f"-> Cargando vector store existente desde '{ruta_persistencia}'...")
        return Chroma(
            persist_directory=ruta_persistencia,
            embedding_function=embeddings
        )

# ============================================================================
# PASO 5: RECUPERACIÓN SEMÁNTICA POR SIMILITUD (RETRIEVAL)
# ============================================================================

def consultar_base_vectorial(vectorstore: Chroma, pregunta: str, k: int = 2):
    """
    Realiza una búsqueda de vecinos más cercanos en el espacio vectorial.
    Recupera los 'k' fragmentos con mayor similitud semántica.
    """
    retriever = vectorstore.as_retriever(search_kwargs={"k": k})
    documentos_recuperados = retriever.invoke(pregunta)
    return documentos_recuperados


# ============================================================================
# DEMOSTRACIÓN EN CLASE (EJECUCIÓN DEL FLUJO COMPLETO)
# ============================================================================

if __name__ == "__main__":
    carpeta_bd = "./Modulo_2/Bloque24-25/vectorstore"
    
    # 1. Limpieza preventiva para no duplicar datos si se re-ejecuta
    if os.path.exists(carpeta_bd):
        shutil.rmtree(carpeta_bd)

    # 2. Cargar documentos
    print("1. Cargando corpus documental...")
    docs_originales = cargar_corpus_soporte()
    print(f"   Documentos base cargados: {len(docs_originales)}")

    # 3. Segmentar con solape (Chunking)
    print("\n2. Segmentando documentos en chunks...")
    chunks_generados = segmentar_documentos(docs_originales, chunk_size=180, chunk_overlap=30)
    print(f"   Chunks generados: {len(chunks_generados)}")
    print(f"   Muestra del Chunk #0:\n   '''{chunks_generados[0].page_content}'''")
    print(f"   Metadatos asociados: {chunks_generados[0].metadata}")

    # 4. Ingesta y persistencia
    print("\n3. Calculando embeddings y persistiendo en Chroma...")
    db = construir_o_cargar_vectorstore(chunks=chunks_generados, ruta_persistencia=carpeta_bd)
    total_vectores = db._collection.count()
    print(f"   ✓ Verificación de almacenamiento: {total_vectores} vectores persistidos con éxito.")

    # 5. Demostración de recuperación semántica
    print("\n4. Ejecutando búsqueda semántica...")
    consulta_usuario = "¿Cómo maneja el sistema cuando la API da error 429 de demasiadas peticiones?"
    print(f"   Consulta formulada: '{consulta_usuario}'")
    
    resultados = consultar_base_vectorial(db, consulta_usuario, k=1)
    
    print("\n--- FRAGMENTO MÁS RELEVANTE RECUPERADO ---")
    for doc in resultados:
        print(f"Fuente: {doc.metadata.get('fuente')} (Sección: {doc.metadata.get('seccion')})")
        print(f"Texto:\n{doc.page_content}\n")
