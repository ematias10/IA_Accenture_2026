# Registro de Revisión Cruzada de Alcance (Peer Review)

> **Proyecto evaluado:** Asistente Normativo de Políticas de TI (Capstone)  
> **Autor del proyecto:** Equipo Capstone  
> **Revisor técnico (par):** Revisor Asignado / Par Técnico  
> **Fecha de revisión:** 2026-11-25  
> **Unidad:** U3.1 - Diseño funcional del proyecto (Bloque 34)  

---

## 1. Pauta de Evaluación Rápida (Lista de Cotejo)

| Criterio Evaluado | Cumple (Sí/No) | Observación del Revisor |
| :--- | :---: | :--- |
| 1. El problema describe un dolor operativo real sin nombrar prematuramente soluciones de IA. | **Sí** | Se enfoca claramente en las 3 horas de demora en soporte de TI. |
| 2. Los RF tienen un solo verbo observable y los RNF incluyen cifras cuantitativas medibles. | **Sí** | RNF-01 (4,0 s) y RNF-02 ($0.006 USD) verificables. |
| 3. El alcance está acotado en los tres cajones sin depender de bases de datos o sistemas de producción reales. | **Sí** | Se declara explícitamente el uso de corpus simulado. |
| 4. Cada ítem del MVP tiene al menos un Criterio de Aceptación (CA) observable y sin ambigüedades. | **Sí** | Cobertura total de RF-01, RF-02, RF-03, RNF-01 y RNF-02. |
| 5. Los hitos terminan en algo ejecutable ("y funciona") y la suma de horas respeta la regla 70/30 (<= 35h). | **Sí** | Total de 27 horas estimadas, dejando margen suficiente para QA y defensa. |

---

## 2. Acierto Principal Destacado por el Revisor

> **Acierto:**  
> La inclusión explícita del caso de abstención en el criterio **CA-03**, donde se define con exactitud cómo debe reaccionar el sistema cuando la pregunta no tiene respaldo documental ("No cuento con información suficiente"). Esto previene alucinaciones desde el diseño.

---

## 3. Hallazgos Constructivos y Resoluciones del Autor

### Hallazgo 1: Falta de prueba de carga o concurrencia básica en los criterios
* **Qué vi:** El criterio `CA-04` evalúa latencia individual en 10 consultas secuenciales, pero no especifica qué ocurre ante un número mínimo de peticiones concurrentes o un payload excesivamente largo.
* **Por qué importa:** En el Gate 3 la comisión o el script de QA puede enviar múltiples requests seguidos o un texto muy extenso, lo que podría elevar la latencia por sobre los 4 segundos.
* **Qué propongo:** Acotar un tamaño máximo de payload de entrada en FastAPI (ej. 1.000 caracteres) y probar con 3 consultas simultáneas.
* **Decisión:** `Aceptado`
* **Acción tomada en la ficha:** Se incorporó en `RNF-01` y en el criterio `CA-04` la validación para payloads de hasta 1.000 caracteres, y se añadió una verificación de degradación bajo ráfaga controlada en el Hito 3.

---

### Hallazgo 2: Ambigüedad en el formato de salida de las citas documentales
* **Qué vi:** En la versión inicial de `CA-02`, se indicaba que la respuesta debía *"citar las fuentes"*, pero no se especificaba la estructura exacta del campo en el JSON de respuesta.
* **Por qué importa:** Si el cliente frontend o la suite de tests automatizados de QA espera una lista `fuentes: [{"documento": "politica.pdf", "chunk_id": 2}]` y el backend devuelve un texto plano pegado al final, las aserciones de `pytest` fallarán.
* **Qué propongo:** Especificar la clave y el tipo de dato JSON esperado en el schema de respuesta.
* **Decisión:** `Aceptado`
* **Acción tomada en la ficha:** Se ajustó la redacción de `CA-02` explicitando que la respuesta de FastAPI debe contener la clave `fuentes: list[str]` con los nombres de archivo exactos, coincidiendo con el modelo Pydantic del Bloque 35.

---

### Hallazgo 3: Propuesta de agregar panel de visualización en Streamlit
* **Qué vi:** El proyecto solo contempla endpoints en FastAPI con documentación Swagger.
* **Por qué importa:** Una interfaz visual en Streamlit facilitaría la demostración en vivo.
* **Qué propongo:** Agregar un Hito H6 de 6 horas para construir una interfaz web gráfica.
* **Decisión:** `Rechazado`
* **Justificación técnica:** Incorporar un frontend en Streamlit aumentaría las horas estimadas de 27 a 33 h, poniendo en riesgo la reserva presupuestaria del 30% exigida para QA (10%), documentación técnica (5%) y preparación de la defensa (10%). La rúbrica del Gate 3 evalúa la API contenerizada en Docker; Swagger satisface plenamente la demostración funcional. Se mantiene en el cajón *Fuera de alcance*.
