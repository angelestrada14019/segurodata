# Ideas de Plataforma — Exploración v2

> **Estado:** EXPLORACIÓN — estas ideas no están en scope del concurso (entrega agosto 2026).  
> **Objetivo:** capturar con rigor técnico, no descartar. Viabilidad a evaluar en fase post-concurso.  
> **Stack actual de referencia:** React + deck.gl + FastAPI (Cloud Run) + Supabase + OpenRouter

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

---

## 3. Mapa interactivo estilo OSIRIS

**Referencia visual:** [osirisai.live](https://www.osirisai.live) — capas de calor con drill-down por zona y paneles de análisis al clic.

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
| 📚 **Fuentes** | Qué datasets informan esta zona: estructurados (F5, F7, F11, F13, F14) y no estructurados (F9 boletines, F10 noticias) | Metadata Supabase |
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

---

## 4. Streaming de alarmas ciudadanas

### Flujo de reporte normal

1. Ciudadano autenticado presiona **"Reportar incidente"** en la app
2. App captura: lat/lon actual, timestamp, tipo de incidente (selección rápida: hurto / riña / sospechoso / otro)
3. Se inserta en Supabase tabla `alarmas_ciudadanas`
4. **Supabase Realtime** → los COMANDANTE_CAI suscritos a ese cuadrante reciben la alerta en tiempo real
5. En el mapa del comandante: aparece un pin parpadeante en la ubicación exacta

### Flujo de pánico (múltiples pulsaciones)

- **5 pulsaciones en < 3 segundos** → alerta tipo `PANICO` (prioridad máxima)
- Diferente visual en el mapa del comandante: pin rojo intermitente + sonido de alerta
- Datos enviados: lat/lon, cuadrante calculado server-side, hora exacta, usuario (anonimizado)

### Esquema de datos

```sql
CREATE TABLE alarmas_ciudadanas (
  id          uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id     uuid REFERENCES auth.users,          -- FK al usuario
  lat         float NOT NULL,
  lon         float NOT NULL,
  upz_cod     varchar,                              -- calculado server-side (spatial lookup)
  cuadrante_id varchar,                            -- calculado server-side
  tipo        varchar CHECK (tipo IN ('REPORTE', 'PANICO')),
  descripcion text,                                -- descripción libre opcional
  estado      varchar DEFAULT 'ACTIVA'
              CHECK (estado IN ('ACTIVA', 'ATENDIDA', 'FALSA_ALARMA')),
  created_at  timestamptz DEFAULT now()
);

-- Índice para queries por cuadrante (consultas de tiempo real)
CREATE INDEX idx_alarmas_cuadrante ON alarmas_ciudadanas (cuadrante_id, estado);
```

### Canal Supabase Realtime para comandantes

```javascript
// El comandante se suscribe a su cuadrante al hacer login
const canal = supabase.channel(`cuadrante-${cuadranteDelComandante}`)
  .on('postgres_changes', {
    event: 'INSERT',
    schema: 'public',
    table: 'alarmas_ciudadanas',
    filter: `cuadrante_id=eq.${cuadranteDelComandante}`
  }, payload => {
    mostrarAlertaEnMapa(payload.new)
    reproducirSonidoAlerta(payload.new.tipo)
  })
  .subscribe()
```

### Consideraciones de viabilidad y operación

| Tema | Consideración |
|------|--------------|
| Anti-spam | Mínimo 60 segundos entre reportes por usuario |
| Privacidad del ciudadano | El comandante ve solo: tipo, hora, cuadrante — nunca el nombre ni cuenta del usuario |
| Falsas alarmas | El comandante puede marcar `FALSA_ALARMA` → el usuario acumula penalizaciones |
| Umbral de suspensión | 3 falsas alarmas confirmadas → cuenta suspendida temporalmente |
| Jurisdicción | Si la alarma cae fuera del cuadrante asignado al comandante → alerta al comandante más cercano |

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

**Concurso — agosto 2026: PWA**
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

**Orden de implementación sugerido (post-concurso):**
1. Idea 1+2 (Roles + Permisos) — base de todo lo demás
2. Idea 3 (Mapa OSIRIS con modal) — mayor impacto visual
3. Idea 4 (Alarmas PWA) — usa Supabase Realtime ya disponible
4. Idea 5 (Tendencias) — extensión del modelo existente
5. Idea 7 (Migrar a React Native Expo) — habilita la idea 6
6. Idea 6 (Botón pánico completo) — requiere nativa
