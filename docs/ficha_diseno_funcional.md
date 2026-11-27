# Ficha de Diseño Funcional del Proyecto (Capstone)

> **Estado:** Aprobada para construcción (Cierre Unidad U3.1 - Bloque 34)  
> **Unidad:** U3.1 - Diseño funcional del proyecto según perfil de salida  
> **Gate asociado:** Gate 3 - Capstone Final  

---

## 1. Problema de negocio

### Contexto y dolor operativo
El equipo de atención a clientes internos de soporte de TI recibe un promedio de 450 solicitudes semanales sobre políticas de seguridad y configuración de accesos. Actualmente, los especialistas dedican más del 40% de su jornada laboral a buscar manualmente en normativas internas dispersas en múltiples archivos PDF, generando demoras promedio de 3 horas por ticket y respuestas inconsistentes entre analistas.

### Impacto cuantitativo estimado
- **Frecuencia del problema:** 450 consultas semanales (aproximadamente 1.800 mensuales).
- **Tiempo perdido / costo actual:** 15 a 20 minutos promedio por búsqueda manual en documentación.
- **Impacto de no resolverlo:** Inconsistencia regulatoria y saturación de analistas senior en tareas repetitivas.

---

## 2. Requerimientos y alcance (MVP)

### Requerimientos Funcionales (RF)
- **RF-01:** El usuario consulta políticas internas mediante preguntas en lenguaje natural a través de una interfaz de API.
- **RF-02:** El sistema recupera los fragmentos normativos relevantes y emite una respuesta fundamentada citando explícitamente el documento fuente `[archivo, sección]`.
- **RF-03:** El sistema abstiene la respuesta ("No cuento con información suficiente en las fuentes") cuando la consulta no está cubierta en el corpus indexado.
- **RF-04:** El supervisor técnico revisa y aprueba o rechaza actualizaciones al prompt de sistema antes de su despliegue mediante un punto de interrupción humano.

### Requerimientos No Funcionales (RNF)
- **RNF-01:** Latencia de respuesta de extremo a extremo menor a 4,0 segundos en el percentil 90 (p90) de las consultas para payloads de hasta 1.000 caracteres.
- **RNF-02:** Costo operativo promedio inferior a $0.006 USD por consulta atendida, registrado en los logs de consumo.
- **RNF-03:** Contención y aislamiento local reproducible en 1 contenedor Docker con tiempo de arranque inferior a 15 segundos.

### Clasificación de Alcance (Los Tres Cajones)

#### Imprescindible (Core del MVP)
- RF-01 (Consulta en lenguaje natural).
- RF-02 (Respuesta fundamentada con citas obligatorias).
- RF-03 (Abstención estricta ante falta de contexto).
- RNF-01 (Latencia acotada) y RNF-02 (Costo registrado).

#### Deseable (Solo si sobra tiempo tras cumplir la regla 70/30)
- RF-04 (Panel de supervisión humana para prompts).
- Soporte para exportar el historial de auditoría de consultas en formato CSV.

#### Fuera de alcance (Exclusiones explícitas y justificadas)
- **Conexión a bases de datos o sistemas corporativos en producción:** Por normativa de seguridad y reproducibilidad, el sistema opera 100% con corpus documental simulado y anonimizado en local.
- **Canales de mensajería externos (WhatsApp / Slack / Teams en vivo):** Quedan descartados para el Gate 3; la interacción se expondrá exclusivamente vía API REST documentada en Swagger (FastAPI).
- **Entrenamiento de modelos fundacionales desde cero:** Inviable por restricciones de cómputo y tiempo del sprint.
- **Interfaz gráfica web personalizada (React / Streamlit):** Descartada para proteger las horas de testing y Docker; la interacción de prueba se realiza sobre la documentación interactiva Swagger `/docs`.

---

## 3. Arquitectura de la solución

### Diagrama de componentes
El diagrama visual de la arquitectura se encuentra versionado en el archivo:  
`docs/diagrama_arquitectura.png`

