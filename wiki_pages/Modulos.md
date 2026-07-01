# Los Módulos del Sistema

> **Estado de implementación (16-jun-2026):**
> - ✅ **Backend FastAPI completo** — 7 endpoints, 36 tests verdes (incl. E3 JWT end-to-end y T5 verificados en vivo contra Supabase real), Dockerfile listo (deploy en Fase 4)
> - ✅ **Modelo XGBoost** — entrenado vía `scripts/train_model.py` con 18 variables. Test temporal (nov 2025 – abr 2026): acierto dentro de ±1 banda 100%, macro-F1 0.867
> - ✅ **Supabase configurado** — migraciones + RLS + hook JWT + Realtime ON. **Artefactos reales del modelo cargados** (`origen='notebook_04'`): 1,918 predicciones + 34,524 SHAP
> - ✅ **change_points**: 40 breakpoints ruptures PELT cargados (F1 DAI 2018-2026), COVID 2020 validado
> - ✅ **Corpus GraphRAG**: 10 chunks RSS reales en pgvector (El Tiempo + El Informante; SEED_DEV eliminados)
> - ⏳ **Frontend React** — pendiente Fase 3 (21 jun)

La aplicación responde 5 preguntas: 4 módulos analíticos (Diagnóstico · Predicción · Prescriptivo · Chatbot causal) más una capa de participación ciudadana (autenticación, mapa interactivo con modal, alertas comunitarias — ver [[Plataforma-Ciudadana]]).

## Perfiles de Usuario

Cuatro perfiles acceden a módulos distintos según su necesidad operacional:

| Perfil | Rol técnico | Módulos que usa | Pregunta clave |
|---|---|---|---|
| **Comandante de Cuadrante / CAI** | `COMANDANTE_CAI` | 1, 2, 3 (solo su cuadrante) | ¿A dónde mando el patrullaje esta semana? |
| **Secretaría Distrital de Seguridad** | `ANALISTA_SDSCJ` | 1, 2, 3, 4 (todas las UPZs) | ¿Qué zonas requieren intervención estructural? |
| **Ciudadano / Habitante de Bogotá** | `CIUDADANO` | 1 (lectura), 4 (chatbot básico), reportes y pánico (opcional) | ¿Es seguro mi barrio hoy? |
| **Periodista / Investigador** | `CIUDADANO` | 1, 4 | ¿Por qué aumentó el crimen en X zona? |

> El diseño de cada módulo prioriza al usuario principal: lenguaje operacional (no jerga de ML), acciones concretas con nombre de CAI y teléfono, sin visualizaciones académicas innecesarias.

---

---

## Módulo 1 — Diagnóstico ("¿Qué está pasando?")

**Usuarios:** Secretaría de Seguridad, ciudadano informado, periodista  
**Tecnología:** React + deck.gl + Supabase Realtime

- **Mapa WebGL interactivo**: choropleth de Bogotá, 112 UPZs coloreadas por nivel de riesgo actual. Hover muestra estadísticas de la UPZ. Click activa el panel de detalle.
- **Zoom adaptativo**: vista ciudad completa → 20 Localidades (zoom < 12) → 112 UPZs (zoom ≥ 12), transición automática con deck.gl `CompositeLayer`. El jurado ve primero la ciudad entera, luego el detalle de zona.
- **Modal de análisis por zona (5 pestañas)**: clic en cualquier UPZ abre un panel lateral contextualizado en esa zona:
  - 📊 **Descripción** — serie histórica NUSE, top 3 tipos de incidente, tendencia últimas 8 semanas
  - 🔮 **Predicción** — nivel de riesgo XGBoost del próximo mes + probabilidades + proyección +4 semanas
  - 💡 **Sugerencia** — diagnóstico causal SHAP + recomendación prescriptiva + CAI responsable
  - 📚 **Fuentes** — qué datasets de datos abiertos informan esta UPZ (trazabilidad visible)
  - 💬 **Chatbot** — pregunta libre contextualizada en la UPZ seleccionada
