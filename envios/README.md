# envios/ — Compartir reportes con Gael y Karla

Carpeta y **rutina de envíos**: cómo se comparten los reportes generados del
proyecto de reclutamiento con **Gael** y **Karla**.

> **Por qué esto vive en GitHub y no solo en tu compu**
>
> Los reportes se generan **localmente** en `documentos_generados/` (esa carpeta
> está en `.gitignore`, junto con todos los `*.docx/*.pdf/*.xlsx`, así que **no**
> se suben a GitHub). Eso está bien para los archivos pesados, pero significa que
> la *configuración* y la *rutina* de envío deben vivir en el repo para estar
> disponibles en **cualquier** computadora (tu laptop y la Mac de Karla) y en
> sesiones web. Por eso esta carpeta `envios/` (config + rutina) **sí** se
> versiona; los archivos que se envían **no**.

---

## Dos métodos de envío (tú eliges en cada envío)

Por cada envío decides el método según si el archivo es **temporal** o de
**largo plazo**:

### 1. Túnel — para envíos TEMPORALES
- El archivo se sirve por un **túnel que se abre con clave** y **se borra después**.
- **No se manda el archivo:** por **iMessage se envía SOLO EL ENLACE**.
- Efímero: para compartir algo puntual sin dejar copia permanente.
- Los archivos temporales se **estacionan en esta carpeta `envios/`** (local) y
  desde ahí se sirven por el túnel.

### 2. Google Drive — para archivos DEFINITIVOS (largo plazo)
- **Solo se sube cuando tú lo pides** (a solicitud). No es automático.
- El archivo definitivo se **guarda** en la carpeta especial de Drive
  (Unidad compartida): **"Generados x Claude"**
  → https://drive.google.com/drive/folders/1UtggVGvXSAKrKY1nXk7mSjw5Go__yWAJ
- Se comparte **enviando el ENLACE de Drive** a Gael y Karla (compartiendo el
  archivo con sus correos). **Nunca se manda adjunto.**

> La rutina automatiza sobre todo los **temporales** (túnel + iMessage). Lo
> **definitivo** (Drive) queda bajo tu control: se sube únicamente cuando lo
> solicitas.

## Qué se envía

Los reportes que produce el proyecto (se regeneran con los scripts de `scripts/`
y quedan en `documentos_generados/`):

| Reporte | Script que lo genera |
|---|---|
| Tabla de universidades objetivo | `scripts/generar_documentos.py` |
| Cartas de reclutamiento (Tier A) | `scripts/generar_documentos.py` |
| Análisis de coaches | `scripts/generar_analisis_docx.py` |
| Reporte WHOOP | `scripts/whoop_reporte.py` |

## A quién

Definido en [`destinatarios.json`](./destinatarios.json): **Gael** y **Karla**.

## Datos privados (nunca en el repo)

Los correos, la clave del túnel y el grupo de iMessage **no se versionan** — este
repo es público. Viven en el archivo **`.env`** (en la raíz del proyecto, está en
`.gitignore`). La config solo referencia los nombres de variable:

| Dato | Variable en `.env` |
|---|---|
| Clave del túnel | `TUNEL_CLAVE` |
| Correo de Gael | `EMAIL_GAEL` |
| Correo de Karla | `EMAIL_KARLA` |
| iMessage de Gael | `IMESSAGE_GAEL` |
| iMessage de Karla | `IMESSAGE_KARLA` |
| Carpeta de Drive (definitivos) | `DRIVE_CARPETA_ID` |

> El enlace se manda a **Gael y a Karla por separado** (no a un grupo), para que
> funcione desde cualquier equipo donde trabajes.

En cada computadora: copia `.env.example` a `.env` y rellena los valores.

## La rutina (árbol de decisión)

Después de **generar** el reporte/archivo pedido:

1. **Preguntar: ¿LO ENVÍO?**
   - **NO** → el archivo **se guarda** en `documentos_generados/` (carpeta ya
     definida). Fin, no se manda nada.
   - **SÍ** → preguntar **¿temporal o definitivo?**

2. Según la respuesta:

   - **Temporal**
     - El archivo se guarda en la carpeta **`envios/`**.
     - Se sirve por el **túnel**, que se **abre con una clave** (la clave real
       vive en `.env` como `TUNEL_CLAVE` — **no** se escribe en el repo porque es
       público) y se **autoborra**.
     - Se manda por **iMessage** el **enlace del túnel**.

   - **Definitivo**
     - El archivo se guarda en la carpeta de Drive **"Generados x Claude"**.
     - Se manda por **iMessage** el **enlace de Drive**.

3. Cada envío se registra en `envios/historial.md`.

> En los dos casos de envío: **solo enlace, nunca adjunto**, y siempre por iMessage.

## Dónde corre

- **Local (laptop / Mac de Karla):** modo natural. La app de escritorio ve
  `documentos_generados/`, puede abrir el **túnel** y subir a **Drive**.
- **Nube (claude.ai/code, web):** NO ve el disco local. Puede regenerar reportes
  y subir a **Drive** (largo plazo), pero el **túnel** (archivos temporales
  locales) requiere estar en la laptop.

## Pendiente para automatizar

- [ ] Rellenar correos/identificadores de Gael y Karla en `destinatarios.json`.
- [ ] (Opcional) `scripts/enviar_reportes.py` que implemente el flujo: elegir
      método (túnel/drive) → resumen → confirmar → enviar → registrar historial.
