"""
Cliente de la API de WHOOP (no oficial).

Autenticación OAuth2 con credenciales en .env:
  WHOOP_CLIENT_ID, WHOOP_CLIENT_SECRET, WHOOP_REFRESH_TOKEN

Expone lecturas de recuperación, sueño y ciclos (strain) para cruzar el estado
fisiológico de Gael con su calendario de competencias y entrenamiento.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, asdict
from typing import Optional

API = "https://api.prod.whoop.com/developer"
TOKEN_URL = "https://api.prod.whoop.com/oauth/oauth2/token"


@dataclass
class Recuperacion:
    fecha: str
    recovery_score: Optional[int]      # 0-100
    hrv_ms: Optional[float]
    rhr_bpm: Optional[float]

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Sueno:
    fecha: str
    horas: Optional[float]             # horas dormidas
    performance_pct: Optional[int]     # 0-100 (% del sueño necesario)
    eficiencia_pct: Optional[float]

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Ciclo:
    fecha: str
    strain: Optional[float]            # 0-21 (carga cardiovascular del día)
    kilojoules: Optional[float]
    fc_promedio: Optional[int]
    fc_maxima: Optional[int]

    def to_dict(self) -> dict:
        return asdict(self)


def _access_token() -> str:
    """Intercambia el refresh_token por un access_token."""
    import requests

    cid = os.getenv("WHOOP_CLIENT_ID")
    secret = os.getenv("WHOOP_CLIENT_SECRET")
    refresh = os.getenv("WHOOP_REFRESH_TOKEN")
    if not all([cid, secret, refresh]):
        raise RuntimeError("Faltan WHOOP_CLIENT_ID/SECRET/REFRESH_TOKEN en .env")

    resp = requests.post(TOKEN_URL, data={
        "grant_type": "refresh_token",
        "refresh_token": refresh,
        "client_id": cid,
        "client_secret": secret,
        "scope": "offline read:recovery read:sleep read:cycles",
    }, timeout=30)
    resp.raise_for_status()
    return resp.json()["access_token"]


def obtener_recuperacion(limite: int = 14) -> list[Recuperacion]:
    """Devuelve las últimas `limite` recuperaciones diarias."""
    import requests

    token = _access_token()
    resp = requests.get(
        f"{API}/v1/recovery",
        headers={"Authorization": f"Bearer {token}"},
        params={"limit": limite},
        timeout=30,
    )
    resp.raise_for_status()
    salida: list[Recuperacion] = []
    for r in resp.json().get("records", []):
        score = r.get("score", {}) or {}
        salida.append(Recuperacion(
            fecha=(r.get("created_at") or "")[:10],
            recovery_score=score.get("recovery_score"),
            hrv_ms=score.get("hrv_rmssd_milli"),
            rhr_bpm=score.get("resting_heart_rate"),
        ))
    return salida


def _get(path: str, limite: int) -> list[dict]:
    import requests
    token = _access_token()
    resp = requests.get(
        f"{API}{path}",
        headers={"Authorization": f"Bearer {token}"},
        params={"limit": limite},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json().get("records", [])


def obtener_sueno(limite: int = 14) -> list[Sueno]:
    """Últimos registros de sueño (duración, performance, eficiencia)."""
    salida: list[Sueno] = []
    for r in _get("/v1/activity/sleep", limite):
        s = r.get("score", {}) or {}
        etapas = s.get("stage_summary", {}) or {}
        milli = sum(etapas.get(k, 0) or 0 for k in (
            "total_light_sleep_time_milli", "total_slow_wave_sleep_time_milli",
            "total_rem_sleep_time_milli"))
        salida.append(Sueno(
            fecha=(r.get("start") or "")[:10],
            horas=round(milli / 3_600_000, 2) if milli else None,
            performance_pct=s.get("sleep_performance_percentage"),
            eficiencia_pct=s.get("sleep_efficiency_percentage"),
        ))
    return salida


def obtener_ciclos(limite: int = 14) -> list[Ciclo]:
    """Últimos ciclos diarios con strain (carga) y frecuencia cardiaca."""
    salida: list[Ciclo] = []
    for r in _get("/v1/cycle", limite):
        s = r.get("score", {}) or {}
        salida.append(Ciclo(
            fecha=(r.get("start") or "")[:10],
            strain=round(s["strain"], 1) if s.get("strain") is not None else None,
            kilojoules=s.get("kilojoule"),
            fc_promedio=s.get("average_heart_rate"),
            fc_maxima=s.get("max_heart_rate"),
        ))
    return salida
