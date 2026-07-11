# Plataforma Ciudadana

> SeguroData no es solo una herramienta de análisis para la policía. Tiene una capa de participación ciudadana que cierra el loop operacional: el ciudadano que reporta un incidente en tiempo real llega directamente al comandante del cuadrante responsable — en menos de 1 segundo, sin ventanas de procesamiento de 24 horas como en "A Denunciar" (Fiscalía, 2017).

---

## Roles y acceso

La plataforma tiene 4 roles con acceso diferenciado. Ver la [[Modulos#matriz-de-acceso-por-rol|Matriz de acceso completa]].

| Rol | Quién | Provisionamiento |
|-----|-------|-----------------|
| **CIUDADANO** | Cualquier persona aprobada | Magic link + aprobación ADMIN |
| **COMANDANTE_CAI** | Oficial con cuadrante asignado | Dominio `@policia.gov.co` + asignación ADMIN |
| **ANALISTA_SDSCJ** | Secretaría Distrital de Seguridad | Dominio `@sdscj.gov.co` |
| **ADMIN** | Equipo SeguroData | Manual |

Ver detalles de implementación en [[Arquitectura#autenticación-y-control-de-acceso]].

---

## Features comprometidas — MVP concurso 13 julio 2026

Estas features están en el alcance de Fase 3 (21 junio – 10 julio 2026).

### Autenticación con roles (Ideas 1 + 2)

**Qué hace:** el usuario no puede crear su propia cuenta. Un administrador la crea por invitación o el sistema la autoprovisiona según el dominio del email institucional. Cada rol ve solo lo que necesita operacionalmente.

**Stack:** Supabase Auth (free tier, 50K MAU) + RLS por `cuadrante_asignado` en JWT claim + middleware JWT en FastAPI.

**Limitación documentada:** el dominio `@policia.gov.co` confirma acceso al buzón, no que el oficial está activo en servicio. Para producción real se requiere integración con el directorio LDAP de la MEBOG. Para el prototipo del concurso, el flujo de invitación manual por ADMIN es suficiente.

**Fase 3:** semana 3 (5–10 julio). Prerequisito: test de integración JWT Supabase↔FastAPI antes de construir el sistema de roles.

---

### Mapa interactivo — modal por zona (Idea 3)

**Qué hace:** transforma el mapa de SeguroData en un sistema OSIRIS-style donde cada zona del mapa es un punto de entrada a todos los módulos del sistema.

**Zoom adaptativo:**
```
Zoom inicial (ciudad completa) → PolygonLayer por LOCALIDAD (20 zonas)
Zoom > 12 (barrios visibles)  → Transición automática a PolygonLayer por UPZ (112 zonas)
```

**Modal de 5 pestañas al clic en cualquier UPZ:**

| Pestaña | Contenido | Fuente |
|---------|-----------|--------|
| 📊 Descripción | Serie histórica NUSE, top 3 tipos de incidente, tendencia 8 semanas | F5 NUSE → Supabase |
| 🔮 Predicción | Nivel de riesgo XGBoost + proyección +4 semanas con banda de confianza | FastAPI `/predict` |
| 💡 Sugerencia | Diagnóstico SHAP + entidad responsable + acción operacional + CAI | Tabla ontológica + OpenRouter |
| 📚 Fuentes | Qué datasets de datos abiertos informan esta UPZ (trazabilidad) | Metadata Supabase |
| 💬 Chatbot | Pregunta libre contextualizada en la UPZ seleccionada | FastAPI `/graphrag` |

**Nota sobre la referencia visual:** la referencia correcta para este estilo de mapa es la interfaz del C4 de Bogotá o Palantir Gotham Crime Intelligence — NO OSIRIS.live (que es una plataforma OSINT de rastreo global de aeronaves y satélites, no de crimen urbano).

**Fase 3:** semana 1 (21–27 junio). Es el plan base del dashboard.

---

### Proyección temporal en Módulo 2 (Idea 5 — integrada, no módulo separado)

**Qué hace:** el Módulo 2 ya predice el nivel de riesgo del próximo mes (XGBoost). La proyección temporal agrega la dimensión visual: muestra cómo ese riesgo evoluciona a lo largo de las próximas 4 semanas.

**Diferencia entre predicción puntual y proyección:**

| | Predicción puntual (XGBoost) | Proyección temporal (Idea 5) |
|--|--|--|
| Output | "El próximo mes: ALTO (82%)" | Gráfica de tendencia con curva +4 semanas |
| Técnica | Modelo ML con 17 features | Extrapolación lineal lag4sem/lag8sem → XGBoost |
| Pregunta | ¿Qué riesgo habrá? | ¿En cuánto tiempo cambia de categoría? |
| Mensaje | Nivel de riesgo del período | "A este ritmo, escalará en ~3 semanas" |

**Técnica para el concurso** (no requiere modelo adicional):
1. Extrapolación lineal de `n_delitos` usando `lag4sem` y `lag8sem` (ya en Silver)
2. Banda de confianza: ±1 desviación estándar de los últimos 3 meses de esa UPZ
3. El `n_delitos` proyectado se pasa al modelo XGBoost → probabilidad de clase ALTO/CRÍTICO
4. Visualización en Recharts (ya en el stack React)

**Por qué no Prophet:** los datos NUSE (F5) comienzan enero 2025. Al momento del concurso habrá ~20 puntos mensuales por UPZ. Prophet (Meta, 2018) necesita 2+ años para detectar estacionalidad anual confiable — con 20 observaciones, los intervalos de confianza serían demasiado amplios para ser útiles. Prophet queda para post-concurso cuando el dataset madure.

**Fase 3:** semana 2 (28 junio – 4 julio), junto con el panel de predicción.

---

## Features opcionales — post-concurso

Estas features tienen schema diseñado y HUs documentadas, pero quedan fuera del alcance del concurso por complejidad operacional y dependencias. Ver el documento `docs/HU-Features-Opcionales.md` en el repositorio para historias de usuario completas, criterios de aceptación y dependencias técnicas.

### Alertas comunitarias en tiempo real (Idea 4) — modelo Waze

Ciudadano reporta un incidente (toca 3 botones: categoría + confirmar) → pin en el mapa visible para todos los usuarios de esa UPZ en <1 segundo (Supabase Realtime). Si 3+ reportes del mismo tipo se acumulan en el mismo cuadrante en 15 minutos → alerta visual al COMANDANTE_CAI.

**Diferenciador vs "A Denunciar" (Fiscalía):** latencia <1s vs ventana de procesamiento de 24 horas. "A Denunciar" es denuncia formal; esto es inteligencia comunitaria en tiempo real.

**Riesgo principal (pre-mortem T4):** reportes anónimos permiten fabricar 3 POSTs → auto-alerta al comandante. Mitigación: requerir cuenta mínima para publicar (no para confirmar).

**Riesgo de sesgo:** reportes se concentran donde hay usuarios de smartphone activos (estratos 4-6). Este sesgo aplica a la capa de visualización, NO al modelo predictivo (que usa NUSE 123 institucional). Los reportes ciudadanos nunca se convierten en features del XGBoost.

### Botón de pánico interno PWA (Idea 6)

Ciudadano con la app abierta presiona el botón de pánico → confirmación de 3 segundos → alerta en el mapa del comandante + Wake Lock (pantalla no se apaga) + PIN para desactivar + SMS fallback al 123 con coordenadas si no hay internet.

**Limitación técnica documentada:** requiere que la app esté en primer plano. La detección con pantalla bloqueada (botón de volumen) requiere React Native o Flutter nativo — no es implementable en PWA. El bloqueo de apagado del teléfono no existe en ningún stack mobile consumer.

---

## Descartado — Idea 7 (PWA vs React Native / Flutter)

Decisión de arquitectura ya tomada. No es una feature a implementar.

- **Concurso:** PWA (React + Vercel) — deploy inmediato, deck.gl nativo, sin tienda de apps
- **Post-concurso:** React Native o Flutter **puro** (no FlutterFlow — demasiado low-code para hardware APIs) si se necesitan notificaciones en background y detección de botón físico
- FlutterFlow genera código Dart difícil de mantener para integraciones con Supabase Realtime + hardware APIs

---

## Riesgos identificados y mitigados

Análisis de riesgo hecho durante el diseño de la plataforma ciudadana, con su resolución:

| Riesgo | Mitigación aplicada | Estado |
|--------|---------------------|--------|
| RLS silenciosa devolvía mapa vacío sin mensaje de error | Endpoint `/whoami` + mensaje explícito en la UI | ✅ Resuelto |
| Cuadrantes de Policía (F4) sin geometría en PostGIS | Tabla `cuadrantes_geom` con índice GIST | ✅ Resuelto |
| Autenticación JWT Supabase↔FastAPI sin test de integración | `tests/test_jwt_e2e.py`, verificado contra Supabase real | ✅ Resuelto |
| Reportes comunitarios anónimos podrían fabricar alertas falsas | Requerir cuenta mínima para publicar (no para confirmar) — feature diferida, ver `docs/HU-Features-Opcionales.md` | Diferido (fuera de esta entrega) |
| Datos de demostración vacíos durante la presentación | Precargar reportes de prueba verosímiles antes de la sustentación | ⏳ Pendiente Fase 4 |
| Sustentación sin guion preparado | Demo script de 10 minutos | ⏳ Pendiente Fase 4 |
