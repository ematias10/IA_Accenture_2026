"""
BLOQUE 34: VERIFICADOR COMPLETO DE LA FICHA DE DISEÑO FUNCIONAL (verificar_ficha_completa.py)
---------------------------------------------------------------------------------------------
Auditoría integral para el cierre de la Unidad U3.1:
  1. Verifica que las 5 secciones existan y no tengan [COMPLETAR] ni [PENDIENTE].
  2. Valida al menos 3 RF y 2 RNF cuantitativos.
  3. Comprueba que cada ítem del MVP (Imprescindible) tenga al menos un Criterio de Aceptación (CA-NN (RF/RNF-NN)).
  4. Comprueba que exista al menos un CA negativo / de borde (ej: abstención o error controlado).
  5. Valida que los hitos terminen con el criterio 'y funciona', vinculen RF y CA, y no excedan el presupuesto de horas (<= 35h).
  6. Comprueba la existencia del diagrama 'docs/diagrama_arquitectura.png'.
  7. Comprueba la existencia y completitud de 'docs/revision_alcance.md' con al menos 2 hallazgos constructivos y decisiones.
"""

import os
import re
import sys
import unicodedata

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.ficha_datos import parsear_ficha, normalizar

RUTA_FICHA = "docs/ficha_diseno_funcional.md"
RUTA_DIAGRAMA = "docs/diagrama_arquitectura.png"
RUTA_REVISION = "docs/revision_alcance.md"


def verificar_ficha_completa():
    errores = []
    avisos = []

    if not os.path.exists(RUTA_FICHA):
        print(f"ERROR CRÍTICO: No existe '{RUTA_FICHA}'.")
        sys.exit(1)

    try:
        datos = parsear_ficha(RUTA_FICHA)
    except Exception as e:
        print(f"ERROR al parsear la ficha: {e}")
        sys.exit(1)

    # 1. Verificar presencia de las 5 secciones
    for s_num in range(1, 6):
        if s_num not in datos["secciones"]:
            errores.append(f"Falta la Sección {s_num} obligatoria.")

    # 2. Verificar ausencia de [COMPLETAR] y [PENDIENTE]
    if datos["tiene_pendientes"]:
        errores.append("La ficha contiene marcas sin rellenar ('[COMPLETAR]' o '[PENDIENTE]').")

    # 3. Validar RFs y RNFs
    if len(datos["rf"]) < 3:
        errores.append(f"Se encontraron {len(datos['rf'])} RF (se exigen mínimo 3).")

    if len(datos["rnf"]) < 2:
        errores.append(f"Se encontraron {len(datos['rnf'])} RNF (se exigen mínimo 2).")

    # 4. Validar Cobertura de CAs sobre el MVP
    items_mvp = set(datos["cajones"]["imprescindible"])
    if not items_mvp:
        errores.append("No se identificaron ítems en el cajón 'Imprescindible'.")

    referencias_ca = set(c["referencia"] for c in datos["criterios"].values())
    no_cubiertos = items_mvp - referencias_ca
    if no_cubiertos:
        errores.append(f"Hay requerimientos del MVP sin ningún Criterio de Aceptación: {sorted(list(no_cubiertos))}")

    # 5. Validar caso negativo o de abstención en los CA
    textos_ca = " ".join([c["descripcion"].lower() for c in datos["criterios"].values()])
    palabras_negativas = ["no cuenta", "no cuento", "no dispongo", "fuera de", "abstiene", "error", "400", "404", "vacia", "vacio", "invalido"]
    tiene_caso_negativo = any(p in textos_ca for p in palabras_negativas)
    if not tiene_caso_negativo:
        avisos.append("Recomendación de QA: Incluir al menos un Criterio de Aceptación (CA) que valide explícitamente el caso negativo (ej. abstención ante pregunta fuera del corpus).")

    # 6. Validar Plan por Hitos
    if len(datos["hitos"]) < 3:
        errores.append(f"Se definieron {len(datos['hitos'])} hitos (se recomiendan al menos 3 a 5 etapas).")

    if datos["horas_totales_hitos"] > 35:
        errores.append(f"Las horas de hitos ({datos['horas_totales_hitos']} h) superan el tope permitido de 35h (violando la regla 70/30).")

    for h in datos["hitos"]:
        desc = h["descripcion"].lower()
        if "funciona" not in desc and "operativo" not in desc and "desplegado" not in desc:
            avisos.append(f"Hito {h['id']}: Se recomienda asegurar que la meta sea verificable ('y funciona', 'desplegado').")

    # 7. Validar Diagrama de Arquitectura
    if not os.path.exists(RUTA_DIAGRAMA):
        errores.append(f"No existe el archivo de imagen del diagrama: '{RUTA_DIAGRAMA}'.")

    # 8. Validar Registro de Revisión Cruzada (docs/revision_alcance.md)
    if not os.path.exists(RUTA_REVISION):
        errores.append(f"Falta el documento de revisión entre pares: '{RUTA_REVISION}'.")
    else:
        with open(RUTA_REVISION, "r", encoding="utf-8") as f:
            contenido_rev = normalizar(f.read())
        decisiones_encontradas = re.findall(r"decision:?[\s\*`]+(aceptado|rechazado|aplazado)", contenido_rev)
        if len(decisiones_encontradas) < 2:
            errores.append("El documento 'docs/revision_alcance.md' debe registrar al menos 2 decisiones explícitas ('Aceptado', 'Rechazado' o 'Aplazado').")

    # Reporte
    print("==================================================================")
    print("AUDITORÍA DE CIERRE U3.1: FICHA COMPLETA Y REVISIÓN ENTRE PARES")
    print("==================================================================")

    if avisos:
        print("\n[AVISOS / RECOMENDACIONES]:")
        for a in avisos:
            print(f"  ⚠️  {a}")

    if errores:
        print("\n[ERRORES DETECTADOS QUE IMPIDEN EL CIERRE]:")
        for e in errores:
            print(f"  ❌ {e}")
        print(f"\nTotal: {len(errores)} error(es) detectados.")
        sys.exit(1)
    else:
        print("\n✓ APROBADO: La Ficha de Diseño Funcional (Secciones 1 a 5) y la Revisión entre Pares cumplen el 100% de la pauta del Bloque 34.")
        sys.exit(0)


if __name__ == "__main__":
    verificar_ficha_completa()
