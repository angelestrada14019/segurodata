# Provenance de Fuentes de Datos — SeguroData Bogotá

> **Criterio de concurso:** Datos al Ecosistema 2026 — MinTIC · Reto #2 Seguridad Ciudadana y Justicia  
> **Criterio evaluado:** "Uso de datos abiertos" (peso Alto) — variedad de fuentes, correcta atribución  
> **Nota:** Todos los datasets son de acceso público y gratuito. Licencia CC BY 4.0 salvo indicación contraria.

---

## F1 — Delito de Alto Impacto (DAI)

| Campo | Valor |
|-------|-------|
| **Entidad** | Secretaría Distrital de Seguridad, Convivencia y Justicia (SDSCJ) |
| **Portal** | datosabiertos.bogota.gov.co ✅ datos.gov.co |
| **URL de descarga** | https://datosabiertos.bogota.gov.co/dataset/delito-de-alto-impacto-bogota-d-c |
| **Resource ID** | `7b270013-42ca-436b-9c1e-3bcb7d280c6b` |
| **Formato** | SHP / GeoJSON |
| **Granularidad** | Localidad × año (21 localidades, 2018–2026) |
| **Período** | 2018–presente — semestral |
| **Registros Bronze** | 21 filas |
| **Licencia** | CC BY 4.0 |
| **Rol en pipeline** | EDA histórico 2018–2026 — NO entra al Silver JOIN (sin desglose UPZ) |
| **Archivo Bronze** | `datos/raw/f1_delito_alto_impacto.parquet` |

## F2 — UPZ Shapefile — IDECA

| Campo | Valor |
|-------|-------|
| **Entidad** | Instituto Distrital de Gestión de Riesgos y Cambio Climático (IDECA) / UAECD Catastro |
| **Portal** | serviciosgis.catastrobogota.gov.co (ArcGIS REST) |
| **URL de descarga** | https://serviciosgis.catastrobogota.gov.co/arcgis/rest/services |
| **Resource ID** | `a5c8c591-0708-420f-8eb7-9f3147e21c40` |
| **Formato** | SHP / GeoJSON |
| **Granularidad** | 112 polígonos UPZ |
| **Período** | Estático |
| **Registros Bronze** | 112 polígonos |
| **Licencia** | CC BY 4.0 |
| **Rol en pipeline** | Base geométrica para todos los spatial joins |
| **Archivo Bronze** | `datos/raw/f2_upz.geojson` |

## F3 — Clima Bogotá — Open-Meteo

| Campo | Valor |
|-------|-------|
| **Entidad** | Open-Meteo (open source weather API) |
| **Portal** | archive-api.open-meteo.com |
| **URL de descarga** | https://archive-api.open-meteo.com/v1/archive?latitude=4.711&longitude=-74.072 |
| **Resource ID** | — REST API sin clave ni registro |
| **Formato** | JSON (API REST) |
| **Granularidad** | Hora × variable (Bogotá lat=4.711, lon=-74.072) |
| **Período** | 2020–presente — diaria |
| **Registros Bronze** | 56,112 filas horarias |
| **Licencia** | Open Database License (ODbL) |
| **Rol en pipeline** | +2 cols Silver: temperatura_c, precipitacion_mm_mes |
| **Archivo Bronze** | `datos/raw/f3_clima_bogota.parquet` |

## F4 — Cuadrantes de Policía MEBOG

| Campo | Valor |
|-------|-------|
| **Entidad** | Policía Nacional — Metropolitana de Bogotá (MEBOG) |
| **Portal** | datosabiertos.bogota.gov.co ✅ datos.gov.co |
| **URL de descarga** | https://datosabiertos.bogota.gov.co/dataset/cuadrante-de-policia-mebog |
| **Resource ID** | `f0ad2ee3-bfd0-4825-9b31-bff9041649fa` |
| **Formato** | GeoJSON |
| **Granularidad** | 599 cuadrantes (polígonos) |
| **Período** | Anual |
| **Registros Bronze** | 599 polígonos |
| **Licencia** | CC BY 4.0 |
| **Rol en pipeline** | +2 cols Silver: cuadrantes_por_km2, CAI más cercano |
| **Archivo Bronze** | `datos/raw/f4_cuadrantes.geojson` |

