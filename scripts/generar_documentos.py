#!/usr/bin/env python3
"""
Genera los documentos del proceso de reclutamiento con la lista REAL y
priorizada de universidades (data/universidades_objetivo.json):

  - Tabla de universidades objetivo (.docx y .xlsx), ordenada por prioridad
  - Cartas de reclutamiento (.docx) en lote para las universidades de
    prioridad ALTA que tengan coach
  - Plan de nutrición (.pdf)

Requiere python-docx, openpyxl y fpdf2 (pip install -r requirements.txt).
Si falta una librería, ese documento se salta con aviso (no aborta).

Uso:
    python3 scripts/generar_documentos.py
    python3 scripts/generar_documentos.py --prioridad alta media   # más cartas
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import DATA, RAIZ  # noqa: E402

SALIDA = RAIZ / "documentos_generados"
_ORDEN_PRIORIDAD = {"alta": 0, "media": 1, "baja": 2, "": 3}


def _intentar(nombre: str, fn) -> None:
    try:
        ruta = fn()
        print(f"OK   {nombre}: {ruta}")
    except ImportError as e:
        print(f"SKIP {nombre}: falta librería ({e.name}). pip install -r requirements.txt")
    except BaseException as e:  # noqa: BLE001  (incluye panics de libs nativas p.ej. fpdf/cffi)
        print(f"ERR  {nombre}: {type(e).__name__}: {e}")


def _slug(texto: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", texto.lower()).strip("_")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prioridad", nargs="+", default=["alta"],
                        help="Prioridades para las que generar cartas (default: alta)")
    args = parser.parse_args()

    SALIDA.mkdir(exist_ok=True)
    universidades = json.loads((DATA / "universidades_objetivo.json").read_text())
    universidades.sort(key=lambda u: (_ORDEN_PRIORIDAD.get(u.get("prioridad", ""), 3),
                                      u.get("universidad", "")))
    tiempos = json.loads((DATA / "tiempos_ejemplo.json").read_text())

    # 1) Tabla de universidades (Word + Excel)
    from documentos.tabla_universidades import generar_docx, generar_xlsx
    _intentar("Tabla universidades (docx)",
              lambda: generar_docx(universidades, SALIDA / "universidades_objetivo.docx"))
    _intentar("Tabla universidades (xlsx)",
              lambda: generar_xlsx(universidades, SALIDA / "universidades_objetivo.xlsx"))

    # 2) Cartas de reclutamiento en lote
    from documentos.carta_reclutamiento import DatosAtleta, generar_carta
    atleta = DatosAtleta(
        email="carlos.moreno@tidmexico.com.mx",
        mejores_tiempos=[f"{t['prueba']} {t['curso']} — {t['tiempo']}" for t in tiempos[:6]],
    )
    prioridades = set(args.prioridad)
    objetivo_cartas = [u for u in universidades
                       if u.get("prioridad") in prioridades and u.get("coach")]
    cartas_dir = SALIDA / "cartas"
    cartas_dir.mkdir(exist_ok=True)
    print(f"\nGenerando cartas para {len(objetivo_cartas)} universidades "
          f"(prioridad {', '.join(sorted(prioridades))})...")
    for u in objetivo_cartas:
        destino = cartas_dir / f"carta_{_slug(u['universidad'])}.docx"
        _intentar(f"Carta {u['universidad']}",
                  lambda u=u, destino=destino: generar_carta(
                      u["coach"], u["universidad"], atleta, destino))

    # 3) Plan de nutrición (PDF)
    from documentos.nutricion_pdf import generar_pdf_nutricion
    plan = {
        "calorias": 3500,
        "macros": {"proteina_g": 180, "carbos_g": 450, "grasa_g": 90},
        "comidas": [
            {"nombre": "Desayuno", "items": ["Avena con fruta", "Huevos", "Yogur griego"]},
            {"nombre": "Comida", "items": ["Pollo", "Arroz", "Verduras"]},
            {"nombre": "Post-entreno", "items": ["Batido de proteína", "Plátano"]},
        ],
        "suplementos": [
            {"nombre": "Creatina", "dosis": "5 g/día"},
            {"nombre": "Vitamina D", "dosis": "2000 UI/día"},
            {"nombre": "Omega-3", "dosis": "2 g/día"},
        ],
    }
    _intentar("Plan nutrición (pdf)",
              lambda: generar_pdf_nutricion(plan, SALIDA / "nutricion.pdf"))


if __name__ == "__main__":
    main()
