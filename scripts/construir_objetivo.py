#!/usr/bin/env python3
"""
Construye la lista OFICIAL de universidades objetivo del proyecto a partir de
las fuentes reales de Karla (NCSA + SwimCloud + Contactos Colegios) y la
escribe en data/universidades_objetivo.json.

Reemplaza la antigua lista de ejemplo (coaches ficticios) por los datos reales.

Uso:
    python3 scripts/construir_objetivo.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import DATA                              # noqa: E402
from reclutamiento.universidades import construir_maestro  # noqa: E402

DESTINO = DATA / "universidades_objetivo.json"


def main() -> None:
    gm = json.loads((DATA / "karla_gm_us_univ.json").read_text())
    contactos = json.loads((DATA / "karla_contactos_colegios.json").read_text())

    maestro = construir_maestro(gm, contactos)
    DESTINO.write_text(json.dumps(maestro, indent=2, ensure_ascii=False))

    por_div: dict[str, int] = {}
    for m in maestro:
        por_div[m["division"]] = por_div.get(m["division"], 0) + 1

    print(f"Escrito {DESTINO.relative_to(DATA.parent)} con {len(maestro)} universidades")
    print("Por división:", por_div)
    con_email = sum(1 for m in maestro if m["email"])
    print(f"Con email de coach: {con_email}/{len(maestro)}")


if __name__ == "__main__":
    main()
