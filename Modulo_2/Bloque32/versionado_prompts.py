"""
BLOQUE 32: VERSIONADO DE PROMPTS Y SUPERVISIÓN HUMANA (HUMAN-IN-THE-LOOP)
--------------------------------------------------------------------------
Objetivos de aprendizaje:
  1. Superar el antipatrón del prompt como string suelto sin trazabilidad.
  2. Implementar un registro estructurado de versiones con cálculo de hash SHA-256.
  3. Establecer un flujo de supervisión humana (Human-in-the-Loop) antes de activar
     versiones críticas en el entorno de producción.
  4. Vincular la inferencia en tiempo de ejecución con la versión y hash exacto del prompt.
"""

import os
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any


def calcular_hash_prompt(texto_prompt: str) -> str:
    """
    Calcula la huella digital criptográfica (SHA-256) del contenido normalizado del prompt.
    Garantiza inmutabilidad y detección de cambios inadvertidos.
    """
    normalizado = texto_prompt.strip().encode("utf-8")
    return hashlib.sha256(normalizado).hexdigest()[:16]  # 16 caracteres para legibilidad


class RegistroPrompts:
    """
    Gestor inmutable de versiones de prompts de sistema con aprobación supervisada.
    """
    def __init__(self, ruta_archivo: str = "registro_prompts.json"):
        self.ruta_archivo = ruta_archivo
        self.versiones: Dict[str, Dict[str, Any]] = {}
        self.version_activa: Optional[str] = None
        self._cargar_registro()

    def _cargar_registro(self):
        """Carga el historial persistido desde JSON si existe."""
        if os.path.exists(self.ruta_archivo):
            try:
                with open(self.ruta_archivo, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.versiones = data.get("versiones", {})
                    self.version_activa = data.get("version_activa")
            except Exception:
                self.versiones = {}
                self.version_activa = None

    def _guardar_registro(self):
        """Persiste el registro completo en disco con formato legible UTF-8."""
        os.makedirs(os.path.dirname(self.ruta_archivo) if os.path.dirname(self.ruta_archivo) else ".", exist_ok=True)
        with open(self.ruta_archivo, "w", encoding="utf-8") as f:
            json.dump({
                "version_activa": self.version_activa,
                "versiones": self.versiones
            }, f, ensure_ascii=False, indent=2)

    def registrar_propuesta(
        self,
        version: str,
        template: str,
        autor: str,
        descripcion: str,
        requiere_supervision: bool = True
    ) -> Dict[str, Any]:
        """
        Registra una nueva versión de prompt en estado 'propuesta' o 'aprobada'.
        Si requiere_supervision=True, no puede ser activada hasta recibir visto bueno.
        """
        if version in self.versiones:
            raise ValueError(f"La versión '{version}' ya existe en el registro. No se permite sobreescritura.")

        prompt_hash = calcular_hash_prompt(template)

        registro = {
            "version": version,
            "hash_sha256": prompt_hash,
            "template": template,
            "autor": autor,
            "descripcion": descripcion,
            "creado_en": datetime.now().isoformat(),
            "estado": "pendiente_aprobacion" if requiere_supervision else "aprobada",
            "aprobado_por": None if requiere_supervision else "auto_aprobado",
            "fecha_aprobacion": None if requiere_supervision else datetime.now().isoformat(),
            "comentarios_revision": ""
        }

        self.versiones[version] = registro

        # Si no requiere supervisión y no hay activa previa, se activa
        if not requiere_supervision and not self.version_activa:
            self.version_activa = version

        self._guardar_registro()
        return registro

    def revisar_y_aprobar(
        self,
        version: str,
        revisor: str,
        aprobado: bool,
        comentarios: str = ""
    ) -> Dict[str, Any]:
        """
        Punto de Supervisión Humana (Human-in-the-Loop):
        El supervisor técnico revisa y aprueba o rechaza la versión candidata.
        """
        if version not in self.versiones:
            raise KeyError(f"La versión '{version}' no existe en el registro.")

        item = self.versiones[version]
        item["aprobado_por"] = revisor
        item["fecha_aprobacion"] = datetime.now().isoformat()
        item["comentarios_revision"] = comentarios
        item["estado"] = "aprobada" if aprobado else "rechazada"

        self._guardar_registro()
        return item

    def activar_version(self, version: str) -> Dict[str, Any]:
        """
        Promueve una versión aprobada a versión activa en producción.
        Falla si la versión está en estado 'pendiente_aprobacion' o 'rechazada'.
        """
        if version not in self.versiones:
            raise KeyError(f"La versión '{version}' no existe en el registro.")

        item = self.versiones[version]
        if item["estado"] != "aprobada":
            raise PermissionError(
                f"Bloqueo de seguridad: La versión '{version}' no puede activarse "
                f"porque su estado actual es '{item['estado']}'. Requiere visto bueno humano."
            )

        self.version_activa = version
        self._guardar_registro()
        return item

    def obtener_prompt_activo(self) -> Tuple[str, str, str]:
        """
        Retorna: (version, hash_sha256, template_texto) de la versión activa en producción.
        """
        if not self.version_activa or self.version_activa not in self.versiones:
            raise RuntimeError("No hay ninguna versión de prompt activa y aprobada en producción.")

        reg = self.versiones[self.version_activa]
        return reg["version"], reg["hash_sha256"], reg["template"]


# ============================================================================
# ENSAMBLE Y AUDITORÍA DE INFERENCIA CON PROMPT VERSIONADO
# ============================================================================

def ejecutar_inferencia_con_version(
    pregunta: str,
    contexto: str,
    registro: RegistroPrompts,
    llm: Any
) -> Dict[str, Any]:
    """
    Ejecuta una consulta garantizando que en el log de auditoría quede
    estampada la versión y el hash SHA-256 del prompt exacto que respondió.
    """
    ver, prompt_hash, template = registro.obtener_prompt_activo()

    prompt_ensamblado = template.format(contexto=contexto, pregunta=pregunta)

    # Invocación al modelo (mock o cliente real)
    respuesta = llm.invoke(prompt_ensamblado)
    contenido = getattr(respuesta, "content", str(respuesta))

    return {
        "pregunta": pregunta,
        "respuesta": contenido,
        "auditoria_prompt": {
            "version": ver,
            "hash_sha256": prompt_hash
        }
    }


# ============================================================================
# DEMOSTRACIÓN EN CONSOLA (BLOQUE 32)
# ============================================================================

if __name__ == "__main__":
    from unittest.mock import MagicMock

    archivo_demo = "./Modulo_2/Bloque32/registro_prompts_demo.json"
    if os.path.exists(archivo_demo):
        os.remove(archivo_demo)

    gestor = RegistroPrompts(ruta_archivo=archivo_demo)

    print("==================================================================")
    print("DEMOSTRACIÓN BLOQUE 32: VERSIONADO Y SUPERVISIÓN DE PROMPTS")
    print("==================================================================\n")

    # 1. Proponer v1.0
    prompt_v1 = "Responde brevemente usando el contexto.\nContexto: {contexto}\nPregunta: {pregunta}"
    gestor.registrar_propuesta(
        version="v1.0",
        template=prompt_v1,
        autor="desarrollador_junior",
        descripcion="Prompt base inicial sin restricciones de citación",
        requiere_supervision=True
    )
    print("1. Propuesta 'v1.0' registrada en estado: 'pendiente_aprobacion'")

    # 2. Intentar activar sin visto bueno (demostración del bloqueo)
    try:
        gestor.activar_version("v1.0")
    except PermissionError as e:
        print(f"2. Intento de activación prematura bloqueado correctamente:\n   -> {e}")

    # 3. Supervisión humana (Chef Ejecutivo aprueba)
    gestor.revisar_y_aprobar(
        version="v1.0",
        revisor="arquitecto_ia_senior",
        aprobado=True,
        comentarios="Aprobado para pruebas preliminares."
    )
    gestor.activar_version("v1.0")
    print("3. Versión 'v1.0' aprobada por supervisor y activada en producción.")

    # 4. Inferencia con auditoría
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = "Respuesta de prueba fundamentada [1]."

    resultado = ejecutar_inferencia_con_version(
        pregunta="¿Cuál es la política de despacho?",
        contexto="Despacho en 48 horas en RM.",
        registro=gestor,
        llm=mock_llm
    )

    print("\n4. Consulta atendida con trazabilidad inmutable:")
    print(f"   • Prompt Activo: {resultado['auditoria_prompt']['version']}")
    print(f"   • Hash SHA-256:  {resultado['auditoria_prompt']['hash_sha256']}")
    print(f"   • Respuesta:     {resultado['respuesta']}")
    print(f"\nRegistro guardado en: {archivo_demo}")
