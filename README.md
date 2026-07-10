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
├── natacion/                 # tiempos de SwimCloud
│   ├── swimcloud.py          #   scraping del perfil público (vía WAF)
│   ├── registro.py           #   escribe registros/natacion.md
│   └── fit.py                #   fit por prueba: tiempos vs estándares NCSA
├── whoop/                    # API no oficial de WHOOP (OAuth2)
│   └── client.py             #   recuperación / HRV / RHR
├── reclutamiento/            # universidades objetivo (fuentes reales)
│   ├── universidades.py      #   normaliza y fusiona NCSA + SwimCloud + Contactos
│   └── priorizar.py          #   heurística de prioridad (división + ranking + beca)
├── documentos/               # generación de documentos
│   ├── tabla_universidades.py#   Word + Excel de universidades objetivo
│   ├── carta_reclutamiento.py#   carta personalizada a un coach (Word)
│   └── nutricion_pdf.py      #   plan de nutrición/suplementación (PDF)
├── scripts/                  # puntos de entrada
│   ├── demo_clasificador.py  #   ← prueba el análisis de correos (sin credenciales)
│   ├── natacion_update.py    #   ← actualiza natacion.md (SwimCloud público)
│   ├── whoop_update.py       #   actualiza whoop.md
│   ├── generar_documentos.py #   genera docx/xlsx/pdf
│   ├── construir_objetivo.py #   ← construye la lista OFICIAL de universidades (datos de Karla)
│   ├── priorizar_universidades.py# prioriza y rellena prioridad → registros/priorizacion.md
│   ├── cruce_ncsa.py         #   cruce histórico NCSA (Karla) × lista de ejemplo previa
│   └── gmail_coaches_sync.py #   sync real de Gmail → registros/
├── registros/                # salidas versionables (natacion.md, whoop.md, cruce_ncsa.md, universidades_maestro.json…)
├── data/                     # fuentes reales (karla_*.json, universidades_objetivo.json) + ejemplos
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

### Universidades objetivo (fuente oficial)
`data/universidades_objetivo.json` es la lista **oficial** de universidades: 50
programas reales (D1/D2/D3/NAIA) provenientes del análisis de reclutamiento de
Karla, unificando tres fuentes: **NCSA**, **SwimCloud** y **Contactos Colegios**
(carpeta NCSA en Drive). Cada entrada trae coach principal, plantel de coaches,
email, teléfono, conferencia, ranking divisional y de qué fuente salió.

Se regenera de forma reproducible desde las fuentes crudas de Karla:
```bash
python3 scripts/construir_objetivo.py     # data/karla_*.json → universidades_objetivo.json
```
El script `scripts/cruce_ncsa.py` es el análisis histórico que documenta el
antes/después de adoptar estos datos (la lista de ejemplo previa tenía coaches
ficticios; ver `registros/cruce_ncsa.md`).

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

# Pipeline de universidades (datos reales de Karla, sin credenciales):
python3 scripts/construir_objetivo.py       # karla_*.json → universidades_objetivo.json (50)
python3 scripts/priorizar_universidades.py  # rellena prioridad → registros/priorizacion.md
python3 scripts/generar_documentos.py       # tabla + cartas (prioridad alta) → documentos_generados/

# Otros (datos de ejemplo de data/):
python3 scripts/demo_clasificador.py    # clasifica correos → registros/coaches.json + universidades.md
python3 scripts/natacion_update.py       # tiempos → registros/natacion.md
python3 scripts/whoop_update.py          # recuperación → registros/whoop.md

# Correr los tests:
python3 tests/test_clasificador.py
```

### Con credenciales
```bash
cp .env.example .env               # rellena NCSA_*, WHOOP_*, etc.
# coloca gmail_credentials.json en la raíz (OAuth Desktop de Google Cloud Console)

python3 scripts/gmail_coaches_sync.py           # sync real de coaches
python3 scripts/gmail_coaches_sync.py --query 'newer_than:6m from:.edu'
python3 scripts/natacion_update.py --swimmer 1234567   # perfil real de SwimCloud
python3 scripts/whoop_update.py --live                 # API real de WHOOP
```

ChromeDriver debe coincidir con tu versión de Chrome:
https://googlechromelabs.github.io/chrome-for-testing/

---

## Pendiente
- **Tiempos actuales de Gael:** los archivos de Karla (`Tiempos/PB Gael Moreno.xlsx`)
  llegan solo hasta 2018 (categoría S8/S9). El motor de fit (`natacion/fit.py`,
  `scripts/fit_por_prueba.py`) ya funciona; falta alimentarlo con sus marcas
  vigentes (idealmente desde su perfil de SwimCloud vía `natacion_update.py`).
- **Estándares por división:** el PDF de NCSA da un solo nivel élite, no cortes
  D1/D2/D3. Para un fit por división habría que sumar tablas de reclutamiento
  (CollegeSwimming/SwimCloud) por división y género.
- Activar `gmail_coaches_sync.py` por **cron** (aún no automático).
- Parser de MeetMobile (endpoints inestables).

## Credenciales
Todo en `.env` / `gmail_credentials.json`, **nunca** al repo (ver `.gitignore`).
Sin base de datos: los registros viven en `.md` / `.json` bajo `registros/`.
