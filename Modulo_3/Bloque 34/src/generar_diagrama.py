"""
Genera 'docs/diagrama_arquitectura.png' para el Bloque 34.
"""

import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches

os.makedirs("docs", exist_ok=True)

fig, ax = plt.subplots(figsize=(10, 6), dpi=150)
fig.patch.set_facecolor('#0f172a')
ax.set_facecolor('#0f172a')

boxes = [
    {"label": "Cliente HTTP / Swagger\n(Frontend / Docs)", "x": 0.08, "y": 0.65, "w": 0.22, "h": 0.2, "color": "#1e293b", "border": "#38bdf8"},
    {"label": "FastAPI App\n(api/main.py)\n[Filtro Anti-Inyección & ContextVar]", "x": 0.38, "y": 0.65, "w": 0.26, "h": 0.2, "color": "#1e293b", "border": "#818cf8"},
    {"label": "Pipeline RAG\n(src/rag.py)\n[Delimitación <contexto>]", "x": 0.72, "y": 0.65, "w": 0.22, "h": 0.2, "color": "#1e293b", "border": "#a855f7"},
    {"label": "Vector Store Local\n(Chroma persistido)\n[docs / embeddings]", "x": 0.72, "y": 0.20, "w": 0.22, "h": 0.2, "color": "#1e293b", "border": "#34d399"},
    {"label": "LLM Gateway\n(src/cliente.py)\n[Reintentos & Backoff]", "x": 0.38, "y": 0.20, "w": 0.26, "h": 0.2, "color": "#1e293b", "border": "#f43f5e"},
    {"label": "Observabilidad\n(app_rag.log & costos)\n[JSON Lines con trace_id]", "x": 0.08, "y": 0.20, "w": 0.22, "h": 0.2, "color": "#1e293b", "border": "#fbbf24"},
]

for b in boxes:
    rect = patches.FancyBboxPatch(
        (b["x"], b["y"]), b["w"], b["h"],
        boxstyle="round,pad=0.03,rounding_size=0.04",
        facecolor=b["color"], edgecolor=b["border"], linewidth=2
    )
    ax.add_patch(rect)
    ax.text(
        b["x"] + b["w"]/2, b["y"] + b["h"]/2, b["label"],
        color="#f8fafc", fontsize=9, fontweight="bold",
        ha="center", va="center", multialignment="center"
    )

arrows = [
    ((0.30, 0.75), (0.38, 0.75), "1. Request"),
    ((0.64, 0.75), (0.72, 0.75), "2. Sanitiza"),
    ((0.83, 0.65), (0.83, 0.40), "3. Top-K"),
    ((0.72, 0.30), (0.64, 0.30), "4. Contexto"),
    ((0.38, 0.30), (0.30, 0.30), "5. Auditoría"),
]

for start, end, txt in arrows:
    ax.annotate(
        "", xy=end, xytext=start,
        arrowprops=dict(arrowstyle="->,head_width=0.4,head_length=0.6", color="#94a3b8", lw=2)
    )
    mid_x = (start[0] + end[0]) / 2
    mid_y = (start[1] + end[1]) / 2 + 0.03
    ax.text(mid_x, mid_y, txt, color="#cbd5e1", fontsize=8, ha="center")

ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis("off")

plt.title("Arquitectura del Sistema Capstone (Gate 3)", color="#f8fafc", fontsize=14, pad=15, fontweight="bold")
plt.tight_layout()
plt.savefig("docs/diagrama_arquitectura.png", facecolor=fig.get_facecolor(), edgecolor='none')
plt.close()
print("Diagrama generado exitosamente en 'docs/diagrama_arquitectura.png'")
