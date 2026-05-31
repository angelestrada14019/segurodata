# REGLAS.md — Restricciones del Concurso y del Proyecto

> Referencia rápida de qué está permitido, qué penaliza y qué el jurado evalúa. Leer antes de tomar cualquier decisión de diseño.

---

## Reglas del concurso "Datos al Ecosistema 2026"

> **⚠️ ALERTA DE FECHA:** La investigación de mayo 2026 encontró que el evento final del concurso es **GovCamps 2026 (primera semana de agosto 2026)**, no el 13 de julio como se estimaba originalmente. Verificar en datos.gov.co antes de planificar hitos finales. Si se confirma agosto, hay ~3 semanas extra.
>
> **Competidor directo identificado:** "Atlas del Crimen" ganó Datos al Ecosistema 2025 con análisis espaciotemporal de criminalidad. Nuestra diferenciación: predicción (no solo descripción), SHAP causal, capa prescriptiva con entidades responsables, y GraphRAG causal para explicar el *por qué* del crimen.
>
> **Competencia:** 349 equipos / 1096 participantes registrados al 19 mayo 2026.

### Obligatorio — si falta esto, descalifican

- [ ] **Datos abiertos** — todo dataset debe ser públicamente accesible. No se pueden usar datos privados, comprados o restringidos.
- [ ] **Repositorio GitHub público** — código completo, reproducible, con instrucciones claras.
- [ ] **Registro en datos.gov.co** — el enlace al proyecto debe registrarse en el portal oficial antes de la fecha límite (**verificar fecha exacta: posiblemente agosto 2026, confirmar en datos.gov.co**).
- [ ] **Priorizar datos de datos.gov.co** — el concurso evalúa explícitamente el uso del portal nacional de datos abiertos + Mapas de Ruta Sectoriales de Datos Estratégicos.
- [ ] **Notebooks CRISP-ML documentados** — 6 notebooks numerados `SeguroData_01` a `SeguroData_06`, uno por fase.
- [ ] **Mínimo 10.000 filas** en el dataset principal. La tabla Silver tiene **111,606 filas × 20 columnas** (base: F5 NUSE 128K registros). ✅ Garantizado.
- [ ] **README.md** completo en el repositorio con descripción, instrucciones de instalación y referencia a los datos.

### Criterios que evalúa el jurado técnico

| Criterio | Peso | Qué buscan |
|----------|------|-----------|
| Calidad del análisis | Alto | EDA profundo, ingeniería de features justificada, comparación de modelos |
| Uso de datos abiertos | Alto | Variedad de fuentes, correcta atribución, no solo un dataset |
| Rigor técnico | Alto | Validación temporal correcta, métricas apropiadas, SHAP values |
| Propuesta de valor | Alto | ¿Qué problema resuelve? ¿Quién lo usaría? ¿Cómo? |
| Estrategias de prevención | Medio-Alto | La mayoría de equipos ignora esto — es una ventaja diferencial |
| Generalización / escalabilidad | Medio | ¿Puede replicarse en otra ciudad? (No hace falta construirlo, solo argumentarlo) |
| Presentación oral | Medio | Claridad, seguridad ante preguntas difíciles |

---

## Restricciones técnicas (lo que NO está permitido)

### Datos
- **No** usar APIs de pago como fuente principal (e.g., Google Maps Platform con créditos pagos)
- **No** usar datos de vigilancia privada, cámaras o datos personales identificables
- **No** hacer scraping de redes sociales sin documentar el proceso y verificar términos de uso

### Modelos
- **No** usar Claude API u otro LLM como sustituto del modelo predictivo — Claude API es solo para los Módulos 3 (Recomendación) y 4 (Chatbot). El modelo predictivo es XGBoost.
- **No** presentar un modelo sin métricas de evaluación comparativas (al menos contra un baseline)
- **No** hacer fine-tuning de LLM sin al menos 200–500 pares de entrenamiento etiquetados — produce un modelo peor que el base

### Evaluación
- **No** usar validación aleatoria (train/test split aleatorio) para series temporales — se debe usar **validación temporal**. En este proyecto: TRAIN = ene–oct 2025, TEST = nov 2025–abr 2026 (F5 NUSE solo disponible 2025–2026)
- **No** reportar accuracy en un dataset de crimen sin reportar también precision, recall y F1 — el accuracy es engañoso con clases desbalanceadas

