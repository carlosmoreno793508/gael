"""
Motor de análisis: toma una lista de correos (crudos o dicts), los clasifica y
produce agregados por Universidad y por Coach, listos para volcar a registros/.

Sin dependencias externas: reutilizable tanto por el demo (datos de ejemplo)
como por el sync real de Gmail.
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Iterable

from correos.clasificador import clasificar_correo


def analizar(correos: Iterable[dict]) -> dict:
    """`correos`: iterables con claves remitente/asunto/cuerpo.
    Devuelve un dict con: total, por_categoria, universidades, coaches, detalle."""
    detalle = []
    por_categoria: dict[str, int] = defaultdict(int)
    universidades: dict[str, dict] = {}
    coaches: dict[str, dict] = {}

    for c in correos:
        r = clasificar_correo(
            c.get("remitente", ""), c.get("asunto", ""), c.get("cuerpo", "")
        )
        por_categoria[r.categoria] += 1
        registro = {**r.to_dict(),
                    "remitente": c.get("remitente", ""),
                    "asunto": c.get("asunto", "")}
        detalle.append(registro)

        if r.universidad and r.categoria in ("COACH", "UNIVERSIDAD"):
            u = universidades.setdefault(r.universidad, {
                "universidad": r.universidad, "division": r.division,
                "correos": 0, "coaches": set(),
            })
            u["correos"] += 1
            u["division"] = u["division"] or r.division
            if r.nombre_coach:
                u["coaches"].add(r.nombre_coach)

        if r.categoria == "COACH" and r.nombre_coach:
            co = coaches.setdefault(r.nombre_coach, {
                "coach": r.nombre_coach, "universidad": r.universidad,
                "division": r.division, "correos": 0,
            })
            co["correos"] += 1

    # sets -> listas para poder serializar a JSON
    for u in universidades.values():
        u["coaches"] = sorted(u["coaches"])

    return {
        "total": len(detalle),
        "por_categoria": dict(por_categoria),
        "universidades": sorted(universidades.values(),
                                key=lambda x: (-x["correos"], x["universidad"])),
        "coaches": sorted(coaches.values(),
                          key=lambda x: (-x["correos"], x["coach"])),
        "detalle": detalle,
    }


def guardar_reportes(resumen: dict, carpeta: Path) -> list[Path]:
    """Vuelca el resumen a registros/: JSON completo + un .md legible."""
    carpeta.mkdir(exist_ok=True)
    escritos = []

    json_path = carpeta / "coaches.json"
    json_path.write_text(json.dumps(resumen, indent=2, ensure_ascii=False))
    escritos.append(json_path)

    md = carpeta / "universidades.md"
    lineas = ["# Universidades y Coaches — actividad de reclutamiento", ""]
    lineas.append(f"- Total correos analizados: **{resumen['total']}**")
    for cat, n in sorted(resumen["por_categoria"].items()):
        lineas.append(f"- {cat}: {n}")
    lineas += ["", "## Universidades", "",
               "| Universidad | División | Correos | Coaches |",
               "|---|---|---|---|"]
    for u in resumen["universidades"]:
        lineas.append(
            f"| {u['universidad']} | {u['division'] or '-'} | {u['correos']} "
            f"| {', '.join(u['coaches']) or '-'} |"
        )
    lineas += ["", "## Coaches", "",
               "| Coach | Universidad | División | Correos |",
               "|---|---|---|---|"]
    for c in resumen["coaches"]:
        lineas.append(
            f"| {c['coach']} | {c['universidad'] or '-'} "
            f"| {c['division'] or '-'} | {c['correos']} |"
        )
    md.write_text("\n".join(lineas) + "\n")
    escritos.append(md)
    return escritos
