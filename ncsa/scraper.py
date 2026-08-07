"""
Scraper del portal NCSA (Next College Student Athlete).

NCSA no expone una API pública, así que iniciamos sesión con Selenium (Chrome
real) y leemos el HTML de la actividad de reclutamiento: qué coaches vieron el
perfil de Gael, qué universidades mostraron interés, mensajes recibidos, etc.

Credenciales: NCSA_EMAIL / NCSA_PASSWORD en .env (nunca en el repo).

Diseño defensivo:
  - Los selectores CSS están centralizados en SELECTORES para que, cuando NCSA
    cambie su maquetado, sólo se toque un lugar.
  - `iniciar_sesion()` y `leer_actividad()` están separados: se puede reusar la
    misma sesión para varias lecturas.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, asdict
from typing import Optional

LOGIN_URL = "https://www.ncsasports.org/login"
ACTIVIDAD_URL = "https://www.ncsasports.org/recruiting/activity"

# Punto único de mantenimiento de selectores (NCSA cambia su HTML con frecuencia).
SELECTORES = {
    "input_email": "input[name='email'], #email",
    "input_password": "input[name='password'], #password",
    "boton_login": "button[type='submit']",
    "tarjeta_actividad": "[data-testid='activity-card'], .activity-item",
    "nombre_coach": ".coach-name, [data-field='coach']",
    "universidad": ".school-name, [data-field='school']",
    "tipo_evento": ".activity-type, [data-field='event']",
    "fecha": ".activity-date, time",
}


@dataclass
class ActividadNCSA:
    coach: Optional[str]
    universidad: Optional[str]
    tipo_evento: Optional[str]   # p.ej. "viewed_profile", "message", "favorite"
    fecha: Optional[str]

    def to_dict(self) -> dict:
        return asdict(self)


def _driver(headless: bool | None = None):
    """Crea un ChromeDriver. Importación perezosa de Selenium."""
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service

    if headless is None:
        headless = os.getenv("CHROME_HEADLESS", "false").lower() == "true"

    opts = Options()
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument("--window-size=1280,1024")

    ruta = os.getenv("CHROMEDRIVER_PATH")
    service = Service(ruta) if ruta else Service()
    return webdriver.Chrome(service=service, options=opts)


def iniciar_sesion(driver=None):
    """Inicia sesión en NCSA con las credenciales de .env. Devuelve el driver."""
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait

    email = os.getenv("NCSA_EMAIL")
    password = os.getenv("NCSA_PASSWORD")
    if not email or not password:
        raise RuntimeError("Faltan NCSA_EMAIL / NCSA_PASSWORD en .env")

    driver = driver or _driver()
    driver.get(LOGIN_URL)
    wait = WebDriverWait(driver, 30)
    wait.until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, SELECTORES["input_email"]))
    ).send_keys(email)
    driver.find_element(By.CSS_SELECTOR, SELECTORES["input_password"]).send_keys(password)
    driver.find_element(By.CSS_SELECTOR, SELECTORES["boton_login"]).click()
    wait.until(EC.url_contains("recruiting"))
    return driver


def leer_actividad(driver) -> list[ActividadNCSA]:
    """Lee las tarjetas de actividad de reclutamiento de la sesión actual."""
    from bs4 import BeautifulSoup

    driver.get(ACTIVIDAD_URL)
    sopa = BeautifulSoup(driver.page_source, "html.parser")

    def _texto(nodo, css):
        el = nodo.select_one(css)
        return el.get_text(strip=True) if el else None

    resultados: list[ActividadNCSA] = []
    for tarjeta in sopa.select(SELECTORES["tarjeta_actividad"]):
        resultados.append(ActividadNCSA(
            coach=_texto(tarjeta, SELECTORES["nombre_coach"]),
            universidad=_texto(tarjeta, SELECTORES["universidad"]),
            tipo_evento=_texto(tarjeta, SELECTORES["tipo_evento"]),
            fecha=_texto(tarjeta, SELECTORES["fecha"]),
        ))
    return resultados


def sincronizar_ncsa() -> list[ActividadNCSA]:
    """Flujo completo: login -> leer actividad -> cerrar driver."""
    driver = iniciar_sesion()
    try:
        return leer_actividad(driver)
    finally:
        driver.quit()