### Alcance
- **No** agregar una segunda ciudad solo por parecer más ambicioso — el jurado no puntúa por cantidad de ciudades, sino por profundidad del análisis. El tiempo gastado en ETL de una segunda ciudad es tiempo robado al modelo principal.

---

## Decisiones de diseño ya tomadas (no reabrir sin justificación fuerte)

| Decisión | Justificación |
|----------|--------------|
| Solo Bogotá | Calidad de datos superior + volumen garantizado + no penalización por enfoque único |
| Granularidad UPZ (no localidad, no barrio) | Balance entre resolución y estabilidad estadística |
| Stack Python + scikit-learn + XGBoost | Reproducible, bien documentado, compatible con CRISP-ML |
| ~~Hawkes Process~~ → **GraphRAG causal** | Hawkes descartado por complejidad/tiempo. GraphRAG (nano-graphrag + Claude API) diferencia mejor: explica el *por qué* del crimen usando boletines SCJ + noticias + Plan Desarrollo |
| SHAP para interpretabilidad | Requerido para la capa prescriptiva y valorado por el jurado técnico |
| Streamlit para dashboard | Fácil de desplegar en Streamlit Cloud, no requiere backend separado |

---

## Preguntas difíciles del jurado — respuestas preparadas

**"¿Su modelo discrimina por estrato?"**
→ Sí lo analizamos. El Notebook 04 incluye análisis de sesgo por estrato socioeconómico. El modelo usa estrato como variable pero los SHAP values permiten identificar si produce predicciones sistemáticamente sesgadas. [Completar con resultados reales del análisis.]

**"¿Qué pasa si el SIEDCO tiene subregistro?"**
→ El subregistro es un problema real en criminología colombiana. Lo mitigamos de dos formas: (1) usamos el crimen reportado como proxy, explicitando la limitación, y (2) cruzamos con otras fuentes (llamadas a emergencias, datos de movilidad anómala) para detectar patrones no capturados por SIEDCO.

**"¿Cómo escala esto a otra ciudad?"**
→ La arquitectura es modular. Para replicar en otra ciudad: sustituir el dataset Socrata por el ID equivalente local, reemplazar los shapefiles de UPZ por la división administrativa local, y recalibrar los thresholds del modelo. El README documenta este proceso.

**"¿Cómo previenen el crimen, no solo lo predicen?"**
→ La capa prescriptiva diagnostica la causa raíz (temporal, estructural, urbanística) y mapea cada diagnóstico a la entidad distrital responsable de la intervención. No mandamos más policías — identificamos qué tipo de intervención necesita cada zona y quién debe ejecutarla.

---

## Checklist final antes de la entrega

> ⚠️ Verificar fecha exacta en datos.gov.co — final GovCamps confirmado primera semana de agosto 2026

- [ ] Repositorio GitHub público con todos los archivos
- [ ] 6 notebooks `SeguroData_01` a `SeguroData_06` completos y ejecutables
- [ ] README.md con instrucciones de instalación + URLs Railway (API) + Vercel (frontend)
- [ ] **Aplicación React + deck.gl** desplegada en Vercel — URL pública, 4 módulos funcionando
- [ ] **FastAPI** desplegado en Railway — `/predict`, `/explain`, `/query` respondiendo
- [ ] **Supabase** configurado — Silver table + SHAP pre-computados + pgvector embeddings cargados
- [ ] Módulo 3 Prescriptivo: tabla ontológica documentada en Notebook 03 + Claude API operacional (nombre CAI incluido)
- [ ] SHAP values pre-computados en Notebook 04 + cargados en Supabase (NO cálculo on-demand)
- [ ] Análisis de sesgo por estrato en Notebook 04
- [ ] `ruptures` — change points detectados y guardados en Supabase tabla `change_points`
- [ ] Enlace registrado en datos.gov.co en la sección "Usos" — **OBLIGATORIO para no ser descalificado**
- [ ] Video pitch de 3 minutos grabado y subido
- [ ] Presentación de 10 minutos preparada
- [ ] Auditoría de git history para API keys: `git log --all -p | grep -iE "api.key|token|secret"`
- [ ] Respuestas para preguntas difíciles ensayadas (ver sección arriba)
