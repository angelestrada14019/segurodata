# DATOS.md — Catálogo de Fuentes de Datos

> Referencia completa de todos los datasets, APIs y fuentes geoespaciales del proyecto.
> **Última verificación:** 20 mayo 2026 — 20 fuentes documentadas. Ver `src/validar_fuentes.py` para validación automática.

---

## Plataformas de datos: CKAN vs Socrata vs ArcGIS

**Distinción crítica** — confundirlos genera 404:

| Portal | Plataforma | SDK/método correcto |
|--------|-----------|-------------------|
| `datosabiertos.bogota.gov.co` | **CKAN** | `requests` + API `/api/3/action/datastore_search` |
| `www.datos.gov.co` | **Socrata** | `sodapy` — `Socrata("www.datos.gov.co", token)` |
| `datos.movilidadbogota.gov.co` | **ArcGIS Hub** | `arcgis_query()` en `src/etl.py` |

> **SIEDCO `2bxu-b96f`**: Este ID da 404 en CKAN. No existe como dataset tabular independiente. Usar **Delito de Alto Impacto** (FUENTE 2) — mismo origen, más reciente y con coordenadas.

---

## Conectores ETL en src/etl.py

```python
from src.etl import ckan_query, ckan_query_all, ckan_download  # CKAN Bogotá
from src.etl import socrata_query                               # datos.gov.co
from src.etl import arcgis_query                               # SDM / Catastro
from src.etl import open_meteo                                  # Clima histórico
```

---

## SDK recomendado: sodapy (solo para datos.gov.co)

Para `www.datos.gov.co` (portal nacional — Policía, Medicina Legal) usar `sodapy`.

```bash
pip install sodapy
```

```python
from sodapy import Socrata
import pandas as pd

def descargar_socrata(portal, dataset_id, app_token=None, where_clause=None, limit=50000):
    """Descarga paginada con sodapy. Registrar token gratis en dev.socrata.com."""
    client = Socrata(portal, app_token)
    todos = []
    offset = 0
    while True:
        params = {"limit": limit, "offset": offset}
        if where_clause:
            params["where"] = where_clause
        batch = client.get(dataset_id, **params)
        if not batch:
            break
        todos.extend(batch)
        offset += limit
    client.close()
    return pd.DataFrame(todos)

# Descarga incremental (solo registros nuevos)
def descargar_incremental(portal, dataset_id, campo_fecha, ultima_fecha, app_token=None):
    where = f"{campo_fecha} > '{ultima_fecha}'"
    return descargar_socrata(portal, dataset_id, app_token=app_token, where_clause=where)
```

> **Importante:** Sin token el límite es 1000 filas/request. Registrar App Token gratis en dev.socrata.com y pasarlo como `app_token` para subir a 50000 filas/request.

---

## Fuentes primarias de crimen

### 1. SIEDCO — Sistema de Información Estadístico, Delincuencial, Contravencional y Operativo

- **Portal:** datosabiertos.bogota.gov.co
- **ID Socrata:** `2bxu-b96f`
- **Período:** Hasta diciembre 2024 (verificar si hay actualización 2025 en el portal)
- **Formato:** JSON via Socrata API / CSV descarga directa
- **Cobertura:** Todos los delitos registrados en Bogotá con georreferencia
- **Variables clave:** fecha_hecho, hora_hecho, localidad, upz, barrio, conducta, latitud, longitud
- **Actualización:** Periódica (verificar frecuencia en portal)
- **Licencia:** Consultar portal
- **Riesgo:** Dataset puede no tener datos de 2025. Ver también dataset #2 (Delito de Alto Impacto) que sí cubre hasta 2026.
- **Nota:** Si los datos por registro no están disponibles: escribir a `dijin.aicri-jef@policia.gov.co` — 10 días hábiles de respuesta.

```python
df_siedco = descargar_socrata("datosabiertos.bogota.gov.co", "2bxu-b96f")
```

---

### 2. Delito de Alto Impacto — Secretaría Distrital de Seguridad ⭐ FUENTE PRINCIPAL

