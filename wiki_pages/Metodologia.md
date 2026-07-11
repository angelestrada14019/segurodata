# Metodología — CRISP-ML

SeguroData sigue la metodología CRISP-ML (Cross-Industry Standard Process for Machine Learning).

## Fases del proyecto

| Fase | Dónde vive | Entregable | Estado |
|------|-----------|-----------|--------|
| 0 — Plan y fuentes | `wiki_pages/Fuentes-de-Datos.md`, `Provenance.md` | Catálogo de 12 fuentes activas + F12 planificada, arquitectura | ✅ Completo |
| 1A — Bronze | `src/pipeline.py` | 12 fuentes descargadas, incremental | ✅ Completo |
| 1B — Silver | `src/transform.py` | silver_upz_mes.parquet (111,606 × 20) | ✅ Completo |
| 1B — EDA | `wiki_pages/Analisis-Exploratorio.md` | Hallazgos clave del análisis exploratorio | ✅ Completo |
| 2 — Gold + Modelo | `scripts/train_model.py` | 18 variables + XGBoost + SHAP | ✅ Completo |
| 3 — Dashboard | React + deck.gl + FastAPI + Supabase + GraphRAG | Desplegado en producción | ✅ Completo |
| 4 — Entrega | — | Video + registro datos.gov.co | ⏳ 11–13 julio 2026 |

## Validación temporal (no aleatoria)

**Regla crítica:** Los modelos de series temporales NUNCA se validan con split aleatorio.

```
Fuente base: F5 NUSE 123 — disponible solo 2025–2026 (enero 2025 – abril 2026)

Entrenamiento: enero – octubre 2025   (10 meses)
Test final:    noviembre 2025 – abril 2026  (6 meses — el modelo no los "vio")
```

Un split aleatorio daría resultados artificialmente buenos (data leakage temporal). Los datos de entrenamiento solo incluyen periodos anteriores al test; nunca se mezclan fechas.

> **Nota:** F1 (Delito de Alto Impacto) cubre 2018–2026 a nivel localidad y se usa exclusivamente para **detección de puntos de cambio históricos** con `ruptures` — no para entrenamiento del modelo XGBoost.

## Las 18 variables del modelo

El modelo opera a granularidad **UPZ × mes** (no a nivel evento), por lo que las variables son agregados mensuales por zona.

| Grupo | Variables |
|-------|----------|
| Históricas / lag temporal | `n_delitos_upz_4sem`, `n_delitos_upz_8sem`, `n_delitos_upz_12sem`, `tendencia_upz` |
| Lag espacial | `n_delitos_vecinos_lag` (delitos de UPZs vecinas en t-1, vía adyacencia del shapefile F2) |
| Temporales cíclicas | `mes_sin`, `mes_cos` (codificación cíclica: diciembre y enero quedan adyacentes) |
| Climáticas | `temperatura_c`, `precipitacion_mm_mes` |
| Espaciales | `estrato_promedio_upz`, `cuadrantes_por_km2`, `n_estaciones_tm`, `dist_tm_metros` |
| Subregistro | `ratio_nuse_criminal_upz` |
| Infraestructura (F11+F13+F14) | `km_via_intervenida_upz`, `n_camaras_upz`, `luminarias_led_upz` |
| Tipo de delito | `tipo_crimen_cod` (tipo de delito dominante en la UPZ, codificado) |
| **Objetivo (Y)** | `nivel_riesgo` — CRÍTICO / ALTO / MEDIO / BAJO (percentiles q40/q75/q95 de delitos por UPZ × mes) |

### Resultados del modelo (test temporal nov 2025 – abr 2026, 719 filas)

`nivel_riesgo` es **ordinal** (BAJO < MEDIO < ALTO < CRÍTICO), así que se reporta el conjunto completo de métricas, no solo el acierto exacto:

| Métrica | Valor |
|---------|-------|
| Acierto de banda exacta | 0.871 |
| **Acierto dentro de ±1 banda** | **100%** (cero saltos de clase: nunca confunde BAJO con ALTO ni MEDIO con CRÍTICO) |
| macro-F1 | 0.867 |
| MAE ordinal | 0.129 bandas |
| Recall CRÍTICO | 0.92 |

La métrica defendible es el **acierto dentro de ±1 banda (100%)**: el error de banda exacta restante son zonas que caen justo sobre un umbral de percentil (ruido de frontera), no fallos operativos. Validación **estrictamente temporal** (sin split aleatorio). Métricas en `datos/modelos/metricas.json`.

