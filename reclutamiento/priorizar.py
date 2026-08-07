"""
Priorización de universidades objetivo para Gael.

Con los datos disponibles del análisis de Karla (división + ranking del equipo
dentro de su división + conferencia) estimamos, de forma TRANSPARENTE y
heurística, qué tan alcanzable/competitiva es cada universidad y con qué
prioridad conviene contactarla.

Señales usadas:
  - División: D1/D2/NAIA ofrecen beca atlética; D3 no (vía académica).
  - rank_div: posición del EQUIPO dentro de su división. Número alto = equipo
    más débil = mayor probabilidad de que un recluta juvenil aporte y entre.

Limitación honesta: esto NO compara los tiempos de Gael contra los estándares
de tiempo de cada universidad (esos "recruiting time standards" no vienen en
los datos de Karla; el PDF de NCSA trae estándares genéricos, no por escuela).
Para un fit por prueba habría que sumar esa fuente. Ver README / próximos pasos.
"""
from __future__ import annotations

import re

# Divisiones donde hay beca atlética
BECA_POSIBLE = {"NCAA D1", "NCAA D2", "NAIA"}


def _rank_num(rank: str) -> int:
    m = re.match(r"(\d+)", rank or "")
    return int(m.group(1)) if m else 9999


def evaluar(u: dict) -> dict:
    """Devuelve {fit, beca, prioridad, motivo} para una universidad."""
    div = u.get("division") or ""
    rank = _rank_num(u.get("rank_div"))
    beca = div in BECA_POSIBLE

    # Categoría de fit según fuerza del equipo (rank_div) y división.
    # Sin rank_div NO asumimos equipo débil: lo marcamos para revisión
    # (las universidades de "Contactos Colegios" suelen ser programas élite
    #  sin ranking capturado, p.ej. Stanford, Florida, Cal, USC).
    if rank == 9999:
        fit = "Sin ranking (revisar)"
    elif div == "NCAA D1":
        if rank <= 60:
            fit = "Aspiracional"      # programa fuerte (reach)
        elif rank <= 110:
            fit = "Competitiva"
        else:
            fit = "Alta probabilidad"
    elif div in ("NCAA D2", "NAIA"):
        fit = "Competitiva" if rank <= 10 else "Alta probabilidad"
    elif div == "NCAA D3":
        fit = "Competitiva" if rank <= 30 else "Alta probabilidad"
    else:
        fit = "Competitiva"

    # Prioridad de contacto
    if fit == "Alta probabilidad":
        prioridad = "alta"
    elif fit in ("Competitiva", "Sin ranking (revisar)"):
        prioridad = "media"
    else:                              # Aspiracional
        prioridad = "baja"

    motivos = [fit.lower()]
    motivos.append("beca atlética posible" if beca else "sin beca atlética (vía académica)")
    if rank != 9999:
        motivos.append(f"equipo #{rank} de su división")

    return {"fit": fit, "beca": beca, "prioridad": prioridad,
            "motivo": "; ".join(motivos)}


_ORDEN_PRIORIDAD = {"alta": 0, "media": 1, "baja": 2}
_ORDEN_DIV = {"NCAA D1": 0, "NCAA D2": 1, "NCAA D3": 2, "NAIA": 3, "NJCAA (JUCO)": 4}


def priorizar(universidades: list[dict]) -> list[dict]:
    """Anota cada universidad con fit/beca/prioridad y devuelve la lista
    ordenada (prioridad alta primero; dentro, por división y ranking)."""
    anotadas = []
    for u in universidades:
        ev = evaluar(u)
        anotadas.append({**u, **ev})
    anotadas.sort(key=lambda x: (_ORDEN_PRIORIDAD.get(x["prioridad"], 9),
                                 _ORDEN_DIV.get(x["division"], 9),
                                 _rank_num(x.get("rank_div"))))
    return anotadas
