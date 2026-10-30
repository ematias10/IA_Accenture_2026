"""
Suite de evaluación automatizada del Bloque 16.
Ejecuta el dataset de prueba, calcula métricas por caso y genera un reporte global.
"""

from pipeline_texto import procesar_texto
from metricas import calcular_metricas
from dataset_eval import CASOS_EVALUACION

def ejecutar_suite_evaluacion():
    resultados = []
    suma_p, suma_r, suma_f1 = 0.0, 0.0, 0.0

    print("=" * 60)
    print("🚀 INICIANDO SUITE DE EVALUACIÓN AUTOMATIZADA (BLOQUE 16)")
    print("=" * 60)

    for caso in CASOS_EVALUACION:
        # Procesar entrada a través del pipeline
        prediccion_tokens = procesar_texto(caso["entrada"])
        referencia_tokens = caso["referencia_esperada"]

        # Calcular métricas para el caso actual
        m = calcular_metricas(prediccion_tokens, referencia_tokens)
        resultados.append({"id": caso["id"], **m})

        suma_p += m["precision"]
        suma_r += m["recall"]
        suma_f1 += m["f1_score"]

        print(f"[{caso['id']}] {caso['descripcion']}")
        print(f"   • Predicción : {prediccion_tokens}")
        print(f"   • Referencia : {referencia_tokens}")
        print(f"   • Métricas   : P: {m['precision']:.2f} | R: {m['recall']:.2f} | F1: {m['f1_score']:.2f}\n")

    total = len(CASOS_EVALUACION)
    prom_p = suma_p / total
    prom_r = suma_r / total
    prom_f1 = suma_f1 / total

    print("=" * 60)
    print("📊 RESUMEN GLOBAL DE RENDIMIENTO DE LA SUITE:")
    print(f"  • Total de casos evaluados : {total}")
    print(f"  • Precisión Promedio       : {prom_p:.2%}")
    print(f"  • Recall Promedio          : {prom_r:.2%}")
    print(f"  • F1-Score Promedio        : {prom_f1:.2%}")
    print("=" * 60)

if __name__ == "__main__":
    ejecutar_suite_evaluacion()