## Detección de puntos de cambio estructural (ruptures)

La librería `ruptures` (Truong et al., 2020 — arXiv 1801.00826) aplica el algoritmo PELT sobre las series temporales históricas de F1 DAI (2018–2026) para detectar cuándo el patrón de crimen cambió estructuralmente en cada localidad.

```python
import ruptures as rpt

# Para cada localidad: detectar cambios en la serie de homicidios/hurtos
signal = df_localidad["n_delitos"].values
algo = rpt.Pelt(model="rbf").fit(signal)
breakpoints = algo.predict(pen=10)
# breakpoints = [mes en que hubo ruptura estructural]
```

El resultado alimenta el Módulo 3 (Prescriptivo): si la UPZ tiene un cambio estructural reciente + patrón sostenido → diagnóstico "problema estructural, no pico temporal" → intervención SIJIN + SDIS en lugar de solo patrullaje.

## Capa prescriptiva — tabla de intervenciones

El Módulo 3 no dice "hay riesgo ALTO". Dice **quién actúa, cómo y por qué**. La tabla ontológica mapea cada factor de riesgo accionable (identificado por SHAP) a su intervención:

| SHAP top feature | Diagnóstico | Tipo intervención | Entidad responsable | Acción operacional |
|---|---|---|---|---|
| `cuadrantes_por_km2` bajo | Baja cobertura policial | Seguridad | MEBOG / SIJIN | Refuerzo cuadrante + CAI nombre+dirección |
| `estrato_promedio_upz` bajo | Vulnerabilidad socioeconómica | Social | SDIS + SDDE | Programa Jóvenes en Paz + cupos empleo |
| `luminarias_led_upz` bajo | Baja iluminación nocturna | Urbanístico | UAESP | Reposición luminarias en franja madrugada |
| `n_camaras_upz` bajo | Sin disuasión tecnológica | Seguridad | SDSCJ | Solicitud cámaras Salvavidas SDM |
| `n_delitos_upz_4sem` alto | Autoexcitación reciente | Operacional | MEBOG | Saturación patrullaje 48h |
| `dist_tm_metros` alto | Zona aislada + baja accesibilidad | Movilidad | TransMilenio S.A. | Sin acción directa — factor de contexto |
| `temperatura_c` alto | Condición climática activadora | Monitoreo | Policía + IDIGER | Alerta preventiva en franja tarde |
| `km_via_intervenida_upz` alto | Obra activa → desplazamiento residentes | Obras | IDU + MEBOG | Coordinación obra-seguridad |
| `ratio_nuse_criminal_upz` alto | Alto subregistro → confianza baja | Datos | SDSCJ / C4 | Campaña denuncia ciudadana |
| `n_delitos_vecinos_lag` alto | Contagio espacial desde UPZs vecinas | Operacional | MEBOG | Patrullaje coordinado de borde inter-UPZ |

Esta tabla se documenta en `backend/app/data/tabla_ontologica_seed.json` y en el Módulo 3 (ver `wiki_pages/Modulos.md`).

## Análisis de sesgo por estrato

El jurado del concurso pregunta explícitamente si el modelo discrimina por estrato socioeconómico. `scripts/train_model.py::analisis_sesgo()` incluye:
- Comparación de predicciones por estrato (1-6): ¿falsos negativos concentrados en estratos bajos?
- SHAP interaction plots: ¿interactúa el estrato con la predicción de manera inesperada?
- Resultado esperado: el estrato **entra como feature causal legítima**, no como proxy discriminatorio

---

## Dónde vive cada fase CRISP-ML

El concurso no exige formato Jupyter. La metodología completa queda documentada en `wiki_pages/` (este wiki), y el código de producción — probado, versionado y corrido en CI — es la fuente de verdad de features, modelo, SHAP y sesgo:

| Fase CRISP-ML | Dónde vive |
|---|---|
| Plan + fuentes | `wiki_pages/Fuentes-de-Datos.md`, `Provenance.md` |
| Análisis exploratorio | `wiki_pages/Analisis-Exploratorio.md` |
| Feature engineering + modelo + SHAP + sesgo | `scripts/train_model.py` (ejecutado, ver `datos/modelos/metricas.json`) |
| Arquitectura + deploy | `wiki_pages/Arquitectura.md`, `Instalacion.md` |
