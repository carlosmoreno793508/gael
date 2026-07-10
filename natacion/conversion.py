"""
Conversión de tiempos entre cursos y puntos FINA.

Objetivo: por cada prueba, elegir la MEJOR marca del nadador (la de mayor puntaje
FINA, sea Curso Largo LCM o Curso Corto SCM) y convertirla a Yardas Cortas (SCY)
para compararla contra los estándares NCSA (que están en SCY).

Fuentes editables:
  - data/fina_base.json           : tiempos base FINA (para calcular puntos)
  - data/conversion_factors.json  : factores a SCY

Si un tiempo ya trae 'puntos' (p.ej. copiado de SwimCloud), se usa ese valor y
no se recalcula con la tabla base.

Sin dependencias externas.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

from natacion.fit import parse_tiempo, formato_tiempo, canonical_evento

_DATA = Path(__file__).resolve().parent.parent / "data"


def _cargar(nombre: str) -> dict:
    return json.loads((_DATA / nombre).read_text())


def fina_points(seg: float, evento: str, curso: str, base: dict) -> Optional[int]:
    """puntos = 1000 * (base/tiempo)^3. None si no hay base para (evento, curso)."""
    b = base.get(curso, {}).get(evento)
    if not b or seg <= 0 or seg == float("inf"):
        return None
    return round(1000 * (b / seg) ** 3)


def to_scy(seg: float, evento: str, curso: str, factores: dict) -> Optional[float]:
    """Convierte a segundos SCY con el factor del evento. None si SCY o sin factor."""
    if curso == "SCY":
        return seg
    tabla = factores.get(f"{curso}_to_SCY", {})
    f = tabla.get(evento)
    return seg * f if f else None


@dataclass
class MejorMarca:
    evento: str
    curso_origen: str
    tiempo_origen: str
    puntos: Optional[int]
    tiempo_scy: str
    scy_segundos: float

    def to_dict(self) -> dict:
        return asdict(self)


def mejor_por_evento(tiempos: list[dict], base: dict, factores: dict) -> list[MejorMarca]:
    """Agrupa por prueba y devuelve, por cada una, la marca de mayor puntaje FINA
    convertida a SCY. `tiempos`: dicts con evento/curso/tiempo (y opcional 'puntos')."""
    # 1) puntuar cada marca
    puntuadas = []
    for t in tiempos:
        evento = canonical_evento(t.get("evento", "")) or t.get("evento", "")
        curso = t.get("curso", "")
        seg = parse_tiempo(t.get("tiempo", ""))
        pts = t.get("puntos")
        if pts is None:
            pts = fina_points(seg, evento, curso, base)
        puntuadas.append((evento, curso, seg, pts))

    # 2) mejor por evento (mayor puntaje; empate: menor tiempo convertido)
    mejor: dict[str, tuple] = {}
    for evento, curso, seg, pts in puntuadas:
        if pts is None:
            continue
        if evento not in mejor or pts > mejor[evento][3]:
            mejor[evento] = (evento, curso, seg, pts)

    # 3) convertir a SCY
    salida: list[MejorMarca] = []
    for evento, curso, seg, pts in mejor.values():
        scy = to_scy(seg, evento, curso, factores)
        if scy is None:
            continue
        salida.append(MejorMarca(
            evento=evento, curso_origen=curso, tiempo_origen=formato_tiempo(seg),
            puntos=pts, tiempo_scy=formato_tiempo(scy), scy_segundos=round(scy, 2),
        ))
    salida.sort(key=lambda m: -(m.puntos or 0))
    return salida


def mejores_marcas_scy(tiempos: list[dict]) -> list[MejorMarca]:
    """Conveniencia: carga las tablas del proyecto y calcula las mejores SCY."""
    base = _cargar("fina_base.json")
    factores = _cargar("conversion_factors.json")
    return mejor_por_evento(tiempos, base, factores)
