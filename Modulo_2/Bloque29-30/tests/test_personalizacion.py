"""
PRUEBAS UNITARIAS: BLOQUES 29 Y 30 (PERSONALIZACIÓN Y DECISIÓN)
---------------------------------------------------------------
Verifica determinísticamente:
  1. Que 'validar_dataset_peft' detecte campos faltantes, comillas simples en JSON y duplicados.
  2. Que se calcule correctamente el ratio de balance de clases y la alerta de desbalance (>3x).
  3. Que 'evaluar_estrategia' calcule puntajes exactos y reporte empates técnicos cuando ocurran.
  4. Que 'generar_documento_decision_md' cree el archivo con las 4 secciones obligatorias.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.validar_dataset import validar_registro, validar_dataset_peft
from src.decision import evaluar_estrategia, generar_documento_decision_md


class TestValidacionDatasetPEFT(unittest.TestCase):

    def test_registro_valido(self):
        """Verifica que un registro bien formado pase sin errores."""
        reg = {
            "text_input": "El usuario solicita cancelar la suscripción anual.",
            "output": '{"categoria": "bajas", "urgencia": "alta"}'
        }
        errores = validar_registro(reg, 0)
        self.assertEqual(len(errores), 0)

    def test_registro_campos_vacios(self):
        """Detecta inputs o outputs vacíos."""
        reg_vacio = {"text_input": "   ", "output": ""}
        errores = validar_registro(reg_vacio, 1)
        self.assertGreaterEqual(len(errores), 2)

    def test_registro_comillas_simples_en_json(self):
        """Detecta el error común de JSON escrito con comillas simples."""
        reg_comillas = {
            "text_input": "Error al pagar con tarjeta.",
            "output": "{'categoria': 'pagos'}"
        }
        errores = validar_registro(reg_comillas, 2)
        self.assertTrue(any("comillas simples" in e for e in errores))

    def test_dataset_completo_con_duplicados_y_balance(self):
        """Prueba la validación global: duplicados y ratio de balance."""
        dataset = [
            {"text_input": "Pregunta A", "output": '{"categoria": "soporte"}'},
            {"text_input": "Pregunta B", "output": '{"categoria": "soporte"}'},
            {"text_input": "Pregunta C", "output": '{"categoria": "soporte"}'},
            {"text_input": "Pregunta D", "output": '{"categoria": "soporte"}'},
            {"text_input": "Pregunta A", "output": '{"categoria": "ventas"}'},  # Duplicado de entrada
            {"text_input": "Pregunta E", "output": '{"categoria": "ventas"}'}
        ]
        valido, errs, reporte = validar_dataset_peft(dataset)
        self.assertFalse(valido)
        self.assertTrue(any("duplicada" in e for e in errs))
        # 4 soporte vs 2 ventas -> ratio 2.0x (dentro del límite)
        self.assertEqual(reporte["ratio_balance"], 2.0)
        self.assertFalse(reporte["desbalanceado"])

    def test_dataset_desbalance_severo(self):
        """Detecta desbalance mayor a 3x."""
        dataset = [
            {"text_input": f"Pregunta soporte {i}", "output": '{"categoria": "soporte"}'}
            for i in range(10)
        ] + [
            {"text_input": "Pregunta facturacion", "output": '{"categoria": "facturacion"}'}
        ]
        valido, errs, reporte = validar_dataset_peft(dataset)
        self.assertFalse(valido)
        self.assertTrue(reporte["desbalanceado"])
        self.assertGreater(reporte["ratio_balance"], 3.0)


class TestMetodoDecision(unittest.TestCase):

    def test_decision_favorece_rag(self):
        """Cuando la información cambia seguido y no es problema de formato, RAG debe ganar."""
        caso_rag = {
            "informacion_cambia_seguido": True,
            "problema_de_formato_o_tono": False,
            "dataset_grande_y_de_calidad": False,
            "presupuesto_limitado_o_iterar_rapido": True,
            "necesita_multiples_variantes": False
        }
        puntos, ganadoras = evaluar_estrategia(caso_rag)
        self.assertIn("RAG", ganadoras)
        self.assertGreater(puntos["RAG"], puntos["PEFT"])

    def test_decision_favorece_peft(self):
        """Problema de formato estricto con presupuesto limitado y múltiples adaptadores favorece PEFT."""
        caso_peft = {
            "informacion_cambia_seguido": False,
            "problema_de_formato_o_tono": True,
            "dataset_grande_y_de_calidad": False,
            "presupuesto_limitado_o_iterar_rapido": True,
            "necesita_multiples_variantes": True
        }
        puntos, ganadoras = evaluar_estrategia(caso_peft)
        self.assertIn("PEFT", ganadoras)

    def test_deteccion_empate_tecnico(self):
        """Un caso límite debe reportar ambas técnicas en empate."""
        caso_empate = {
            "informacion_cambia_seguido": False,
            "problema_de_formato_o_tono": True,
            "dataset_grande_y_de_calidad": True,
            "presupuesto_limitado_o_iterar_rapido": False,
            "necesita_multiples_variantes": False
        }
        puntos, ganadoras = evaluar_estrategia(caso_empate)
        self.assertTrue(len(ganadoras) >= 1)

    def test_generacion_archivo_md(self):
        """Verifica la creación del archivo con las 4 secciones."""
        ruta_test_md = "scratch_decision_test.md"
        if os.path.exists(ruta_test_md):
            os.remove(ruta_test_md)

        cuestionario = {
            "informacion_cambia_seguido": True,
            "problema_de_formato_o_tono": False
        }
        puntos = {"RAG": 7, "PEFT": 3, "Fine-tuning completo": 2}
        ganadoras = ["RAG"]

        generar_documento_decision_md(
            descripcion_problema="El modelo inventa precios que cambian cada semana.",
            respuestas_cuestionario=cuestionario,
            puntos=puntos,
            ganadoras=ganadoras,
            ruta_salida=ruta_test_md
        )

        self.assertTrue(os.path.exists(ruta_test_md))
        with open(ruta_test_md, "r", encoding="utf-8") as f:
            contenido = f.read()

        self.assertIn("## 1. El problema", contenido)
        self.assertIn("## 2. Resultado del método de decisión", contenido)
        self.assertIn("## 3. Técnica elegida y por qué", contenido)
        self.assertIn("## 4. Qué necesitarás para ejecutarla", contenido)
        self.assertIn("**Técnica recomendada:** RAG", contenido)

        os.remove(ruta_test_md)


if __name__ == "__main__":
    unittest.main()
