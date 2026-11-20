"""
BLOQUE 29: VALIDACIÓN Y BALANCEO DE DATASETS PARA PEFT / FINE-TUNING
-------------------------------------------------------------------
Objetivos de aprendizaje:
  1. Validar la estructura y limpieza de un dataset de ajuste fino (PEFT/LoRA).
  2. Detectar errores silenciosos comunes:
     - Campos obligatorios vacíos o nulos (text_input, output).
     - Salidas que no sean JSON válido o usen comillas simples.
     - Filas duplicadas que sesguen el entrenamiento.
  3. Calcular el balance entre clases objetivo (la razón max/min debe ser menor a 3x).
"""

import json
from collections import Counter
from typing import List, Dict, Any, Tuple


def validar_registro(registro: Dict[str, Any], index: int) -> List[str]:
    """
    Verifica un único registro del dataset en busca de inconsistencias o campos faltantes.
    Retorna una lista de mensajes de error encontrados.
    """
    errores = []

    # 1. Comprobar existencia y no-vacuidad de campos clave
    if "text_input" not in registro or not str(registro.get("text_input", "")).strip():
        errores.append(f"Fila {index}: 'text_input' ausente o vacío.")

    if "output" not in registro or not str(registro.get("output", "")).strip():
        errores.append(f"Fila {index}: 'output' ausente o vacío.")
        return errores  # Si no hay output, no se puede validar formato

    output_str = str(registro["output"]).strip()

    # 2. Validación de formato estructurado (si el output pretende ser JSON)
    if output_str.startswith("{") or output_str.endswith("}"):
        try:
            parsed = json.loads(output_str)
            if not isinstance(parsed, dict):
                errores.append(f"Fila {index}: 'output' no es un objeto JSON diccionario válido.")
        except json.JSONDecodeError as e:
            # Comprueba si el error es por uso de comillas simples en lugar de dobles
            if "'" in output_str:
                errores.append(f"Fila {index}: 'output' usa comillas simples en vez de JSON válido (dobles comillas). Error: {e}")
            else:
                errores.append(f"Fila {index}: 'output' no es un JSON válido. Error: {e}")

    return errores


def validar_dataset_peft(registros: List[Dict[str, Any]]) -> Tuple[bool, List[str], Dict[str, Any]]:
    """
    Valida un conjunto completo de datos para PEFT y calcula estadísticas de balance.
    
    Retorna:
      - es_valido (bool)
      - lista_errores (list)
      - reporte_estadistico (dict)
    """
    todos_errores = []
    textos_vistos = set()
    conteo_clases = Counter()

    for idx, reg in enumerate(registros):
        # Validar consistencia individual
        errs = validar_registro(reg, idx)
        todos_errores.extend(errs)

        # Detectar duplicados en la entrada
        inp = str(reg.get("text_input", "")).strip()
        if inp:
            if inp in textos_vistos:
                todos_errores.append(f"Fila {idx}: Entrada duplicada detectada ('{inp[:40]}...').")
            else:
                textos_vistos.add(inp)

        # Contabilizar clases si existe campo 'categoria' o viene en el output JSON
        categoria = reg.get("categoria")
        if not categoria and "output" in reg:
            try:
                parsed = json.loads(reg["output"])
                categoria = parsed.get("categoria") or parsed.get("clasificacion")
            except Exception:
                pass

        if categoria:
            conteo_clases[str(categoria)] += 1

    # Análisis de balance de clases
    desbalanceado = False
    ratio_balance = 1.0
    if len(conteo_clases) > 1:
        frecuencias = list(conteo_clases.values())
        max_freq = max(frecuencias)
        min_freq = min(frecuencias)
        ratio_balance = round(max_freq / min_freq, 2) if min_freq > 0 else float("inf")
        if ratio_balance > 3.0:
            desbalanceado = True
            todos_errores.append(
                f"Desbalance severo de clases: razón max/min es {ratio_balance:.1f}x (el estándar exige < 3.0x)."
            )

    reporte = {
        "total_registros": len(registros),
        "registros_unicos": len(textos_vistos),
        "distribucion_clases": dict(conteo_clases),
        "ratio_balance": ratio_balance,
        "desbalanceado": desbalanceado
    }

    es_valido = len(todos_errores) == 0
    return es_valido, todos_errores, reporte