- **Capas toggleables**: crimen por tipo · cámaras Salvavidas SDM · densidad cuadrantes · alumbrado público · estaciones TransMilenio
- **Slider temporal**: reproducir la evolución del crimen mes a mes (2025–2026)
- **Heatmap**: densidad de incidentes NUSE por franja horaria y día de la semana
- **Tendencia con change points**: serie histórica 2018–2026 (F1 DAI) con marcadores en los puntos de ruptura detectados por `ruptures`
- **Realtime**: cuando llegan datos nuevos del NUSE (mensual), Supabase Realtime actualiza el mapa sin recargar la página

---

## Módulo 2 — Predicción ("¿Qué va a pasar?")

**Usuarios:** Comandante de CAI, planeación policial  
**Tecnología:** XGBoost + SHAP + FastAPI (Railway) + Supabase

> **¿Qué predice exactamente?** XGBoost predice el nivel de riesgo del **próximo mes**, no el estado actual. Las features de entrada (n_delitos de las últimas 4, 8 y 12 semanas, tendencia reciente, delitos en UPZs vecinas, cobertura policial, clima, estacionalidad, estrato) describen el presente — el modelo aprendió qué nivel de riesgo sigue a cada combinación de esas condiciones. El output categórico (CRÍTICO/ALTO/MEDIO/BAJO) es la predicción del período siguiente. Ejemplo: si Kennedy tuvo 43 hurtos en las últimas 4 semanas con baja cobertura de cuadrantes y es temporada de diciembre → el modelo predice ALTO para enero con 82% de probabilidad.

- **Predicción por UPZ**: seleccionar UPZ + mes → FastAPI `/predict` → nivel de riesgo CRÍTICO/ALTO/MEDIO/BAJO + probabilidades de cada clase
- **Mapa predictivo**: todas las 112 UPZs coloreadas rojo/naranja/amarillo/verde para el mes seleccionado
- **Top-10 UPZs en riesgo ALTO o CRÍTICO**: tabla con las UPZs más críticas + nombre del CAI responsable
- **SHAP values**: los 3 features que más explican el riesgo en esa UPZ (cargados desde Supabase — pre-computados, sin cálculo on-demand)
- **Cambio estructural**: indicador si la UPZ tiene un breakpoint reciente (ruptures) — "Riesgo estructural persistente" vs "Pico temporal"
- **Proyección temporal +4 semanas**: gráfica de tendencia con `lag4sem` y `lag8sem` del Silver — muestra si la UPZ está subiendo o bajando de categoría, con banda de confianza (±1 desv. est. de los últimos 3 meses). El `n_delitos` proyectado se pasa al modelo para calcular la probabilidad de clase futura. Ejemplo de output: *"A este ritmo, UPZ Kennedy escalará de MEDIO a ALTO en ~3 semanas."*

---

## Módulo 3 — Prescriptivo ("¿Qué hacer?")

**Usuarios:** Comandante de CAI, Secretaría de Seguridad  
**Tecnología:** Tabla ontológica + SHAP + ruptures + OpenRouter (Gemini Flash / Claude Haiku)

Este módulo no dice "hay riesgo ALTO". Dice **quién actúa, qué hace, cuándo y por qué**.

### Cómo funciona:

```
1. Usuario selecciona UPZ en el mapa
2. Sistema obtiene: SHAP top-3 features + ¿hay breakpoint reciente?
3. Tabla ontológica mapea: feature → diagnóstico → entidad → acción
4. El LLM configurado (OpenRouter — variable LLM_MODEL en Railway) genera el mensaje operacional:
```

> *"**UPZ 44 — Américas (Kennedy)** lleva 14 meses con hurto estructuralmente elevado desde el cambio detectado en octubre 2023. El factor dominante es baja cobertura de cuadrantes (SHAP +0.34), agravado por obra IDU activa en Av. 1° de Mayo (SHAP +0.21).*
>
> *Intervención recomendada:*
> *• **MEBOG/SIJIN**: Operativo de inteligencia + saturación cuadrante 48h*
> *• **IDU**: Solicitar coordinación obra-seguridad para reducir puntos ciegos*
> *• **CAI Américas**: Cra 68 #6-05, tel 3820000 — turno comandante: Sgto. García*"

### La tabla ontológica (17 filas — documentada en Notebook 03):

