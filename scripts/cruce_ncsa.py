#!/usr/bin/env python3
"""
Cruce del análisis de NCSA de Karla con nuestros datos del repo.

Fuentes:
  - data/karla_gm_us_univ.json        (hoja "GM US Univ Swimming": NCSA + SwimCloud)
  - data/karla_contactos_colegios.json (carpeta NCSA: "Contactos Colegios")
  - data/universidades_objetivo.json   (nuestra lista del repo)

Produce:
  - registros/universidades_maestro.json  (lista unificada y deduplicada)
  - registros/cruce_ncsa.md               (reporte legible del cruce)

Sin dependencias externas.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import DATA, REGISTROS  # noqa: E402

FILLER = {"university", "college", "the", "of", "institute", "technology", "smu", "tcu", "byu"}


def norm(nombre: str) -> str:
    """Normaliza el nombre de una universidad para comparar.
    Conserva tokens distintivos como 'state', 'austin', 'milwaukee' para no
    confundir p.ej. 'University of Arizona' con 'Arizona State University'."""
    n = nombre.lower()
    n = re.sub(r"\(.*?\)", " ", n)          # quita paréntesis
    n = re.sub(r"[^a-z ]", " ", n)          # quita puntuación
    tokens = [t for t in n.split() if t not in FILLER]
    return " ".join(sorted(tokens))


def es_match(a: str, b: str) -> bool:
    """Coinciden si comparten los mismos tokens distintivos, permitiendo que
    uno omita el campus (subconjunto) SIN colapsar 'state'/'wesleyan' etc."""
    ta, tb = set(norm(a).split()), set(norm(b).split())
    if ta == tb:
        return True
    distintivos = {"state", "wesleyan", "milwaukee", "green", "bay", "baptist"}
    menor, mayor = (ta, tb) if len(ta) <= len(tb) else (tb, ta)
    if menor and menor < mayor:                       # subconjunto propio
        extra = mayor - menor
        return not (extra & distintivos)              # el campus extra no debe ser distintivo
    return False


def cargar(nombre):
    return json.loads((DATA / nombre).read_text())


def main() -> None:
    gm = cargar("karla_gm_us_univ.json")
    contactos = cargar("karla_contactos_colegios.json")
    nuestras = cargar("universidades_objetivo.json")

    karla = [{**u, "_origen": "GM US Univ"} for u in gm] + \
            [{**u, "_origen": "Contactos NCSA"} for u in contactos]

    # --- Lista maestra unificada (dedup por nombre normalizado) ---
    maestro: list[dict] = []
    for u in karla:
        existente = next((m for m in maestro if es_match(m["universidad"], u["universidad"])), None)
        if existente:
            existente.setdefault("fuentes", set()).add(u.get("fuente", u["_origen"]))
            existente.setdefault("coaches", set()).add(u.get("coach", ""))
            existente["origenes"].add(u["_origen"])
        else:
            maestro.append({
                "universidad": u["universidad"], "division": u.get("division"),
                "conferencia": u.get("conferencia"), "estado": u.get("estado", ""),
                "coach": u.get("coach", ""), "email": u.get("email", ""),
                "fuentes": {u.get("fuente", u["_origen"])},
                "coaches": {u.get("coach", "")}, "origenes": {u["_origen"]},
                "rank_div": u.get("rank_div", ""),
            })

    # --- Cruce con NUESTRAS universidades ---
    cruce = []
    for n in nuestras:
        match = next((m for m in maestro if es_match(m["universidad"], n["universidad"])), None)
        if match:
            coach_real = match["coach"]
            conflicto = (n.get("coach") and coach_real and
                         n["coach"].lower() not in {c.lower() for c in match["coaches"]})
            cruce.append({
                "nuestra": n["universidad"], "nuestro_coach": n.get("coach"),
                "match_karla": match["universidad"], "coach_real": coach_real,
                "coaches_reales": sorted(c for c in match["coaches"] if c),
                "fuentes": sorted(match["fuentes"]),
                "conflicto_coach": bool(conflicto),
            })
        else:
            cruce.append({"nuestra": n["universidad"], "nuestro_coach": n.get("coach"),
                          "match_karla": None})

    # universidades de Karla que NO teníamos
    nuestras_norm = [n["universidad"] for n in nuestras]
    solo_karla = [m for m in maestro
                  if not any(es_match(m["universidad"], nn) for nn in nuestras_norm)]

    # --- Serializar sets ---
    for m in maestro:
        m["fuentes"] = sorted(m["fuentes"])
        m["coaches"] = sorted(c for c in m["coaches"] if c)
        m["origenes"] = sorted(m["origenes"])

    (REGISTROS / "universidades_maestro.json").write_text(
        json.dumps(maestro, indent=2, ensure_ascii=False))

    # --- Estadísticas ---
    por_div, por_fuente = {}, {}
    for m in maestro:
        por_div[m["division"]] = por_div.get(m["division"], 0) + 1
        for f in m["fuentes"]:
            por_fuente[f] = por_fuente.get(f, 0) + 1

    # --- Reporte Markdown ---
    L = ["# Cruce NCSA (Karla) × nuestros datos", "",
         f"- Universidades únicas tras deduplicar: **{len(maestro)}**",
         f"- Por división: " + ", ".join(f"{k}: {v}" for k, v in sorted(por_div.items())),
         f"- Por fuente: " + ", ".join(f"{k}: {v}" for k, v in sorted(por_fuente.items())),
         "",
         "## 1. Cruce con nuestras universidades objetivo", "",
         "| Nuestra universidad | Nuestro coach | ¿En NCSA de Karla? | Coach real (Karla) | Conflicto |",
         "|---|---|---|---|---|"]
    for c in cruce:
        if c["match_karla"]:
            L.append(f"| {c['nuestra']} | {c['nuestro_coach'] or '-'} | ✅ {', '.join(c['fuentes'])} "
                     f"| {', '.join(c['coaches_reales']) or c['coach_real'] or '-'} "
                     f"| {'⚠️ SÍ' if c['conflicto_coach'] else 'no'} |")
        else:
            L.append(f"| {c['nuestra']} | {c['nuestro_coach'] or '-'} | ❌ no está | - | - |")

    L += ["", "## 2. Universidades de Karla que NO teníamos (nuevos objetivos)", "",
          "| Universidad | Div | Conf | Coach | Fuente |", "|---|---|---|---|---|"]
    for m in sorted(solo_karla, key=lambda x: (x["division"] or "", x["universidad"])):
        L.append(f"| {m['universidad']} | {m['division']} | {m['conferencia'] or '-'} "
                 f"| {m['coach'] or '-'} | {', '.join(m['fuentes'])} |")

    (REGISTROS / "cruce_ncsa.md").write_text("\n".join(L) + "\n")

    # --- Consola ---
    print(f"Maestro: {len(maestro)} universidades | por división {por_div} | por fuente {por_fuente}")
    print(f"Nuevos objetivos de Karla no presentes en nuestra lista: {len(solo_karla)}")
    print("\nCruce con nuestras universidades:")
    for c in cruce:
        if c["match_karla"]:
            flag = "  ⚠️ CONFLICTO de coach" if c["conflicto_coach"] else ""
            print(f"  ✅ {c['nuestra']}: coincide ({', '.join(c['fuentes'])}); "
                  f"coach real = {', '.join(c['coaches_reales']) or '-'}{flag}")
        else:
            print(f"  ❌ {c['nuestra']}: NO está en el análisis NCSA de Karla")
    print(f"\nEscritos: registros/universidades_maestro.json, registros/cruce_ncsa.md")


if __name__ == "__main__":
    main()
