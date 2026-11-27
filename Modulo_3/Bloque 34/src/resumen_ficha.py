"""
BLOQUE 34: RESUMEN CUANTITATIVO DE LA FICHA (resumen_ficha.py)
--------------------------------------------------------------
Imprime el balance cuantitativo de horas, criterios de aceptación,
cobertura del MVP y estado general de la ficha.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.ficha_datos import parsear_ficha


def mostrar_resumen(ruta_ficha: str = "./Modulo_3/Bloque 34/docs/ficha_diseno_funcional.md"):
    try:
        datos = parsear_ficha(ruta_ficha)
    except Exception as e:
        print(f"Error al leer la ficha: {e}")
        return

    print("==================================================================")
    print("RESUMEN TÉCNICO DE FICHA DE DISEÑO FUNCIONAL (BLOQUE 34)")
    print("==================================================================")

    # 1. Secciones
    print(f"\n[1] SECCIONES ACTIVAS ({len(datos['secciones'])}/5):")
    for s_num in range(1, 6):
        nombre = datos['secciones'].get(s_num, "FALTANTE")
        check = "✓" if s_num in datos['secciones'] else "❌"
        print(f"   {check} Sección {s_num}: {nombre}")

    # 2. Requerimientos vs Criterios
    total_rf = len(datos['rf'])
    total_rnf = len(datos['rnf'])
    total_ca = len(datos['criterios'])
    print(f"\n[2] ALCANCE Y CRITERIOS:")
    print(f"   • Requerimientos Funcionales (RF):     {total_rf}")
    print(f"   • Requerimientos No Funcionales (RNF): {total_rnf}")
    print(f"   • Criterios de Aceptación (CA):        {total_ca}")

    # Cobertura de RF imprescindibles
    imp_rf = set(datos['cajones']['imprescindible'])
    cubiertos_por_ca = set(c['referencia'] for c in datos['criterios'].values())

    no_cubiertos = imp_rf - cubiertos_por_ca
    if no_cubiertos:
        print(f"   ⚠️  Alerta: Los siguientes ítems imprescindibles no tienen CA asociado: {no_cubiertos}")
    else:
        print(f"   ✓ Cobertura 100%: Todos los requerimientos del MVP tienen CA asociado.")

    # 3. Plan por Hitos y Horas
    horas = datos['horas_totales_hitos']
    print(f"\n[3] PLAN POR HITOS (Presupuesto de Tiempo):")
    print(f"   • Cantidad de hitos definidos: {len(datos['hitos'])}")
    print(f"   • Horas totales estimadas:     {horas} h")

    for h in datos['hitos']:
        print(f"     - {h['id']} ({h['horas']} h): {h['descripcion']}")
        print(f"       -> Cubre: {', '.join(h['cubre'])} | Comprueba: {', '.join(h['comprueba_con'])}")

    # 4. Regla 70/30 (Referencia Módulo 3: ~56h totales, ~39h dev máx, ~17h QA/Defensa)
    print(f"\n[4] REGLA 70/30 Y MARGEN OPERATIVO:")
    print(f"   • Horas estimadas en hitos: {horas} h")
    if horas > 35:
        print(f"   ⚠️  ADVERTENCIA: Las horas de hitos ({horas} h) exceden el tope recomendado de desarrollo.")
    else:
        print(f"   ✓ Horas acotadas: Deja reserva adecuada para QA, documentación y defensa final.")

    if datos['tiene_pendientes']:
        print("\n❌ ATENCIÓN: La ficha aún tiene etiquetas [PENDIENTE] o [COMPLETAR].")
    else:
        print("\n✓ SIN PENDIENTES: Lista para revisión cruzada y aprobación.")
    print("==================================================================")


if __name__ == "__main__":
    ruta = sys.argv[1] if len(sys.argv) > 1 else "./Modulo_3/Bloque 34/docs/ficha_diseno_funcional.md"
    mostrar_resumen(ruta)
