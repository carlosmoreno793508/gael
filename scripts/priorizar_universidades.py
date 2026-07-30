#!/usr/bin/env python3
"""
Prioriza las universidades objetivo y rellena el campo `prioridad` en
data/universidades_objetivo.json, además de escribir un reporte legible.

Uso:
    python3 scripts/priorizar_universidades.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import DATA, REGISTROS               # noqa: E402
from reclutamiento.priorizar import priorizar     # noqa: E402

OBJETIVO = DATA / "universidades_objetivo.json"


def main() -> None:
    universidades = json.loads(OBJETIVO.read_text())
    anotadas = priorizar(universidades)

    # Rellenar prioridad (y estatus por defecto) en el archivo oficial
    prioridad_por_uni = {a["universidad"]: a["prioridad"] for a in anotadas}
    for u in universidades:
        u["prioridad"] = prioridad_por_uni.get(u["universidad"], u.get("prioridad", ""))
        if not u.get("estatus"):
            u["estatus"] = "por contactar"
    OBJETIVO.write_text(json.dumps(universidades, indent=2, ensure_ascii=False))

    # Conteos
    from collections import Counter
    por_prioridad = Counter(a["prioridad"] for a in anotadas)
    por_fit = Counter(a["fit"] for a in anotadas)

    # Reporte
    L = ["# Priorización de universidades objetivo — Gael", "",
         "_Heurística basada en división + ranking del equipo + posibilidad de "
         "beca. NO compara tiempos de Gael contra estándares por universidad "
         "(pendiente sumar esa fuente)._", "",
         f"- Total: **{len(anotadas)}**",
         "- Por prioridad: " + ", ".join(f"{k}: {v}" for k, v in por_prioridad.most_common()),
         "- Por fit: " + ", ".join(f"{k}: {v}" for k, v in por_fit.most_common()),
         "",
         "| # | Universidad | Div | Rank | Beca | Fit | Prioridad | Coach |",
         "|---|---|---|---|---|---|---|---|"]
    for i, a in enumerate(anotadas, 1):
        L.append(f"| {i} | {a['universidad']} | {a['division']} | {a.get('rank_div') or '-'} "
                 f"| {'Sí' if a['beca'] else 'No'} | {a['fit']} | {a['prioridad']} "
                 f"| {a.get('coach') or '-'} |")
    (REGISTROS / "priorizacion.md").write_text("\n".join(L) + "\n")

    print(f"Priorizadas {len(anotadas)} universidades → {por_prioridad}")
    print("Top 8 recomendadas para contactar primero:")
    for a in anotadas[:8]:
        print(f"  [{a['prioridad']:5}] {a['universidad']:38} {a['division']:8} "
              f"{a['fit']:18} coach={a.get('coach') or '-'}")
    print("\nEscritos: data/universidades_objetivo.json (con prioridad), "
          "registros/priorizacion.md")


if __name__ == "__main__":
    main()
