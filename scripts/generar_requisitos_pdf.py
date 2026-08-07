#!/usr/bin/env python3
"""
Genera el PDF de requisitos (SAT / Duolingo / TOEFL) por universidad.

Fuentes:
  - data/universidades_requisitos.json  (datos PUBLICOS de las unis)
  - .env: GAEL_SAT, GAEL_DUOLINGO_META   (datos personales de Gael, privados)

Salida:
  - documentos_generados/Gael_Universidades_SAT_Duolingo_TOEFL.pdf

Uso:
    python3 scripts/generar_requisitos_pdf.py
"""
from __future__ import annotations

import json
import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ENV_PATH = RAIZ / ".env"
DATA_PATH = RAIZ / "data" / "universidades_requisitos.json"
SALIDA = RAIZ / "documentos_generados"

NAVY = "#1b2a4a"
ROJO = "#c0392b"
VERDE = "#1e7d34"
NARANJA = "#d68910"
GRIS = "#6b7280"


def esc(s) -> str:
    """Escapa caracteres especiales para los Paragraph de reportlab (& < >)."""
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def cargar_env() -> None:
    if not ENV_PATH.exists():
        return
    for linea in ENV_PATH.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        k, _, v = linea.partition("=")
        os.environ.setdefault(k.strip(), v.strip())


def color_duolingo(u: dict) -> str:
    val = str(u.get("duolingo", ""))
    if u.get("duolingo_acepta") is False or val.lower().startswith("no acepta"):
        return ROJO
    if val.lower().startswith("verificar") or u.get("duolingo_acepta") is None:
        return NARANJA
    if val.lower().startswith("acepta"):
        return NARANJA
    return VERDE


def generar(destino: Path | None = None) -> Path:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
    )

    cargar_env()
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    unis = data["universidades"]
    sat_gael = os.environ.get("GAEL_SAT", "—")
    meta_duo = os.environ.get("GAEL_DUOLINGO_META", "—")

    SALIDA.mkdir(exist_ok=True)
    destino = destino or (SALIDA / "Gael_Universidades_SAT_Duolingo_TOEFL.pdf")

    est_uni = ParagraphStyle("uni", fontName="Helvetica-Bold", fontSize=9, leading=11)
    est_sat = ParagraphStyle("sat", fontName="Helvetica-Bold", fontSize=9, leading=11, alignment=1)
    est_pol = ParagraphStyle("pol", fontName="Helvetica", fontSize=6.5, leading=8, textColor=colors.HexColor(GRIS), alignment=1)
    est_cel = ParagraphStyle("cel", fontName="Helvetica-Bold", fontSize=9, leading=11, alignment=1)
    est_head = ParagraphStyle("head", fontName="Helvetica-Bold", fontSize=9, leading=11, textColor=colors.white, alignment=1)
    est_head_l = ParagraphStyle("headl", fontName="Helvetica-Bold", fontSize=9, leading=11, textColor=colors.white)
    est_titulo = ParagraphStyle("tit", fontName="Helvetica-Bold", fontSize=18, leading=22, textColor=colors.white, alignment=1)
    est_sub = ParagraphStyle("sub", fontName="Helvetica", fontSize=9.5, leading=13, textColor=colors.HexColor("#c7d2e2"), alignment=1)
    est_intro = ParagraphStyle("intro", fontName="Helvetica", fontSize=8.5, leading=12, textColor=colors.HexColor("#333333"))
    est_nota = ParagraphStyle("nota", fontName="Helvetica", fontSize=7, leading=9.5, textColor=colors.HexColor("#555555"))

    # Banda de titulo
    banda = Table(
        [[Paragraph("Gael Moreno Sarmiento", est_titulo)],
         [Paragraph("SAT &middot; Duolingo &middot; TOEFL &mdash; puntajes m&iacute;nimos (pregrado internacional)", est_sub)]],
        colWidths=[180 * mm],
    )
    banda.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(NAVY)),
        ("TOPPADDING", (0, 0), (-1, 0), 10), ("BOTTOMPADDING", (0, 1), (-1, 1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))

    intro = Paragraph(
        f"SAT actual de Gael: <b>{sat_gael}</b> &middot; meta Duolingo <b>{meta_duo}</b>. "
        "La columna SAT muestra el rango de admitidos (medio 50%) con la etiqueta de si es "
        "opcional u obligatorio. En rojo, las que exigen SAT por encima del actual de Gael. "
        "Duolingo en rojo = no acepta DET (solo TOEFL/IELTS).",
        est_intro,
    )

    # Tabla principal
    filas = [[
        Paragraph("Universidad", est_head_l),
        Paragraph("SAT", est_head),
        Paragraph("Duolingo", est_head),
        Paragraph("TOEFL iBT", est_head),
    ]]
    for u in unis:
        sat_col = colors.HexColor(ROJO) if u.get("sat_bloqueante") else colors.HexColor("#1b2a4a")
        est_sat_c = ParagraphStyle("satc", parent=est_sat, textColor=sat_col)
        est_duo_c = ParagraphStyle("duoc", parent=est_cel, textColor=colors.HexColor(color_duolingo(u)))
        filas.append([
            Paragraph(esc(u["universidad"]), est_uni),
            [Paragraph(esc(u.get("sat", "-")), est_sat_c),
             Paragraph(esc(u.get("sat_politica", "")), est_pol)],
            Paragraph(esc(u.get("duolingo", "-")), est_duo_c),
            Paragraph(esc(u.get("toefl_ibt", "-")), est_cel),
        ])

    tabla = Table(filas, colWidths=[78 * mm, 40 * mm, 32 * mm, 30 * mm], repeatRows=1)
    estilo = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(NAVY)),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.HexColor("#e2e6ec")),
    ]
    for i in range(1, len(filas)):
        if i % 2 == 0:
            estilo.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#f5f7fa")))
    tabla.setStyle(TableStyle(estilo))

    notas = [
        "El SAT es el rango del medio 50% de admitidos (Common Data Set / fuentes publicas); 'opcional' = no lo exigen, es solo referencia.",
        "Duolingo (verde) = acepta DET; el numero es el minimo. La meta de Gael supera todos los minimos que aceptan DET.",
        "'No acepta' (rojo) = solo aceptan TOEFL iBT o IELTS.",
        "SAT en rojo = exigen SAT por encima del actual de Gael (bloqueante).",
        "TOEFL '~ (s/min.)' = no publican piso rigido; es el nivel competitivo orientativo (escala 0-120).",
        f"Fuentes: {data.get('fuente', '')}",
    ]

    doc = SimpleDocTemplate(
        str(destino), pagesize=letter,
        leftMargin=15 * mm, rightMargin=15 * mm, topMargin=13 * mm, bottomMargin=13 * mm,
    )
    elems = [banda, Spacer(1, 8), intro, Spacer(1, 8), tabla, Spacer(1, 8)]
    for n in notas:
        elems.append(Paragraph("&bull; " + n, est_nota))
    doc.build(elems)
    return destino


if __name__ == "__main__":
    ruta = generar()
    print(f"PDF generado: {ruta}")