- **Portal:** datosabiertos.bogota.gov.co
- **ID Socrata:** `7b270013-42ca-436b-9c1e-3bcb7d280c6b`
- **Período:** Enero 2018 – marzo 2026 (**actualizado 20 abril 2026** ✅)
- **Organización:** Secretaría Distrital de Seguridad, Convivencia y Justicia
- **Formatos:** REST Esri, WMS, WFS, SHP, KMZ, DXF, GPKG, GeoJSON
- **Actualización:** Semestral
- **Licencia:** CC BY-SA 4.0
- **Cobertura geográfica:** Bogotá D.C. con desagregación por UPZ
- **Variables:** Tipología de delito, geolocalización, fecha, UPZ
- **Diccionarios:** `DiccionarioDatosSDSCJ.pdf` y `CatalogoObjetosSDSCJ.pdf` disponibles en el portal
- **Valor diferencial:** Más reciente que SIEDCO, incluye datos hasta 2026. Usar como fuente principal de crimen.

```python
df_alto_impacto = descargar_socrata("datosabiertos.bogota.gov.co", "7b270013-42ca-436b-9c1e-3bcb7d280c6b")
# También descargable como GeoJSON directamente
```

---

### 3. NUSE 123 — Incidentes C4 Número Único de Seguridad y Emergencias ⭐ FEATURE DE SUBREGISTRO

- **Portal:** datosabiertos.bogota.gov.co
- **Plataforma:** CKAN Datastore — resource_id `30d65a8b-d0ed-4e95-977e-0d7cc2ea89ef`
- **⚠️ Nota:** El ID Socrata `9bdf518e-b756-4865-983f-0521111fbcd1` es el dataset page. El resource_id de CKAN Datastore es `30d65a8b-d0ed-4e95-977e-0d7cc2ea89ef`.
- **Formato COD_UPZ:** `"UPZ" + número sin ceros` (ej. Chapinero = `"UPZ99"`, sin localización = `"UPZ999"`)
- **Período:** Enero 2015 – marzo 2026 (**actualización mensual** ✅)
- **Organización:** Secretaría Distrital de Seguridad, Convivencia y Justicia
- **Formato:** CSV (datos principales + diccionario de campos + clasificador de incidentes)
- **Actualización:** **MENSUAL** — la fuente de crimen de mayor frecuencia
- **Licencia:** CC BY-SA 4.0
- **Descripción:** Llamadas al 123 que fueron procesadas como incidente real de emergencia/seguridad. Excluye llamadas rechazadas.
- **Valor diferencial:** Captura incidentes que nunca llegan a SIEDCO (denuncia formal). Útil para modelar percepción de inseguridad y subregistro parcial. Responde la pregunta del jurado: "¿Qué hacen con el subregistro?"

```python
df_nuse = descargar_socrata("datosabiertos.bogota.gov.co", "9bdf518e-b756-4865-983f-0521111fbcd1")
```

---

### 4. Datos Nacionales — Policía Nacional en datos.gov.co

Para validación cruzada y comparativa Bogotá vs. promedio nacional.

- **Portal:** datos.gov.co
- **Licencia:** Datos abiertos públicos

| Dataset | ID Socrata | Descripción |
|---------|-----------|-------------|
| HOMICIDIO | `m8fd-ahd9` | Homicidios nacionales por municipio |
| HURTO PERSONAS | `4rxi-8m8d` | Hurto a personas por municipio |
| HURTO ABIGEATO | `p88b-5ac7` | Referencia adicional |

```python
df_homicidios = descargar_socrata("www.datos.gov.co", "m8fd-ahd9")
df_hurto = descargar_socrata("www.datos.gov.co", "4rxi-8m8d")
```

- **Limitación:** Desagregación a nivel municipal, no UPZ. Usar para contexto y benchmarking.

---

## Fuentes geoespaciales

### 5. Shapefiles UPZ — Unidades de Planeamiento Zonal

