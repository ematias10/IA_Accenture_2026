"""
BLOQUE 34: PARSEADOR DE FICHA DE DISEÑO FUNCIONAL (ficha_datos.py)
------------------------------------------------------------------
Extrae las estructuras de datos clave desde 'docs/ficha_diseno_funcional.md':
  - Secciones presentes
  - Requerimientos Funcionales (RF) y No Funcionales (RNF)
  - Cajones de alcance (Imprescindible, Deseable, Fuera de alcance)
  - Criterios de Aceptación (CA) y su vinculación con RF/RNF
  - Plan de construcción por hitos (H-XX, horas estimadas, RF cubiertos, CA de comprobación)
"""

import os
import re
import unicodedata
from typing import Dict, List, Any, Optional


def normalizar(texto: str) -> str:
    sin_tildes = unicodedata.normalize("NFD", texto)
    return "".join(c for c in sin_tildes if unicodedata.category(c) != "Mn").lower()


def parsear_ficha(ruta_archivo: str = "docs/ficha_diseno_funcional.md") -> Dict[str, Any]:
    if not os.path.exists(ruta_archivo):
        raise FileNotFoundError(f"No se encontró el archivo '{ruta_archivo}'.")

    with open(ruta_archivo, "r", encoding="utf-8") as f:
        contenido = f.read()

    resultado: Dict[str, Any] = {
        "ruta": ruta_archivo,
        "secciones": {},
        "rf": {},
        "rnf": {},
        "cajones": {"imprescindible": [], "deseable": [], "fuera_de_alcance": []},
        "criterios": {},
        "hitos": [],
        "horas_totales_hitos": 0,
        "tiene_pendientes": False
    }

    # Verificar marcas pendientes o sin completar
    if "[completar" in normalizar(contenido) or "[pendiente" in normalizar(contenido):
        resultado["tiene_pendientes"] = True

    # 1. Identificar Secciones (1 a 5)
    patron_seccion = r"(?m)^##\s*(\d)\.\s*(.+)$"
    for match in re.finditer(patron_seccion, contenido):
        num_sec = int(match.group(1))
        tit_sec = match.group(2).strip()
        resultado["secciones"][num_sec] = tit_sec

    # 2. Extraer RF y RNF (soporta ** en cualquier lugar)
    patron_rf = r"(?m)^-\s*\*?\*?(RF-\d{2})\*?\*?:\s*(.+)$"
    for match in re.finditer(patron_rf, contenido):
        resultado["rf"][match.group(1)] = match.group(2).strip(" *`")

    patron_rnf = r"(?m)^-\s*\*?\*?(RNF-\d{2})\*?\*?:\s*(.+)$"
    for match in re.finditer(patron_rnf, contenido):
        resultado["rnf"][match.group(1)] = match.group(2).strip(" *`")

    # 3. Extraer Cajones de Alcance
    m_imp = re.search(r"(?i)###?\s*Imprescindible.*?\n(.*?)(?=###?\s*Deseable|###?\s*Fuera|##|\Z)", contenido, re.DOTALL)
    if m_imp:
        resultado["cajones"]["imprescindible"] = re.findall(r"(RF-\d{2}|RNF-\d{2})", m_imp.group(1))

    m_des = re.search(r"(?i)###?\s*Deseable.*?\n(.*?)(?=###?\s*Fuera|##|\Z)", contenido, re.DOTALL)
    if m_des:
        resultado["cajones"]["deseable"] = re.findall(r"(RF-\d{2}|RNF-\d{2})", m_des.group(1))

    m_fue = re.search(r"(?i)###?\s*Fuera de alcance.*?\n(.*?)(?=##|\Z)", contenido, re.DOTALL)
    if m_fue:
        resultado["cajones"]["fuera_de_alcance"] = [l.strip("- *`") for l in m_fue.group(1).splitlines() if l.strip().startswith("-")]

    # 4. Extraer Criterios de Aceptación (soporta **CA-01 (RF-01):** desc o CA-01 (RF-01): desc)
    patron_ca = r"(?m)^-\s*\*?\*?(CA-\d{2})\*?\*?\s*\((RF-\d{2}|RNF-\d{2})\)\*?\*?:\s*(.+)$"
    for match in re.finditer(patron_ca, contenido):
        ca_id = match.group(1)
        ref_id = match.group(2)
        desc = match.group(3).strip(" *`")
        resultado["criterios"][ca_id] = {
            "referencia": ref_id,
            "descripcion": desc
        }

    # 5. Extraer Hitos (H-X o H1)
    patron_hito = r"(?m)^-\s*\*?\*?(H\d+)\*?\*?\s*\((\d+)\s*h\):\s*\*?\*?([^\.]+)\*?\*?\.\s*Cubre:\s*([^.]+)\.\s*Se comprueba con:\s*([^.]+)\."
    for match in re.finditer(patron_hito, contenido):
        h_id = match.group(1)
        horas = int(match.group(2))
        desc = match.group(3).strip(" *`")
        cubiertos = re.findall(r"(RF-\d{2}|RNF-\d{2})", match.group(4))
        criterios_comprobacion = re.findall(r"(CA-\d{2})", match.group(5))

        resultado["hitos"].append({
            "id": h_id,
            "horas": horas,
            "descripcion": desc,
            "cubre": cubiertos,
            "comprueba_con": criterios_comprobacion
        })
        resultado["horas_totales_hitos"] += horas

    return resultado
