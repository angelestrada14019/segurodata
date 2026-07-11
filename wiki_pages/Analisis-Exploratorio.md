# Análisis Exploratorio de Datos (EDA)

> Hallazgos sobre `datos/procesados/silver_upz_mes.parquet` (111,606 filas × 20 columnas, 120 UPZs, 19 localidades, ene 2025 – abr 2026). Change points estructurales (`ruptures` sobre F1 DAI 2018–2026) ya están documentados en [[Arquitectura]] y [[Metodologia]] — no se repiten aquí.

## Resumen general

| Métrica | Valor |
|---|---|
| Filas totales (todos los tipos NUSE) | 111,606 |
| Filas de crimen de alto impacto (`es_crimen=True`) | 25,400 |
| UPZs con datos | 120 |
| Localidades | 19 |
| Tipos de incidente distintos (crimen) | 19 |
| Rango temporal | Enero 2025 – Abril 2026 |

## 1. Calidad del dato: geocodificación incompleta

El 7.5% de los registros de crimen (93,453 de 1,240,652 delitos acumulados) llegan con `upz_cod="999"`, un código centinela para incidentes sin geocodificación precisa a nivel UPZ — todos concentrados en la localidad de Ciudad Bolívar. Este subregistro espacial es consistente con el fenómeno ya documentado en el feature `ratio_nuse_criminal_upz` (Barrera et al., Uniandes 2023): la calidad de geocodificación no es uniforme en toda la ciudad. Estos registros se excluyen de los rankings por UPZ de abajo — no se le asigna una geometría inventada.

## 2. Distribución espacial: concentración real, no uniforme

**Top 5 UPZs por delitos acumulados** (excluyendo el centinela `999`):

| UPZ | Localidad | Delitos acumulados |
|---|---|---|
| 28 | Suba | 45,623 |
| 71 | Suba | 43,005 |
| 85 | Bosa | 33,624 |
| 84 | Bosa | 30,991 |
| 82 | Kennedy | 25,042 |

**Top 5 localidades:** Ciudad Bolívar (180,021), Suba (150,812), Kennedy (146,225), Engativá (121,525), Bosa (96,268). Estas 5 localidades concentran el 46% del crimen total de la ciudad — justifica un modelo a nivel UPZ (granularidad fina) en vez de localidad: dentro de Suba, por ejemplo, la UPZ 28 tiene casi el doble de incidentes que UPZs vecinas de la misma localidad.

## 3. Tipos de incidente: la riña domina, no el hurto

| Tipo de incidente | Total |
|---|---|
| Riña | 598,873 |
| Maltrato | 200,935 |
| Hurto en proceso | 128,926 |
| Narcóticos | 102,364 |
| Hurto efectuado | 62,774 |
| Lesiones personales | 42,650 |

La riña es, por volumen, el incidente NUSE más frecuente — casi 3× el maltrato y más de 4× el hurto en proceso. El modelo predictivo no colapsa esto a "hurto" (el imaginario típico de "crimen urbano"): `tipo_crimen_cod` entra al XGBoost como el tipo dominante real por UPZ×mes, que en buena parte de la ciudad es riña o maltrato, no hurto.

## 4. Estacionalidad: más modesta de lo que sugiere la suma cruda

**Nota metodológica:** la primera pasada (suma cruda de delitos por mes calendario) mostraba enero–abril con casi el doble de delitos que el resto del año — pero esto es un artefacto: enero–abril están presentes en el dataset dos veces (2025 y 2026), mientras mayo–diciembre solo aparecen una vez (2025). Normalizando por número de períodos observados, la estacionalidad real es mucho más modesta:

| Mes | Promedio de delitos (normalizado) |
|---|---|
| Enero | 66,421 |
| Febrero | 70,938 |
| Marzo | 82,281 |
| Abril | 76,835 |
| Mayo | 78,783 |
| Diciembre | 85,574 |

Hay una tendencia leve hacia niveles más altos en marzo y diciembre, pero no el patrón dramático que sugería la lectura ingenua. Esto refuerza por qué el modelo usa `mes_sin`/`mes_cos` (codificación cíclica suave) en vez de tratar el mes como categoría con saltos abruptos.

## 5. Por qué el modelo usa SHAP y no correlaciones simples

Las correlaciones lineales univariadas entre variables candidatas y delitos totales por UPZ son, en su mayoría, débiles o nulas:

| Variable | Correlación con delitos totales (UPZ) |
|---|---|
| `estrato_promedio_upz` | −0.03 |
| `precipitacion_mm_mes` | −0.001 |
| `temperatura_c` | −0.02 |
| `cuadrantes_por_km2` | **+0.37** |

Esto no significa que estas variables no importen — significa que su relación con el riesgo es **multivariada y condicional**, no lineal ni aislada (por eso el modelo usa XGBoost + SHAP en vez de seleccionar features por correlación simple, ver [[Metodologia]]). El caso de `cuadrantes_por_km2` es un ejemplo clásico de **causalidad inversa** que hay que interpretar con cuidado: la correlación positiva no significa "más policía causa más crimen" — significa que la Policía ya asigna más cuadrantes a las zonas que históricamente tienen más incidentes. El modelo lo usa como señal de cobertura relativa, no como palanca causal aislada.

## 6. Lo que ya está resuelto en `ruptures` (no se repite aquí)

La detección de cambios estructurales (40 breakpoints PELT sobre F1 DAI 2018–2026, con la baja de COVID-19 en 2020 validada empíricamente en 17 localidades) está documentada con el detalle completo en [[Arquitectura]] y visible como capa de mapa en el Módulo 1 — ver [[Modulos]].
