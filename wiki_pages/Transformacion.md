# TRANSFORMACION.md — Capa Silver

> Este documento es para el equipo que tiene a cargo la transformación de datos.
> Describe qué recibe la capa Silver, qué debe producir, y cómo ejecutarla.

---

## Contexto en la arquitectura

```
Bronze  datos/raw/          ← ya construido (src/pipeline.py)
Silver  datos/procesados/   ← este documento — src/transform.py
Gold    datos/features/     ← siguiente etapa (Notebook 03)
Model   datos/modelos/      ← siguiente etapa (Notebook 04)
```

La capa Silver **no toma decisiones de modelo**. Su única responsabilidad es:
- Limpiar los datos crudos
- Agregarlos a nivel UPZ × mes
- Hacer los spatial joins necesarios
- Unir todo en una tabla lista para analizar

**La selección de variables y el análisis de correlación ocurren en Gold (Notebook 03)**, no aquí. Silver produce todas las variables candidatas sin filtrar ninguna.

---

## Qué recibe (Bronze)

Archivos en `datos/raw/` generados por `src/pipeline.py`:

| Archivo | Fuente | Filas Bronze | Descripción |
|---------|--------|-------------|-------------|
| `f1_delito_alto_impacto.parquet` | F1 | **21** | Totales de delitos por localidad × año (2018–2026). **No tiene UPZ** — granularidad localidad (21 localidades). Solo para EDA histórico |
| `f2_upz.geojson` | F2 | 112 | Polígonos UPZ de Bogotá — base espacial para todos los spatial joins |
| `f3_clima_bogota.parquet` | F3 | ~56,000 | Clima horario 2020→hoy (temperatura, lluvia, viento) |
| `f4_cuadrantes.geojson` | F4 | 599 | Polígonos de cuadrantes policiales con nombre del CAI |
| `f5_nuse_123.parquet` | F5 | **128,314** | **Fuente principal** — incidentes NUSE 123 por UPZ × mes × tipo (86 tipos, 2025–2026). Genera las filas de Silver |
| `f7_estratificacion.parquet` | F7 | ~44,260 | Manzanas con estrato + geometría WKT |
| `f8_transmilenio.geojson` | F8 | 153 | Puntos de estaciones TransMilenio |
| `datos/raw/boletines_scj/` | F9 | N/A | PDFs boletines mensuales SCJ (corpus texto para GraphRAG) |
| `datos/raw/noticias_rss.jsonl` | F10 | N/A | Artículos RSS 3 feeds (corpus texto para GraphRAG) |

> **F6** (Hurto Personas — Policía Nacional, 638,569 filas a nivel municipio) no entra al Silver — sin desglose UPZ. Solo benchmarking nacional.  
> **F9/F10** no entran en XGBoost — son corpus de texto para los Módulos 3 y 4 (GraphRAG — OpenRouter).

---

## Qué produce (Silver)

Archivos en `datos/procesados/`:

| Archivo | Paso | Filas reales | Descripción |
|---------|------|-------------|-------------|
| `delitos_localidad_anio.parquet` | f1 | ~2,079 | DAI por localidad × año — referencia EDA histórico (no entra al Silver JOIN) |
| `clima_diario.parquet` | f3 | ~2,338 | Temperatura y lluvia promedio diaria (horario → diario) |
| `features_cuadrantes_upz.csv` | f4 | 111 | Cuadrantes/km² + nombre del CAI por UPZ |
| `delitos_upz_mes.parquet` | f5 | **111,606** | Todos los 86 tipos NUSE × UPZ × mes + lags + flag `es_crimen` |
| `nuse_upz_mes.parquet` | f5 | ~9,600 | Incidentes NUSE totales agregados por UPZ × mes (todos los tipos) |
| `estrato_por_upz.csv` | f7 | 43 | Estrato promedio ponderado — 43 UPZs cubiertas por el spatial join |
| `features_tm_upz.csv` | f8 | 112 | `n_estaciones_tm` y `dist_tm_metros` por UPZ |
| **`silver_upz_mes.parquet`** | silver | **111,606** | **Tabla final: 111,606 filas × 23 columnas** (20 base + F11/F13/F14) — llave: upz_cod × anio × mes × tipo_crimen |

