# Reclutamiento — Gael Moreno Sarmiento

Herramientas en Python para el proceso de reclutamiento universitario de natación:
análisis de correos de **coaches** y **universidades (Unis)**, sincronización con
**NCSA**, scraping de tiempos (SwimCloud), datos de WHOOP y generación de
documentos.

> **Nota:** el proyecto original corre localmente en la Mac de Karla. Este repo
> contiene el módulo de **análisis de correos + integración NCSA**, construido
> para funcionar contra la cuenta de coaches (`gmail_credentials.json`).

---

## Estructura del repo (carpetas que se editan)

```
gael/
├── correos/                  # análisis de correos (Coaches / Unis)
│   ├── clasificador.py       #   ← núcleo: clasifica y extrae datos (sin deps)
│   ├── analisis.py           #   agrega por universidad y coach → reportes
│   └── gmail_client.py       #   lee correos vía Gmail API (OAuth)
├── ncsa/                     # integración con NCSA
│   ├── scraper.py            #   login web con Selenium + lectura de actividad
│   └── cloudflare.py         #   cookies de Chrome + curl_cffi (SwimCloud/WAF)
├── scripts/                  # puntos de entrada
│   ├── demo_clasificador.py  #   ← prueba TODO sin credenciales
│   └── gmail_coaches_sync.py #   sync real de Gmail → registros/
├── registros/                # salidas versionables (coaches.json, universidades.md)
├── data/                     # datos de ejemplo (correos_ejemplo.json)
├── tests/                    # tests del clasificador
├── config.py                 # rutas + carga de .env
├── requirements.txt
├── .env.example              # plantilla de credenciales (.env nunca se sube)
└── .gitignore
```

---

## Cómo interactúa con NCSA, correos, Unis y Coaches

### 1. Correos (Gmail) → Coaches / Unis
`correos/gmail_client.py` lee mensajes de la cuenta de coaches vía **Gmail API**
(OAuth de solo lectura). Cada correo pasa por `correos/clasificador.py`, que decide:

| Categoría | Cómo se detecta |
|---|---|
| **COACH** | dominio `.edu` + firma/palabras de coach ("Head Swimming Coach"), no institucional |
| **UNIVERSIDAD** | `.edu` o dirección institucional (`admissions@`, `athletics@`) con contexto de reclutamiento |
| **PLATAFORMA** | dominio conocido (NCSA, AthletesUSA, …) |
| **OTRO** | sin relación |

Además extrae **universidad** (del dominio), **división** (NCAA D1/D2/D3, NAIA,
NJCAA/JUCO) y **nombre del coach**. `correos/analisis.py` agrega todo y escribe
`registros/coaches.json` + `registros/universidades.md`.

### 2. NCSA (portal de reclutamiento)
NCSA **no tiene API pública**. `ncsa/scraper.py` inicia sesión con **Selenium**
(Chrome real) usando `NCSA_EMAIL` / `NCSA_PASSWORD` del `.env`, y lee la
actividad: qué coaches vieron el perfil, qué universidades marcaron interés,
mensajes, etc. Los selectores están centralizados en `SELECTORES` para
sobrevivir cambios de maquetado.

### 3. Cloudflare (SwimCloud)
Sitios detrás de Cloudflare WAF se resuelven con `ncsa/cloudflare.py`: importa
las cookies activas de Chrome (`browser_cookie3`) y hace la request con
`curl_cffi` imitando el fingerprint TLS de Chrome — sin abrir un browser
completo. Fallback: Selenium.

---

## Empezar

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Probar TODO el pipeline SIN credenciales:
python3 scripts/demo_clasificador.py

# Correr los tests:
python3 tests/test_clasificador.py
```

### Con credenciales
```bash
cp .env.example .env               # rellena NCSA_*, WHOOP_*, etc.
# coloca gmail_credentials.json en la raíz (OAuth Desktop de Google Cloud Console)

python3 scripts/gmail_coaches_sync.py           # sync real de coaches
python3 scripts/gmail_coaches_sync.py --query 'newer_than:6m from:.edu'
```

ChromeDriver debe coincidir con tu versión de Chrome:
https://googlechromelabs.github.io/chrome-for-testing/

---

## Pendiente
- Activar `gmail_coaches_sync.py` por **cron** (aún no automático).
- Parser de MeetMobile (endpoints inestables).

## Credenciales
Todo en `.env` / `gmail_credentials.json`, **nunca** al repo (ver `.gitignore`).
Sin base de datos: los registros viven en `.md` / `.json` bajo `registros/`.
