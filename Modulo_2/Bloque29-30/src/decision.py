"""
BLOQUE 30: FUNCIÓN DE DECISIÓN DE PERSONALIZACIÓN Y GENERADOR DE ESQUELETO
---------------------------------------------------------------------------
Objetivos de aprendizaje:
  1. Reemplazar la intuición por una función algorítmica fundada en 5 variables de negocio.
  2. Asignar puntajes ponderados para RAG, PEFT y Fine-Tuning completo.
  3. Gestionar y transparentar los empates como señales de análisis cualitativo humano.
  4. Generar automáticamente el archivo Markdown exigido: 'docs/decision_personalizacion.md'.
"""

import os
from typing import Dict, List, Tuple, Any


def evaluar_estrategia(respuestas: Dict[str, bool]) -> Tuple[Dict[str, int], List[str]]:
    """
    Calcula los puntajes ponderados para cada técnica de personalización.
    
    Variables evaluadas:
      1. informacion_cambia_seguido: Conocimiento dinámico vs estático.
      2. problema_de_formato_o_tono: Estilo, tono o gramática estricta vs contenido factual.
      3. dataset_grande_y_de_calidad: Existencia de datos etiquetados curados.
      4. presupuesto_limitado_o_iterar_rapido: Restricciones de cómputo y horas hombre.
      5. necesita_multiples_variantes: Arquitecturas multi-tenant o adaptadores por cliente.
    """
    puntos = {"RAG": 0, "PEFT": 0, "Fine-tuning completo": 0}

    # 1. Dinamismo de la información
    if respuestas.get("informacion_cambia_seguido", False):
        puntos["RAG"] += 3  # RAG es mandatorio si la información cambia a diario o semanalmente
    else:
        puntos["PEFT"] += 1
        puntos["Fine-tuning completo"] += 1

    # 2. Naturaleza del problema
    if respuestas.get("problema_de_formato_o_tono", False):
        puntos["PEFT"] += 2
        puntos["Fine-tuning completo"] += 2
    else:
        puntos["RAG"] += 2

    # 3. Disponibilidad y madurez de datos
    if respuestas.get("dataset_grande_y_de_calidad", False):
        puntos["Fine-tuning completo"] += 2
        puntos["PEFT"] += 1
    else:
        puntos["RAG"] += 1
        puntos["PEFT"] += 1  # PEFT tolera datasets acotados (~100-300 ejemplos)

    # 4. Restricción de presupuesto y tiempo de iteración
    if respuestas.get("presupuesto_limitado_o_iterar_rapido", False):
        puntos["RAG"] += 2
        puntos["PEFT"] += 2
    else:
        puntos["Fine-tuning completo"] += 1

    # 5. Adaptabilidad multi-variante (multi-tenant)
    if respuestas.get("necesita_multiples_variantes", False):
        puntos["PEFT"] += 3  # Los adaptadores LoRA ocupan ~10-50MB frente a gigabytes del modelo completo
        puntos["RAG"] += 1

    # Determinar técnica(s) ganadora(s)
    max_score = max(puntos.values())
    ganadoras = [tec for tec, score in puntos.items() if score == max_score]

    return puntos, ganadoras