---

## Columnas de la tabla Silver final

La tabla `silver_upz_mes.parquet` tiene **una fila por UPZ × mes × tipo de incidente** (86 tipos NUSE). La columna `es_crimen` distingue los 19 tipos de alto impacto criminal del resto.

**Llave primaria**: `upz_cod` × `anio` × `mes` × `tipo_crimen`

| Columna | Origen | Tipo | Descripción |
|---------|--------|------|-------------|
| `upz_cod` | F5 | str | Código de la UPZ (ej. "044", "099") |
| `anio` | F5 | int | Año (2025–2026) |
| `mes` | F5 | int | Mes (1–12) |
| `tipo_crimen` | F5 | str | Tipo de incidente NUSE (86 tipos: HURTO, RUIDO, ACCIDENTE, …) |
| `es_crimen` | F5 | bool | **True** = uno de los 19 tipos de alto impacto criminal; **False** = desorden urbano |
| `cod_localidad` | F5 | str | Código de localidad (01–20) |
| `nom_localidad` | F5 | str | Nombre de la localidad (ej. "KENNEDY", "SUBA") |
| `n_delitos` | F5 | int | Conteo de incidentes de este tipo en la UPZ ese mes |
| `n_delitos_upz_4sem` | F5 (lag 1m) | int | Conteo del mes anterior ≈ 4 semanas |
| `n_delitos_upz_8sem` | F5 (lag acum 2m) | int | Suma de los 2 meses anteriores ≈ 8 semanas |
| `tipo_delito_dominante` | F5 | str | Tipo de crimen más frecuente en esa UPZ ese mes |
| `franja_dominante_mes` | F5 | str | Franja horaria con más incidentes (madrugada/mañana/tarde/noche) |
| `n_incidentes_nuse` | F5 | int | Total de llamadas al 123 en la UPZ ese mes (todos los tipos) |
| `ratio_nuse_delitos_upz` | F5 | float | n_incidentes_nuse / n_delitos — proxy de subregistro |
| `temperatura_c` | F3 | float | Temperatura promedio del mes (°C) |
| `precipitacion_mm_mes` | F3 | float | Lluvia acumulada del mes (mm) |
| `estrato_promedio_upz` | F7 | float | Estrato promedio ponderado por manzana en la UPZ (1–6) |
| `cuadrantes_por_km2` | F4 | float | Densidad de cuadrantes policiales en la UPZ |
| `n_estaciones_tm` | F8 | int | Estaciones TransMilenio dentro de la UPZ |
| `dist_tm_metros` | F8 | float | Distancia del centroide de la UPZ al TM más cercano |

> **23 columnas totales** (20 base + 3 de F11/F13/F14). Estas son **todas las variables candidatas** para el modelo. En Gold (Notebook 03) se analizará correlación, VIF y SHAP para seleccionar las 17 que entran al XGBoost.  
> F9/F10 (boletines + noticias) no aparecen en la silver — son corpus de texto para GraphRAG (Módulos 3 y 4 — OpenRouter).

---

## Cómo ejecutar

### Requisito previo

Los archivos Bronze deben existir. Si no están:

```bash
python src/pipeline.py        # descarga todas las fuentes (F1-F10)
# o por fuente estructurada:
python src/pipeline.py --source f1 f2 f3 f4 f5 f7 f8
# fuentes no estructuradas (corpus LLM — F9/F10):
python src/pipeline.py --source f9   # PDFs boletines SCJ
python src/pipeline.py --source f10  # RSS noticias
```

### Comandos de transform

