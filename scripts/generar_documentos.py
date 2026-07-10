#!/usr/bin/env python3
"""
Genera los documentos del proceso de reclutamiento:
  - Tabla de universidades objetivo (.docx y .xlsx)
  - Carta de reclutamiento de ejemplo (.docx)
  - Plan de nutrición (.pdf)

Requiere python-docx, openpyxl y fpdf2 (pip install -r requirements.txt).
Si falta alguna librería, ese documento se salta con un aviso (no aborta).

Uso:
    python3 scripts/generar_documentos.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import DATA, RAIZ  # noqa: E402

SALIDA = RAIZ / "documentos_generados"


def _intentar(nombre: str, fn) -> None:
    try:
        ruta = fn()
        print(f"OK   {nombre}: {ruta}")
    except ImportError as e:
        print(f"SKIP {nombre}: falta librería ({e.name}). pip install -r requirements.txt")
    except Exception as e:  # noqa: BLE001
        print(f"ERR  {nombre}: {e}")


def main() -> None:
    SALIDA.mkdir(exist_ok=True)
    universidades = json.loads((DATA / "universidades_objetivo.json").read_text())
    tiempos = json.loads((DATA / "tiempos_ejemplo.json").read_text())

    from documentos.tabla_universidades import generar_docx, generar_xlsx
    _intentar("Tabla universidades (docx)",
              lambda: generar_docx(universidades, SALIDA / "universidades.docx"))
    _intentar("Tabla universidades (xlsx)",
              lambda: generar_xlsx(universidades, SALIDA / "universidades.xlsx"))

    from documentos.carta_reclutamiento import DatosAtleta, generar_carta
    atleta = DatosAtleta(
        email="carlos.moreno@tidmexico.com.mx",
        mejores_tiempos=[f"{t['prueba']} {t['curso']} — {t['tiempo']}" for t in tiempos[:5]],
    )
    _intentar("Carta reclutamiento (docx)",
              lambda: generar_carta("Jane Doe", "Stanford University", atleta,
                                    SALIDA / "carta_stanford.docx"))

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
