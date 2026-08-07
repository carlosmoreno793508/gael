#!/usr/bin/env python3
"""
Sincroniza correos de coaches desde Gmail y genera los reportes de
Universidades y Coaches.

REQUIERE credenciales (gmail_credentials.json + OAuth). Para probar el pipeline
sin credenciales usa scripts/demo_clasificador.py.

Uso:
    python3 scripts/gmail_coaches_sync.py
    python3 scripts/gmail_coaches_sync.py --query 'newer_than:6m from:.edu'

Pendiente: activar por cron (ver README) — aún no está corriendo automático.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import REGISTROS, cargar_env      # noqa: E402
from correos.analisis import analizar, guardar_reportes  # noqa: E402


def main() -> None:
    cargar_env()
    parser = argparse.ArgumentParser(description="Sync de correos de coaches (Gmail)")
    parser.add_argument("--query", help="Query de Gmail personalizada")
    parser.add_argument("--max", type=int, default=200, help="Máx. correos a leer")
    args = parser.parse_args()

    # Import perezoso: sólo aquí se toca la Gmail API.
    from correos.gmail_client import buscar_correos, QUERY_COACHES

    query = args.query or QUERY_COACHES
    print(f"Buscando en Gmail: {query!r}")
    correos = [
        {"remitente": c.remitente, "asunto": c.asunto, "cuerpo": c.cuerpo}
        for c in buscar_correos(query, max_resultados=args.max)
    ]
    print(f"Correos recuperados: {len(correos)}")

    resumen = analizar(correos)
    print("Por categoría:", resumen["por_categoria"])
    print(f"Universidades: {len(resumen['universidades'])} | "
          f"Coaches: {len(resumen['coaches'])}")

    escritos = guardar_reportes(resumen, REGISTROS)
    for p in escritos:
        print("Escrito:", p)


if __name__ == "__main__":
    main()