- **Fuente:** IDECA (Infraestructura de Datos Espaciales para el Distrito Capital) via datosabiertos.bogota.gov.co
- **Dataset ID:** `808582fc-ffc8-4649-8428-7e1fd8d3820c`
- **Última actualización:** 15/02/2023
- **Licencia:** CC BY 4.0
- **URLs directas verificadas:**
  - **GeoJSON:** `https://datosabiertos.bogota.gov.co/dataset/808582fc-ffc8-4649-8428-7e1fd8d3820c/resource/a5c8c591-0708-420f-8eb7-9f3147e21c40/download/unidadplaneamientolocal.json`
  - **SHP (ZIP):** `https://datosabiertos.bogota.gov.co/dataset/808582fc-ffc8-4649-8428-7e1fd8d3820c/resource/3a3e1181-b986-46aa-a952-cb76a25d4850/download/unidadplaneamientolocal.zip`
  - **KMZ:** `https://datosabiertos.bogota.gov.co/dataset/808582fc-ffc8-4649-8428-7e1fd8d3820c/resource/94e6a299-5d89-484f-b082-bee4263a3181/download/unidadplaneamientolocal.kmz`
- **⚠️ Nota:** El nombre oficial en IDECA es "Unidad de Planeamiento Local" (UPL). Verificar al descargar que el conteo es de **112 polígonos** (UPZ) y no 117 (UPL son divisiones distintas).

```python
import geopandas as gpd

url_geojson = "https://datosabiertos.bogota.gov.co/dataset/808582fc.../download/unidadplaneamientolocal.json"
upz = gpd.read_file(url_geojson)
upz = upz.to_crs(epsg=4326)  # WGS84 para Folium
print(f"Zonas cargadas: {len(upz)}")  # Verificar: debe ser 112
```

### 6. Shapefiles Localidades

- **Fuente:** IDECA / datos.gov.co
- **Portal:** datosabiertos.bogota.gov.co → Localidades Bogotá D.C.
- **Contenido:** 20 polígonos de localidades de Bogotá
- **Uso:** Drilldown en el dashboard (localidad → UPZ)

### 7. Cuadrantes de Policía ⭐ NUEVA FUENTE

- **Portal:** datosabiertos.bogota.gov.co / IDECA
- **URL:** `https://datosabiertos.bogota.gov.co/dataset/cuadrantes-de-policia-bogota-d-c`
- **URL IDECA:** `https://www.ideca.gov.co/recursos/mapas/cuadrantes-de-policia`
- **Formatos:** REST Esri, WMS, WFS, SHP
- **Descripción:** Shapefile de cuadrantes de policía de Bogotá — sectores geográficos fijos que reciben patrullaje diferenciado según características criminológicas, demográficas y económicas.
- **Valor:** Permite calcular el número de cuadrantes por UPZ → feature de "densidad de cobertura policial". Esencial para la capa prescriptiva (intervención tipo MEBOG/SIJIN).

```python
cuadrantes = gpd.read_file("data/raw/shapefiles/cuadrantes_policia.shp")
# Spatial join con UPZ para calcular cuadrantes por zona
cuadrantes_por_upz = gpd.sjoin(upz, cuadrantes, how="left", predicate="intersects")
```

### 8. Red vial y TransMilenio

- **Fuente:** TransMilenio S.A.
- **Portal principal:** datosabiertos.bogota.gov.co → organización TransMilenio
- **Portal ArcGIS dedicado:** `https://datosabiertos-transmilenio.hub.arcgis.com/`
- **Datasets disponibles:**
  - Estaciones troncales: `https://datosabiertos.bogota.gov.co/dataset/estaciones-troncales-de-transmilenio`
  - Rutas troncales, rutas zonales, paradas SITP
  - **GTFS** (General Transit Feed Specification) — formato estándar, útil para accesibilidad por UPZ
- **Formatos:** CSV, ZIP, GeoJSON, KML, ArcGIS REST
- **Uso:** Feature de proximidad a estaciones TransMilenio por UPZ (distancia media al centroide de estación más cercana). Correlación entre concentración de crimen y nodos de alta afluencia.

### 9. Catastro Distrital

- **Fuente:** Secretaría Distrital de Hacienda (Catastro Bogotá)
- **URL:** datosabiertos.bogota.gov.co → Catastro
- **Nota:** Catastro Bogotá tiene su propio portal de datos abiertos. Ver `catastrobogota.gov.co`
- **Variables:** Estrato por manzana, uso del suelo, densidad de predios comerciales
- **Uso:** Features de estrato promedio por UPZ y densidad comercial

