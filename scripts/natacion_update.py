#!/usr/bin/env python3
"""
Actualiza registros/natacion.md con los mejores tiempos.

Entry point más fácil del proyecto: NO requiere credenciales para el perfil
público de SwimCloud.

El ID de SwimCloud de Gael se toma de data/gael.json (swimcloud_id) si no se
pasa --swimmer. Además de registros/natacion.md, escribe
data/tiempos_gael_swimcloud.json en el formato que consume scripts/fit_por_prueba.py.

Uso:
    # Con datos de ejemplo (sin red):
    python3 scripts/natacion_update.py --ejemplo

    # En vivo, contra el perfil de Gael (usa data/gael.json):
    python3 scripts/natacion_update.py

    # Otro nadador:
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


def _id_gael() -> str | None:
    try:
        return json.loads((DATA / "gael.json").read_text()).get("swimcloud_id")
    except FileNotFoundError:
        return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Actualiza registros/natacion.md")
    parser.add_argument("--swimmer", help="ID de SwimCloud (default: el de data/gael.json)")
    parser.add_argument("--ejemplo", action="store_true", help="Usar data/tiempos_ejemplo.json")
    args = parser.parse_args()

    swimmer = args.swimmer or (None if args.ejemplo else _id_gael())

    if swimmer:
        from natacion.swimcloud import obtener_tiempos
        print(f"Descargando tiempos de SwimCloud (swimmer {swimmer})...")
        tiempos = obtener_tiempos(swimmer)
    else:
        print("Modo ejemplo: usando data/tiempos_ejemplo.json")
        crudos = json.loads((DATA / "tiempos_ejemplo.json").read_text())
        tiempos = [Tiempo(**t) for t in crudos]

    destino = escribir_natacion_md(tiempos, REGISTROS / "natacion.md")
    print(f"{len(tiempos)} tiempos escritos en {destino}")

    # JSON para el motor de fit (evento/curso/tiempo)
    fit_json = DATA / "tiempos_gael_swimcloud.json"
    fit_json.write_text(json.dumps({
        "nadador": "Gael Moreno Sarmiento",
        "fuente": f"SwimCloud swimmer {swimmer}" if swimmer else "ejemplo",
        "tiempos": [{"evento": t.prueba, "curso": t.curso, "tiempo": t.tiempo} for t in tiempos],
    }, indent=2, ensure_ascii=False))
    print(f"Tiempos para fit en {fit_json}  →  "
          f"python3 scripts/fit_por_prueba.py --tiempos {fit_json.relative_to(DATA.parent)}")


if __name__ == "__main__":
    main()