## F5 — Incidentes NUSE 123 — C4

| Campo | Valor |
|-------|-------|
| **Entidad** | Centro de Comando, Control, Comunicaciones y Cómputo (C4) — Secretaría Seguridad |
| **Portal** | datosabiertos.bogota.gov.co ✅ datos.gov.co |
| **URL de descarga** | https://datosabiertos.bogota.gov.co/dataset/incidentes-nuse-123-c4 |
| **Resource ID** | `30d65a8b-d0ed-4e95-977e-0d7cc2ea89ef` |
| **Formato** | CKAN Datastore API (paginación) |
| **Granularidad** | UPZ × mes × tipo incidente (86 tipos) |
| **Período** | 2022–presente — mensual |
| **Registros Bronze** | 128,314 registros |
| **Licencia** | CC BY 4.0 |
| **Rol en pipeline** | BASE DE FILAS Silver: genera las 111,606 filas de silver_upz_mes.parquet |
| **Archivo Bronze** | `datos/raw/f5_nuse_123.parquet` |

## F6 — Hurto a Personas — Policía Nacional

| Campo | Valor |
|-------|-------|
| **Entidad** | Policía Nacional de Colombia |
| **Portal** | www.datos.gov.co ✅ datos.gov.co (Socrata) |
| **URL de descarga** | https://www.datos.gov.co/resource/4rxi-8m8d.json |
| **Resource ID** | `4rxi-8m8d` |
| **Formato** | Socrata JSON API |
| **Granularidad** | Municipio × día (Bogotá = 1 municipio) |
| **Período** | 2010–presente — mensual |
| **Registros Bronze** | 638,569 filas |
| **Licencia** | Datos Abiertos Colombia CC BY 4.0 |
| **Rol en pipeline** | Benchmarking nacional — NO entra al Silver JOIN (sin desglose UPZ) |
| **Archivo Bronze** | `datos/raw/f6_hurto_pn.parquet` |

## F7 — Estratificación por manzana — SDP

| Campo | Valor |
|-------|-------|
| **Entidad** | Secretaría Distrital de Planeación (SDP) |
| **Portal** | datosabiertos.bogota.gov.co ✅ datos.gov.co |
| **URL de descarga** | https://datosabiertos.bogota.gov.co/dataset/estratificacion-por-manzana |
| **Resource ID** | `29f2d770-bd5d-4450-9e95-8737167ba12f` |
| **Formato** | JSON / GeoPackage |
| **Granularidad** | Manzana (polígono) — ~115K manzanas |
| **Período** | Según necesidad |
| **Registros Bronze** | 44,260 registros |
| **Licencia** | CC BY 4.0 |
| **Rol en pipeline** | +1 col Silver: estrato_promedio_upz (promedio ponderado por área) |
| **Archivo Bronze** | `datos/raw/f7_estratificacion.parquet` |

## F8 — Estaciones TransMilenio

| Campo | Valor |
|-------|-------|
| **Entidad** | TransMilenio S.A. |
| **Portal** | gis.transmilenio.gov.co (ArcGIS REST) |
| **URL de descarga** | https://gis.transmilenio.gov.co/arcgis/rest/services |
| **Resource ID** | `9be8b6fb-8059-492f-a866-4a1ac031c502` |
| **Formato** | ArcGIS Feature Service JSON |
| **Granularidad** | 153 puntos (estaciones) |
| **Período** | Estático |
| **Registros Bronze** | 153 estaciones |
| **Licencia** | CC BY 4.0 |
| **Rol en pipeline** | +2 cols Silver: dist_tm_metros (distancia centroide UPZ a TM), n_estaciones_tm |
| **Archivo Bronze** | `datos/raw/f8_transmilenio.geojson` |

## F9 — Boletines SCJ — Sec. Distrital Seguridad