```text
[ Cliente HTTP / Swagger ]
           │ (1) Request JSON con trace_id
           ▼
[ FastAPI App (api/main.py) ]
           │ (2) Sanitización y filtro anti-inyección
           ▼
[ Pipeline RAG Orquestado (src/rag.py) ]
    ├──► [ Vector Store Local (Chroma) ]  (Recuperación Top-K)
    └──► [ LLM Gateway (src/cliente.py) ] (Invocación con reintentos y backoff)
           │ (3) Logging estructurado y métricas
           ▼
[ Observabilidad & Auditoría (app_rag.log / registros_costo.jsonl) ]
```

### Descripción del flujo de componentes
1. **Cliente HTTP / Swagger:** Envía la consulta en lenguaje natural con encabezados estándar.
2. **FastAPI App (`api/main.py`):** Recibe la solicitud, inicializa el `trace_id` aislado en `contextvars` y ejecuta el filtro de sanitización de inyección de prompt.
3. **Pipeline RAG Orquestado (`src/rag.py`):** Recupera los fragmentos más relevantes desde el **Vector Store Local (Chroma)** persistido en disco y delimita el contexto en etiquetas `<contexto>`.
4. **LLM Gateway (`src/cliente.py`):** Envía el prompt ensamblado al modelo generativo mediante un cliente modular con reintentos exponenciales y control de *rate limits*.
5. **Observabilidad & Auditoría:** Registra cada llamada en formato JSON estructurado en `app_rag.log` y contabiliza los tokens/costos en `registros_costo.jsonl`.

---

## 4. Criterios de aceptación

- **CA-01 (RF-01):** Al enviar una petición POST a `/consultar` con un payload JSON `{"pregunta": "¿Cuál es el protocolo de contraseñas?"}`, el servicio retorna código HTTP 200 con un campo JSON `respuesta` que contiene texto legible y no vacío.
- **CA-02 (RF-02):** Para la consulta de políticas del CA-01, la respuesta incluye una clave JSON `fuentes` con una lista no vacía de nombres de archivo (ej. `["politica_seguridad_v2.pdf"]`) y en el cuerpo del texto aparecen citas explícitas correlacionadas.
- **CA-03 (RF-03):** Ante una consulta intencionalmente no cubierta en el corpus documental (ej. *"¿Cuál es el menú del casino de la empresa?"*), el servicio retorna HTTP 200 con la respuesta exacta: *"No cuento con información suficiente en las fuentes para responder a su consulta"*, y la clave `fuentes` devuelve una lista vacía `[]`.
- **CA-04 (RNF-01):** En una corrida automatizada de 10 consultas secuenciales con preguntas válidas de hasta 1.000 caracteres, el 90% (al menos 9 peticiones) completa su ciclo y retorna respuesta en un tiempo inferior a 4,0 segundos medido en el cliente.
- **CA-05 (RNF-02):** En cada consulta procesada, se escribe una línea en `registros_costo.jsonl` con el `trace_id`, conteo de tokens de entrada y salida, y el costo calculado en USD, comprobando que el promedio sea inferior a $0.006 USD.
- **CA-06 (RF-04):** Si se propone una nueva versión de prompt de sistema, el registro lo almacena en estado `pendiente_aprobacion` y bloquea su activación en el pipeline hasta que un supervisor envíe la aprobación explícita `aprobado: True`.

---

## 5. Plan de construcción por hitos

- **H1 (6 h):** Endpoint base en FastAPI con documentación Swagger y validación Pydantic y funciona. Cubre: RF-01. Se comprueba con: CA-01.
- **H2 (8 h):** Integración de Chroma persistido con pipeline RAG y formato de citas y funciona. Cubre: RF-02, RF-03. Se comprueba con: CA-02, CA-03.
- **H3 (5 h):** Capa de observabilidad estructurada con contextvars y registro de costos y funciona. Cubre: RNF-01, RNF-02. Se comprueba con: CA-04, CA-05.
- **H4 (4 h):** Filtro anti-inyección de prompt y módulo de versionado supervisado y funciona. Cubre: RF-04. Se comprueba con: CA-06.
- **H5 (4 h):** Empaquetado en Dockerfile reproducible y prueba de levantamiento local y funciona. Cubre: RNF-03. Se comprueba con: CA-01, CA-04.

*Presupuesto total estimado en hitos: **27 horas*** (lo que deja 29 horas de margen respecto a las 56h del Módulo 3, asegurando holgadamente la reserva del 30% para QA, documentación y preparación de la defensa para el Gate 3).
