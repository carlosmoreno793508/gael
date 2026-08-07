#!/usr/bin/env python3
"""
Demo del pipeline de análisis de correos — SIN credenciales.

Lee data/correos_ejemplo.json, clasifica cada correo (Coach / Universidad /
Plataforma / Otro), imprime el resumen y escribe los reportes en registros/.

Punto de entrada más fácil para probar el proyecto:
    python3 scripts/demo_clasificador.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import DATA, REGISTROS           # noqa: E402
from correos.analisis import analizar, guardar_reportes  # noqa: E402


def main() -> None:
    correos = json.loads((DATA / "correos_ejemplo.json").read_text())
    resumen = analizar(correos)

    print(f"Correos analizados: {resumen['total']}")
    print("Por categoría:", resumen["por_categoria"])
    print("\nUniversidades detectadas:")
    for u in resumen["universidades"]:
        print(f"  - {u['universidad']:12} {u['division'] or '':8} "
              f"({u['correos']} correo/s) coaches={u['coaches'] or '-'}")
    print("\nCoaches detectados:")
    for c in resumen["coaches"]:
        print(f"  - {c['coach']:14} {c['universidad'] or '-':10} {c['division'] or ''}")

    escritos = guardar_reportes(resumen, REGISTROS)
    print("\nReportes escritos:")
    for p in escritos:
        print(f"  - {p.relative_to(Path(__file__).resolve().parent.parent)}")


if __name__ == "__main__":
    main()
