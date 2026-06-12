# Investigación de Fuentes de Datos

> Esta página documenta el **proceso de investigación** de fuentes — qué se evaluó, por qué se activó o descartó cada candidato. Para los metadatos completos (URLs, Resource IDs, licencias) de las fuentes activas, ver [[Provenance]].

---

## Plataformas de datos — distinción crítica

Confundir estas plataformas genera errores 404:

| Portal | Plataforma | SDK correcto |
|--------|-----------|-------------|
| `datosabiertos.bogota.gov.co` | **CKAN** | `requests` + `/api/3/action/datastore_search` (ver `src/etl.py`) |
| `www.datos.gov.co` | **Socrata** | `sodapy` — `Socrata("www.datos.gov.co", token)` |
| `data-movilidadbogota.opendata.arcgis.com` | **ArcGIS Hub** | `arcgis_query()` en `src/etl.py` |
| `serviciosgis.catastrobogota.gov.co` | **ArcGIS REST** | `arcgis_query()` en `src/etl.py` |

> **App Token Socrata:** Sin token el límite es 1,000 filas/request. Registrar token gratis en dev.socrata.com y pasar como `app_token` para subir a 50,000 filas/request.

---

## Fuentes activas — resumen (ver Provenance para detalles)

Las 14 fuentes activas del proyecto, organizadas por grupo:

**Grupo 1 — Estructuradas → XGBoost + mapa:**
F1 (DAI), F2 (UPZ), F3 (Clima), F4 (Cuadrantes), F5 (NUSE 123 ★), F6 (Hurto PN — benchmarking), F7 (Estratificación), F8 (TransMilenio), F11 (IDU Obras), F13 (Cámaras SDM), F14 (Alumbrado UAESP)

**Grupo 2 — Texto → GraphRAG + pgvector:**
F9 (Boletines SCJ), F10 (RSS × 3 feeds: El Tiempo, Espectador, El Informante Soy Yo)

**Planificada (Fase 3):**
F12 — Plan de Desarrollo Bogotá 2024-2027 (Acuerdo 927/2024) — corpus GraphRAG adicional

---

## Fuentes investigadas y descartadas

Durante la investigación (mayo 2026) se evaluaron 20+ fuentes. Las siguientes no se incorporaron al modelo activo:

### Descartadas automáticamente — granularidad insuficiente (sin desglose UPZ)

| Fuente | ID / URL | Motivo |
|--------|---------|--------|
| HOMICIDIO PN | Socrata `m8fd-ahd9` | Solo municipio/departamento — sin UPZ |
| HURTO ABIGEATO PN | Socrata `p88b-5ac7` | Solo municipio/departamento |
| Lesiones no fatales Medicina Legal | Socrata `79dd-d24f` | Solo localidad — sin UPZ. Requeriría cruce indirecto |
| Lesiones fatales Medicina Legal | Socrata `2kpj-cktv` | Solo municipio/departamento |
| Incautación estupefacientes PN | Socrata `kk69-w2jj` | Solo municipio |
| Tasa Desempleo SDDE | datosabiertos.bogota.gov.co | Solo ciudad completa — sin desglose UPZ |
| Banco de la República SUAMECA | suameca.banrep.gov.co | Solo nivel departamental |
| Encuesta Multipropósito Bogotá 2021 | microdatos.dane.gov.co | `cod_upz` disponible pero solo en microdatos protegidos; última disponible 2021 |
| Fiscalía General | fiscalia.gov.co | Solo nivel municipal |

### Descartadas por inaccesibilidad técnica o costo

| Fuente | Motivo |
|--------|--------|
| SIEDCO `2bxu-b96f` | Endpoint 404 en CKAN Bogotá — no existe como dataset tabular descargable |
| Twitter/X `#inseguridad` | API de pago ($100+/mes) — viola reglas del concurso |
| Cámaras CCTV seguridad C4 | Sin API pública — circuito cerrado de la Secretaría (Ley 1581/2012) |
| Google Street View | API de pago para 150K+ imágenes — viola restricción de costos |
| Redes sociales scraping | Viola términos de uso y reglas del concurso |
| Siniestros Viales CKAN Bogotá | STALE — última actualización oct 2021 |

### Investigadas pero de baja prioridad para la entrega

Estas fuentes son técnicamente viables pero requieren más trabajo de integración del que justifica su aporte marginal al modelo, dado el cronograma del concurso:

| Fuente | Por qué no se priorizó |
|--------|----------------------|
| OpenStreetMap POI (bares, ATMs, parques) vía Overpass API | Requiere `overpy` + spatial join adicional. La evidencia causal existe (Springer 2024, PMC 2012) pero F11/F13/F14 ya cubren los vectores de intervención más relevantes |
| VIIRS Nighttime Lights (NASA/NOAA) | F14 (Alumbrado UAESP) ya captura iluminación a nivel UPZ. VIIRS requeriría `rasterio` + `rasterstats` + descarga de GeoTIFFs mensuales |
| Grupo de Uso Económico por manzana (UAECD) | Candidato válido para una segunda iteración del modelo — densidad comercial es predictor de crimen. Requiere spatial join + agregación por UPZ. No en scope v1 |
| Dane Censo 2018 microdatos | El `estrato_promedio_upz` de F7 ya captura la dimensión socioeconómica principal |
| SCJ histórico tabular 2015–2017 | Solo dashboards web sin exportación masiva; 2018-2026 ya cubierto por F1 |
| El Periodista Soy Yo / Noticias Caracol | Contenido audiovisual — ciudadanos envían videos a TV. Sin RSS de texto integrable |

---

## Nota sobre el SIEDCO

El ID `2bxu-b96f` (SIEDCO) da 404 en CKAN Bogotá y no existe como dataset tabular descargable a mayo 2026. La fuente equivalente y más reciente es **F1 — Delito de Alto Impacto** (`7b270013-42ca-436b-9c1e-3bcb7d280c6b`), que cubre 2018-2026 y tiene desglose por UPZ. Para crimen con geolocalización individual, **F5 — NUSE 123** es la fuente principal del modelo.
