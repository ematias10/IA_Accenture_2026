# Bloque 34: Criterios de Aceptación, Plan por Hitos y Revisión Cruzada (Cierre U3.1)

Este módulo completa formalmente la **Ficha de Diseño Funcional** (`docs/ficha_diseno_funcional.md`) y el **Registro de Revisión entre Pares** (`docs/revision_alcance.md`), habilitando la transición a la **Unidad U3.2: Exposición de servicios con FastAPI**.

---

## 1. Estructura del Repositorio

```text
bloque_34_criterios_e_hitos/
├── requirements.txt                   # Dependencias de visualización
├── README.md                          # Guía paso a paso para el laboratorio
├── docs/
│   ├── ficha_diseno_funcional.md      # Ficha completa con las 5 secciones
│   ├── diagrama_arquitectura.png      # Diagrama de componentes arquitectónicos
│   └── revision_alcance.md            # Registro auditable de revisión entre pares
└── src/
    ├── ficha_datos.py                 # Parser estructural de la ficha en Python
    ├── resumen_ficha.py               # Balance cuantitativo de cobertura y horas
    ├── verificar_ficha_completa.py    # Auditoría estática integral de cierre
    └── generar_diagrama.py            # Generador visual del diagrama de arquitectura
```

---

## 2. Comandos de Ejecución

### A. Inspeccionar el Balance de Requerimientos y Horas
```bash
python3 src/resumen_ficha.py
```
*Muestra en consola las 5 secciones, la cobertura del 100% del MVP y el balance de 27 horas bajo la regla 70/30.*

### B. Ejecutar la Auditoría Completa de la Ficha y la Revisión Cruzada
```bash
python3 src/verificar_ficha_completa.py
```
*Verifica que no queden pendientes, que todos los ítems tengan CA, que exista el caso negativo y que la revisión entre pares contenga al menos 2 decisiones documentadas.*

### C. Generar o Actualizar el Diagrama de Arquitectura
```bash
python3 src/generar_diagrama.py
```

---

## 3. Commit Final del Hito U3.1
Una vez que el script `python3 src/verificar_ficha_completa.py` retorne `✓ APROBADO`:
```bash
git add docs/ficha_diseno_funcional.md docs/diagrama_arquitectura.png docs/revision_alcance.md src/
git commit -m "completa la ficha de diseno funcional con criterios, plan por hitos y revision cruzada"
git push
```