```bash
# Ver qué haría sin ejecutar nada
python src/transform.py --dry-run

# Ver estado de todos los pasos
python src/transform.py --status

# Ejecutar todo (orden automático, f7 al final por ser pesado)
python src/transform.py

# Ejecutar un paso específico
python src/transform.py --step f1
python src/transform.py --step f1 f3 f5

# Solo construir la tabla final (requiere que los otros pasos ya existan)
python src/transform.py --step silver

# Forzar re-cálculo aunque Bronze no haya cambiado
python src/transform.py --step f7 --force

# Ver progreso detallado
python src/transform.py --verbose
```

### Ejemplo de salida

```
------------------------------------------------------------
  SeguroData Bogota - Pipeline de transformacion (Silver)
------------------------------------------------------------
[OK] f1_delitos               updated  rows=   2,079  2,079 filas | 21 localidades | 2018-2026 (EDA ref)
[OK] f3_clima                 updated  rows=   2,338  2,338 dias | 2020-01-01 a 2026-04-30
[OK] f4_cuadrantes            updated  rows=     111  111 UPZs | 4,821 cuadrantes | con nombre CAI
[OK] f5_nuse                  updated  rows= 111,606  111,606 filas | 120 UPZs | 86 tipos | 19 localidades
[OK] f7_estrato               updated  rows=      43  43 UPZs cubiertas | estrato 1.2-5.8
[OK] f8_transmilenio          updated  rows=     112  112 UPZs | dist media al TM: 1,240m
[OK] silver_table             updated  rows= 111,606  111,606 filas | 20 columnas | 120 UPZs | ene2025-abr2026
```

### Desde notebook / Colab

```python
from src.transform import run_transform

# Correr todo
resultados = run_transform(verbose=True)

# Leer la tabla Silver
import polars as pl
silver = pl.read_parquet("datos/procesados/silver_upz_mes.parquet")
print(silver.describe())
print(silver.schema)
```

---

## Advertencia: paso F7 (estratificación) es pesado

El spatial join de 115K manzanas contra 112 UPZs carga toda la geometría en RAM.

```
RAM estimada en Colab gratuito: ~8GB disponibles → F7 consume ~4-5GB
```

**Si falla por memoria en Colab gratuito:**

Opción A — Usar Colab Pro (más RAM):
```python
# Solo ejecutar este paso en Colab Pro
from src.transform import transform_f7_estrato, TransformState
result = transform_f7_estrato(TransformState(), force=True, verbose=True)
```

Opción B — Ejecutar localmente y subir el CSV:
```bash
# Local (requiere geopandas instalado)
python src/transform.py --step f7 --verbose
# Luego subir datos/procesados/estrato_por_upz.csv al repo o Drive
```

Opción C — Una vez calculado, el archivo se reutiliza siempre:
```
estrato_por_upz.csv es estático (el estrato cambia muy poco).
Con ejecutarlo una sola vez es suficiente para todo el proyecto.
```

---

## Qué NO hace esta capa

| Tarea | Dónde se hace |
|-------|---------------|
| Selección de variables (cuáles entran al modelo) | Gold — Notebook 03 |
| Análisis de correlación entre variables | Gold — Notebook 03 |
| Normalización / escalado para XGBoost | Gold — Notebook 03 |
| Definición de `nivel_riesgo` (ALTO/MEDIO/BAJO) | Gold — Notebook 03 |
| Balanceo de clases (SMOTE u otras técnicas) | Gold — Notebook 03 |
| Entrenamiento del modelo | Model — Notebook 04 |

---

## Dependencias de pasos

```
f1  ──► delitos_localidad_anio.parquet  (EDA histórico — NO entra al silver_table)
f3  ──┐
f4  ──┤
f5  ──┼──► silver_table ──► datos/procesados/silver_upz_mes.parquet
f7  ──┤                      (111,606 filas × 20 cols)
f8  ──┘

f2 (UPZ shapefile) se usa internamente en f4, f7 y f8 pero no produce
un archivo Silver propio — es la base de todos los spatial joins.

f9  ──► datos/procesados/boletines_corpus.json    (corpus texto → pgvector / GraphRAG)
f10 ──► (datos/raw/noticias_rss.jsonl ya filtrado)
```

El orquestador `run_transform()` respeta este orden automáticamente.
