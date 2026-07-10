#!/usr/bin/env python3
"""
Actualiza registros/natacion.md con los mejores tiempos.

Entry point más fácil del proyecto: NO requiere credenciales para el perfil
público de SwimCloud.

Uso:
    # Con datos de ejemplo (sin red):
    python3 scripts/natacion_update.py

    # En vivo, contra un perfil público de SwimCloud:
    python3 scripts/natacion_update.py --swimmer 1234567
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import DATA, REGISTROS         # noqa: E402
from natacion.swimcloud import Tiempo      # noqa: E402
from natacion.registro import escribir_natacion_md  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Actualiza registros/natacion.md")
    parser.add_argument("--swimmer", help="ID de SwimCloud (si se omite, usa datos de ejemplo)")
    args = parser.parse_args()

    if args.swimmer:
        from natacion.swimcloud import obtener_tiempos
        print(f"Descargando tiempos de SwimCloud (swimmer {args.swimmer})...")
        tiempos = obtener_tiempos(args.swimmer)
    else:
        print("Sin --swimmer: usando data/tiempos_ejemplo.json")
        crudos = json.loads((DATA / "tiempos_ejemplo.json").read_text())
        tiempos = [Tiempo(**t) for t in crudos]

    destino = escribir_natacion_md(tiempos, REGISTROS / "natacion.md")
    print(f"{len(tiempos)} tiempos escritos en {destino}")


if __name__ == "__main__":
    main()
