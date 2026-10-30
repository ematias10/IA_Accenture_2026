"""
Módulo de cálculo de métricas para evaluación de tareas de PLN y extracción.
Calcula Precisión, Exhaustividad (Recall) y F1-Score comparando listas de tokens o etiquetas.
"""

def calcular_metricas(prediccion: list[str], referencia: list[str]) -> dict:
    """Calcula Precisión, Recall y F1-Score comparando listas de tokens o etiquetas.

    Args:
        prediccion: Lista de tokens o etiquetas devueltas por el modelo/pipeline.
        referencia: Lista de tokens o etiquetas esperadas (Ground Truth).

    Returns:
        Diccionario con precisión, recall y f1_score redondeados a 4 decimales.
    """
    set_pred = set(prediccion)
    set_ref = set(referencia)

    # Verdaderos Positivos: elementos presentes en ambos conjuntos
    aciertos = len(set_pred & set_ref)

    # Precisión: aciertos sobre todo lo predicho por el modelo
    precision = aciertos / len(set_pred) if set_pred else 0.0

    # Recall (Exhaustividad): aciertos sobre todo lo esperado en la referencia
    recall = aciertos / len(set_ref) if set_ref else 0.0

    # F1-Score: media armónica entre precisión y recall
    if precision + recall > 0:
        f1 = 2 * (precision * recall) / (precision + recall)
    else:
        f1 = 0.0

    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "aciertos": aciertos,
        "total_predicho": len(set_pred),
        "total_referencia": len(set_ref)
    }

if __name__ == "__main__":
    # Prueba rápida demostrativa (La analogía del perro aduanero)
    # 10 maletas con fruta prohibida en el lote (Referencia)
    maletas_reales = [f"maleta_{i}" for i in range(1, 11)]

    # Caso A: Perro tímido (alta precisión, bajo recall)
    deteccion_timido = ["maleta_1", "maleta_2"]
    res_timido = calcular_metricas(deteccion_timido, maletas_reales)
    print("Caso Perro Tímido:", res_timido)

    # Caso B: Perro ansioso (baja precisión, alto recall)
    deteccion_ansioso = [f"maleta_{i}" for i in range(1, 101)]
    res_ansioso = calcular_metricas(deteccion_ansioso, maletas_reales)
    print("Caso Perro Ansioso:", res_ansioso)
