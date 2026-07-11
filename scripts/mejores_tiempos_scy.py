#!/usr/bin/env python3
"""
Toma los tiempos de un nadador, elige por prueba la mejor marca (mayor puntaje
FINA, sea CL/LCM o CC/SCM) y la convierte a Yardas Cortas (SCY). Escribe:
  - data/tiempos_gael_scy.json   (formato consumible por fit_por_prueba.py)
  - registros/mejores_tiempos_scy.md

Uso:
    python3 scripts/mejores_tiempos_scy.py --tiempos data/tiempos_gael_pb.json
    # y luego el fit:
    python3 scripts/fit_por_prueba.py --tiempos data/tiempos_gael_scy.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import DATA, REGISTROS                      # noqa: E402
from natacion.conversion import mejores_marcas_scy       # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tiempos", default=str(DATA / "tiempos_gael_pb.json"))
    args = parser.parse_args()

    datos = json.loads(Path(args.tiempos).read_text())
    tiempos = datos.get("pb") or datos.get("tiempos") or []
    advertencia = datos.get("ADVERTENCIA")

    # SCY directo por prueba (referencia; suele ser marca de carga/entrenamiento)
    from natacion.fit import canonical_evento, parse_tiempo, formato_tiempo
    scy_directo: dict[str, str] = {}
    for t in tiempos:
        if t.get("curso") == "SCY":
            ev = canonical_evento(t.get("evento", "")) or t.get("evento", "")
            seg = parse_tiempo(t.get("tiempo", ""))
            prev = scy_directo.get(ev)
            if prev is None or seg < parse_tiempo(prev):
                scy_directo[ev] = formato_tiempo(seg)

    marcas = mejores_marcas_scy(tiempos)

    # Guardar en formato de fit (curso SCY)
    salida = {
        "nadador": datos.get("nadador", "Gael Moreno Sarmiento"),
        "fuente": f"Mejores marcas (FINA) convertidas a SCY desde {Path(args.tiempos).name}",
        "tiempos": [{"evento": m.evento, "curso": "SCY", "tiempo": m.tiempo_scy,
                     "origen": f"{m.tiempo_origen} {m.curso_origen}", "puntos": m.puntos}
                    for m in marcas],
    }
    if advertencia:
        salida["ADVERTENCIA"] = advertencia
    (DATA / "tiempos_gael_scy.json").write_text(json.dumps(salida, indent=2, ensure_ascii=False))

    # Reporte
    L = ["# Mejores marcas por prueba → convertidas a SCY (yardas)", ""]
    if advertencia:
        L += [f"> ⚠️ **{advertencia}**", ""]
    L += ["_Por prueba se toma la mejor marca (CL/CC/SCY) y se expresa en SCY. Las "
          "marcas métricas suelen ser descendidas (tapered); el 'SCY directo' suele "
          "ser de carga de temporada. Conversiones aproximadas (factores editables)._", "",
          "| Prueba | Mejor marca (origen) | Curso | Puntos FINA | → SCY (yds) | SCY directo (ref.) |",
          "|---|---|---|---|---|---|"]
    for m in marcas:
        ref = scy_directo.get(m.evento, "-")
        conv = "" if m.curso_origen == "SCY" else "≈ "
        L.append(f"| {m.evento} | {m.tiempo_origen} | {m.curso_origen} | {m.puntos or '-'} "
                 f"| **{conv}{m.tiempo_scy}** | {ref} |")
    (REGISTROS / "mejores_tiempos_scy.md").write_text("\n".join(L) + "\n")

    print(f"{len(marcas)} pruebas convertidas a SCY.")
    for m in marcas[:12]:
        print(f"  {m.evento:11} {m.tiempo_origen:8} {m.curso_origen}  "
              f"({m.puntos or '-'} pts) → SCY {m.tiempo_scy}")
    print("\nEscritos: data/tiempos_gael_scy.json, registros/mejores_tiempos_scy.md")
    if advertencia:
        print(f"⚠️  {advertencia}")


if __name__ == "__main__":
    main()
