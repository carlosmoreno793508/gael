#!/usr/bin/env python3
"""
Entra a NCSA (login con Selenium), lee la actividad de reclutamiento (qué
coaches/universidades vieron el perfil o escribieron) y guarda:
  - registros/ncsa_actividad.json
  - registros/ncsa_actividad.md

REQUIERE (en la Mac, red abierta):
  - Chrome + ChromeDriver de la MISMA versión
  - .env con NCSA_EMAIL y NCSA_PASSWORD

Uso:
    python3 scripts/ncsa_sync.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import REGISTROS, cargar_env       # noqa: E402


def main() -> None:
    cargar_env()  # lee NCSA_EMAIL / NCSA_PASSWORD / CHROMEDRIVER_PATH desde .env
    from ncsa.scraper import sincronizar_ncsa

    print("Entrando a NCSA y leyendo actividad de reclutamiento...")
    actividad = sincronizar_ncsa()
    datos = [a.to_dict() for a in actividad]

    (REGISTROS / "ncsa_actividad.json").write_text(
        json.dumps(datos, indent=2, ensure_ascii=False))

    L = ["# Actividad de reclutamiento en NCSA", "",
         f"- Eventos leídos: **{len(datos)}**", "",
         "| Coach | Universidad | Tipo | Fecha |", "|---|---|---|---|"]
    for a in datos:
        L.append(f"| {a.get('coach') or '-'} | {a.get('universidad') or '-'} "
                 f"| {a.get('tipo_evento') or '-'} | {a.get('fecha') or '-'} |")
    (REGISTROS / "ncsa_actividad.md").write_text("\n".join(L) + "\n")

    print(f"{len(datos)} eventos guardados en registros/ncsa_actividad.json y .md")
    for a in datos[:15]:
        print(f"  {a.get('fecha') or '-':12} {a.get('universidad') or '-':28} "
              f"{a.get('coach') or '-':22} {a.get('tipo_evento') or ''}")
    if not datos:
        print("\n(0 eventos: revisa que el login fue exitoso y que los selectores de "
              "ncsa/scraper.py coincidan con el HTML actual de NCSA — pueden requerir ajuste.)")


if __name__ == "__main__":
    main()
