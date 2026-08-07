#!/usr/bin/env python3
"""
enviar_reportes.py — Rutina de envios a Gael y Karla.

Flujo (arbol de decision):
  1. Tomar un archivo (argumento) o elegir uno de documentos_generados/.
  2. Preguntar: ¿LO ENVIO?
       NO  -> el archivo se queda en documentos_generados/. Fin.
       SI  -> preguntar: temporal o definitivo.
  3. Temporal:
       - copia el archivo a envios/
       - abre el tunel (con TUNEL_CLAVE) y obtiene el enlace
       - manda por iMessage SOLO el enlace, a Gael y Karla POR SEPARADO
  4. Definitivo:
       - sube el archivo a la carpeta de Drive (DRIVE_CARPETA_ID)
       - manda por iMessage el enlace de Drive, a Gael y Karla por separado
  5. Registra el envio en envios/historial.md

Datos privados: en .env (TUNEL_CLAVE, EMAIL_*, IMESSAGE_*, DRIVE_CARPETA_ID,
y opcionalmente TUNEL_CMD / DRIVE_SUBIR_CMD). El .env NO se sube al repo.

Nota: el envio real por iMessage y el tunel corren en tu Mac. Desde otro equipo
el script prepara todo y te deja el enlace para mandarlo a mano.

Uso:
    python3 scripts/enviar_reportes.py [ruta/al/archivo]
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ENV_PATH = RAIZ / ".env"
CONFIG_PATH = RAIZ / "envios" / "destinatarios.json"
CARPETA_ENVIOS = RAIZ / "envios"
CARPETA_DOCS = RAIZ / "documentos_generados"
HISTORIAL = CARPETA_ENVIOS / "historial.md"


# --------------------------------------------------------------------------- #
# .env y configuracion
# --------------------------------------------------------------------------- #
def cargar_env() -> None:
    """Carga .env en el entorno (sin dependencias externas)."""
    if not ENV_PATH.exists():
        return
    for linea in ENV_PATH.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        clave, _, valor = linea.partition("=")
        os.environ.setdefault(clave.strip(), valor.strip())


def env(nombre: str, default: str = "") -> str:
    return os.environ.get(nombre, default).strip()


def cargar_destinatarios() -> list[dict]:
    """Lee envios/destinatarios.json y resuelve correos/handles desde el .env."""
    cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    dests: list[dict] = []
    for d in cfg.get("destinatarios", []):
        if not d.get("activo", True):
            continue
        dests.append(
            {
                "nombre": d.get("nombre", "?"),
                "email": env(d["email_env"]) if d.get("email_env") else d.get("email", ""),
                "imessage": env(d["imessage_env"]) if d.get("imessage_env") else d.get("imessage", ""),
            }
        )
    return dests


# --------------------------------------------------------------------------- #
# Interaccion
# --------------------------------------------------------------------------- #
def preguntar(texto: str) -> str:
    try:
        return input(texto).strip()
    except EOFError:
        return ""


def si_no(texto: str) -> bool:
    return preguntar(f"{texto} [s/N]: ").lower() in {"s", "si", "sí", "y", "yes"}


def elegir_archivo(argv: list[str]) -> Path | None:
    """Toma el archivo del argumento, o deja elegir uno de documentos_generados/."""
    if argv:
        p = Path(argv[0]).expanduser()
        if not p.exists():
            print(f"No existe el archivo: {p}")
            return None
        return p
    if not CARPETA_DOCS.exists():
        print(f"No hay carpeta {CARPETA_DOCS}. Genera un reporte primero.")
        return None
    archivos = sorted(
        (f for f in CARPETA_DOCS.iterdir() if f.is_file()),
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    )
    if not archivos:
        print(f"No hay archivos en {CARPETA_DOCS}. Genera un reporte primero.")
        return None
    print("\nArchivos en documentos_generados/ (mas reciente primero):")
    for i, f in enumerate(archivos, 1):
        print(f"  {i}. {f.name}")
    sel = preguntar("Elige el numero del archivo a enviar: ")
    if not sel.isdigit() or not (1 <= int(sel) <= len(archivos)):
        print("Seleccion invalida.")
        return None
    return archivos[int(sel) - 1]


# --------------------------------------------------------------------------- #
# Canales
# --------------------------------------------------------------------------- #
def _extraer_url(salida: str) -> str:
    for linea in reversed(salida.strip().splitlines()):
        linea = linea.strip()
        if linea.startswith("http://") or linea.startswith("https://"):
            return linea
    return ""


def abrir_tunel_temporal(archivo: Path, clave: str) -> str:
    """Sirve el archivo por un tunel temporal (se abre con clave, se autoborra).

    Enchufa tu herramienta via TUNEL_CMD en el .env. Es una plantilla que puede
    usar {archivo} y {clave}; debe imprimir la URL del tunel en su salida.
    """
    cmd_tpl = env("TUNEL_CMD")
    if not cmd_tpl:
        print("  [tunel] No hay TUNEL_CMD en .env.")
        print(f"          Abre el tunel manualmente para: {archivo}  (clave: {clave})")
        return preguntar("  Pega aqui la URL del tunel (o Enter para cancelar): ")
    cmd = cmd_tpl.format(archivo=str(archivo), clave=clave)
    print(f"  [tunel] Ejecutando tu comando de tunel...")
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    url = _extraer_url(res.stdout)
    if not url:
        if res.stdout:
            print(res.stdout)
        if res.stderr:
            print(res.stderr)
        url = preguntar("  No detecte la URL. Pegala aqui: ")
    return url


def subir_a_drive(archivo: Path) -> str:
    """Sube el archivo definitivo a la carpeta de Drive y devuelve el enlace.

    Enchufa tu metodo via DRIVE_SUBIR_CMD en el .env (plantilla con {archivo} y
    {carpeta}); debe imprimir el enlace de Drive. Si no esta configurado, pide
    subirlo a mano y pegar el enlace.
    """
    carpeta = env("DRIVE_CARPETA_ID")
    cmd_tpl = env("DRIVE_SUBIR_CMD")
    if not cmd_tpl:
        print("  [Drive] No hay DRIVE_SUBIR_CMD en .env.")
        print(f"          Sube '{archivo.name}' a la carpeta de Drive (id {carpeta}).")
        return preguntar("  Pega aqui el enlace de Drive: ")
    cmd = cmd_tpl.format(archivo=str(archivo), carpeta=carpeta)
    print("  [Drive] Subiendo a Drive con tu comando...")
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    url = _extraer_url(res.stdout)
    if not url:
        if res.stdout:
            print(res.stdout)
        if res.stderr:
            print(res.stderr)
        url = preguntar("  No detecte el enlace. Pegalo aqui: ")
    return url


def enviar_imessage(handle: str, mensaje: str) -> bool:
    """Envia un iMessage via la app Messages. Solo funciona en macOS."""
    if not handle:
        print("  [iMessage] Falta el handle (rellena IMESSAGE_* en .env). Omitido.")
        return False
    if sys.platform != "darwin":
        print(f"  [iMessage] (No es Mac) Envia manual a {handle}:  {mensaje}")
        return False
    applescript = (
        'on run {b, m}\n'
        '  tell application "Messages"\n'
        '    set s to 1st service whose service type = iMessage\n'
        '    send m to buddy b of s\n'
        '  end tell\n'
        'end run'
    )
    try:
        subprocess.run(
            ["osascript", "-e", applescript, handle, mensaje],
            check=True,
            capture_output=True,
            text=True,
        )
        print(f"  [iMessage] Enviado a {handle}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  [iMessage] Error enviando a {handle}: {e.stderr or e}")
        return False


# --------------------------------------------------------------------------- #
# Historial
# --------------------------------------------------------------------------- #
def registrar_historial(archivo: Path, tipo: str, dests: list[dict], enlace: str) -> None:
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
    para = ", ".join(d["nombre"] for d in dests) or "-"
    canal = "iMessage (túnel)" if tipo == "temporal" else "iMessage (Drive)"
    fila = f"| {fecha} | {para} | {archivo.name} | {canal} | {enlace} |\n"
    if not HISTORIAL.exists():
        HISTORIAL.write_text(
            "# Historial de envíos\n\n"
            "| Fecha | Para | Reporte | Canal | Enlace |\n"
            "|---|---|---|---|---|\n",
            encoding="utf-8",
        )
    with HISTORIAL.open("a", encoding="utf-8") as fh:
        fh.write(fila)
    print(f"  [historial] Registrado en {HISTORIAL.relative_to(RAIZ)}")


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main() -> int:
    cargar_env()
    archivo = elegir_archivo(sys.argv[1:])
    if archivo is None:
        return 1

    print(f"\nArchivo: {archivo.name}")

    # 2. ¿LO ENVIO?
    if not si_no("¿LO ENVÍO?"):
        # NO -> se queda en documentos_generados/
        CARPETA_DOCS.mkdir(exist_ok=True)
        if archivo.parent != CARPETA_DOCS:
            destino = CARPETA_DOCS / archivo.name
            shutil.copy2(archivo, destino)
            print(f"No se envía. Guardado en {destino.relative_to(RAIZ)}")
        else:
            print(f"No se envía. Queda en {archivo.relative_to(RAIZ)}")
        return 0

    # SI -> temporal o definitivo
    opt = preguntar("¿Temporal o definitivo? [t/d]: ").lower()
    tipo = "temporal" if opt.startswith("t") else "definitivo" if opt.startswith("d") else ""
    if not tipo:
        print("Opción inválida. Cancelado.")
        return 1

    dests = cargar_destinatarios()

    if tipo == "temporal":
        CARPETA_ENVIOS.mkdir(exist_ok=True)
        en_envios = CARPETA_ENVIOS / archivo.name
        if archivo.resolve() != en_envios.resolve():
            shutil.copy2(archivo, en_envios)
        print(f"Copiado a {en_envios.relative_to(RAIZ)}")
        enlace = abrir_tunel_temporal(en_envios, env("TUNEL_CLAVE"))
    else:
        enlace = subir_a_drive(archivo)

    if not enlace:
        print("Sin enlace. Cancelado (no se envió nada).")
        return 1

    # Resumen y confirmacion final antes de disparar los iMessage
    print("\nResumen del envío:")
    print(f"  Tipo:   {tipo}")
    print(f"  Enlace: {enlace}")
    print(f"  Para (por separado): {', '.join(d['nombre'] for d in dests)}")
    if not si_no("¿Confirmo y mando el enlace por iMessage?"):
        print("Cancelado. El enlace ya está listo arriba por si lo mandas a mano.")
        return 0

    # Envio POR SEPARADO a cada destinatario
    for d in dests:
        print(f"- {d['nombre']}:")
        enviar_imessage(d["imessage"], enlace)

    registrar_historial(archivo, tipo, dests, enlace)
    print("\nListo.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
