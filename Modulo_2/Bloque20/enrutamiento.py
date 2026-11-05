"""
MÓDULO DE ENRUTAMIENTO Y RESILIENCIA ORQUESTADA (Bloques 19 y 20)
---------------------------------------------------------------
Objetivos centrales:
  1. Enrutamiento condicional con RunnableBranch según el contenido del mensaje.
  2. Preservación del payload original con RunnablePassthrough.assign().
  3. Resiliencia local por rama con with_fallbacks (Bloque 20).
  4. Red de seguridad global para capturar errores imprevistos (Bloque 20).
"""

import os
from dotenv import load_dotenv

# Componentes esenciales de LangChain Expression Language (LCEL)
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import (
    RunnableBranch,
    RunnablePassthrough,
    RunnableLambda
)
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

# ============================================================================
# 1. PASO DE CLASIFICACIÓN DEFENSIVO (ROUTER)
# ============================================================================

# Prompt de sistema conciso para forzar una única etiqueta de decisión
plantilla_clasificacion = PromptTemplate.from_template(
    "Clasifica el siguiente mensaje de soporte técnico en una sola palabra: "
    "pregunta, queja o sugerencia. Responde ÚNICAMENTE con esa palabra, sin puntuación ni texto adicional.\n\n"
    "{mensaje}"
)

def construir_paso_clasificacion(modelo):
    """
    Construye la cadena que determina la categoría de la entrada.
    
    DETALLE TÉCNICO CRÍTICO:
    El modelo puede devolver espacios en blanco, mayúsculas o saltos de línea 
    (ej: 'Queja\n' o ' queja.'). 
    Se encadena una función lambda normalizadora: .strip().lower()
    para garantizar que las comparaciones de igualdad posteriores no fallen en silencio.
    """
    return (
        plantilla_clasificacion
        | modelo
        | StrOutputParser()
        | (lambda texto: texto.strip().lower())
    )

# ============================================================================
# 2. DEFINICIÓN DE LAS RUTAS ESPECIALIZADAS Y SUS FALLBACKS
# ============================================================================

# Fallback: Respuesta de contingencia estructurada y estática.
# Se envuelve en RunnableLambda para que sea un componente ejecutable de LCEL.
# No realiza llamadas a la API, no consume tokens y no puede fallar por problemas de red.
respuesta_respaldo_queja = RunnableLambda(
    lambda x: (
        "Hemos recibido tu reporte de manera prioritaria. En este momento nuestros sistemas "
        "de procesamiento automático experimentan una alta demanda, pero tu reclamo ya quedó "
        "registrado en la cola de atención preferente de nuestro equipo técnico."
    )
)

def construir_cadena_queja_segura(cadena_queja_original):
    """
    DETALLE TÉCNICO (Bloque 20): Resiliencia Local por Paso.
    
    Si 'cadena_queja_original' arroja una excepción en tiempo de ejecución 
    (HTTP 429 Too Many Requests, timeout, caída del proveedor de IA o corte de red),
    el método .with_fallbacks([fallback]) intercepta el error automáticamente y deriva 
    la ejecución al plan de contingencia sin romper el flujo del usuario.
    """
    return cadena_queja_original.with_fallbacks([respuesta_respaldo_queja])

def construir_rutas_especializadas(modelo):
    """
    Crea las cadenas específicas para cada categoría.
    Cada ruta tiene su propio tono, objetivo y estructura adaptada a la intención.
    """
    parser = StrOutputParser()

    # Ruta 1: Pregunta técnica (precisa y explicativa)
    ruta_pregunta = (
        PromptTemplate.from_template("Responde con claridad técnica a la siguiente consulta:\n\n{mensaje}")
        | modelo
        | parser
    )

    # Ruta 2: Queja (tono empático y resolutivo)
    ruta_queja = (
        PromptTemplate.from_template("Responde a este reclamo con profunda empatía y ofrece una disculpa institucional:\n\n{mensaje}")
        | modelo
        | parser
    )

    # Ruta 3: Sugerencia (agradecimiento y canalización)
    ruta_sugerencia = (
        PromptTemplate.from_template("Agradece la siguiente sugerencia y explica cómo será evaluada:\n\n{mensaje}")
        | modelo
        | parser
    )

    # Aplicamos el blindaje local (Bloque 20) exclusivamente sobre la ruta de quejas
    ruta_queja_protegida = construir_cadena_queja_segura(ruta_queja)

    return ruta_pregunta, ruta_queja_protegida, ruta_sugerencia

