"""
Cliente ligero de la Gmail API.

Autenticación OAuth2:
  - gmail_credentials.json : client secret descargado de Google Cloud Console
                             (NO se sube al repo).
  - gmail_token.json       : token de acceso/refresh (se genera en el primer
                             login y tampoco se sube).

Este módulo aísla toda la dependencia de Google para que el resto del proyecto
(el clasificador, los reportes) funcione sin credenciales.
"""
from __future__ import annotations

import base64
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

# Alcance de solo lectura: sincronizamos, no enviamos ni borramos.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

RAIZ = Path(__file__).resolve().parent.parent
CRED_PATH = RAIZ / "gmail_credentials.json"
TOKEN_PATH = RAIZ / "gmail_token.json"


@dataclass
class CorreoCrudo:
    id: str
    remitente: str
    asunto: str
    cuerpo: str
    fecha: str


def _servicio():
    """Construye el servicio de Gmail. Importa las libs de Google de forma
    perezosa para no obligar a instalarlas si sólo se usa el clasificador."""
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    creds = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CRED_PATH.exists():
                raise FileNotFoundError(
                    f"Falta {CRED_PATH.name}. Descárgalo de Google Cloud Console "
                    "(OAuth client, tipo Desktop) y colócalo en la raíz del proyecto."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(CRED_PATH), SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN_PATH.write_text(creds.to_json())
    return build("gmail", "v1", credentials=creds)


def _decodificar_cuerpo(payload: dict) -> str:
    """Extrae el texto plano de un payload de mensaje de Gmail."""
    def _de(data: str) -> str:
        return base64.urlsafe_b64decode(data.encode()).decode("utf-8", "replace")

    if payload.get("mimeType") == "text/plain" and payload.get("body", {}).get("data"):
        return _de(payload["body"]["data"])
    for parte in payload.get("parts", []) or []:
        texto = _decodificar_cuerpo(parte)
        if texto:
            return texto
    return ""


def buscar_correos(query: str, max_resultados: int = 100) -> Iterator[CorreoCrudo]:
    """Itera sobre correos que cumplen una query de Gmail (sintaxis Gmail).

    Ejemplo de query para coaches:
        'newer_than:1y (subject:recruit OR from:.edu OR "swim coach")'
    """
    service = _servicio()
    resp = service.users().messages().list(
        userId="me", q=query, maxResults=min(max_resultados, 500)
    ).execute()
    for meta in resp.get("messages", [])[:max_resultados]:
        msg = service.users().messages().get(
            userId="me", id=meta["id"], format="full"
        ).execute()
        headers = {h["name"].lower(): h["value"] for h in msg["payload"].get("headers", [])}
        yield CorreoCrudo(
            id=msg["id"],
            remitente=headers.get("from", ""),
            asunto=headers.get("subject", ""),
            cuerpo=_decodificar_cuerpo(msg["payload"]),
            fecha=headers.get("date", ""),
        )


# Query por defecto para pescar correos de reclutamiento
QUERY_COACHES = (
    'newer_than:2y ('
    'subject:(recruit OR roster OR scholarship OR swimming OR commit) '
    'OR "swim coach" OR "head coach" OR "recruiting coordinator"'
    ')'
)
