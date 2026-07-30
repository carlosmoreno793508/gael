"""
Cruce del fit de tiempos de Gael con las universidades objetivo.

Idea: el fit contra el corte élite de NCSA nos dice el NIVEL del atleta. Ese nivel
se traduce en qué tan reclutable es en cada división, y con eso re-priorizamos.

Limitación honesta: no hay cortes de reclutamiento por universidad, así que el
fit por-universidad se estima con: nivel del atleta (nº de pruebas que cumplen el
corte élite) + división + ranking del equipo. Es una guía, no un veredicto.
"""
from __future__ import annotations

import re

BECA_POSIBLE = {"NCAA D1", "NCAA D2", "NAIA"}


def _rank_num(rank: str) -> int:
    m = re.match(r"(\d+)", rank or "")
    return int(m.group(1)) if m else 9999


def nivel_atleta(cumplidos: int) -> str:
    """Traduce el nº de pruebas que cumplen el corte élite NCSA a un nivel."""
    if cumplidos >= 4:
        return "D1"
    if cumplidos >= 1:
        return "D1/D2 frontera"
    return "D2/D3"


def fit_universidad(u: dict, nivel: str) -> dict:
    """Devuelve {fit_tiempos, prioridad} para una universidad dado el nivel del atleta.
    Modelo para un atleta nivel 'D1' (ajustar si el nivel es menor)."""
    div = u.get("division") or ""
    rank = _rank_num(u.get("rank_div"))
    beca = div in BECA_POSIBLE

    if nivel != "D1":
        # Modelo conservador si el atleta no llega a nivel D1
        if div in ("NCAA D2", "NAIA"):
            return {"fit_tiempos": "Competitivo (con beca)", "prioridad": "alta"}
        if div == "NCAA D3":
            return {"fit_tiempos": "Competitivo", "prioridad": "media"}
        return {"fit_tiempos": "Reach", "prioridad": "media" if rank <= 110 else "alta"}

    # Atleta nivel D1
    if div == "NCAA D3":
        return {"fit_tiempos": "Muy por encima (sin beca atlética)", "prioridad": "media"}
    if div == "NAIA":
        return {"fit_tiempos": "Muy por encima (con beca)", "prioridad": "alta"}
    if div == "NCAA D2":
        return {"fit_tiempos": "Por encima del nivel (con beca)", "prioridad": "alta"}
    # D1
    if rank == 9999:
        return {"fit_tiempos": "Programa élite — reach (aporta en espalda)", "prioridad": "media"}
    if rank <= 35:
        return {"fit_tiempos": "Élite — reach (aporta en espalda)", "prioridad": "media"}
    if rank <= 110:
        return {"fit_tiempos": "Competitivo / reclutable (con beca)", "prioridad": "alta"}
    return {"fit_tiempos": "Reclutable, aporta pronto (con beca)", "prioridad": "alta"}


_ORDEN_PRIORIDAD = {"alta": 0, "media": 1, "baja": 2}
_ORDEN_DIV = {"NCAA D1": 0, "NCAA D2": 1, "NCAA D3": 2, "NAIA": 3}


def cruzar(universidades: list[dict], nivel: str) -> list[dict]:
    salida = []
    for u in universidades:
        salida.append({**u, **fit_universidad(u, nivel)})
    salida.sort(key=lambda x: (_ORDEN_PRIORIDAD.get(x["prioridad"], 9),
                               _ORDEN_DIV.get(x["division"], 9),
                               _rank_num(x.get("rank_div"))))
    return salida