---

## Fuentes socioeconómicas

### 10. Alumbrado Público — UAESP ⭐ NUEVA FUENTE

- **Portal:** datosabiertos.bogota.gov.co / IDECA
- **URL:** `https://datosabiertos.bogota.gov.co/dataset/luminarias_upz-bogota-d-c`
- **URL IDECA:** `https://www.ideca.gov.co/recursos/mapas/alumbrado-publico-bogota-dc`
- **Última actualización IDECA:** 17 febrero 2026 ✅
- **Organización:** UAESP (Unidad Administrativa Especial de Servicios Públicos)
- **Variables:** Número de luminarias por tecnología (LED, sodio, haluros metálicos) desagregadas por localidad y **UPZ**
- **Licencia:** Uso abierto — organizaciones públicas, privadas y ciudadanía
- **Valor:** Feature directa de iluminación pública por UPZ — una de las 27 variables urbanísticas del modelo. Variable prácticamente estática (cambio anual mínimo).

```python
import pandas as pd
df_alumbrado = pd.read_csv("data/raw/alumbrado_upz.csv")
# Columnas esperadas: upz_codigo, upz_nombre, luminarias_led, luminarias_sodio, luminarias_total
```

### 11. DANE — Censo de Población y Vivienda 2018

- **URL:** `https://microdatos.dane.gov.co/index.php/catalog/643`
- **Acceso:** Descarga libre con registro básico en microdatos.dane.gov.co
- **Formatos:** CSV, SAV (SPSS), DTA (Stata) + metadatos JSON/DDI
- **Código UPZ:** Disponible en los microdatos de la Encuesta Multipropósito 2017 (`catalog/565`)
- **Variables:** Población por UPZ/barrio, hacinamiento, nivel educativo
- **Procesador REDATAM:** `https://systema59.dane.gov.co/bincol/rpwebengine.exe/PortalAction?lang=esp` para consultas sin descarga
- **Nota:** La tasa de desempleo por UPZ no está desagregada en los datos libres del censo. Usar Encuesta Multipropósito con código UPZ (cod_upz en catalog/565).

### 12. Encuesta Multipropósito Bogotá (EMB)

- **URL:** datosabiertos.bogota.gov.co + microdatos.dane.gov.co (catalog/565)
- **Periodicidad:** Cada 2–3 años (última disponible 2021)
- **Variables clave:** Seguridad percibida por localidad, victimización reportada (diferente a SIEDCO — captura subregistro), `cod_upz` disponible en microdatos
- **Uso:** Variable de contexto social + respuesta al jurado sobre subregistro

### 13. Estratificación Socioeconómica — SDP

- **Fuente:** Secretaría Distrital de Planeación
- **URL:** `https://datosabiertos.bogota.gov.co/dataset/estratificacion-rural-bogota-d-c`
- **URL SDP:** `https://www.sdp.gov.co/transparencia/datos-abiertos/datos-abiertos`
- **Última actualización:** Enero 2025 ✅
- **Formatos:** GPKG, GeoJSON, SHP, KMZ, DXF
- **Variables:** Estrato 1–6 por manzana catastral
- **Nota:** Estratificación rural y urbana en datasets separados
- **Uso:** Feature de estrato promedio por UPZ + variable de análisis de sesgo (Notebook 05)

### 14. Tasa de Desempleo — SDDE

- **Fuente:** Secretaría Distrital de Desarrollo Económico
- **URL:** `https://datosabiertos.bogota.gov.co/dataset/tasa-de-desempleo-bogota-d-c`
- **Organización:** SDDE + DANE (Gran Encuesta Integrada de Hogares)
- **Actualización:** Trimestral
- **Variables:** Tasa de desempleo trimestral para Bogotá (agregada por ciudad, no UPZ)
- **Nota:** Para desagregación por zona usar DANE GEIH con código de UPL/UPZ cuando disponible.
- **Contexto 2025:** Bogotá cerró 2025 con 6.5% de desempleo, mínimo histórico desde 2007.

---

## APIs de tiempo real

### 15. Open-Meteo — Variables climáticas

