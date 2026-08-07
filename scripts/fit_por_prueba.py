#!/usr/bin/env python3
"""
Fit por prueba: compara los tiempos de Gael contra los estándares de NCSA y
escribe registros/fit_por_prueba.md.

Uso:
    python3 scripts/fit_por_prueba.py                       # usa data/tiempos_gael_pb.json
    python3 scripts/fit_por_prueba.py --tiempos data/mis_tiempos.json

IMPORTANTE: por defecto usa los PB de 2017-2018 (desactualizados). Para un
análisis útil, pasa un archivo con los tiempos ACTUALES de Gael (mismo formato:
lista bajo la clave "pb" con evento/curso/tiempo).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import DATA, REGISTROS                         # noqa: E402
from natacion.fit import cargar_estandares, evaluar_fit    # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tiempos", default=str(DATA / "tiempos_gael_pb.json"),
                        help="Archivo JSON con los tiempos del nadador")
    args = parser.parse_args()

    datos_std = json.loads((DATA / "estandares_ncsa.json").read_text())
    datos_nadador = json.loads(Path(args.tiempos).read_text())

    idx = cargar_estandares(datos_std)
    tiempos = datos_nadador.get("pb") or datos_nadador.get("tiempos") or []
    fits = evaluar_fit(tiempos, idx)

    cumplidos = [f for f in fits if f.cumple]
    advertencia = datos_nadador.get("ADVERTENCIA")

    L = ["# Fit por prueba — Gael vs estándares NCSA", ""]
    if advertencia:
        L += [f"> ⚠️ **{advertencia}**", ""]
    L += [f"- Estándar: {datos_std['fuente']}",
          f"- _{datos_std['nota']}_",
          f"- Pruebas evaluadas: **{len(fits)}** | cumple el corte: **{len(cumplidos)}**",
          "",
          "| Prueba | Curso | Tiempo Gael | Estándar NCSA | Δ (s) | % sobre corte | ¿Cumple? |",
          "|---|---|---|---|---|---|---|"]
    for f in fits:
        signo = "" if f.delta_seg < 0 else "+"
        L.append(f"| {f.evento} | {f.curso} | {f.tiempo_nadador} | {f.tiempo_estandar} "
                 f"| {signo}{f.delta_seg} | {signo}{f.pct_off}% | {'✅' if f.cumple else '❌'} |")
    (REGISTROS / "fit_por_prueba.md").write_text("\n".join(L) + "\n")

    print(f"Evaluadas {len(fits)} pruebas; cumple {len(cumplidos)}.")
    if advertencia:
        print(f"⚠️  {advertencia}")
    print("Pruebas más cercanas al corte NCSA:")
    for f in fits[:5]:
        signo = "" if f.delta_seg < 0 else "+"
        print(f"  {f.evento:10} {f.curso}  Gael {f.tiempo_nadador:8} vs {f.tiempo_estandar:8} "
              f"({signo}{f.pct_off}%) {'CUMPLE' if f.cumple else ''}")
    print("\nEscrito: registros/fit_por_prueba.md")


if __name__ == "__main__":
    main()
