# CLAUDE.md — Reglas del proyecto `gael`

## 🔒 REGLA #1 — Privacidad (NUNCA descuidar)

**NUNCA exponer información sensible en archivos versionados.** Toda info sensible
va SIEMPRE en `.env` (que está en `.gitignore` y jamás se sube).

Va en `.env` (privado), nunca en el repo:
- Credenciales, claves, tokens, contraseñas (ej. `TUNEL_CLAVE`).
- Datos personales de Gael: SAT, metas, fechas de examen (`GAEL_*`).
- Contactos: correos y handles de iMessage de Gael y Karla (`EMAIL_*`, `IMESSAGE_*`).
- Cualquier dato privado de una persona (sobre todo de un menor).

En los archivos que SÍ se versionan (`.json`, `.md`, `.py`) solo va info **pública o
genérica**, referenciando las variables del `.env` (ej. `email_env: "EMAIL_GAEL"`).

**Antes de CADA commit/push:** revisar que no se cuele nada sensible. Si aparece,
sacarlo del archivo y moverlo a `.env` antes de subir. El repo es **público**: una
clave o dato personal en el repo queda expuesto a cualquiera.

## Estructura relacionada
- `.env` — datos privados (local, en `.gitignore`). `.env.example` = plantilla sin valores.
- `data/universidades_requisitos.json` — datos PÚBLICOS de admisiones (SAT/Duolingo/TOEFL).
- `envios/` — rutina de envíos (túnel temporal / Drive definitivo). Ver `envios/README.md`.
- `registros/guia_entrevistas_coaches.md` — guía de charlas con coaches.
- `scripts/` — generadores y rutina de envíos.
