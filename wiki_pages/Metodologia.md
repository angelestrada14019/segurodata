# Metodología — CRISP-ML

SeguroData sigue la metodología CRISP-ML (Cross-Industry Standard Process for Machine Learning).

## Fases del proyecto

| Fase | Notebooks | Entregable | Estado |
|------|-----------|-----------|--------|
| 0 — Plan y fuentes | SeguroData_01 | Catálogo de 20 fuentes, arquitectura | ✅ Completo |
| 1A — Bronze | src/pipeline.py | 10 fuentes descargadas, incremental | ✅ Completo |
| 1B — Silver | src/transform.py | silver_upz_mes.parquet (111,606 × 20) | ✅ Completo |
| 2 — Gold + Modelo | SeguroData_03 + 04 | 14 variables + XGBoost + SHAP | ⏳ Fase actual |
| 3 — Dashboard | SeguroData_05 | React + deck.gl + FastAPI + Supabase + GraphRAG | ⏳ Jun 2026 |
| 4 — Entrega | SeguroData_06 | Deploy + registro datos.gov.co | ⏳ Jul 2026 |

## Validación temporal (no aleatoria)

**Regla crítica:** Los modelos de series temporales NUNCA se validan con split aleatorio.

```
Fuente base: F5 NUSE 123 — disponible solo 2025–2026 (enero 2025 – abril 2026)

Entrenamiento: enero – octubre 2025   (10 meses)
Test final:    noviembre 2025 – abril 2026  (6 meses — el modelo no los "vio")
```

Un split aleatorio daría resultados artificialmente buenos (data leakage temporal). Los datos de entrenamiento solo incluyen periodos anteriores al test; nunca se mezclan fechas.

> **Nota:** F1 (Delito de Alto Impacto) cubre 2018–2026 a nivel localidad y se usa exclusivamente para **detección de puntos de cambio históricos** con `ruptures` — no para entrenamiento del modelo XGBoost.

## Las 17 variables del modelo

| Grupo | Variables |
|-------|----------|
| Históricas (lag) | n_delitos_upz_4sem, n_delitos_upz_8sem, tipo_delito_dominante |
| Temporales | dia_semana, franja_horaria, mes, es_fin_semana |
| Climáticas | temperatura_c, precipitacion_mm |
| Espaciales | estrato_promedio_upz, cuadrantes_por_km2, n_estaciones_tm, dist_tm_metros |
| Subregistro | ratio_nuse_delitos_upz |
| Infraestructura (F11+F13+F14) | km_via_intervenida_upz, n_camaras_upz, luminarias_led_upz |
| **Objetivo (Y)** | nivel_riesgo — ALTO / MEDIO / BAJO |

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

El Módulo 3 no dice "hay riesgo ALTO". Dice **quién actúa, cómo y por qué**. La tabla de 17 filas (una por variable del modelo) mapea:

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
| `franja_dominante_mes` madrugada | Crimen nocturno | Seguridad | MEBOG turno noche | Operativo nocturno focalizado |

Esta tabla se documenta en la celda 1 de Notebook 03 antes de escribir cualquier código.

## Análisis de sesgo por estrato

El jurado del concurso pregunta explícitamente si el modelo discrimina por estrato socioeconómico. El Notebook 04 incluye:
- Comparación de predicciones por estrato (1-6): ¿falsos negativos concentrados en estratos bajos?
- SHAP interaction plots: ¿interactúa el estrato con la predicción de manera inesperada?
- Resultado esperado: el estrato **entra como feature causal legítima**, no como proxy discriminatorio
