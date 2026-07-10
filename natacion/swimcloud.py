"""
Scraping de tiempos de SwimCloud.

SwimCloud está detrás de Cloudflare WAF. Estrategia de dos niveles:
  1. Rápido: `ncsa.cloudflare.get_con_cookies_chrome` (curl_cffi + cookies de
     Chrome) — no abre browser.
  2. Fallback: Selenium (Chrome real) si Cloudflare bloquea la vía rápida.

El perfil público NO requiere login. Parseamos la tabla de mejores tiempos con
BeautifulSoup.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from typing import Optional

BASE = "https://www.swimcloud.com"
DOMINIO = "swimcloud.com"


@dataclass
class Tiempo:
    prueba: str          # p.ej. "100 Free"
    curso: str           # SCM / LCM / SCY
    tiempo: str          # "51.23"
    fecha: Optional[str] = None
    competencia: Optional[str] = None
    puntos_fina: Optional[int] = None

    def segundos(self) -> float:
        """Convierte 'mm:ss.xx' o 'ss.xx' a segundos (útil para ordenar/comparar)."""
        m = re.match(r"(?:(\d+):)?(\d+(?:\.\d+)?)", self.tiempo.strip())
        if not m:
            return float("inf")
        minutos = int(m.group(1)) if m.group(1) else 0
        return minutos * 60 + float(m.group(2))

    def to_dict(self) -> dict:
        return asdict(self)


def _html_perfil(swimmer_id: str) -> str:
    """Descarga el HTML del perfil, con fallback a Selenium si Cloudflare bloquea."""
    url = f"{BASE}/swimmer/{swimmer_id}/"
    try:
        from ncsa.cloudflare import get_con_cookies_chrome
        return get_con_cookies_chrome(url, DOMINIO)
    except Exception:
        # Fallback: Selenium
        from ncsa.scraper import _driver
        driver = _driver()
        try:
            driver.get(url)
            return driver.page_source
        finally:
            driver.quit()


def parsear_tiempos(html: str) -> list[Tiempo]:
    """Parsea la tabla de mejores tiempos del perfil de SwimCloud."""
    from bs4 import BeautifulSoup

    sopa = BeautifulSoup(html, "html.parser")
    tiempos: list[Tiempo] = []
    for fila in sopa.select("table tbody tr"):
        celdas = [c.get_text(strip=True) for c in fila.select("td")]
        if len(celdas) < 2:
            continue
        prueba, tiempo = celdas[0], celdas[1]
        if not re.search(r"\d", tiempo):
            continue
        curso = "SCY"
        mc = re.search(r"\b(SCY|SCM|LCM)\b", " ".join(celdas))
        if mc:
            curso = mc.group(1)
        tiempos.append(Tiempo(
            prueba=prueba, curso=curso, tiempo=tiempo,
            fecha=celdas[2] if len(celdas) > 2 else None,
            competencia=celdas[3] if len(celdas) > 3 else None,
        ))
    return tiempos


def obtener_tiempos(swimmer_id: str) -> list[Tiempo]:
    """Flujo completo: descarga perfil público y devuelve la lista de tiempos."""
    return parsear_tiempos(_html_perfil(swimmer_id))
