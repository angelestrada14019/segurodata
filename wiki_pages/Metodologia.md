# Metodología — CRISP-ML

SeguroData sigue la metodología CRISP-ML (Cross-Industry Standard Process for Machine Learning).

## Fases del proyecto

| Fase | Notebooks | Entregable | Estado |
|------|-----------|-----------|--------|
| 0 — Plan y fuentes | SeguroData_01 | Catálogo de 20 fuentes, arquitectura | ✅ Completo |
| 1A — Bronze | src/pipeline.py | 10 fuentes descargadas, incremental | ✅ Completo |
| 1B — Silver | src/transform.py | silver_upz_mes.parquet (111,606 × 20) | ✅ Completo |
| 2 — Gold + Modelo | SeguroData_03 + 04 | 14 variables + XGBoost + SHAP | ⏳ Fase actual |
| 3 — Dashboard | SeguroData_05 | Streamlit + Claude API + GraphRAG | ⏳ Jun 2026 |
| 4 — Entrega | SeguroData_06 | Deploy + registro datos.gov.co | ⏳ Jul 2026 |

## Validación temporal (no aleatoria)

**Regla crítica:** Los modelos de series temporales NUNCA se validan con split aleatorio.

```
Entrenamiento: 2022-2023 (datos históricos)
Validación:    2024      (datos de prueba — el modelo no los "vio")
Test final:    ene-mar 2025 (holdout definitivo)
```

Un split aleatorio daría resultados artificialmente buenos (data leakage temporal).

## Las 14 variables del modelo

| Grupo | Variables |
|-------|----------|
| Históricas (lag) | n_delitos_upz_4sem, n_delitos_upz_8sem, tipo_delito_dominante |
| Temporales | dia_semana, franja_horaria, mes, es_fin_semana |
| Climáticas | temperatura_c, precipitacion_mm |
| Espaciales | estrato_promedio_upz, cuadrantes_por_km2, n_estaciones_tm, dist_tm_metros |
| Subregistro | ratio_nuse_delitos_upz |
| **Objetivo (Y)** | nivel_riesgo — ALTO / MEDIO / BAJO |

## Análisis de sesgo por estrato

El jurado del concurso pregunta explícitamente si el modelo discrimina por estrato socioeconómico. El Notebook 04 incluye:
- Comparación de predicciones por estrato (1-6): ¿falsos negativos concentrados en estratos bajos?
- SHAP interaction plots: ¿interactúa el estrato con la predicción de manera inesperada?
- Resultado esperado: el estrato **entra como feature causal legítima**, no como proxy discriminatorio
