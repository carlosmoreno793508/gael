"""
Normalización y fusión de universidades objetivo.

Reúne las fuentes reales (hoja "GM US Univ Swimming" y "Contactos Colegios" de
la carpeta NCSA de Karla) en una sola lista deduplicada, que es la fuente
oficial del proyecto: data/universidades_objetivo.json.

Sin dependencias externas.
"""
from __future__ import annotations

import re

FILLER = {"university", "college", "the", "of", "institute", "technology", "smu", "tcu", "byu"}

# Orden canónico de divisiones para ordenar la salida
ORDEN_DIV = {"NCAA D1": 0, "NCAA D2": 1, "NCAA D3": 2, "NAIA": 3, "NJCAA (JUCO)": 4}

_DIV_NORMAL = {
    "D1": "NCAA D1", "D2": "NCAA D2", "D3": "NCAA D3",
    "NAIA": "NAIA", "NJCAA": "NJCAA (JUCO)", "JUCO": "NJCAA (JUCO)",
}


def normalizar_division(div: str | None) -> str | None:
    if not div:
        return div
    return _DIV_NORMAL.get(div.strip(), div)


def norm(nombre: str) -> str:
    """Normaliza el nombre a un conjunto ordenado de tokens distintivos."""
    n = re.sub(r"\(.*?\)", " ", nombre.lower())
    n = re.sub(r"[^a-z ]", " ", n)
    tokens = [t for t in n.split() if t not in FILLER]
    return " ".join(sorted(tokens))


def es_match(a: str, b: str) -> bool:
    """True si dos nombres refieren a la misma universidad.

    Coincidencia EXACTA sobre tokens normalizados. Deliberadamente NO usa
    coincidencia por subconjunto: aunque ayudaría con campus ('Texas' vs
    'Texas - Austin'), colapsaría universidades distintas que comparten raíz
    ('Virginia' vs 'West Virginia', 'Arizona' vs 'Arizona State',
    'Wisconsin' vs 'Wisconsin - Milwaukee'). Los duplicados reales entre las
    fuentes de Karla (Yale, West Virginia) tienen nombre idéntico."""
    return norm(a) == norm(b)


def _mejor_coach(actual: dict, nuevo: dict) -> None:
    """Prefiere un Head Coach (no interino/asistente) como coach principal."""
    pos_nueva = (nuevo.get("posicion") or "").lower()
    pos_actual = (actual.get("coach_posicion") or "").lower()
    nuevo_es_head = "head coach" in pos_nueva and "interim" not in pos_nueva and "assistant" not in pos_nueva
    actual_es_head = "head coach" in pos_actual and "interim" not in pos_actual and "assistant" not in pos_actual
    if nuevo.get("coach") and (nuevo_es_head and not actual_es_head or not actual.get("coach")):
        actual["coach"] = nuevo["coach"]
        actual["coach_posicion"] = nuevo.get("posicion", "")


def construir_maestro(gm: list[dict], contactos: list[dict]) -> list[dict]:
    """Fusiona ambas fuentes en una lista deduplicada y ordenada."""
    entradas = [{**u, "_origen": "GM US Univ"} for u in gm] + \
               [{**u, "_origen": "Contactos NCSA"} for u in contactos]

    maestro: list[dict] = []
    for u in entradas:
        m = next((x for x in maestro if es_match(x["universidad"], u["universidad"])), None)
        if m is None:
            m = {
                "universidad": u["universidad"],
                "division": normalizar_division(u.get("division")),
                "conferencia": u.get("conferencia") or "",
                "ciudad": u.get("ciudad") or "",
                "estado": u.get("estado") or "",
                "coach": "", "coach_posicion": "",
                "coaches": set(), "email": u.get("email") or "",
                "telefono": u.get("telefono") or "",
                "rank_div": u.get("rank_div") or "",
                "fuentes": set(),
                "prioridad": "", "estatus": "",   # a llenar por el equipo
            }
            if u.get("requisitos"):
                m["requisitos"] = u["requisitos"]
            maestro.append(m)
        # completar campos faltantes con lo que traiga cada fuente
        m["conferencia"] = m["conferencia"] or (u.get("conferencia") or "")
        m["email"] = m["email"] or (u.get("email") or "")
        m["telefono"] = m["telefono"] or (u.get("telefono") or "")
        m["rank_div"] = m["rank_div"] or (u.get("rank_div") or "")
        m["estado"] = m["estado"] or (u.get("estado") or "")
        m["ciudad"] = m["ciudad"] or (u.get("ciudad") or "")
        if u.get("coach"):
            m["coaches"].add(u["coach"])
        m["fuentes"].add(u.get("fuente", u["_origen"]))
        _mejor_coach(m, u)

    # serializar sets y limpiar campos internos
    for m in maestro:
        m["coaches"] = sorted(c for c in m["coaches"] if c)
        m["fuentes"] = sorted(m["fuentes"])
        m.pop("coach_posicion", None)

    maestro.sort(key=lambda x: (ORDEN_DIV.get(x["division"], 9),
                                _rank_num(x["rank_div"]), x["universidad"]))
    return maestro


def _rank_num(rank: str) -> int:
    m = re.match(r"(\d+)", rank or "")
    return int(m.group(1)) if m else 9999
