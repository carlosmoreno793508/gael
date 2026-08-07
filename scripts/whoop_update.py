#!/usr/bin/env python3
"""
Actualiza registros/whoop.md con las últimas recuperaciones de WHOOP.

Uso:
    python3 scripts/whoop_update.py            # datos de ejemplo (sin credenciales)
    python3 scripts/whoop_update.py --live     # WHOOP API (requiere .env)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import DATA, REGISTROS, cargar_env   # noqa: E402
from whoop.client import Recuperacion             # noqa: E402


def _emoji(score) -> str:
    if score is None:
        return "•"
    return "🟢" if score >= 67 else "🟡" if score >= 34 else "🔴"


def escribir_md(recs: list[Recuperacion], destino: Path) -> Path:
    lineas = ["# Registro WHOOP — recuperación", "",
              "| Fecha | Recovery | Estado | HRV (ms) | RHR (bpm) |",
              "|---|---|---|---|---|"]
    for r in recs:
        lineas.append(
            f"| {r.fecha} | {r.recovery_score if r.recovery_score is not None else '-'} "
            f"| {_emoji(r.recovery_score)} | {r.hrv_ms or '-'} | {r.rhr_bpm or '-'} |"
        )
    destino.write_text("\n".join(lineas) + "\n")
    return destino


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", help="Usar la API real de WHOOP")
    args = parser.parse_args()

    if args.live:
        cargar_env()
        from whoop.client import obtener_recuperacion
        recs = obtener_recuperacion(limite=14)
    else:
        print("Modo ejemplo: data/whoop_ejemplo.json")
        recs = [Recuperacion(**r) for r in json.loads((DATA / "whoop_ejemplo.json").read_text())]

    destino = escribir_md(recs, REGISTROS / "whoop.md")
    print(f"{len(recs)} recuperaciones escritas en {destino}")


if __name__ == "__main__":
    main()
