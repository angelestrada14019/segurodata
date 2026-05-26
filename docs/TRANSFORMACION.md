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

| Archivo | Fuente | Descripción |
|---------|--------|-------------|
| `f1_delito_alto_impacto.parquet` | F1 | ~500K+ registros de delitos con lat/lon/fecha/hora/UPZ |
| `f2_upz.geojson` | F2 | 112 polígonos UPZ de Bogotá |
| `f3_clima_bogota.parquet` | F3 | Clima horario 2020→hoy (temperatura, lluvia, viento) |
| `f4_cuadrantes.geojson` | F4 | Polígonos de cuadrantes policiales |
| `f5_nuse_123.parquet` | F5 | Incidentes de llamadas al 123 por UPZ/año/mes |
| `f7_estratificacion.parquet` | F7 | ~115K manzanas con estrato + geometría WKT |
| `f8_transmilenio.geojson` | F8 | Puntos de estaciones TransMilenio |

> F6 (Hurto Personas — Policía Nacional) no entra al modelo, solo sirve para contexto oral. No tiene paso de transformación.

---

## Qué produce (Silver)

Archivos en `datos/procesados/`:

| Archivo | Paso | Filas aprox. | Descripción |
|---------|------|-------------|-------------|
| `delitos_upz_mes.parquet` | f1 | ~10,000 | Crimen agregado por UPZ × mes con lags |
| `clima_diario.parquet` | f3 | ~2,300 | Temperatura y lluvia promedio diaria |
| `nuse_upz_mes.parquet` | f5 | ~8,000 | Incidentes NUSE agregados por UPZ × mes |
| `estrato_por_upz.csv` | f7 | 112 | Estrato promedio ponderado por UPZ |
| `features_cuadrantes_upz.csv` | f4 | 112 | Cuadrantes/km² y área por UPZ |
| `features_tm_upz.csv` | f8 | 112 | Estaciones TM y distancia al TM más cercano |
| **`silver_upz_mes.parquet`** | silver | ~10,000 | **Tabla final con todas las variables unidas** |

---

## Columnas de la tabla Silver final

La tabla `silver_upz_mes.parquet` tiene una fila por **UPZ × mes** con estas columnas:

| Columna | Origen | Tipo | Descripción |
|---------|--------|------|-------------|
| `upz_cod` | F1/F2 | str | Código de la UPZ |
| `anio` | F1 | int | Año (2020–2024) |
| `mes` | F1 | int | Mes (1–12) |
| `n_delitos` | F1 | int | Delitos en la UPZ ese mes |
| `tipo_delito_dominante` | F1 | str | Categoría de delito más frecuente |
| `franja_dominante_mes` | F1 | str | Franja horaria con más delitos (madrugada/mañana/tarde/noche) |
| `n_delitos_upz_4sem` | F1 (lag 1m) | int | Delitos del mes anterior ≈ 4 semanas |
| `n_delitos_upz_8sem` | F1 (lag acum 2m) | int | Suma de los 2 meses anteriores ≈ 8 semanas |
| `temperatura_c` | F3 | float | Temperatura promedio del mes (°C) |
| `precipitacion_mm_mes` | F3 | float | Lluvia acumulada del mes (mm) |
| `n_incidentes_nuse` | F5 | int | Llamadas al 123 en la UPZ ese mes |
| `ratio_nuse_delitos_upz` | F5/F1 | float | n_incidentes_nuse / n_delitos (proxy de subregistro) |
| `estrato_promedio_upz` | F7 | float | Estrato promedio ponderado (1–6) |
| `cuadrantes_por_km2` | F4 | float | Densidad de cuadrantes policiales |
| `area_upz_km2` | F4 | float | Área de la UPZ en km² |
| `n_estaciones_tm` | F8 | int | Estaciones TransMilenio dentro de la UPZ |
| `dist_tm_metros` | F8 | float | Distancia del centroide de la UPZ al TM más cercano |
| `es_mitad_anio` | calculado | bool | True si mes 6–8 (temporada lluvias) |

> Estas son **todas las variables candidatas**. En Gold (Notebook 03) se analizará la correlación y se seleccionarán las 14 que entran al modelo XGBoost.

---

## Cómo ejecutar

### Requisito previo

Los archivos Bronze deben existir. Si no están:

```bash
python src/pipeline.py        # descarga todas las fuentes
# o por fuente:
python src/pipeline.py --source f1 f2 f3 f4 f5 f7 f8
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
[OK] f1_delitos               updated  rows=  10,752  10,752 filas | 112 UPZs | 2020-2024
[OK] f3_clima                 updated  rows=   2,336  2,336 dias | 2020-01-01 a 2026-05-24
[OK] f4_cuadrantes            updated  rows=     112  112 UPZs | 4,821 cuadrantes totales
[OK] f5_nuse                  updated  rows=   8,400  8,400 filas | 12,450,000 incidentes totales
[OK] f7_estrato               updated  rows=     112  112 UPZs | estrato 1.2-5.8
[OK] f8_transmilenio          updated  rows=     112  112 UPZs | dist media al TM: 1,240m
[OK] silver_table             updated  rows=  10,752  10,752 filas | 18 columnas | 112 UPZs
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
f1  ──┐
f3  ──┤
f4  ──┼──► silver_table ──► datos/procesados/silver_upz_mes.parquet
f5  ──┤
f7  ──┤
f8  ──┘

f2 (UPZ shapefile) se usa internamente en f4, f7 y f8 pero no produce
un archivo Silver propio — es la base de todos los spatial joins.
```

El orquestador `run_transform()` respeta este orden automáticamente.