- **URL:** `https://api.open-meteo.com/v1/forecast`
- **Estado:** ACTIVO ✅. Gratuito, sin API key.
- **Variables disponibles:** temperatura (°C), precipitación (mm/h), velocidad viento, humedad relativa
- **Resolución temporal:** Horaria / diaria
- **Cobertura:** Bogotá (lat: 4.6097, lon: -74.0817)
- **Historial:** API de datos históricos disponible en misma URL con `start_date` / `end_date`

```python
import requests

def get_clima_bogota(fecha_inicio, fecha_fin):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": 4.6097,
        "longitude": -74.0817,
        "daily": ["temperature_2m_max", "precipitation_sum"],
        "hourly": ["temperature_2m", "precipitation"],
        "start_date": fecha_inicio,
        "end_date": fecha_fin,
        "timezone": "America/Bogota"
    }
    return requests.get(url, params=params).json()

clima = get_clima_bogota("2019-01-01", "2024-12-31")
```

### 16. Socrata Open Data API

- **Documentación:** dev.socrata.com
- **Endpoints base:**
  - Bogotá: `https://datosabiertos.bogota.gov.co/resource/{dataset_id}.json`
  - Nacional: `https://www.datos.gov.co/resource/{dataset_id}.json`
- **Parámetros SoQL útiles:**
  - `$limit` / `$offset` — paginación
  - `$where` — filtros (e.g., `$where=fecha_hecho > '2022-01-01'`)
  - `$select` — columnas específicas
  - `$order` — ordenamiento
- **Con sodapy:** ver snippet al inicio de este documento.

### 17. Mapas — OpenStreetMap / Nominatim

- **URL:** nominatim.openstreetmap.org
- **Uso:** Geocodificación de direcciones, validación de coordenadas
- **Límite:** 1 request/segundo (respetar rate limit)
- **Nota:** Solo para geocodificación auxiliar. Las fuentes principales ya tienen coordenadas.

---

## Fuentes complementarias

### 18. Banco de la República — SUAMECA ⭐ NUEVA FUENTE

- **URL:** `https://suameca.banrep.gov.co/descarga-multiple-de-datos/`
- **Buscador de series:** `https://suameca.banrep.gov.co/buscador-de-series/`
- **Acceso:** Descarga directa sin autenticación
- **Contenido relevante:**
  - Series históricas de PIB, desempleo, inflación por departamento
  - Datos de criminalidad por departamento (últimos 20 años): homicidios, hurtos, indicadores jurídicos
- **Formato:** Excel / CSV
- **Limitación:** Nivel departamental solamente (no UPZ)
- **Valor:** Contexto macroeconómico para la presentación oral. Paper BanRep sobre criminalidad en Colombia disponible para citar.

### 19. Secretaría Distrital de Seguridad (SCJ) — Estadísticas y Boletines

- **URL estadísticas:** `https://scj.gov.co/cifras/estadisticas-mapas`
- **URL datos abiertos:** `https://scj.gov.co/en/transparencia/datos-abiertos/seccion-datos-abiertos`
- **Contenido:**
  - Boletines mensuales de indicadores de seguridad (PDF) — series históricas por localidad
  - Cruce de fuentes: SIEDCO + NUSE + RNMC (Registro Nacional Medidas Correctivas) + SIDIJUS
  - Mapas de calor por localidad en portal SCJ
- **Actualización:** Mensual
- **Valor para LLM:** Los PDFs de boletines mensuales son corpus ideal para fine-tuning de la capa generativa (lenguaje operacional de seguridad ciudadana real).

### 20. Fiscalía General de la Nación

- **URL:** `https://www.fiscalia.gov.co/colombia/gestion/estadisticas/`
- **Contenido:** Estadísticas de imputaciones, delitos judicializados, tasas de impunidad
- **Acceso:** Descarga directa (CSV/Excel)
- **Limitación:** Granularidad municipal, no UPZ
- **Valor:** Complementa SIEDCO con el ciclo completo del delito (denuncia → judicialización). Útil para presentación.

---

## Fuentes para la capa prescriptiva

### Directorio de Entidades Distritales

- **URL:** bogota.gov.co → Directorio de entidades
- **Uso:** Mapeo intervención → entidad responsable

