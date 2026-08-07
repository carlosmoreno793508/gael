"""
Motor de "fit por prueba": compara los tiempos de un nadador contra una tabla
de estándares (p.ej. los cortes de NCSA) y reporta, por prueba y curso, si los
cumple y por cuánto.

Sin dependencias externas.

Limitaciones a tener presentes (ver README):
  - Los estándares de NCSA Spring Champs son UN nivel élite, no cortes por
    división (D1/D2/D3). Un "fit por división" real necesita esas tablas.
  - El resultado sólo es tan bueno como los tiempos de entrada: deben ser los
    ACTUALES del nadador.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from typing import Optional

# Normalización de nombres de prueba desde distintas fuentes
_STROKE = {
    "free": "Free", "freestyle": "Free", "fly": "Fly", "butterfly": "Fly",
    "back": "Back", "backstroke": "Back", "breast": "Breast",
    "breaststroke": "Breast", "im": "IM", "medley": "IM",
}


def parse_tiempo(t: str) -> float:
    """'mm:ss.xx' | 'h:mm:ss.xx' | 'ss.xx' -> segundos (float). inf si inválido."""
    if not t:
        return float("inf")
    t = str(t).strip().lstrip("0") or "0"
    partes = t.split(":")
    try:
        segs = 0.0
        for p in partes:
            segs = segs * 60 + float(p)
        return segs
    except ValueError:
        return float("inf")


def formato_tiempo(seg: float) -> str:
    if seg == float("inf"):
        return "-"
    m, s = divmod(seg, 60)
    return f"{int(m)}:{s:05.2f}" if m else f"{s:.2f}"


def canonical_evento(texto: str) -> Optional[str]:
    """'50 m Free' | '100 Yrds free' | '200 IM' -> '50 Free' etc."""
    m = re.search(r"(\d{2,4})\s*(?:m|yrds?|yd|yards)?\s*([A-Za-z]+)", texto)
    if not m:
        return None
    dist = int(m.group(1))
    stroke = _STROKE.get(m.group(2).lower())
    if not stroke:
        return None
    return f"{dist} {stroke}"


@dataclass
class FitPrueba:
    evento: str
    curso: str
    tiempo_nadador: str
    tiempo_estandar: str
    delta_seg: float          # negativo = por debajo del estándar (lo cumple)
    pct_off: float            # % por encima del estándar (0 o menos = cumple)
    cumple: bool

    def to_dict(self) -> dict:
        return asdict(self)


def cargar_estandares(data: dict) -> dict:
    """Indexa estándares por (evento, curso) -> segundos."""
    idx = {}
    for e in data.get("estandares", []):
        idx[(e["evento"], e["curso"])] = parse_tiempo(e["tiempo"])
    return idx


def evaluar_fit(tiempos: list[dict], estandares_idx: dict) -> list[FitPrueba]:
    """`tiempos`: dicts con evento/curso/tiempo. Devuelve el fit por prueba
    para las que tengan estándar disponible."""
    salida = []
    for t in tiempos:
        evento = canonical_evento(t.get("evento", "")) or t.get("evento", "")
        curso = t.get("curso", "")
        clave = (evento, curso)
        if clave not in estandares_idx:
            continue
        seg = parse_tiempo(t.get("tiempo", ""))
        std = estandares_idx[clave]
        delta = seg - std
        pct = (delta / std * 100) if std else float("inf")
        salida.append(FitPrueba(
            evento=evento, curso=curso,
            tiempo_nadador=formato_tiempo(seg), tiempo_estandar=formato_tiempo(std),
            delta_seg=round(delta, 2), pct_off=round(pct, 1), cumple=seg <= std,
        ))
    # ordenar: primero los más cercanos al estándar
    salida.sort(key=lambda x: x.pct_off)
    return salida
