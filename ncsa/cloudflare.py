"""
Helper para sitios detrás de Cloudflare WAF (SwimCloud, etc.).

Truco clave del proyecto: en lugar de resolver el challenge de Cloudflare,
importamos las cookies activas de Chrome (donde el usuario ya pasó el challenge)
con browser_cookie3 y hacemos la request con curl_cffi, que imita el
fingerprint TLS/JA3 de Chrome real. Así evitamos abrir un browser completo
cuando no hace falta (mucho más rápido que Selenium).

Si Cloudflare igual bloquea, el fallback es Selenium (ver ncsa.scraper._driver).
"""
from __future__ import annotations


def get_con_cookies_chrome(url: str, dominio: str, timeout: int = 30):
    """GET a `url` reutilizando las cookies de Chrome para `dominio`.

    Devuelve el texto HTML. Lanza si la respuesta no es 200.
    """
    import browser_cookie3
    from curl_cffi import requests as cffi_requests

    cookies = browser_cookie3.chrome(domain_name=dominio)
    resp = cffi_requests.get(
        url,
        cookies={c.name: c.value for c in cookies},
        impersonate="chrome",   # fingerprint TLS de Chrome
        timeout=timeout,
    )
    if resp.status_code != 200:
        raise RuntimeError(
            f"{url} respondió {resp.status_code} "
            f"(posible challenge de Cloudflare no resuelto; abre el sitio en "
            f"Chrome una vez y reintenta, o usa el fallback de Selenium)."
        )
    return resp.text
