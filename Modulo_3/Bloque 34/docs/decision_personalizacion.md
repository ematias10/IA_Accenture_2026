# Decisión de Arquitectura: Personalización del Modelo

## 1. El problema
El clasificador de tickets de soporte suele alterar la estructura JSON solicitada, provocando caídas en el backend de ingesta.

## 2. Resultado del método de decisión
### Respuestas al cuestionario operativo:
- **informacion_cambia_seguido:** No
- **problema_de_formato_o_tono:** Sí
- **dataset_grande_y_de_calidad:** No
- **presupuesto_limitado_o_iterar_rapido:** Sí
- **necesita_multiples_variantes:** Sí

### Puntuación obtenida:
- **RAG:** 4 puntos
- **PEFT (LoRA):** 9 puntos
- **Fine-tuning completo:** 3 puntos

**Técnica recomendada:** PEFT

## 3. Técnica elegida y por qué
[COMPLETAR: Justifica por qué se adopta la recomendación algorítmica o cómo se resolvió el empate. Explica el impacto en costo de cómputo, volumen de datos disponible y tiempo de iteración.]

## 4. Qué necesitarás para ejecutarla
- **Volumen de datos:** [Ej: 150 ejemplos balanceados en formato JSON]
- **Esfuerzo de etiquetado:** [Ej: 150 ejemplos * 4 min/ejemplo = 10 horas humanas especializadas]
- **Infraestructura:** [Ej: 1 instancia GPU A10G o servicio gestionado Vertex AI/Gemini Tuning]
