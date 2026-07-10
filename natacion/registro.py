"""Genera/actualiza registros/natacion.md a partir de una lista de tiempos."""
from __future__ import annotations

from pathlib import Path

from natacion.swimcloud import Tiempo

# Orden canónico de pruebas para la tabla
ORDEN_PRUEBAS = [
    "50 Free", "100 Free", "200 Free", "400 Free", "800 Free", "1500 Free",
    "50 Back", "100 Back", "200 Back",
    "50 Breast", "100 Breast", "200 Breast",
    "50 Fly", "100 Fly", "200 Fly",
    "200 IM", "400 IM",
]


def _clave_orden(t: Tiempo) -> tuple:
    try:
        i = ORDEN_PRUEBAS.index(t.prueba)
    except ValueError:
        i = len(ORDEN_PRUEBAS)
    return (t.curso, i, t.prueba)


def escribir_natacion_md(tiempos: list[Tiempo], destino: Path,
                         nombre: str = "Gael Moreno Sarmiento") -> Path:
    lineas = [f"# Mejores tiempos — {nombre}", "",
              "_Fuente: SwimCloud (perfil público)._", ""]
    por_curso: dict[str, list[Tiempo]] = {}
    for t in sorted(tiempos, key=_clave_orden):
        por_curso.setdefault(t.curso, []).append(t)

    nombres_curso = {"LCM": "Piscina larga (LCM)", "SCM": "Piscina corta (SCM)",
                     "SCY": "Yardas (SCY)"}
    for curso in ("LCM", "SCM", "SCY"):
        if curso not in por_curso:
            continue
        lineas += [f"## {nombres_curso.get(curso, curso)}", "",
                   "| Prueba | Tiempo | Fecha | Competencia |",
                   "|---|---|---|---|"]
        for t in por_curso[curso]:
            lineas.append(
                f"| {t.prueba} | {t.tiempo} | {t.fecha or '-'} | {t.competencia or '-'} |"
            )
        lineas.append("")

    destino.write_text("\n".join(lineas))
    return destino