| SHAP top feature | Diagnóstico | Entidad | Acción |
|---|---|---|---|
| `cuadrantes_por_km2` bajo | Baja cobertura policial | MEBOG / SIJIN | Refuerzo cuadrante + CAI |
| `estrato_promedio_upz` bajo | Vulnerabilidad socioeconómica | SDIS + SDDE | Jóvenes en Paz + empleo |
| `luminarias_led_upz` bajo | Baja iluminación nocturna | UAESP | Reposición luminarias madrugada |
| `n_camaras_upz` bajo | Sin disuasión tecnológica | SDSCJ | Solicitud cámaras Salvavidas |
| `km_via_intervenida_upz` alto | Obra activa → puntos ciegos | IDU + MEBOG | Coordinación obra-seguridad |
| `n_delitos_upz_4sem` alto | Autoexcitación reciente | MEBOG | Saturación patrullaje 48h |
| `temperatura_c` alto | Activador climático (tarde/noche) | IDIGER + Policía | Alerta preventiva |
| `ratio_nuse_criminal_upz` alto | Alto subregistro | SDSCJ / C4 | Campaña denuncia ciudadana |

---

## Módulo 4 — Chatbot Causal ("¿Por qué?")

**Usuarios:** Ciudadano, periodista, funcionario distrital, investigador  
**Tecnología:** FastAPI (Railway) + pgvector + OpenRouter (GraphRAG)

Permite preguntas en lenguaje natural. El sistema busca en el knowledge graph de boletines SCJ + noticias + Plan de Desarrollo:

**Ejemplo de interacción:**

> 👤 *"¿Por qué aumentó el hurto en Kennedy en octubre 2023?"*
>
> 🤖 *"Según el Boletín SCJ de noviembre 2023, el incremento en Kennedy (especialmente UPZs Américas y Timiza) coincide con: (1) el desplazamiento de grupos dedicados al hurto de celulares desde La Candelaria tras operativos de octubre, y (2) el inicio de obras IDU en Av. 1° de Mayo que redujo la visibilidad policial en la zona. El Plan de Desarrollo 2024-2027 contempla la instalación de 45 cámaras adicionales en las UPZs afectadas (meta 2.3.1 del Programa Bogotá Avanza en Seguridad)."*

El chatbot cita fuentes reales con número de boletín y fecha — no genera respuestas genéricas. El modelo LLM se configura vía variable de entorno `LLM_MODEL` en FastAPI (Railway). Por defecto: `google/gemini-flash-1.5` vía OpenRouter (gratuito). La `OPENROUTER_API_KEY` permanece en Railway — nunca se expone al browser.

---

## Matriz de acceso por rol

La plataforma tiene 4 roles con acceso diferenciado via Supabase Auth + RLS:

| Módulo / Feature | Sin login | CIUDADANO | COMANDANTE_CAI | ANALISTA_SDSCJ | ADMIN |
|---|---|---|---|---|---|
| Mapa heatmap (Módulo 1) | ✅ lectura | ✅ | ✅ | ✅ | ✅ |
| Modal 5 pestañas por UPZ | ✅ parcial | ✅ | ✅ | ✅ | ✅ |
| Predicción por UPZ (Módulo 2) | ❌ | ❌ | ✅ solo su cuadrante | ✅ todas | ✅ |
| Proyección +4 semanas | ❌ | ❌ | ✅ su zona | ✅ | ✅ |
| Prescriptivo (Módulo 3) | ❌ | ❌ | ✅ solo su cuadrante | ✅ | ✅ |
| Chatbot causal (Módulo 4) | ❌ | ✅ básico | ✅ | ✅ + SHAP completo | ✅ |
| Reportes comunitarios (opcional) | ❌ | ✅ | ✅ recibe alertas | ✅ | ✅ |
| Botón de pánico (opcional) | ❌ | ✅ | ✅ recibe alarma | ✅ | ✅ |
| Gestión de usuarios | ❌ | ❌ | ❌ | ❌ | ✅ |

*Implementación: Supabase Auth (email + magic link) + RLS por `cuadrante_asignado` en JWT claim. La predicción filtra UPZs usando el mapeo `cuadrante_id → upz_cod` de F4 Cuadrantes (Supabase PostGIS).  
Ver detalles técnicos en [[Arquitectura#autenticación-y-control-de-acceso]] y [[Plataforma-Ciudadana]].*
