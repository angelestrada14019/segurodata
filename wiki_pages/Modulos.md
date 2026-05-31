# Los 4 Módulos del Sistema

La aplicación React tiene 4 páginas, cada una respondiendo una pregunta diferente a sus usuarios objetivo.

---

## Módulo 1 — Diagnóstico ("¿Qué está pasando?")

**Usuarios:** Secretaría de Seguridad, ciudadano informado, periodista  
**Tecnología:** React + deck.gl + Supabase Realtime

- **Mapa WebGL interactivo**: choropleth de Bogotá, 112 UPZs coloreadas por nivel de riesgo actual. Hover muestra estadísticas de la UPZ. Click activa el panel de detalle.
- **Capas toggleables**: crimen por tipo · cámaras Salvavidas SDM · densidad cuadrantes · alumbrado público · estaciones TransMilenio
- **Slider temporal**: reproducir la evolución del crimen mes a mes (2025–2026)
- **Heatmap**: densidad de incidentes NUSE por franja horaria y día de la semana
- **Tendencia con change points**: serie histórica 2018–2026 (F1 DAI) con marcadores en los puntos de ruptura detectados por `ruptures`
- **Realtime**: cuando llegan datos nuevos del NUSE (mensual), Supabase Realtime actualiza el mapa sin recargar la página

---

## Módulo 2 — Predicción ("¿Qué va a pasar?")

**Usuarios:** Comandante de CAI, planeación policial  
**Tecnología:** XGBoost + SHAP + FastAPI + Supabase

- **Predicción por UPZ**: seleccionar UPZ + mes → FastAPI `/predict` → nivel de riesgo ALTO/MEDIO/BAJO + probabilidades de cada clase
- **Mapa predictivo**: todas las 112 UPZs coloreadas rojo/amarillo/verde para el mes seleccionado
- **Top-10 UPZs en riesgo ALTO**: tabla con las UPZs más críticas + nombre del CAI responsable
- **SHAP values**: los 3 features que más explican el riesgo en esa UPZ (cargados desde Supabase — pre-computados, sin cálculo on-demand)
- **Cambio estructural**: indicador si la UPZ tiene un breakpoint reciente (ruptures) — "Riesgo estructural persistente" vs "Pico temporal"

---

## Módulo 3 — Prescriptivo ("¿Qué hacer?")

**Usuarios:** Comandante de CAI, Secretaría de Seguridad  
**Tecnología:** Tabla ontológica + SHAP + ruptures + Claude API

Este módulo no dice "hay riesgo ALTO". Dice **quién actúa, qué hace, cuándo y por qué**.

### Cómo funciona:

```
1. Usuario selecciona UPZ en el mapa
2. Sistema obtiene: SHAP top-3 features + ¿hay breakpoint reciente?
3. Tabla ontológica mapea: feature → diagnóstico → entidad → acción
4. Claude API genera el mensaje operacional en lenguaje del comandante:
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
**Tecnología:** LangChain + Supabase pgvector + Claude API (GraphRAG)

Permite preguntas en lenguaje natural. El sistema busca en el knowledge graph de boletines SCJ + noticias + Plan de Desarrollo:

**Ejemplo de interacción:**

> 👤 *"¿Por qué aumentó el hurto en Kennedy en octubre 2023?"*
>
> 🤖 *"Según el Boletín SCJ de noviembre 2023, el incremento en Kennedy (especialmente UPZs Américas y Timiza) coincide con: (1) el desplazamiento de grupos dedicados al hurto de celulares desde La Candelaria tras operativos de octubre, y (2) el inicio de obras IDU en Av. 1° de Mayo que redujo la visibilidad policial en la zona. El Plan de Desarrollo 2024-2027 contempla la instalación de 45 cámaras adicionales en las UPZs afectadas (meta 2.3.1 del Programa Bogotá Avanza en Seguridad)."*

El chatbot cita fuentes reales con número de boletín y fecha — no genera respuestas genéricas.
