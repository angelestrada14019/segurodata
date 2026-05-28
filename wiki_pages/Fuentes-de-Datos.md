# Fuentes de Datos

SeguroData usa **10 fuentes activas** de datos abiertos + 2 planificadas. Todas son públicas y gratuitas.

## Arquitectura de fuentes

Las fuentes se dividen en dos grupos según su rol:

### Grupo 1 — Fuentes estructuradas (F1-F8) → XGBoost
Estas fuentes alimentan la tabla Silver y el modelo predictivo.

| # | Fuente | Entidad | Filas Bronze | Rol en Silver | datos.gov.co |
|---|--------|---------|-------------|--------------|:---:|
| F1 | Delito de Alto Impacto (DAI) | SDSCJ | 21 | EDA histórico (no UPZ) | ✅ |
| F2 | UPZ Shapefile — IDECA | Catastro | 112 | Base geométrica spatial joins | ❌ |
| F3 | Clima Bogotá — Open-Meteo | Open-Meteo | 56,112 | +temperatura, +precipitación | ❌ |
| F4 | Cuadrantes Policía MEBOG | Policía Nacional | 599 | +cuadrantes/km², +CAI | ✅ |
| **F5** | **NUSE 123 — C4** | **C4 / SDSCJ** | **128,314** | **BASE: genera las 111,606 filas Silver** | **✅** |
| F6 | Hurto Personas PN | Policía Nacional | 638,569 | Benchmarking nacional (no UPZ) | ✅ |
| F7 | Estratificación — SDP | SDP | 44,260 | +estrato_promedio_upz | ✅ |
| F8 | Estaciones TransMilenio | TM S.A. | 153 | +dist_tm, +n_estaciones | ❌ |

**Total Bronze: 868,140 registros → Silver: 111,606 filas × 20 columnas**

### Grupo 2 — Fuentes no estructuradas (F9-F10) → GraphRAG + Claude API
Estas fuentes **no entran en XGBoost**. Son corpus de texto para el GraphRAG que alimenta los Módulos 3 y 4.

| # | Fuente | Tipo | Actualización |
|---|--------|------|--------------|
| F9 | Boletines SCJ — PDFs mensuales | PDF texto | Mensual |
| F10 | Noticias RSS — El Tiempo / Espectador | RSS | Diaria |

### Planificadas (F11-F12)

| # | Fuente | Estado | Fase |
|---|--------|--------|------|
| F11 | IDU Calzada + Estado Superficial (obras viales) | ⏳ Planificada | Fase 2 |
| F12 | Plan Desarrollo Bogotá 2024-2027 (Acuerdo 927/2024) | ⏳ Planificada | Fase 3 |

## Referencia completa

Para URLs, Resource IDs, licencias y evidencia causal de cada fuente, ver: [docs/FUENTES_PROVENANCE.md](https://github.com/angelestrada14019/segurodata/blob/main/docs/FUENTES_PROVENANCE.md)