def generar_documento_decision_md(
    descripcion_problema: str,
    respuestas_cuestionario: Dict[str, bool],
    puntos: Dict[str, int],
    ganadoras: List[str],
    justificacion_cualitativa: str = "",
    requisitos_ejecucion: str = "",
    ruta_salida: str = "docs/decision_personalizacion.md"
) -> str:
    """
    Construye y escribe en disco el archivo Markdown con las 4 secciones
    obligatorias para el repositorio según el Bloque 30.
    """
    os.makedirs(os.path.dirname(ruta_salida) if os.path.dirname(ruta_salida) else ".", exist_ok=True)

    if len(ganadoras) > 1:
        resultado_txt = f"**Empate técnico entre:** {', '.join(ganadoras)}\n*(Requiere desempate cualitativo según costos de etiquetado o infraestructura)*"
    else:
        resultado_txt = f"**Técnica recomendada:** {ganadoras[0]}"

    seccion_justificacion = justificacion_cualitativa if justificacion_cualitativa.strip() else (
        "[COMPLETAR: Justifica por qué se adopta la recomendación algorítmica o cómo se resolvió el empate. "
        "Explica el impacto en costo de cómputo, volumen de datos disponible y tiempo de iteración.]"
    )

    seccion_requisitos = requisitos_ejecucion if requisitos_ejecucion.strip() else (
        "- **Volumen de datos:** [Ej: 150 ejemplos balanceados en formato JSON]\n"
        "- **Esfuerzo de etiquetado:** [Ej: 150 ejemplos * 4 min/ejemplo = 10 horas humanas especializadas]\n"
        "- **Infraestructura:** [Ej: 1 instancia GPU A10G o servicio gestionado Vertex AI/Gemini Tuning]"
    )

    cuestionario_md = "\n".join([f"- **{k}:** {'Sí' if v else 'No'}" for k, v in respuestas_cuestionario.items()])

    contenido = f"""# Decisión de Arquitectura: Personalización del Modelo

## 1. El problema
{descripcion_problema.strip()}

## 2. Resultado del método de decisión
### Respuestas al cuestionario operativo:
{cuestionario_md}

### Puntuación obtenida:
- **RAG:** {puntos['RAG']} puntos
- **PEFT (LoRA):** {puntos['PEFT']} puntos
- **Fine-tuning completo:** {puntos['Fine-tuning completo']} puntos

{resultado_txt}

## 3. Técnica elegida y por qué
{seccion_justificacion}

## 4. Qué necesitarás para ejecutarla
{seccion_requisitos}
"""

    with open(ruta_salida, "w", encoding="utf-8") as f:
        f.write(contenido)

    return contenido


if __name__ == "__main__":
    print("================================================================")
    print("DEMOSTRACIÓN: EVALUACIÓN DE ARQUITECTURA DE PERSONALIZACIÓN")
    print("================================================================\n")

    # 1. Caso de prueba: Clasificador de incidentes con formato JSON rebelde
    problema_negocio = (
        "El clasificador de tickets de soporte suele alterar la estructura JSON "
        "solicitada, provocando caídas en el backend de ingesta."
    )

    cuestionario = {
        "informacion_cambia_seguido": False,       # La taxonomía de tickets es fija
        "problema_de_formato_o_tono": True,        # El problema es netamente sintáctico/formato
        "dataset_grande_y_de_calidad": False,      # Solo tenemos ~180 ejemplos curados
        "presupuesto_limitado_o_iterar_rapido": True, # Presupuesto acotado
        "necesita_multiples_variantes": True       # Se requiere un adaptador por cliente
    }

    print("1. Evaluando cuestionario operativo...")
    for variable, valor in cuestionario.items():
        print(f"   • {variable}: {'Sí' if valor else 'No'}")

    # 2. Calcular puntajes con el algoritmo
    puntajes, recomendadas = evaluar_estrategia(cuestionario)

    print("\n2. Puntuación calculada por el algoritmo:")
    for tecnica, score in puntajes.items():
        print(f"   -> {tecnica}: {score} puntos")

    if len(recomendadas) > 1:
        print(f"\n   ⚠️ EMPATE TÉCNICO DETECTADO: {', '.join(recomendadas)}")
        print("   (Requiere resolución cualitativa en el documento Markdown)")
    else:
        print(f"\n   ✓ TÉCNICA RECOMENDADA: {recomendadas[0]}")

    # 3. Generar el documento Markdown para el repositorio
    ruta_doc = "docs/decision_personalizacion.md"
    generar_documento_decision_md(
        descripcion_problema=problema_negocio,
        respuestas_cuestionario=cuestionario,
        puntos=puntajes,
        ganadoras=recomendadas,
        ruta_salida=ruta_doc
    )
    print(f"\n3. Entregable generado en: {ruta_doc}")
