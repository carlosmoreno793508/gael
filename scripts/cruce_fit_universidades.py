#!/usr/bin/env python3
"""
Cruza el fit de tiempos de Gael con las universidades objetivo y re-prioriza.

Encadena: data/tiempos_gael_scy.json + data/estandares_ncsa.json (fit) con
data/universidades_objetivo.json. Escribe:
  - data/universidades_objetivo.json  (actualiza prioridad + fit_tiempos)
  - registros/cruce_fit_universidades.md

Uso:
    python3 scripts/cruce_fit_universidades.py
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import DATA, REGISTROS                          # noqa: E402
from natacion.fit import cargar_estandares, evaluar_fit      # noqa: E402
from reclutamiento.cruce_fit import nivel_atleta, cruzar     # noqa: E402


def main() -> None:
    # 1) Fit de Gael
    estandares = json.loads((DATA / "estandares_ncsa.json").read_text())
    scy = json.loads((DATA / "tiempos_gael_scy.json").read_text())
    idx = cargar_estandares(estandares)
    fits = evaluar_fit(scy.get("tiempos", []), idx)
    cumplidos = [f for f in fits if f.cumple]
    nivel = nivel_atleta(len(cumplidos))
    fuertes = ", ".join(f.evento for f in cumplidos) or "-"

    # 2) Cruce con universidades
    universidades = json.loads((DATA / "universidades_objetivo.json").read_text())
    cruzadas = cruzar(universidades, nivel)

    # actualizar el archivo oficial con prioridad + fit_tiempos
    por_uni = {c["universidad"]: c for c in cruzadas}
    for u in universidades:
        c = por_uni.get(u["universidad"])
        if c:
            u["prioridad"] = c["prioridad"]
            u["fit_tiempos"] = c["fit_tiempos"]
    (DATA / "universidades_objetivo.json").write_text(
        json.dumps(universidades, indent=2, ensure_ascii=False))

    por_prioridad = Counter(c["prioridad"] for c in cruzadas)

    # 3) Reporte
    L = ["# Cruce fit de tiempos × universidades objetivo — Gael", "",
         f"- Nivel estimado del atleta: **{nivel}** "
         f"(cumple el corte élite NCSA en {len(cumplidos)} pruebas: {fuertes})",
         f"- Prioridades tras el cruce: " +
         ", ".join(f"{k}: {v}" for k, v in por_prioridad.most_common()),
         "",
         "> El fit por-universidad se estima con nivel del atleta + división + "
         "ranking del equipo (no hay cortes de reclutamiento por escuela). Guía, "
         "no veredicto.",
         "",
         "| # | Universidad | Div | Rank | Fit de tiempos | Prioridad | Coach |",
         "|---|---|---|---|---|---|---|"]
    for i, c in enumerate(cruzadas, 1):
        L.append(f"| {i} | {c['universidad']} | {c['division']} | {c.get('rank_div') or '-'} "
                 f"| {c['fit_tiempos']} | {c['prioridad']} | {c.get('coach') or '-'} |")
    (REGISTROS / "cruce_fit_universidades.md").write_text("\n".join(L) + "\n")

    print(f"Nivel del atleta: {nivel} (cumple {len(cumplidos)} pruebas: {fuertes})")
    print(f"Prioridades: {dict(por_prioridad)}")
    print("Top 10 objetivos tras el cruce de tiempos:")
    for c in cruzadas[:10]:
        print(f"  [{c['prioridad']:5}] {c['universidad']:38} {c['division']:8} "
              f"{c['fit_tiempos']}")
    print("\nEscritos: data/universidades_objetivo.json, registros/cruce_fit_universidades.md")


if __name__ == "__main__":
    main()
