# Ideas de Plataforma — Exploración v2

> **Estado:** EXPLORACIÓN — estas ideas no están en scope de esta entrega (13 julio 2026).  
> **Objetivo:** capturar con rigor técnico, no descartar. Viabilidad a evaluar en fase post-concurso.  
> **Stack actual de referencia:** React + deck.gl + FastAPI (Railway) + Supabase + OpenRouter

---

## 1. Autenticación con roles — login sin registro manual

**Concepto:** el usuario no puede crear su propia cuenta. Un administrador la crea por invitación o el sistema la autoprovisiona según el dominio del email institucional.

### Roles propuestos

| Rol | Quién | Acceso |
|-----|-------|--------|
| CIUDADANO | Cualquier persona con cuenta aprobada | Mapa descriptivo + botón de alarma |
| COMANDANTE_CAI | Oficial de policía por cuadrante | + Predicciones + prescriptivo de su zona |
| ANALISTA_SDSCJ | Secretaría Distrital de Seguridad | + Chatbot causal + datos SHAP completos |
| ADMIN | Equipo SeguroData | Todo + gestión de usuarios y roles |

### Stack disponible — sin agregar dependencias

**Supabase Auth** (ya en el stack) soporta nativamente:
- Magic link (invitación por email)
- OAuth Google / GitHub
- Email + contraseña

**Supabase RLS** (Row Level Security): políticas de acceso a nivel de fila en PostgreSQL — el rol se guarda en una tabla `user_profiles` y se valida en cada query, sin pasar por FastAPI.

### Autoaprovisionamiento por dominio institucional

```
@policia.gov.co   → COMANDANTE_CAI  (pendiente asignación de cuadrante por ADMIN)
@sdscj.gov.co     → ANALISTA_SDSCJ
cualquier otro    → CIUDADANO (requiere aprobación de ADMIN)
```

### Preguntas abiertas de viabilidad

- ¿Cómo verificamos que el correo institucional es legítimo? (el dominio no garantiza identidad)
- ¿El CIUDADANO se autoaprovisionan libremente o requieren aprobación?
- ¿Qué pasa con oficiales que no tienen correo `@policia.gov.co`?

### Veredicto técnico

**Estado:** ✅ VIABLE para el concurso

Supabase Auth free tier (50,000 MAU, magic link, OAuth) cubre todo sin dependencias nuevas. El autoaprovisionamiento por dominio se implementa con Auth Hooks de Supabase (función PostgreSQL que dispara al crear el usuario).

**Limitación real:** el dominio `@policia.gov.co` no garantiza identidad del oficial — solo que alguien tiene acceso al buzón. Para el prototipo del concurso es aceptable. En producción requeriría integración con el directorio LDAP de la MEBOG, fuera del alcance del reto.

**Alternativa si no se implementa:** demo sin auth mostrando capturas de pantalla de los roles. Aceptable pero menos impactante — el 90% de los proyectos en concursos de datos no tienen auth real.

---

## 2. Permisos basados en rol (matriz completa)

