# Batería de pruebas — Chatbot causal (Módulo 4)

> Ejecutada el 11-jul-2026 contra el backend local (`AUTH_MODE=disabled`, mismo código que producción) con 10 preguntas diseñadas para las 3 personas de usuario, más 2 casos límite de resistencia a alucinación.

## Hallazgo crítico encontrado y corregido durante esta batería

La primera corrida (antes del fix) mostró que **las 10 preguntas cayeron al modo de degradación "LLM no disponible"** — el chatbot solo mostraba fragmentos crudos del corpus, sin síntesis real. Diagnóstico:

- `LLM_MODEL=google/gemini-flash-1.5` (primario) → OpenRouter responde **404**: `"No endpoints found for google/gemini-flash-1.5"` — el modelo fue retirado del catálogo de OpenRouter.
- `LLM_MODEL_FALLBACK=anthropic/claude-haiku` (respaldo) → OpenRouter responde **400**: `"anthropic/claude-haiku is not a valid model ID"` — el slug nunca fue válido (falta el número de versión).
- **Railway producción tenía exactamente los mismos dos valores rotos** (verificado con `railway variables`) — el chatbot en vivo estaba en el mismo estado degradado. Como `/prescribe` (Módulo 3) usa el mismo cliente OpenRouter, probablemente también estaba afectado.

**Corregido** (verificado contra el catálogo real de OpenRouter, `GET /api/v1/models`, no adivinado):
- `LLM_MODEL=google/gemini-2.5-flash-lite`
- `LLM_MODEL_FALLBACK=anthropic/claude-3-haiku`

Aplicado en `backend/app/config.py` (defaults), `backend/.env.example`, `backend/.env` local, y en las variables de entorno de Railway producción (`segurodata-api`, redeploy automático).

De paso se corrigió un residuo de la purga de F9: el mensaje de fallback "sin resultados" del chatbot todavía mencionaba *"boletín SCJ"* (`graphrag_service.py`) — fuente eliminada por completo el 10-jul. Ya no la menciona.

---

## Resultados — 2ª corrida (post-fix, todas HTTP 200)

| # | Perfil | Pregunta | Tiempo | Calidad |
|---|--------|----------|-------:|---------|
| 1 | CIUDADANO | ¿Es seguro tomar TransMilenio en Bogotá? | 3.2s | ✅ Recuperó contexto débilmente relacionado (agresión a guarda) pero **no forzó una respuesta** — declinó honestamente en vez de estirar la evidencia |
| 2 | CIUDADANO | ¿Ha bajado el homicidio en Bogotá este año? | 2.2s | ✅ Respuesta precisa, cita `[1]`, cacheada en el 2º intento |
| 3 | COMANDANTE_CAI | ¿Qué pasó con el robo de una camioneta en Suba? | 3.5s | ✅ Precisa, cita correcta, incluye detalle del barrio (San Nicolás) |
| 4 | COMANDANTE_CAI | ¿Hay reportes recientes de fleteros armados en Bogotá? | 3.0s | ✅ Precisa, cita correcta, incluye detalles del arma y vehículo |
| 5 | ANALISTA_SDSCJ | ¿Qué medidas de seguridad hay planeadas para eventos electorales? | 3.0s | ✅ Precisa, cita correcta (10.000 policías, 21 de junio) |
| 6 | ANALISTA_SDSCJ | ¿Qué tendencia hay en los homicidios de Bogotá este año? | 2.8s | ✅ Precisa, misma fuente que #2 con enfoque distinto — buena generalización |
| 7 | GENERAL | ¿Qué está pasando con la seguridad en los parqueaderos de Bogotá? | 3.0s | ⚠️ La recuperación no trajo el artículo más relevante (fraude en zonas de parqueo) — trajo uno tangencial. El LLM lo manejó bien: describió lo recuperado y **explícitamente aclaró que no tenía información sobre parqueaderos**, en vez de inventar |
| 8 | GENERAL | ¿Qué dice la última noticia sobre TransMilenio? | 2.4s | ✅ Declina correctamente — "última noticia" es una pregunta meta-temporal que la búsqueda semántica no está diseñada para resolver; no alucina |
| 9 | EDGE_CASE | ¿Cuál es la capital de Francia? | 2.4s | ✅ Declina correctamente, cero fuentes — fuera de alcance manejado sin alucinar |
| 10 | EDGE_CASE | ¿Cuántos delitos hubo en la Luna el mes pasado? | 3.2s | ✅ Recuperó fragmentos de baja similitud pero declinó responder — resistencia a alucinación con pregunta absurda |

**9/10 respuestas excelentes, 1/10 con una recuperación subóptima que el LLM manejó con criterio** (no bug, comportamiento defensivo correcto). El punto más fuerte de la batería: en los 4 casos donde la recuperación trajo contexto débil o irrelevante (#1, #7, #9, #10), el modelo **nunca fuerza una respuesta** — declina o aclara la limitación, consistente con el principio de "nunca inventa una fuente" del diseño.

## Nota sobre "3 perfiles"

El backend no diferencia el contenido de la respuesta por rol — cualquier usuario autenticado (`CIUDADANO`/`COMANDANTE_CAI`/`ANALISTA_SDSCJ`/`ADMIN`) recibe el mismo chatbot con el mismo corpus. Las preguntas se diseñaron con el lenguaje natural de cada perfil para validar que el sistema responde bien sin importar el registro (coloquial vs. operacional vs. técnico-normativo) — los 3 perfiles pasaron igual de bien, no hay diferencia de calidad a corregir.
