"""
PRUEBAS UNITARIAS: BLOQUE 28 (LATENCIA Y COSTO DEL FLUJO RAG)
--------------------------------------------------------------
Verifica determinísticamente:
  1. Que el context manager 'medir()' capture duraciones válidas mayores a 0 ms.
  2. Que la función 'calcular_costo_usd()' aplique las tarifas por millón de tokens.
  3. Que 'registrar_evento_jsonl()' serialice JSON Lines válidos con codificación UTF-8.
  4. Que 'ejecutar_flujo_rag_instrumentado()' funcione de extremo a extremo usando Mocks,
     aislando las etapas y calculando los totales sin consumir cuota de API.
"""

import os
import sys
import time
import json
import unittest
from unittest.mock import MagicMock

# Asegurar que 'src' esté en el path de importación
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.registro_rag import (
    medir,
    calcular_costo_usd,
    registrar_evento_jsonl,
    ejecutar_flujo_rag_instrumentado,
    Document
)


class TestRegistroRAG(unittest.TestCase):

    def test_context_manager_medir(self):
        """Valida que el context manager registre el tiempo de la etapa en ms."""
        tiempos = {}
        with medir("etapa_prueba", tiempos):
            time.sleep(0.02)  # Pausa de 20 ms
        
        self.assertIn("etapa_prueba", tiempos)
        self.assertGreaterEqual(tiempos["etapa_prueba"], 15.0)

    def test_calculo_costo_usd_determinista(self):
        """Verifica que el costo en USD sea exacto según el tarifario de referencia."""
        # 1,000,000 tokens de entrada = $0.075 USD
        # 1,000,000 tokens de salida  = $0.300 USD
        costo_millon = calcular_costo_usd(1_000_000, 1_000_000)
        self.assertEqual(round(costo_millon, 3), 0.375)

        # Caso típico de RAG: 150 input tokens, 50 output tokens
        # Input: (150 / 1M) * 0.075 = 0.00001125
        # Output: (50 / 1M) * 0.300 = 0.00001500
        # Total = 0.00002625
        costo_rag_tipico = calcular_costo_usd(150, 50)
        self.assertAlmostEqual(costo_rag_tipico, 0.0000263, places=7)

        # Caso borde: 0 tokens
        self.assertEqual(calcular_costo_usd(0, 0), 0.0)

    def test_registro_evento_jsonl(self):
        """Verifica la persistencia en formato JSON Lines (una línea por registro)."""
        archivo_temporal = "test_trazas_temp.jsonl"
        if os.path.exists(archivo_temporal):
            os.remove(archivo_temporal)

        evento_demo = {
            "pregunta": "¿Cómo funciona el backoff?",
            "k": 3,
            "costo_usd": 0.000045,
            "tiempo_total_ms": 1500.5
        }

        registrar_evento_jsonl(evento_demo, archivo=archivo_temporal)
        registrar_evento_jsonl(evento_demo, archivo=archivo_temporal)

        self.assertTrue(os.path.exists(archivo_temporal))
        with open(archivo_temporal, "r", encoding="utf-8") as f:
            lineas = f.readlines()

        self.assertEqual(len(lineas), 2)
        for l in lineas:
            obj = json.loads(l)
            self.assertEqual(obj["pregunta"], "¿Cómo funciona el backoff?")
            self.assertEqual(obj["k"], 3)

        os.remove(archivo_temporal)

    def test_flujo_rag_instrumentado_con_mocks(self):
        """
        Verifica la ejecución del flujo RAG instrumentado aislando Chroma y el LLM con Mocks.
        Comprueba que el evento resultante contenga todas las claves requeridas para el Gate 2.
        """
        mock_vectorstore = MagicMock()
        mock_retriever = MagicMock()
        doc_ejemplo = Document(
            page_content="Backoff exponencial con 3 reintentos.",
            metadata={"fuente": "api_docs.txt"}
        )
        mock_retriever.invoke.return_value = [doc_ejemplo]
        mock_vectorstore.as_retriever.return_value = mock_retriever

        # Simulación de respuesta de LLM con usage_metadata
        mock_llm = MagicMock()
        mock_respuesta = MagicMock()
        mock_respuesta.content = "El cliente reintenta hasta 3 veces [1]."
        mock_respuesta.usage_metadata = {
            "input_tokens": 120,
            "output_tokens": 25,
            "total_tokens": 145
        }
        mock_llm.invoke.return_value = mock_respuesta

        archivo_log_test = "test_log_flujo.jsonl"
        if os.path.exists(archivo_log_test):
            os.remove(archivo_log_test)

        resultado = ejecutar_flujo_rag_instrumentado(
            pregunta="¿Cuántos reintentos hace la API?",
            vectorstore=mock_vectorstore,
            llm=mock_llm,
            k=1,
            archivo_logs=archivo_log_test
        )

        # Validaciones estructurales del reporte
        self.assertIn("timestamp", resultado)
        self.assertEqual(resultado["pregunta"], "¿Cuántos reintentos hace la API?")
        self.assertEqual(resultado["k"], 1)
        self.assertIn("embed_y_busqueda", resultado["tiempos_ms"])
        self.assertIn("generacion", resultado["tiempos_ms"])
        self.assertGreater(resultado["tiempo_total_ms"], 0)
        self.assertEqual(resultado["tokens"]["input_tokens"], 120)
        self.assertEqual(resultado["tokens"]["output_tokens"], 25)
        self.assertGreater(resultado["costo_usd"], 0)
        self.assertIn("[1]", resultado["respuesta"])

        # Comprobar que se haya escrito en el archivo JSONL
        self.assertTrue(os.path.exists(archivo_log_test))
        os.remove(archivo_log_test)


if __name__ == "__main__":
    unittest.main()