# ============================================================================
# 3. ENSAMBLAJE DE LA BIFURCACIÓN CONDICIONAL (RunnableBranch)
# ============================================================================

def construir_sistema_orquestado(paso_clasificacion, ruta_pregunta, ruta_queja, ruta_sugerencia):
    """
    Ensambla el flujo condicional completo.
    
    DETALLE 1: RunnablePassthrough.assign()
    Si usáramos una tubería simple, la salida del clasificador ('queja') reemplazaría 
    todo el diccionario de entrada y perderíamos {'mensaje': '...'}.
    Con .assign(categoria=paso_clasificacion), se conserva el payload original y se le 
    inyecta una nueva clave con el resultado de la clasificación:
    {'mensaje': 'El sistema se cayó', 'categoria': 'queja'}

    DETALLE 2: RunnableBranch
    Evalúa en orden tuplas de la forma (condicion, ruta):
      - condición: Función que evalúa el diccionario y retorna True o False.
      - ruta: Cadena ejecutable que se activa si la condición es verdadera.
      
    DETALLE 3: Ruta por defecto (Fallback estructural)
    El ÚLTIMO argumento de RunnableBranch (aquí 'ruta_pregunta') es obligatorio y va
    sin condición. Si el clasificador devuelve una etiqueta desconocida o anómala,
    el flujo nunca queda en un punto ciego y toma este camino por omisión.
    """
    bifurcacion = RunnableBranch(
        (lambda x: x["categoria"] == "queja", ruta_queja),
        (lambda x: x["categoria"] == "sugerencia", ruta_sugerencia),
        ruta_pregunta  # Camino por defecto ante cualquier otra salida
    )

    cadena_completa = (
        RunnablePassthrough.assign(categoria=paso_clasificacion)
        | bifurcacion
    )
    return cadena_completa

# ============================================================================
# 4. RED DE SEGURIDAD GLOBAL (Bloque 20)
# ============================================================================

def procesar_mensaje_seguro(cadena, texto_mensaje):
    """
    DETALLE TÉCNICO (Bloque 20): Red de Seguridad Global.
    
    ¿Qué sucede si lo que falla es el clasificador inicial o la infraestructura base?
    Los fallbacks locales dentro de las rutas no se activarían porque la falla ocurre ANTES.
    
    Esta función envuelve la llamada exterior a .invoke() en un bloque try/except 
    para garantizar que el sistema NUNCA arroje una pantalla de error no controlada 
    o un traceback al usuario final.
    """
    try:
        # Se envía siempre como diccionario con la clave que esperan los PromptTemplates
        return cadena.invoke({"mensaje": texto_mensaje})
    except Exception as error:
        # En producción real, este bloque registra la traza del error en Datadog/CloudWatch
        print(f"[ERROR CRÍTICO CAPTURADO]: {error}")
        return (
            "Disculpa, tuvimos un inconveniente técnico temporal al procesar tu solicitud. "
            "Por favor, intenta nuevamente en unos minutos."
        )

# ============================================================================
# BLOQUE DE EJECUCIÓN DIRECTA (DEMOSTRACIÓN EN CLASE)
# ============================================================================

if __name__ == "__main__":
    # Inyección de dependencias: se inicializa el modelo una sola vez afuera
    # para permitir sustituirlo fácilmente por un Mock durante las pruebas unitarias.
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.2)

    # 1. Construir componentes
    clasificador = construir_paso_clasificacion(llm)
    c_pregunta, c_queja, c_sugerencia = construir_rutas_especializadas(llm)

    # 2. Ensamblar cadena
    cadena_soporte = construir_sistema_orquestado(
        clasificador, c_pregunta, c_queja, c_sugerencia
    )

    # 3. Probar ejecución protegida
    mensaje_ejemplo = "Llevo tres días intentando restablecer mi acceso y el portal sigue bloqueado."
    print("Iniciando procesamiento orquestado...\n")
    
    respuesta = procesar_mensaje_seguro(cadena_soporte, mensaje_ejemplo)
    
    print("--- RESULTADO OBTENIDO ---")
    print(respuesta)