| Feature | Sin login | CIUDADANO | COMANDANTE_CAI | ANALISTA_SDSCJ | ADMIN |
|---------|-----------|-----------|----------------|----------------|-------|
| Mapa heatmap público (Módulo 1) | ✅ lectura | ✅ | ✅ | ✅ | ✅ |
| Predicción por UPZ (Módulo 2) | ❌ | ❌ | ✅ solo su cuadrante | ✅ todas las UPZs | ✅ |
| Sugerencias prescriptivas (Módulo 3) | ❌ | ❌ | ✅ solo su cuadrante | ✅ | ✅ |
| Chatbot causal (Módulo 4) | ❌ | ✅ básico | ✅ | ✅ completo + SHAP | ✅ |
| Botón de alarma ciudadana | ❌ | ✅ | ✅ | ✅ | ✅ |
| Recibir alarmas de ciudadanos | ❌ | ❌ | ✅ su cuadrante | ✅ todas | ✅ |
| Tendencias predictivas (Idea #5) | ❌ | ❌ | ✅ su zona | ✅ | ✅ |
| Panel de gestión de usuarios | ❌ | ❌ | ❌ | ❌ | ✅ |

### Implementación técnica

```typescript
// React — guard de ruta por rol
<ProtectedRoute requiredRole="COMANDANTE_CAI">
  <PrediccionPage />
</ProtectedRoute>

// FastAPI — middleware de auth
# JWT de Supabase → decodificar → verificar rol en user_profiles
# El backend NUNCA confía en el rol que manda el frontend

// Supabase RLS — ejemplo
CREATE POLICY "comandante solo ve su cuadrante"
  ON predicciones FOR SELECT
  USING (cuadrante_id = auth.jwt()->>'cuadrante_asignado');
```

### Veredicto técnico

**Estado:** ✅ VIABLE — requiere Idea 1 implementada primero

La policy RLS del ejemplo es SQL correcto de Supabase. El JWT puede incluir `cuadrante_asignado` como claim personalizado via Auth Hook.

**Corrección importante:** la predicción del modelo es por UPZ, no por cuadrante. La policy debe usar el mapeo `cuadrante_id → upz_cod(s)` disponible en F4 (columna `PCUNOMCAI`), no una columna que no existe en la tabla de predicciones. Sin este mapeo, la policy falla silenciosamente devolviendo cero filas.

**Sin alternativa:** si Idea 1 no se implementa, esta idea no aplica.

---

## 3. Mapa interactivo estilo C4 / Palantir

**Referencia visual:** interfaz del C4 de Bogotá o Palantir Gotham Crime Intelligence — capas de calor con drill-down por zona y paneles de análisis al clic.

> ⚠️ **Nota:** la referencia original a `osirisai.live` era incorrecta. OSIRIS.live es una plataforma OSINT global de rastreo de aeronaves, satélites y conflictos armados — no tiene relación con análisis de crimen urbano. Usar esa referencia ante el jurado sería rebatible.

### Comportamiento por nivel de zoom

```
Zoom inicial (ciudad completa)
  → PolygonLayer por LOCALIDAD (20 zonas de Bogotá)
  → Color gradiente: ALTO (rojo) → MEDIO (amarillo) → BAJO (verde)

Al hacer zoom > 12 (barrios visibles)
  → Transición automática a PolygonLayer por UPZ (112 zonas)
  → Mismo esquema de colores

Al hacer clic en cualquier localidad o UPZ
  → Modal lateral con 5 pestañas:
```

### Modal de análisis por zona (5 pestañas)

| Pestaña | Contenido | Fuente de datos |
|---------|-----------|----------------|
| 📊 **Descripción** | Qué está pasando: serie histórica NUSE, top 3 tipos de incidente, tendencia últimas 8 semanas | F5 NUSE → Silver → Supabase |
| 🔮 **Predicción** | Nivel de riesgo XGBoost (ALTO/MEDIO/BAJO) + probabilidades de cada clase | FastAPI `/predict` → XGBoost |
| 💡 **Sugerencia** | Texto prescriptivo: causa dominante + entidad responsable + acción operacional | Tabla ontológica + OpenRouter |
| 📚 **Fuentes** | Qué datasets informan esta zona: estructurados (F5, F7, F11, F13, F14) y no estructurados (F10 noticias) | Metadata Supabase |
| 💬 **Chatbot** | Pregunta libre contextualizada en la UPZ seleccionada — el GraphRAG filtra por zona | FastAPI `/graphrag` con upz_ctx |

### Aclaración: ¿predicción = XGBoost O IA generativa?

**Ambos son necesarios — responden preguntas distintas y no son excluyentes:**

| Capa | Tecnología | Pregunta que responde | Ejemplo de salida |
|------|-----------|----------------------|------------------|
| Nivel de riesgo | XGBoost pre-entrenado | "¿Cuánto riesgo hay?" | "ALTO — 82% de probabilidad" |
| Factores causales | XGBoost + SHAP pre-computado | "¿Qué variable explica más el riesgo?" | "Cuadrantes/km² (+0.34 SHAP)" |
| Narrativa explicativa | OpenRouter + GraphRAG | "¿Por qué está pasando esto?" | "Según boletín SCJ mar-2026, el aumento en Kennedy coincide con..." |
| Recomendación operacional | Tabla ontológica + OpenRouter | "¿Qué hacer y quién lo hace?" | "Operativo MEBOG 48h + solicitar cámaras SDSCJ" |

El XGBoost produce el número; el LLM produce el texto operacional. Son capas que se suman.

### Layers deck.gl adicionales para este mapa

```javascript
// Ya planificados en el stack actual — se activan/desactivan con toggles
new PolygonLayer({ id: 'localidades', data: localidades, getFillColor: d => riskColor(d.riesgo) })
new PolygonLayer({ id: 'upzs',       data: upzs,       getFillColor: d => riskColor(d.nivel_riesgo) })
new ScatterplotLayer({ id: 'camaras', data: camaras })        // F13 Cámaras Salvavidas
new HeatmapLayer({ id: 'heatmap',    data: incidentes })      // Densidad de incidentes NUSE
new ScatterplotLayer({ id: 'alarmas', data: alarmasActivas }) // Alarmas ciudadanas en tiempo real
```

### Veredicto técnico

**Estado:** ✅ VIABLE — es esencialmente el plan actual de Fase 3 con refinamiento UX

**Corrección crítica sobre la referencia:** `osirisai.live` NO es una plataforma de análisis de crimen urbano. Es una plataforma OSINT global que rastrea aeronaves, satélites, redes CCTV y conflictos en tiempo real (alternativa open-source a Palantir). Usar esta referencia ante el jurado puede ser rebatida. Referencias correctas: PredPol/Geolitica (descontinuado por sesgo algorítmico documentado), la interfaz del C4 de Bogotá, o Palantir Gotham Crime Intelligence.

El zoom-level switching (Localidades → UPZs) está confirmado en deck.gl via `CompositeLayer`. Esfuerzo: ~4 horas. El modal de 5 pestañas reorganiza los Módulos 1-4 existentes sin agregar nueva lógica de negocio.

**Único elemento genuinamente nuevo:** la pestaña "Fuentes" (qué datasets de datos abiertos informan esta UPZ). Tiene alto valor para el criterio de trazabilidad del concurso. Ningún equipo competidor probablemente la tiene.

**Sin alternativa necesaria:** este diseño ya es el plan de Fase 3. Sustituir referencia OSIRIS antes de la presentación oral.

**Tiger T1 resuelto:** la migración a Railway (siempre activo) elimina el riesgo de cold start en el panel prescriptivo/chatbot del modal. El tab "Sugerencia" y el tab "Chatbot" responden sin demora desde el primer clic.

---

## 4. Streaming de alertas comunitarias — modelo Waze

> **Aclaración de concepto:** esta idea no es un sistema de denuncia formal (como "A Denunciar" de la Fiscalía). Es un modelo de reporte comunitario en tiempo real al estilo de Waze: cualquier ciudadano toca un botón, selecciona una categoría ("están robando", "accidente", "persona sospechosa") y el pin aparece en el mapa compartido. Si varios reportes se acumulan en el mismo cuadrante en poco tiempo, el sistema escala automáticamente al COMANDANTE_CAI.

### Flujo de reporte ciudadano (modelo Waze)

1. Ciudadano — con o sin cuenta — toca **"Reportar"** en el mapa
2. Selección rápida de categoría (máximo 3 toques):

   ```
   🔴 Robo / Hurto      🟠 Riña / Violencia
   🟡 Persona sospechosa  🔵 Accidente / Bloqueo
   ⚪ Otro
   ```

3. App captura: lat/lon, timestamp, categoría, descripción libre opcional
4. Pin aparece en el mapa de todos los usuarios de esa zona en <1 segundo (Supabase Realtime)
5. Otros ciudadanos pueden **confirmar** el reporte (+1 en el pin)
6. El reporte **expira automáticamente** a las 2 horas si nadie lo confirma ni atiende

### Escalada automática al comandante

```
Si en los últimos 15 minutos hay ≥ 3 reportes del mismo tipo
en el mismo cuadrante → se genera alerta automática al COMANDANTE_CAI
```

El comandante ve en su panel: tipo de evento + cantidad de reportes + mapa de calor del cluster.
**El comandante decide si actuar — el sistema no despacha automáticamente.** (Ver crítica abajo.)

### Esquema de datos

```sql
CREATE TABLE reportes_comunidad (
  id            uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id       uuid REFERENCES auth.users,   -- nullable: reportes anónimos permitidos
  lat           float NOT NULL,
  lon           float NOT NULL,
  upz_cod       varchar,                      -- calculado server-side (spatial lookup)
  cuadrante_id  varchar,                      -- calculado server-side
  categoria     varchar CHECK (categoria IN ('ROBO', 'RIÑA', 'SOSPECHOSO', 'ACCIDENTE', 'OTRO')),
  descripcion   text,
  confirmaciones int DEFAULT 0,              -- votos de la comunidad
  estado        varchar DEFAULT 'ACTIVO'
                CHECK (estado IN ('ACTIVO', 'ATENDIDO', 'FALSO', 'EXPIRADO')),
  created_at    timestamptz DEFAULT now(),
  expires_at    timestamptz DEFAULT now() + interval '2 hours'
);

-- Alerta automática cuando se alcanza el umbral por cuadrante
CREATE TABLE alertas_cluster (
  id           uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  cuadrante_id varchar NOT NULL,
  upz_cod      varchar,
  categoria    varchar,
  n_reportes   int,
  creada_at    timestamptz DEFAULT now(),
  vista_por_comandante boolean DEFAULT false
);

CREATE INDEX idx_reportes_cuadrante_activos
  ON reportes_comunidad (cuadrante_id, categoria, created_at)
  WHERE estado = 'ACTIVO';
```

### Canal Supabase Realtime — dos audiencias

```javascript
// CIUDADANOS: ven todos los reportes activos de su UPZ (mapa público)
supabase.channel('reportes-upz-' + upzCod)
  .on('postgres_changes', { event: '*', table: 'reportes_comunidad',
      filter: `upz_cod=eq.${upzCod}` }, actualizarMapa)
  .subscribe()

// COMANDANTE: solo ve las alertas de cluster de su cuadrante
supabase.channel('alertas-' + cuadranteId)
  .on('postgres_changes', { event: 'INSERT', table: 'alertas_cluster',
      filter: `cuadrante_id=eq.${cuadranteId}` }, mostrarAlertaEnPanel)
  .subscribe()
```

### Consideraciones de operación

| Tema | Consideración |
|------|--------------|
| ¿Requiere cuenta? | Reportes básicos: anónimos (más participación). Confirmaciones: requieren cuenta (evita bots) |
| Anti-spam | Máximo 1 reporte por IP/dispositivo cada 5 minutos. Máximo 3 reportes por cuenta por hora |
| Expiración | 2 horas sin confirmación → estado `EXPIRADO`, pin desaparece del mapa |
| Comandante no despacha automáticamente | El cluster genera una alerta visual, no una orden. El comandante evalúa y decide |
| Jurisdicción | Si el reporte cae fuera del cuadrante del comandante → va al comandante del cuadrante correcto (server-side) |

### Veredicto técnico

**Estado:** ✅ VIABLE técnicamente — con problemas estructurales importantes que el jurado puede señalar

---

**Lo que funciona bien:**

Supabase Realtime free tier soporta el caso de uso (200 conexiones concurrentes, 2M mensajes/mes). La diferencia con "A Denunciar" (Fiscalía) es fundamental y articulable: "A Denunciar" es un sistema de denuncia formal con ventana de 24 horas. Este modelo es inteligencia comunitaria en tiempo real, no una denuncia. Son capas complementarias, no competidoras.

La visualización Waze-style (pines en el mapa que los vecinos pueden confirmar) es un modelo que el jurado reconoce y entiende sin explicación. Aumenta el criterio de "impacto ciudadano" del concurso.

---

**Problema 1 — Sesgo de acceso digital (inherente a toda app web, no exclusivo de esta idea):**

Cualquier app web o PWA tiene sesgo de acceso digital: requiere smartphone, conectividad y disposición a instalar/usar la app. Esto correlaciona con estrato socioeconómico en Bogotá. Este sesgo existe en Waze, WhatsApp, Instagram — no es exclusivo de esta feature.

**La distinción crítica de diseño:** ese sesgo aplica a la capa de *visualización* (qué pines aparecen en el mapa), pero NO contamina la capa de *predicción* del modelo, siempre y cuando los reportes ciudadanos nunca sean features de entrada al XGBoost. Los módulos de predicción y prescripción usan únicamente datos institucionales (F5 NUSE 123, F1 DAI, F13 cámaras, F14 alumbrado) que capturan crimen real sin depender de quién tiene smartphone.

**Regla de diseño no negociable:** los reportes de la tabla `reportes_comunidad` son una capa de conciencia situacional en tiempo real. Jamás deben convertirse en un feature del modelo XGBoost. Si se convirtieran en feature, el sesgo de estrato de los reportantes se propagaría directamente a las predicciones.

**Los módulos sin sesgo de acceso digital:**
- Módulo 2 (Predicción XGBoost): alimentado por NUSE 123 institucional — llegan de todos los estratos
- Módulo 3 (Prescriptivo): usa output del modelo + tabla ontológica — sin input ciudadano
- Vista COMANDANTE_CAI: usa datos F5 + predicciones — no depende de reportes voluntarios

**Los módulos con sesgo de acceso digital (aceptado, no resuelto):**
- Reportes comunitarios Waze (esta idea)
- Botón de pánico ciudadano (Idea 6)
- Cualquier vista del rol CIUDADANO

Este sesgo es el mismo que tiene cualquier app de participación ciudadana. No invalida los módulos operacionales de la policía ni el modelo predictivo. Documentarlo honestamente en la presentación.

---

**Problema 2 — Escalada automática al comandante sin verificación:**

Enviar una alerta al comandante basada en 3 reportes ciudadanos no verificados implica un riesgo operacional real. Falsos reportes coordinados (3 personas que se conocen) pueden manipular el sistema fácilmente. Si el comandante actúa sobre una alerta falsa → recursos policiales desperdiciados → el comandante pierde confianza en el sistema.

**Mitigación implementada en el diseño:** el comandante decide si actuar (no despacho automático). El umbral de 3 reportes solo genera una notificación visual, no una orden. Este diseño ya es el correcto.

**Pero el umbral de 3 puede ser demasiado bajo.** Para producción real, evaluar umbral dinámico basado en el historial de falsos positivos de esa zona.

---

**Problema 3 — Efecto de vigilancia vecinal:**

Históricamente, apps de reporte comunitario (Neighbors de Amazon/Ring, Citizen en EE.UU.) han generado casos documentados de vigilantismo y señalamiento racial. Un ciudadano que reporta repetidamente "persona sospechosa" en su cuadra sin que haya crimen real puede generar perfil de vigilancia sobre esa persona.

**Para el concurso:** mencionar este riesgo proactivamente en la presentación oral demuestra madurez del equipo. El jurado de un concurso público de datos va a valorar que el equipo lo identificó.

---

**Para el concurso (recomendación práctica):**

El schema puede crearse en Supabase en Fase 2 sin costo adicional. Para el demo, mostrar el flujo con dos dispositivos: ciudadano reporta → pin aparece en el mapa del comandante. Tener video de respaldo si falla la conectividad. No demostrar la escalada automática en vivo — simularla con datos pre-cargados para evitar dependencia de N reportes reales.

**Alternativa si no se implementa:** mostrar el schema + flujo de datos en diagrama en Notebook 05. El concepto Waze-style es suficientemente conocido para explicarse en 30 segundos sin demo en vivo.

---

## 5. Predicción con tendencias ("si no actúas, esto ocurrirá")

**Concepto:** en lugar de solo decir "esta UPZ está en ALTO", mostrar la trayectoria: "a este ritmo, sin intervención, en 4 semanas la probabilidad de escalar a ALTO es del 73%".

### Visualización propuesta

```
Gráfica de línea por UPZ:
├── Histórico visible: últimas 8 semanas (lag8sem — ya calculado en Silver)
├── Proyección punteada: +4 semanas con banda de confianza (percentil 25-75)
└── Mensaje contextual: "→ Sin intervención: probabilidad ALTO en 4 sem = 73%"

Trigger de alerta automática:
└── Si la proyección sube de categoría (MEDIO→ALTO) → alerta push al COMANDANTE_CAI
```

### Técnica para el concurso (rápida de implementar)

- Usar `lag4sem` y `lag8sem` existentes en Silver para extrapolación lineal
- Banda de confianza: desviación estándar de los últimos 3 meses de esa UPZ
- No requiere nuevo modelo — usa los features ya calculados

### Técnica para post-concurso

- **Prophet** (Meta/Facebook): forecasting con estacionalidad semanal y mensual automática
- Entrada: serie mensual de `n_delitos` por UPZ (mínimo 12 puntos, ya disponibles)
- Ventaja vs extrapolación lineal: detecta picos estacionales (fin de año, Semana Santa, vacaciones)
- Output: intervalo de predicción por semana → nivel de riesgo proyectado

### Veredicto técnico

**Estado:** ✅ VIABLE con extrapolación lineal — ⚠️ Prophet NO viable con los datos actuales del proyecto

**Por qué Prophet no funciona aquí:** los datos NUSE (F5) comienzan enero 2025. Al momento del concurso habrá ~20 puntos mensuales por UPZ. Prophet (Taylor & Letham, *The American Statistician*, 2018) necesita 2+ años de datos para detectar estacionalidad anual de forma confiable. Con 20 observaciones mensuales por UPZ, los intervalos de confianza serán tan amplios que la proyección no agrega información útil — la banda de incertidumbre cubriría prácticamente todos los valores posibles.

**Alternativa para el concurso (1-2 días de implementación):** extrapolación lineal con `lag4sem` y `lag8sem` ya presentes en `silver_upz_mes.parquet` + banda de ±1 desviación estándar de los últimos 3 meses. Produce salidas como: *"UPZ Kennedy — sin intervención, en 3 semanas: probabilidad de escalar a ALTO = 73%"*. Honesto y suficiente.

**Prophet para post-concurso:** válido cuando el dataset tenga 2+ años de datos (disponible ~2027 con series NUSE continuas).

---

## 6. Botón de pánico con grabación de voz

**Concepto:** activación de emergencia con múltiples pulsaciones → grabación de audio + GPS activo + pantalla que no se apaga, sincronizado cuando haya conexión.

### Flujo de emergencia

1. Usuario presiona el botón de pánico **5 veces en < 3 segundos** (o mantiene presionado 3 segundos)
2. La app activa simultáneamente:
   - **Wake Lock API** → pantalla no se apaga
   - **MediaRecorder API** → inicia grabación de audio del entorno
   - **Geolocation API** → captura GPS cada 10 segundos
   - **IndexedDB** → guarda audio + coordenadas localmente (funciona sin internet)
3. Si hay internet disponible: sube en tiempo real a Supabase Storage
4. Si no hay internet: Service Worker + Background Sync → sincroniza cuando se reconecte
5. La grabación solo se detiene cuando el usuario ingresa un PIN de desactivación (evita que el agresor la detenga)

### Compatibilidad de APIs web (PWA)

| API | Chrome / Android | Safari / iOS | Notas |
|-----|-----------------|--------------|-------|
| Wake Lock API | ✅ Chrome 84+ | ✅ iOS 16.4+ | Mantiene pantalla encendida |
| MediaRecorder (primer plano) | ✅ | ✅ | Grabación mientras app visible |
| MediaRecorder (background) | ✅ Android | ❌ iOS | **Limitación crítica en iOS** |
| Geolocation | ✅ | ✅ | Funciona offline — guarda coords localmente |
| Background Sync | ✅ Chrome | ❌ Safari | Solo Android/Chrome garantizado |
| IndexedDB (almacenamiento local) | ✅ | ✅ | Sin límite práctico para audio corto |

**Limitación crítica en iOS:** si el usuario bloquea el teléfono o cambia de app, la grabación se interrumpe. No hay solución en PWA — requiere aplicación nativa.

### Alternativa offline sin internet (funciona en cualquier teléfono)

```javascript
// Fallback: abrir SMS pre-redactado con coordenadas al número de emergencia
const lat = posicion.coords.latitude.toFixed(5)
const lon = posicion.coords.longitude.toFixed(5)
const sms = `sms:123?body=EMERGENCIA UPZ${upzCod} lat:${lat} lon:${lon}`
window.open(sms)
// Los SMS funcionan sin internet y llegan al 123 con las coordenadas exactas
```

### Problema de activación accidental

- El patrón de 5 pulsaciones requiere feedback visual progresivo (contador regresivo)
- Pantalla de confirmación de 3 segundos antes de activar — con botón de cancelar
- Vibración del teléfono como confirmación háptica al activar

### Veredicto técnico

**Estado:** ❌ Concepto original (hardware button con pantalla bloqueada + bloqueo de apagado) NO VIABLE en ningún stack — ✅ VIABLE con rediseño a botón interno en la app

---

**Por qué la detección de hardware con pantalla bloqueada no funciona:**

- **PWA (cualquier browser):** el OS bloquea todos los eventos JavaScript cuando la pantalla está bloqueada. No existe ninguna Web API que los intercepte. Imposible.
- **React Native / Flutter en Android:** posible via background service + `VolumeButtonReceiver`, pero requiere `AccessibilityService` — un permiso que Google restringe desde Android 12 y que Play Store suele rechazar sin justificación de accesibilidad real.
- **iOS con pantalla bloqueada:** imposible en cualquier stack sin jailbreak. Apple no expone ninguna API para que apps de terceros intercepten botones físicos con el teléfono bloqueado. Solo el OS (Emergency SOS nativo) tiene ese acceso.

---

**Por qué el bloqueo de apagado del teléfono no existe en apps de terceros:**

No hay ninguna API en PWA, React Native, Flutter ni Kotlin/Swift nativo para prevenir el apagado físico en dispositivos consumer. El `Device Admin API` de Android funciona solo en dispositivos enterprise con MDM enrollment previo. Apple no tiene equivalente. El sistema operativo permite el apagado siempre — es una característica de seguridad intencional del hardware, no una limitación técnica subsanable.

**Lo que Wake Lock API sí hace:** mantiene la pantalla encendida mientras la app está en primer plano y el dispositivo está conectado. No previene el apagado físico.

---

**Rediseño correcto para el concurso — botón interno en la app:**

Dado que la app necesita estar abierta de todas formas para que funcione el hardware button en PWA, un botón interno grande tiene exactamente la misma restricción operacional con menor complejidad. Flujo viable:

1. Usuario presiona el botón de pánico visible en la app
2. Confirmación de 3 segundos (evita activación accidental)
3. Alarma → Supabase Realtime → pin en mapa del comandante (<1 seg)
4. Wake Lock activo → pantalla no se apaga mientras alarma esté activa
5. PIN de desactivación dentro de la app
6. SMS fallback al 123 con coordenadas si no hay internet

**Para post-concurso (React Native o Flutter puro — no FlutterFlow):** hardware button en background en Android. iOS sigue siendo imposible. FlutterFlow no es adecuado para integraciones con hardware APIs — genera código Dart difícil de mantener para este nivel de complejidad.

---

## 7. PWA vs. Aplicación nativa — análisis de viabilidad

**Contexto:** el stack actual es React (web) → una PWA es la extensión natural y la más rápida. Pero las ideas 4 y 6 tienen limitaciones en PWA, especialmente en iOS.

### Tabla comparativa para este proyecto

| Criterio | PWA | React Native (Expo) | Flutter | Kotlin (solo Android) |
|---------|-----|---------------------|---------|----------------------|
| Código compartido con la web actual | ✅ total | ✅ parcial (lógica JS) | ❌ Dart | ❌ |
| Deploy sin App Store | ✅ | ❌ | ❌ | ❌ |
| Deck.gl / WebGL | ✅ nativo | ⚠️ via WebView | ❌ | ❌ |
| Grabación audio en background | ❌ iOS | ✅ | ✅ | ✅ |
| Wake Lock | ✅ Android/Chrome | ✅ | ✅ | ✅ |
| Notificaciones push | ✅ Android; ⚠️ iOS 16.4+ | ✅ | ✅ | ✅ |
| Background Sync GPS | ✅ Android | ✅ | ✅ | ✅ |
| Acceso a SMS nativo | ❌ | ✅ | ✅ | ✅ |
| Curva de aprendizaje | ✅ ya saben React | ✅ mismo JS/TS | ⚠️ Dart | ⚠️ |
| Tiempo de desarrollo MVP | Rápido | Medio (2-4 sem extra) | Medio | Lento |
| Empaquetado para tiendas | N/A | Expo EAS Build | Flutter build | gradle |

### Recomendación por fases

**Esta entrega (13 julio 2026): PWA**
```
✅ Ya está en el stack → deploy inmediato a Vercel
✅ Ideas 1, 2, 3 y 5 funcionan perfectamente en PWA
✅ Idea 4 (alarmas) funciona con Supabase Realtime en PWA
⚠️ Idea 6 (grabación background) queda limitada a Android / primer plano iOS
```

**Post-concurso: React Native (Expo)**
```
→ Misma lógica JS/TypeScript que la web — máxima reutilización de código
→ Acceso completo a APIs nativas: grabación en background, notificaciones, GPS foreground/background
→ Expo EAS Build: genera APK (Android) + IPA (iOS) sin Xcode ni Android Studio local
→ Puede compartir hooks, servicios, y lógica de negocio con el frontend React actual
→ Estimado: 3-4 semanas para migrar las features de emergencia (ideas 4 y 6)
```

### Limitación a documentar para el demo del concurso

> La idea 6 (grabación sin apagar + botón de pánico persistente) requiere que la app esté en primer plano en iOS PWA. Para el MVP del concurso, el botón de pánico envía: alerta geolocalizada (Supabase Realtime) + grabación de audio activa mientras la app sea visible + SMS de respaldo con coordenadas. La grabación en background completa queda para React Native (Expo) en fase post-concurso.

### Veredicto técnico

**Estado:** ✅ Análisis técnico mayormente correcto — sin acción requerida para el concurso (es una decisión de arquitectura, no una feature)

**Matiz sobre Flutter vs React Native no mencionado en el doc:** Flutter tiene acceso más directo a APIs de plataforma (background services, hardware buttons) que React Native via Expo. Si el objetivo post-concurso es la Idea 6 completa (hardware button en background en Android), Flutter puro es técnicamente superior. FlutterFlow (builder visual low-code de Flutter) **no es adecuado** para integraciones complejas con Supabase Realtime + hardware APIs — genera código Dart difícil de mantener y no permite el control granular que requieren esas integraciones.

**Corrección sobre notificaciones push iOS en PWA:** disponibles desde iOS 16.4 (2023), pero solo si el usuario ha agregado el sitio al Home Screen previamente. Para el comandante (usuario recurrente con dispositivo asignado), este onboarding es manejable.

**Decisión confirmada:** PWA para el concurso. React Native o Flutter puro para post-concurso si el proyecto se materializa.

---

## Dependencias cruzadas entre ideas

```
Idea 1 (Roles) ──────────────────────────► Idea 2 (Permisos)
                                              │
                                              ├──► Idea 3 (Mapa — quién ve qué pestaña)
                                              ├──► Idea 4 (quién recibe alarmas)
                                              └──► Idea 5 (quién ve tendencias)

Idea 4 (Alarmas) ────────────────────────► Idea 6 (extensión con grabación)
                                              │
                                              └──► Idea 7 (PWA vs nativa — decide la capacidad de 6)

Idea 3 (Mapa modal) ─────────────────────► Chatbot contextualizado por UPZ (Módulo 4 existente)
```

**Orden de implementación sugerido para el concurso (Fase 3):**
1. Idea 3 (Mapa 5-tabs + zoom) — ya es el plan, semana 1
2. Idea 5 (Tendencias +4sem) — semana 2
3. Ideas 1+2 (Roles + Permisos) — semana 3, base de 4 y 6
4. Idea 6 (Botón pánico interno) — semana 3, solo si Idea 4 schema está listo

**Orden de implementación sugerido (post-concurso):**
1. Idea 4 (Alarmas Waze completa) — schema ya existe
2. Idea 7 (Migrar a React Native / Flutter puro) — habilita la idea 6 completa
3. Idea 6 (Hardware button en background) — requiere nativa Android

---

## Pre-Mortem — Riesgos Abiertos y Acciones Pendientes

Resultado del pre-mortem ejecutado el 2026-06-02. Los tigers HIGH resueltos (T1 cold start → Railway) y aceptados (T2 expires_at → WHERE filter) se omiten.

### Tigers activos

**[T3 — HIGH] Demo Waze vacío en presentación oral**
- Riesgo: el mapa de reportes comunitarios tendrá cero pines reales en la sustentación.
- Acción: pre-cargar reportes de simulación con timestamps del día anterior. Documentar en el demo script que son datos de un escenario piloto, no reportes reales — esto es honesto y no compromete la credibilidad.
- Responsable: definir antes del ensayo general (Fase 4).

**[T4 — HIGH] Cluster anónimo = 3 POSTs fabricados disparan alerta policial**
- Riesgo: sin cuenta requerida, cualquier atacante envía 3 requests y genera una alerta al comandante.
- Acción: cambiar el diseño — requerir cuenta mínima (Supabase Auth anónima con device fingerprint) para publicar reportes básicos. Solo confirmaciones (+1) pueden ser completamente anónimas.
- Impacto en schema: `user_id` deja de ser nullable para INSERT; se permite auth anónima de Supabase.

**[T5 — HIGH] RLS silenciosa → comandante ve mapa vacío sin mensaje de error**
- Riesgo: policy mal configurada devuelve 0 filas sin error HTTP. No hay forma de distinguir "no hay datos" de "política mal configurada" desde el frontend.
- Acción: (1) crear endpoint de diagnóstico `GET /whoami` que retorna rol + cuadrante_asignado del JWT; (2) en el frontend, si el mapa de predicciones devuelve 0 filas, mostrar mensaje "Verifica tu cuadrante asignado" en lugar de mapa vacío.
- Ver tarea en CRONOGRAMA.md Fase 3 semana 3.

**[T6 — MEDIUM] "73% probabilidad" de la proyección tendencial no es probabilidad XGBoost**
- Riesgo: la extrapolación lineal predice `n_delitos_futuro`, no una probabilidad de clase. Presentarlo como "73% probabilidad de ALTO" es estadísticamente incorrecto.
- Acción: implementar el pipeline completo: `lag4sem/lag8sem → extrapolación → n_delitos_proyectado → XGBoost.predict_proba([n_delitos_proyectado, ...features_fijas]) → probabilidad de clase ALTO`. El `n_delitos_proyectado` entra como feature al modelo junto con las demás variables del mes proyectado.
- Si el pipeline completo es demasiado complejo: etiquetar honestamente como "tendencia estimada" en lugar de "probabilidad", evitando el claim estadístico incorrecto.

**[T7 — MEDIUM] F4 Cuadrantes no está en Supabase PostGIS — prerequisito de Ideas 4 y 6**
- Riesgo: el spatial lookup `lat/lon → cuadrante_id` requiere `ST_Within(point, cuadrante_geom)` en PostGIS. Si F4 no está cargado, todos los reportes tienen `cuadrante_id = null` y nunca llegan al comandante.
- Acción: agregar carga de F4 como tarea explícita en Fase 2 (ver CRONOGRAMA.md). Crear función RPC en Supabase: `get_cuadrante_from_coords(lat, lon) → cuadrante_id`.

### Elephants activos

**[E1 — HIGH] Sin orden de corte para Fase 3 — 5 features en 3 semanas**
- Riesgo: si el tiempo aprieta, no está definido qué se sacrifica primero.
- Orden de corte (de menor a mayor impacto en el concurso):
  1. Idea 6 (botón pánico) — se puede mostrar en diagrama
  2. Ideas 1+2 (Auth/Roles) — demo sin auth es viable
  3. Idea 5 (tendencias) — segunda prioridad alta
  4. Modal 5-tabs + zoom layers — es el plan base, no se puede cortar

**[E2 — HIGH] Sin demo script — bugs se descubren en vivo ante el jurado**
- Riesgo: una demo de 10 minutos sin guión previo garantiza que algo falla en el peor momento.
- Acción: escribir demo script en Fase 4 con: UPZs de ejemplo (Kennedy para ALTO, Usaquén para BAJO), clicks exactos, datos preexistentes en Supabase, respuestas preparadas a interrupciones, plan B si falla la conectividad (video de 3 minutos ya grabado).
- Ver tarea en CRONOGRAMA.md Fase 4.

**[E3 — MEDIUM] JWT Supabase Auth ↔ FastAPI nunca testeado end-to-end**
- Riesgo: la integración requiere que FastAPI use la clave pública de Supabase (o el JWT secret) para validar el token, y que los claims personalizados (`rol`, `cuadrante_asignado`) estén en el payload. Este flujo tiene varios puntos de falla que solo se descubren ejecutándolo.
- Acción: crear test de integración mínimo antes de construir el sistema de roles completo. Ver tarea en CRONOGRAMA.md Fase 3 semana 3.