| Tipo de intervención | Entidad responsable | Fuente de datos relacionada |
|---------------------|-------------------|---------------------------|
| Patrullaje / respuesta inmediata | MEBOG / SIJIN / PONAL | Cuadrantes de Policía |
| Desempleo y vulnerabilidad social | SDDE (Secretaría de Desarrollo Económico) | Tasa de desempleo |
| Atención a familias en riesgo | SDIS (Secretaría de Integración Social) | EMB / DANE |
| Iluminación pública | UAESP | Alumbrado Público por UPZ |
| Espacio público y vías | IDU (Instituto de Desarrollo Urbano) | Catastro / Uso del suelo |
| Convivencia / mediación | Secretaría de Seguridad Ciudadana | SCJ boletines |

### Informes de Seguridad — Secretaría Distrital de Seguridad

- **URL:** scj.gov.co → Informes estadísticos
- **Uso:** Datos históricos de intervenciones + resultados. Corpus para fine-tuning del LLM si se decide implementar (requiere mínimo 200–500 pares).

---

## Datos científicos / literatura de referencia

| Paper | Autores | Relevancia |
|-------|---------|-----------|
| Hawkes Process en Bogotá | Riascos et al. (Uniandes) | Baseline colombiano más sólido, desplegado operacionalmente |
| Homicidios en Bogotá con árbol de decisión | Simanca et al. | Benchmark directo para comparación |
| Hawkes en red lineal de calles (Bucaramanga) | D'Angelo et al. | Mejora de precisión espacial |
| Estado del arte CNN-LSTM 2025 | D'Angelo et al. (revisión) | Modelo de referencia internacional |
| Criminalidad en Colombia | Banco de la República | Datos económicos + criminológicos departamentales |

---

## Estrategia de almacenamiento

- **Parquet** — para datasets dinámicos >50K filas (SIEDCO, Delito Alto Impacto, NUSE 123, Clima)
- **CSV** — para tablas estáticas pequeñas (Alumbrado, Estratificación, Desempleo trimestral)
- **SHP / GeoJSON** — para datos geoespaciales (UPZ, Localidades, Cuadrantes, TransMilenio)
- **Git LFS** — para archivos >100MB (shapefiles grandes o modelos `.joblib`)
- **Descarga incremental:** Usar `$where=fecha_hecho > '{ultima_fecha}'` en Socrata para actualización semanal

---

## Checklist de descarga — Semana 1

### Fuentes primarias de crimen
- [ ] **Delito de Alto Impacto** (resource `aba0e25d-...` CKAN) → `data/raw/delito_alto_impacto.geojson` ⭐
- [ ] **NUSE 123 incidentes** (CKAN resource `30d65a8b-...`) → `data/raw/nuse_incidentes.parquet` ⭐
- [ ] Homicidios nacionales (Socrata `m8fd-ahd9`) → `data/raw/homicidios_nacional.parquet`
- [ ] Hurto personas (Socrata `4rxi-8m8d`) → `data/raw/hurto_personas_nacional.parquet`

### Fuentes geoespaciales
- [ ] UPZ shapefile (CKAN resource `a5c8c591-...`) → `data/raw/shapefiles/UPZ_Bogota.json` (verificar N=112)
- [ ] Cuadrantes de Policía (CKAN resource `f0ad2ee3-...`) → `data/raw/shapefiles/cuadrantes_policia.shp`
- [ ] Estaciones TransMilenio (CKAN `9be8b6fb-...`) → `data/raw/transmilenio_estaciones.csv`
- [ ] Estratificación manzana (CKAN resource `29f2d770-...`) → `data/raw/estratificacion_manzana.gpkg`
- [ ] Uso económico por manzana (CKAN `grupo_uso-por-manzana`) → `data/raw/uso_economico_manzana.gpkg`