| Campo | Valor |
|-------|-------|
| **Entidad** | Secretaría Distrital de Seguridad, Convivencia y Justicia (SDSCJ) |
| **Portal** | scj.gov.co (no en datos.gov.co — entidad distrital, uso libre) |
| **URL de descarga** | https://scj.gov.co/cifras/estadisticas-mapas |
| **Resource ID** | — scraping web PDFs públicos |
| **Formato** | PDF (boletines mensuales) |
| **Granularidad** | Documento / mes (ciudad completa) |
| **Período** | 2018–presente — mensual |
| **Registros Bronze** | N/A (texto — no filas) |
| **Licencia** | Información pública — uso libre (entidad distrital Bogotá) |
| **Rol en pipeline** | Corpus LLM — GraphRAG (Fase 3) — NO entra en XGBoost |
| **Archivo Bronze** | `datos/raw/boletines_scj/*.pdf` |

## F10 — Noticias RSS — Seguridad Bogotá

| Campo | Valor |
|-------|-------|
| **Entidad** | El Tiempo S.A. / El Espectador (Casa Editorial El Tiempo) |
| **Portal** | RSS público — sin autenticación |
| **URL de descarga** | https://www.eltiempo.com/rss/bogota.xml + https://feeds.elespectador.com/elespectador/justicia |
| **Resource ID** | — feeds RSS públicos |
| **Formato** | RSS/XML (feedparser) |
| **Granularidad** | Artículo / fecha |
| **Período** | Diaria — últimas 100–200 noticias |
| **Registros Bronze** | N/A (texto — no filas) |
| **Licencia** | RSS público — uso no comercial, sin ToS violation |
| **Rol en pipeline** | Corpus LLM — GraphRAG (Fase 3) — NO entra en XGBoost |
| **Archivo Bronze** | `datos/raw/noticias_rss.jsonl` |

## F11 — IDU — Calzada y Estado Superficial

| Campo | Valor |
|-------|-------|
| **Entidad** | Instituto de Desarrollo Urbano (IDU) |
| **Portal** | datosabiertos.bogota.gov.co ✅ (organización IDU) |
| **URL de descarga** | https://datosabiertos.bogota.gov.co/organization/idu |
| **Resource ID** | CC BY 4.0 (datasets SHP/CSV) |
| **Formato** | SHP (geometrías) + CSV (condición superficial) |
| **Granularidad** | Segmento vial (puede spatial-join con UPZ) |
| **Período** | Mensual (último: abr 2026) |
| **Registros Bronze** | ~miles de segmentos viales |
| **Licencia** | CC BY 4.0 |
| **Rol en pipeline** | ⏳ PLANIFICADA Fase 2: feature km_via_intervenida_upz para XGBoost + corpus GraphRAG |
| **Archivo Bronze** | `datos/raw/f11_idu_calzada/` (pendiente) |

## F12 — Plan de Desarrollo Bogotá 2024-2027 — "Bogotá Camina Segura"

| Campo | Valor |
|-------|-------|
| **Entidad** | Secretaría Distrital de Planeación (SDP) / Alcaldía Mayor de Bogotá |
| **Portal** | sdp.gov.co — documento público oficial |
| **URL de descarga** | https://sdp.gov.co/pdd-bogota-camina-segura + Acuerdo 927 de 2024 — Concejo de Bogotá |
| **Resource ID** | — documento público (Acuerdo 927/2024) |
| **Formato** | PDF + Excel (Anexo 2: 424 metas) |
| **Granularidad** | Ciudad (sin desglose UPZ) |
| **Período** | Estático (aprobado sep 2024) |
| **Registros Bronze** | 1 PDF + 424 metas tabuladas |
| **Licencia** | Documento público — uso libre |
| **Rol en pipeline** | ⏳ PLANIFICADA Fase 3: corpus GraphRAG para Claude API (contexto político-institucional) |
| **Archivo Bronze** | `datos/raw/f12_pdd/` (pendiente) |

---

## Variables causales identificadas — ¿Por qué ocurre el crimen?

Esta tabla documenta las variables causales que explican el incremento o reducción del crimen en una UPZ, con evidencia empírica citada. Es la base del análisis "¿qué hacer?" del Módulo 3 (Recomendación) vía Claude API.

