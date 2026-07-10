"""
Clasificador de correos de reclutamiento.

Toma un correo (remitente + asunto + cuerpo) y decide si viene de:
  - COACH        : un entrenador universitario escribiendo directamente
  - UNIVERSIDAD  : comunicación institucional/admisiones/equipo (no un coach personal)
  - PLATAFORMA   : NCSA u otras plataformas de reclutamiento (notificaciones)
  - OTRO         : no relacionado con reclutamiento

Además extrae metadatos útiles:
  - universidad (nombre inferido del dominio o del texto)
  - division    (NCAA D1 / D2 / D3, NAIA, NJCAA/JUCO)
  - nombre_coach
  - señales que dispararon la clasificación (para auditar)

Sin dependencias externas: sólo la librería estándar, así se puede correr y
probar sin credenciales ni red.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from typing import Optional


# --- Dominios de plataformas de reclutamiento -------------------------------
DOMINIOS_PLATAFORMA = {
    "ncsasports.org": "NCSA",
    "ncsacollegerecruiting.com": "NCSA",
    "athletesusa.org": "AthletesUSA",
    "sportsrecruits.com": "SportsRecruits",
    "fieldlevel.com": "FieldLevel",
}

# --- Dominios institucionales que NO son un coach personal ------------------
PREFIJOS_INSTITUCIONALES = (
    "admissions@", "admision@", "info@", "noreply@", "no-reply@",
    "recruiting@", "athletics@", "compliance@", "financialaid@",
)

# --- Palabras clave de coach (en el texto o la firma) -----------------------
PALABRAS_COACH = (
    "head coach", "assistant coach", "swim coach", "swimming coach",
    "head swimming coach", "recruiting coordinator", "director of swimming",
    "entrenador", "head men's swimming", "head women's swimming",
    "volunteer coach", "associate head coach",
)

# --- Señales de reclutamiento en asunto/cuerpo ------------------------------
PALABRAS_RECLUTAMIENTO = (
    "recruit", "recruiting", "roster", "scholarship", "official visit",
    "unofficial visit", "verbal", "commit", "questionnaire",
    "time standard", "prospect", "student-athlete", "student athlete",
    "swim team", "swimming program", "walk-on", "national letter of intent",
    "nli", "beca", "reclutamiento", "equipo de natación",
)

# --- Detección de división --------------------------------------------------
_RE_DIVISION = [
    (re.compile(r"\bncaa\s*d(?:ivision)?\s*i{1,3}\b|\bdivision\s+(?:one|two|three|i{1,3})\b|\bncaa\s*d[123]\b|\bd[123]\b", re.I), "detectar_ncaa"),
    (re.compile(r"\bnaia\b", re.I), "NAIA"),
    (re.compile(r"\bnjcaa\b|\bjuco\b|\bjunior college\b", re.I), "NJCAA (JUCO)"),
]


@dataclass
class ResultadoClasificacion:
    categoria: str                       # COACH | UNIVERSIDAD | PLATAFORMA | OTRO
    confianza: float                     # 0.0 - 1.0
    universidad: Optional[str] = None
    division: Optional[str] = None
    nombre_coach: Optional[str] = None
    plataforma: Optional[str] = None
    senales: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def _dominio(remitente: str) -> str:
    m = re.search(r"@([\w.-]+)", remitente or "")
    return m.group(1).lower() if m else ""


def _universidad_desde_dominio(dominio: str) -> Optional[str]:
    """Deriva un nombre legible de universidad desde un dominio .edu.
    p.ej. 'athletics.stanford.edu' -> 'Stanford'."""
    if not dominio.endswith(".edu"):
        return None
    partes = dominio.replace(".edu", "").split(".")
    # el segmento significativo suele ser el último antes de .edu
    base = partes[-1] if partes else ""
    subdominios_ruido = {"mail", "athletics", "email", "go", "www", "alumni"}
    if base in subdominios_ruido and len(partes) >= 2:
        base = partes[-2]
    return base.capitalize() if base else None


def _detectar_division(texto: str) -> Optional[str]:
    for regex, etiqueta in _RE_DIVISION:
        m = regex.search(texto)
        if m:
            if etiqueta == "detectar_ncaa":
                t = m.group(0).lower().replace(" ", "")
                if "iii" in t or "three" in t or "d3" in t:
                    return "NCAA D3"
                if "ii" in t or "two" in t or "d2" in t:
                    return "NCAA D2"
                return "NCAA D1"
            return etiqueta
    return None


_STOPWORDS_NOMBRE = {"the", "head", "assistant", "associate", "our", "your", "coach", "swim"}


def _es_nombre_valido(candidato: str) -> bool:
    palabras = candidato.split()
    return bool(palabras) and not any(p.lower() in _STOPWORDS_NOMBRE for p in palabras)


def _detectar_nombre_coach(texto: str) -> Optional[str]:
    """Busca 'Coach <Nombre>' o una firma tipo 'Nombre Apellido, Head Coach'.
    Nota: sin re.I en las clases [A-Z]/[a-z] para respetar la capitalización
    real de los nombres propios."""
    m = re.search(r"\bCoach\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", texto)
    if m and _es_nombre_valido(m.group(1)):
        return m.group(1).strip()
    # Firma: 'Jane Doe, Head Women's Swimming Coach'
    m = re.search(
        r"([A-Z][a-z]+\s+[A-Z][a-z]+)\s*,\s*(?:head|assistant|associate|"
        r"men'?s|women'?s|swim|swimming|\s)*coach",
        texto, re.I,
    )
    if m and _es_nombre_valido(m.group(1)):
        return m.group(1).strip()
    return None


def clasificar_correo(remitente: str, asunto: str = "", cuerpo: str = "") -> ResultadoClasificacion:
    """Clasifica un correo. `remitente` puede venir como 'Nombre <a@b.com>' o 'a@b.com'."""
    dominio = _dominio(remitente)
    texto = f"{asunto}\n{cuerpo}".lower()
    texto_original = f"{asunto}\n{cuerpo}"
    senales: list[str] = []

    division = _detectar_division(texto)
    if division:
        senales.append(f"division:{division}")

    # 1) Plataforma de reclutamiento (dominio conocido)
    for dom, nombre in DOMINIOS_PLATAFORMA.items():
        if dominio == dom or dominio.endswith("." + dom):
            senales.append(f"dominio_plataforma:{dom}")
            return ResultadoClasificacion(
                categoria="PLATAFORMA", confianza=0.95, plataforma=nombre,
                division=division, senales=senales,
            )

    universidad = _universidad_desde_dominio(dominio)
    es_edu = dominio.endswith(".edu")
    if es_edu:
        senales.append("dominio:.edu")

    hay_coach = any(p in texto for p in PALABRAS_COACH)
    hay_recluta = any(p in texto for p in PALABRAS_RECLUTAMIENTO)
    if hay_coach:
        senales.append("palabra_coach")
    if hay_recluta:
        senales.append("palabra_reclutamiento")

    institucional = any((remitente or "").lower().startswith(p) or dominio.startswith("noreply")
                        for p in PREFIJOS_INSTITUCIONALES)
    # revisamos también la parte local del correo
    local = (re.match(r"[^@<]*<?([^@]+)@", (remitente or "").replace(" ", "")) or [None, ""])[1].lower()
    if any(local.startswith(p.rstrip("@")) for p in PREFIJOS_INSTITUCIONALES):
        institucional = True
    if institucional:
        senales.append("remitente_institucional")

    nombre_coach = _detectar_nombre_coach(texto_original)
    if nombre_coach:
        senales.append(f"coach:{nombre_coach}")

    # 2) COACH: dominio .edu (o firma de coach) + señales de coach/reclutamiento,
    #    y NO es una dirección institucional genérica.
    if (es_edu or hay_coach) and (hay_coach or hay_recluta) and not institucional:
        confianza = 0.9 if (es_edu and hay_coach) else 0.75 if es_edu else 0.6
        return ResultadoClasificacion(
            categoria="COACH", confianza=confianza, universidad=universidad,
            division=division, nombre_coach=nombre_coach, senales=senales,
        )

    # 3) UNIVERSIDAD: comunicación institucional (.edu o dirección genérica)
    #    con contexto de reclutamiento, pero sin firma de coach personal.
    if es_edu or (institucional and hay_recluta):
        confianza = 0.7 if hay_recluta else 0.5
        return ResultadoClasificacion(
            categoria="UNIVERSIDAD", confianza=confianza, universidad=universidad,
            division=division, senales=senales,
        )

    # 4) OTRO
    return ResultadoClasificacion(
        categoria="OTRO", confianza=0.4 if not hay_recluta else 0.5,
        universidad=universidad, division=division, senales=senales,
    )


if __name__ == "__main__":
    # Demo rápida
    ejemplos = [
        ("John Smith <jsmith@athletics.stanford.edu>",
         "Interested in your recruiting profile",
         "Hi Gael, we are NCAA Division I and interested in your recruiting "
         "profile. Best, Jane Doe, Head Women's Swimming Coach, Stanford."),
        ("recruiting@ncsasports.org", "New coach viewed your profile",
         "A college coach just viewed your NCSA profile."),
        ("admissions@utexas.edu", "Your application to UT Austin",
         "Thank you for your interest in our swim program and scholarship options."),
        ("promos@tienda.com", "50% de descuento", "Ofertas de verano"),
    ]
    for rem, asu, cue in ejemplos:
        r = clasificar_correo(rem, asu, cue)
        print(f"{r.categoria:12} conf={r.confianza:.2f} uni={r.universidad} "
              f"div={r.division} coach={r.nombre_coach} << {rem}")