### Fuentes complementarias y nuevas
- [ ] Datos climáticos históricos 2019–2024 (Open-Meteo archive) → `data/raw/clima_bogota.parquet`
- [ ] Alumbrado Público UAESP → `data/raw/alumbrado_upz.csv` (stale 2022 — complementar con VIIRS)
- [ ] Lesiones no fatales Medicina Legal (Socrata `79dd-d24f`) → `data/raw/lesiones_no_fatales.parquet`
- [ ] Lesiones fatales Medicina Legal (Socrata `2kpj-cktv`) → `data/raw/lesiones_fatales.parquet`
- [ ] Incautación estupefacientes (Socrata `kk69-w2jj`, filtrar Bogotá) → `data/raw/incautaciones.parquet`
- [ ] OSM POI Bogotá (Overpass API) → `data/raw/osm_poi_bogota.geojson`
- [ ] VIIRS composite mensual 2020–2024 (NASA Earthdata) → `data/raw/viirs/` (GeoTIFF por mes)

### Configuración técnica
- [ ] Registrar App Token gratuito en dev.socrata.com → guardar en `.env` como `SOCRATA_APP_TOKEN`
- [ ] Registrar cuenta gratuita en NASA Earthdata (nasa.gov/earthdata) para VIIRS
- [ ] Instalar dependencias: `pip install -r requirements.txt`
- [ ] Verificar conteo UPZ shapefile (debe ser exactamente 112 polígonos)
- [ ] Ejecutar `python src/validar_fuentes.py` → genera `fuentes_validadas.xlsx` con estado de URLs

---

## Fuentes nuevas (15–20) — añadidas en investigación mayo 2026

### 15. Grupo de Uso Económico por Manzana (UAECD) ⭐ FEATURE DENSIDAD COMERCIAL

- **Portal:** datosabiertos.bogota.gov.co
- **Plataforma:** CKAN — dataset slug `grupo_uso-por-manzana`
- **Última actualización:** 1 enero 2026 ✅ — versiones históricas desde 2012
- **Variables:** `uso_predominante`: Residencia · Comercio y oficinas · Depósitos y parqueaderos · Industrial · Dotacional
- **Granularidad:** Por manzana catastral (más fino que UPZ)
- **Licencia:** CC BY 4.0
- **Valor:** Feature de densidad comercial sólida por UPZ. "Comercio y oficinas" = proxy de bares, vida nocturna → predictor de crimen violento (PMC 2012, Springer 2024).

```python
uso = gpd.read_file("data/raw/uso_economico_manzana.gpkg")
uso_upz = gpd.sjoin(uso, upz).groupby("codigo_upz")["uso_predominante"].value_counts(normalize=True).unstack()
pct_comercio_upz = uso_upz.get("Comercio y oficinas", 0)
```

### 16. Lesiones no Fatales de Causa Externa (Medicina Legal) ⭐ PROXY SUBREGISTRO

- **Portal:** www.datos.gov.co
- **Plataforma:** Socrata — `79dd-d24f`
- **Período:** Enero 2024 – Marzo 2026 (actualización mensual) ✅
- **Variables clave:** `a_o_del_hecho`, `mes_del_hecho`, `rango_de_hora_del_hecho_x_3_horas`, `localidad_del_hecho`, `escenario_del_hecho`, `circunstancia_del_hecho` (riña/robo/violencia doméstica), `mecanismo_causal`, `presunto_agresor`, `dias_de_incapacidad_medicolegal`
- **Granularidad geográfica:** Localidad (no UPZ) — cruzar con tabla UPZ→localidad
- **Valor:** Captura violencias que llegan a urgencias pero no a SIEDCO. Segundo proxy de subregistro: ratio lesiones_ML/delitos_formales por localidad.

```python
from src.etl import socrata_query
df_lesiones = socrata_query("79dd-d24f", where="localidad_del_hecho IS NOT NULL")
```

### 17. Lesiones Fatales de Causa Externa (Medicina Legal)

- **Portal:** www.datos.gov.co
- **Plataforma:** Socrata — `2kpj-cktv`
- **Variables:** fecha_hecho, localidad_del_hecho, causa_de_muerte, clase_de_accidente_de_transito
- **Valor:** Cross-valida homicidios entre Policía Nacional (FUENTE 3) y Medicina Legal. La diferencia entre ambas fuentes = indicador de calidad del dato.

### 18. Incautación de Estupefacientes (Policía Nacional)

