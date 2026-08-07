"""
Genera un PDF de plan de nutrición / suplementación con fpdf2.

Recibe una estructura de comidas y suplementos y produce un PDF simple y
legible. Importación perezosa de fpdf.
"""
from __future__ import annotations

from pathlib import Path


def generar_pdf_nutricion(plan: dict, destino: Path,
                          nombre: str = "Gael Moreno Sarmiento") -> Path:
    """`plan` = {
        'calorias': 3500,
        'macros': {'proteina_g': 180, 'carbos_g': 450, 'grasa_g': 90},
        'comidas': [{'nombre': 'Desayuno', 'items': ['Avena', 'Huevos']}, ...],
        'suplementos': [{'nombre': 'Creatina', 'dosis': '5 g/día'}, ...],
    }"""
    from fpdf import FPDF

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, f"Plan de nutricion - {nombre}", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, f"Objetivo calorico: {plan.get('calorias', '-')} kcal/dia",
             new_x="LMARGIN", new_y="NEXT")
    macros = plan.get("macros", {})
    if macros:
        pdf.cell(0, 8, "Macros: " + ", ".join(f"{k}: {v}" for k, v in macros.items()),
                 new_x="LMARGIN", new_y="NEXT")

    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 9, "Comidas", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    for comida in plan.get("comidas", []):
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 7, str(comida.get("nombre", "")), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 11)
        for item in comida.get("items", []):
            pdf.cell(0, 6, f"  - {item}", new_x="LMARGIN", new_y="NEXT")

    supl = plan.get("suplementos", [])
    if supl:
        pdf.ln(2)
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 9, "Suplementacion", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 11)
        for s in supl:
            pdf.cell(0, 6, f"  - {s.get('nombre','')}: {s.get('dosis','')}",
                     new_x="LMARGIN", new_y="NEXT")

    pdf.output(str(destino))
    return destino
