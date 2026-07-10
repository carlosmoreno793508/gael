"""Configuración central: rutas del proyecto y carga de .env."""
from __future__ import annotations

from pathlib import Path

RAIZ = Path(__file__).resolve().parent
REGISTROS = RAIZ / "registros"
DATA = RAIZ / "data"

REGISTROS.mkdir(exist_ok=True)


def cargar_env() -> None:
    """Carga variables de .env si python-dotenv está instalado. No falla si no."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv(RAIZ / ".env")
