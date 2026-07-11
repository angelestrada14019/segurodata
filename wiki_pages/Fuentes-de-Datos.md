# Fuentes de Datos

SeguroData usa **12 fuentes activas** de datos abiertos + 1 planificada (F12). Todas son públicas y gratuitas.

> **Regla de fuentes quirúrgicas:** Antes de proponer una fuente nueva, completar el checklist de investigación (ver sección al final). Las fuentes se agregan solo si tienen granularidad UPZ, licencia abierta, evidencia causal y esfuerzo justificado.

---

## Grupo 1 — Fuentes estructuradas (F1-F8, F11, F13, F14) → XGBoost + mapa

Estas fuentes alimentan la tabla Silver y el modelo predictivo.

| # | Fuente | Entidad | Filas Bronze | Rol en Silver / Mapa | datos.gov.co |
|---|--------|---------|-------------|----------------------|:---:|
| F1 | Delito de Alto Impacto (DAI) | SDSCJ | 21 | EDA histórico + **ruptures** (cambios estructurales 2018–2026) | ✅ |
| F2 | UPZ Shapefile — IDECA | Catastro | 112 | Base geométrica spatial joins | ❌ |
| F3 | Clima Bogotá — Open-Meteo | Open-Meteo | 56,112 | +temperatura, +precipitación | ❌ |
| F4 | Cuadrantes Policía MEBOG | Policía Nacional | 599 | +cuadrantes/km², +CAI nombre+dirección | ✅ |
| **F5** | **NUSE 123 — C4** | **C4 / SDSCJ** | **128,314** | **BASE: genera las 111,606 filas Silver** | **✅** |
| F6 | Hurto Personas PN | Policía Nacional | 638,569 | Benchmarking nacional (no UPZ) | ✅ |
| F7 | Estratificación — SDP | SDP | 44,260 | +estrato_promedio_upz | ✅ |
| F8 | Estaciones TransMilenio | TM S.A. | 153 | +dist_tm, +n_estaciones | ❌ |
| **F11** | **Malla Vial + Obras IDU** | **IDU / IDECA** | ~miles segs. | **+km_via_intervenida_upz** | ✅ |
| **F13** | **Cámaras Salvavidas SDM** | **SDM** | 92 puntos | **+n_camaras_upz + capa deck.gl** | ❌ ArcGIS Hub |
| **F14** | **Alumbrado Público UAESP** | **UAESP** | 112 filas | **+luminarias_led_upz (granularidad nativa UPZ)** | ✅ |

**Total Bronze: ~870,000+ registros → Silver: 111,606 filas × 20 columnas**

---

## Grupo 2 — Fuente no estructurada (F10) → GraphRAG + pgvector

Esta fuente **no entra en XGBoost**. Es corpus de texto indexado en Supabase pgvector para el Módulo 4 (chatbot causal) y el Módulo 3 (contexto prescriptivo).

> **F10 incluye tres feeds RSS verificados:** El Tiempo (seguridad Bogotá), El Espectador (judicial nacional), y El Informante Soy Yo — [elinformantesoyyo.com](https://elinformantesoyyo.com) (política de seguridad, operativos, contexto institucional). Los tres feeds son accesibles con `feedparser` sin autenticación.

| # | Fuente | Tipo | Actualización | Procesamiento |
|---|--------|------|--------------|--------------|
| F10 | Noticias RSS — El Tiempo / Espectador / El Informante Soy Yo | RSS | Diaria | feedparser → sentence-transformers → pgvector |

---

## Planificada (F12)

| # | Fuente | Estado | Fase |
|---|--------|--------|------|
| F12 | Plan Desarrollo Bogotá 2024-2027 (Acuerdo 927/2024) | ⏳ Planificada | Fase 3 |

---

## Fuentes investigadas y descartadas

| Fuente | Razón descarte |
|--------|---------------|
| El Periodista Soy Yo — Noticias Caracol | Contenido audiovisual (ciudadanos envían videos a TV). Sin RSS de texto — no integrable como corpus. |
| SIMUR cámaras C4 (red CCTV seguridad) | Sin API pública — circuito cerrado de la Secretaría |
| Feeds de video en tiempo real | Inviable legalmente (Ley 1581/2012) + sin API |
| Google Street View | API de pago — viola reglas concurso |
| SIEDCO `2bxu-b96f` | Endpoint 404 — no disponible en CKAN Bogotá |
| Twitter/X #inseguridad | API de pago ($100+/mes) — viola reglas |
| Tasa Desempleo SDDE | Solo ciudad completa — sin granularidad UPZ |

---

## Referencia completa

Para URLs, Resource IDs, licencias y evidencia causal de cada fuente: [[Provenance]]