| Variable causal | Evidencia empírica | Fuente en SeguroData | Estado |
|-----------------|-------------------|---------------------|--------|
| Estrato socioeconómico bajo | Correlación histórica NUSE × estrato (SDSCJ Bogotá 2020–2024); mayor exposición a crimen de oportunidad | F7 → feature `estrato_promedio_upz` | ✅ Implementado |
| Baja densidad policial (cuadrantes/km²) | Riascos, Anzola & Bohórquez (2016) — Modelo estadístico de crimen en Bogotá, UNAL | F4 → feature `cuadrantes_por_km2` | ✅ Implementado |
| Alta distancia a TransMilenio | Mayor vulnerabilidad peatonal en zonas de baja cobertura de transporte masivo (Flórez & Gómez 2019) | F8 → feature `dist_tm_metros` | ✅ Implementado |
| Temperatura alta / baja precipitación | Teoría de actividades rutinarias (Cohen & Felson 1979); validado para Bogotá (SCJ 2022) | F3 → features `temperatura_c`, `precipitacion_mm` | ✅ Implementado |
| Subregistro alto (ratio NUSE/delitos formales) | SCJ Boletín dic 2024: 30–40% subregistro en estratos 1–2; NUSE capta incidentes no denunciados | F5 → feature `ratio_nuse_delitos_upz` | ✅ Implementado |
| Obras viales activas (IDU) | Desplazamiento de residentes, reducción iluminación nocturna, flujo de trabajadores → oportunidad de hurto (SCJ Observatorio 2023) | F11 IDU → feature `km_via_intervenida_upz` | ⏳ Fase 2 |
| Incumplimiento metas Plan de Desarrollo seguridad | Acuerdo 927 de 2024 — programa "Bogotá avanza en seguridad" ($7.5 billones COP); seguimiento SDP 2025 | F12 PDD → GraphRAG corpus | ⏳ Fase 3 |
| Desempleo local | DANE ECV Bogotá 2023: correlación hurto × tasa desempleo por UPZ (r=0.62) | No implementado — DANE microdatos requieren procesamiento especial | ❌ Descartado por complejidad |

---

## Cumplimiento criterios del concurso "Datos al Ecosistema 2026"

| Criterio del concurso | Evidencia en SeguroData | Estado |
|-----------------------|------------------------|--------|
| ≥ 10,000 filas en dataset principal | Silver: **111,606 filas × 20 columnas** (F5 NUSE como base) | ✅ |
| Repositorio GitHub público + README completo | https://github.com/angelestrada14019/segurodata | ✅ |
| Datos de datos.gov.co | F1, F4, F5, F6, F7 registrados en portal nacional | ✅ (5 de 10 fuentes) |
| Variedad de fuentes (no solo un dataset) | 10 fuentes activas de 8 plataformas distintas | ✅ |
| Correcta atribución | Este documento — URL y Resource ID para cada fuente | ✅ |
| No datos privados ni de pago | Todas las fuentes son públicas y gratuitas | ✅ |
| Reproducible (instrucciones instalación) | `pip install -r requirements.txt; python src/pipeline.py` | ✅ |
| 6 notebooks CRISP-ML documentados | SeguroData_01 a _06 (01 completo, 02–06 en progreso) | ⏳ En progreso |

---

## Fuentes investigadas y descartadas

Durante la investigación se evaluaron 20+ fuentes. Las siguientes se descartaron por incompatibilidad con el modelo UPZ:

| Fuente | ID Socrata / URL | Por qué se descarta |
|--------|----------------|---------------------|
| HOMICIDIO PN | m8fd-ahd9 | Granularidad municipio/departamento — sin desglose UPZ |
| HURTO ABIGEATO PN | p88b-5ac7 | Granularidad municipio/departamento |
| Lesiones no fatales Medicina Legal | 79dd-d24f | Granularidad municipio/departamento |
| Lesiones fatales Medicina Legal | 2kpj-cktv | Granularidad municipio/departamento |
| Incautación estupefacientes PN | kk69-w2jj | Granularidad municipio/departamento |
| SIEDCO Fiscalía General | 2bxu-b96f | Endpoint 404 — no disponible a mayo 2026 |
| Twitter/X #inseguridad | API — $100+/mes | Viola reglas del concurso (scraping redes sociales) + costo |
| SCJ histórico tabular 2015–2017 | scj.gov.co Observatorio | Solo dashboards web, sin exportación masiva; 2018–2026 ya cubierto por F1 |

> Para contexto completo de las 20 fuentes investigadas, ver `docs/INVESTIGACION_FUENTES.md`.