- **Portal:** www.datos.gov.co
- **Plataforma:** Socrata — `kk69-w2jj`
- **Variables:** `departamento`, `municipio`, `codigo_dane`, `clase_bien` (tipo droga), `fecha_hecho`, `cantidad`
- **Granularidad:** Municipal — filtrar `municipio='BOGOTA D.C.'`
- **Valor:** Proxy de presencia de economías ilegales. Variable contextual anual (no feature directa UPZ).

### 19. OpenStreetMap POI — Overpass API ⭐ FEATURE ATRACTORES DE CRIMEN

- **Endpoint:** `https://overpass-api.de/api/interpreter`
- **Librería:** `overpy>=0.6.0`
- **Categorías relevantes:** `amenity=bar/pub/nightclub` (vida nocturna) · `amenity=atm/bank` (hurto) · `amenity=park` · `shop=convenience`
- **Licencia:** ODbL — completamente libre
- **Valor:** Densidad de bares, ATMs, parques por UPZ. Validado por Springer 2024 y PMC 2012.

```python
import overpy
api = overpy.Overpass()
# Bares en Bogotá (bounding box aproximado)
result = api.query("""
    [out:json];
    node["amenity"="bar"](4.48,-74.22,4.84,-73.99);
    out;
""")
bares_gdf = gpd.GeoDataFrame(
    [{"lat": n.lat, "lon": n.lon, "amenity": n.tags.get("amenity")} for n in result.nodes],
    geometry=gpd.points_from_xy([n.lon for n in result.nodes], [n.lat for n in result.nodes])
)
bares_por_upz = gpd.sjoin(upz, bares_gdf).groupby("codigo_upz").size()
```

### 20. VIIRS Nighttime Lights — NASA/NOAA ⭐ ILUMINACIÓN REAL (reemplaza stale UAESP)

- **URL:** `https://eogdata.mines.edu/products/vnl/`
- **Acceso:** Registro gratuito en NASA Earthdata (nasa.gov/earthdata)
- **Frecuencia:** Composites mensuales cloud-free desde 2012
- **Resolución:** ~750m por píxel → agregar por UPZ con `rasterstats`
- **Valor:** Mide iluminación REAL desde satélite (vs infraestructura declarada del UAESP stale). ScienceDirect 2025 confirma correlación negativa con crimen.

```python
import rasterio
from rasterstats import zonal_stats

with rasterio.open("data/raw/viirs_2024_01.tiff") as src:
    stats = zonal_stats(upz, src.read(1), affine=src.transform,
                        stats=["mean", "max"], nodata=src.nodata)
upz["luz_nocturna_media"] = [s["mean"] for s in stats]
```

---

## Fuentes descartadas y por qué

| Fuente | Razón de descarte | Alternativa |
|--------|------------------|------------|
| SIEDCO `2bxu-b96f` | 404 en CKAN Bogotá — no existe como dataset tabular | FUENTE 2 (Delito de Alto Impacto) |
| SIMUR (movilidad urbana) | Datos fragmentados, acceso inconsistente | FUENTE 13 (sensores SDM via ArcGIS REST) |
| Cámaras CCTV seguridad | Ley 1581/2012 — ubicaciones no son datos abiertos | FUENTE 10 (cámaras tráfico SDM) |
| Siniestros Viales CKAN Bogotá | STALE — última actualización oct 2021 | FUENTE 11 (SDM versión diaria) |
| Tasa Desempleo SDDE portal | Sin actualizar desde dic 2023 | FUENTE 14 (DANE EMB) |
| Redes sociales scraping | Viola reglas del concurso. X API ahora $100+/mes. | Google Trends (opcional, 2da prioridad) |
| APIs de pago (Google Maps) | Viola reglas del concurso | Open-Meteo, IDECA, OSM Overpass |
| IDU Obras activas | Sin endpoint descargable — solo mapa interactivo | IDU Estado Superficial vial (proxy deterioro) |
| Violencia Intrafamiliar SDS | Solo tasa por 100K hab para Bogotá completo, sin UPZ | FUENTE 16 (Medicina Legal) |
| Google Street View | Requiere API de pago para 150K+ imágenes. Viola restricción. | FUENTE 19 (OSM POI) + FUENTE 20 (VIIRS) |
| INPEC datos penitenciarios | Desagregación nacional, no aporta al modelo UPZ | No aplica |
