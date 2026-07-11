# Historias de Usuario — Features Opcionales Post-Concurso

> **Estado:** POST-CONCURSO — estas features tienen diseño completo pero quedan fuera del alcance de esta entrega (13 julio 2026) por dependencias y complejidad operacional.  
> **Prerequisito común:** Ideas 1+2 (Supabase Auth + RLS) deben estar implementadas antes que cualquier HU de este documento.  
> **Referencia técnica:** `docs/ideas_plataforma_ciudadana.md` contiene análisis de viabilidad, veredictos técnicos y evaluación crítica detallada de cada idea.

---

## Idea 4 — Alertas Comunitarias en Tiempo Real (modelo Waze)

**Concepto:** reportes ciudadanos ligeros (no denuncias formales) que aparecen en el mapa en tiempo real y se escalan automáticamente al COMANDANTE_CAI cuando se supera un umbral de concentración.

**Diferenciador vs "A Denunciar" (Fiscalía):** latencia <1s vs 24h de procesamiento. No reemplaza la denuncia formal — es inteligencia situacional complementaria.

**Nota de sesgo:** los reportes tienen sesgo de acceso digital (más reportes en estratos 4-6). Este sesgo aplica solo a la capa de visualización. Los reportes ciudadanos NUNCA deben convertirse en features del modelo XGBoost — contaminarían las predicciones con sesgo socioeconómico.

---

### HU-01: Reportar un incidente en tiempo real

**Como** CIUDADANO autenticado,  
**quiero** reportar un incidente tocando 3 botones (categoría + confirmar)  
**para** alertar a mi comunidad y al comandante del cuadrante en menos de 1 segundo.

**Criterios de aceptación:**
- CA1: El pin aparece en el mapa de todos los usuarios de esa UPZ en < 1 segundo (Supabase Realtime)
- CA2: El `cuadrante_id` y `upz_cod` se calculan **server-side** via spatial lookup PostGIS (`ST_Within(point, cuadrante_geom)`) — nunca en el cliente
- CA3: El reporte expira automáticamente a las 2 horas si no recibe confirmaciones (campo `expires_at`)
- CA4: Máximo 1 reporte por cuenta cada 5 minutos (anti-spam por `user_id`)
- CA5: Categorías disponibles: ROBO · RIÑA · SOSPECHOSO · ACCIDENTE · OTRO
- CA6: Descripción libre opcional (campo `descripcion text`)

**Dependencias técnicas:** F4 Cuadrantes cargado en Supabase PostGIS (pre-mortem T7), Auth implementada (Ideas 1+2)

---

### HU-02: Ver reportes activos en el mapa

**Como** CIUDADANO o COMANDANTE_CAI,  
**quiero** ver los pines de reportes activos en mi zona en el mapa  
**para** tener conciencia situacional en tiempo real.

**Criterios de aceptación:**
- CA1: Solo se muestran reportes con `estado = 'ACTIVO'` y `expires_at > now()`
- CA2: El CIUDADANO ve pines de su UPZ; el COMANDANTE_CAI ve su cuadrante completo (RLS)
- CA3: Los pines tienen color por categoría: rojo=ROBO, naranja=RIÑA, amarillo=SOSPECHOSO
- CA4: Hover en el pin muestra: categoría, hora, cantidad de confirmaciones

---

### HU-03: Confirmar un reporte ciudadano (+1)

**Como** CIUDADANO en la zona de un reporte activo,  
**quiero** confirmar el reporte de otro ciudadano (+1)  
**para** aumentar la credibilidad del aviso para el comandante.

**Criterios de aceptación:**
- CA1: Máximo 1 confirmación por cuenta por reporte (evita spam de confirmaciones)
- CA2: Las confirmaciones anónimas son aceptadas (baja fricción de participación)
- CA3: El contador de confirmaciones es visible en el pin del mapa
- CA4: Si el reporte alcanza 5+ confirmaciones → el pin cambia de tamaño (más visible)

---

### HU-04: Recibir alerta de cluster de reportes (COMANDANTE_CAI)

**Como** COMANDANTE_CAI suscrito a mi cuadrante,  
**quiero** recibir una alerta cuando se detecte un cluster de reportes  
**para** tomar decisiones operacionales rápidas sin tener que monitorear el mapa constantemente.

**Criterios de aceptación:**
- CA1: Umbral de escalada: ≥ 3 reportes del mismo `categoria` en el mismo `cuadrante_id` en ≤ 15 minutos
- CA2: La alerta llega por Supabase Realtime al panel del comandante (tabla `alertas_cluster`)
- CA3: La alerta muestra: tipo de evento + cantidad de reportes + mapa de calor del cluster
- CA4: **El comandante decide si actuar** — el sistema NO despacha automáticamente. La alerta es informativa, no una orden
- CA5: El comandante puede marcar la alerta como `ATENDIDA` o `FALSA_ALARMA`

**Nota de seguridad (pre-mortem T4):** el umbral de 3 reportes es abusable con cuentas coordinadas. En producción, usar umbral dinámico basado en historial de falsos positivos de esa zona + rate limiting por IP.

---

## Idea 6 — Botón de Pánico Interno PWA

**Concepto:** botón visible en la app que el ciudadano puede presionar en caso de emergencia. Dispara una alerta al comandante del cuadrante más cercano, mantiene la pantalla encendida, y envía SMS al 123 si no hay internet.

**Limitación técnica documentada:**
- La detección con pantalla bloqueada (botón de volumen del hardware) requiere React Native o Flutter nativo — imposible en PWA
- El bloqueo de apagado del teléfono no existe en ningún stack mobile consumer (ni iOS, ni Android consumer)
- Wake Lock API mantiene la PANTALLA encendida (no el teléfono apagado) — funciona en Chrome/Android y iOS 16.4+ en primer plano

---

### HU-05: Activar alerta de emergencia con botón de pánico

**Como** CIUDADANO con la app abierta,  
**quiero** presionar un botón de pánico visible desde cualquier pantalla  
**para** alertar al comandante de mi cuadrante y mantener evidencia de mi ubicación.

**Criterios de aceptación:**
- CA1: El botón es visible desde cualquier vista de la app (componente flotante o en nav bar)
- CA2: Al presionar: pantalla de confirmación de 3 segundos con cuenta regresiva y botón de cancelar
- CA3: Si se confirma: alerta con `tipo = 'PANICO'` insertada en `alarmas_ciudadanas` → Supabase Realtime → pin en mapa del comandante en < 1 segundo
- CA4: Wake Lock se activa automáticamente (mantiene pantalla encendida mientras alarma activa)
- CA5: El `cuadrante_id` se calcula server-side (FastAPI spatial lookup), no en el cliente
- CA6: El ciudadano recibe confirmación visual de que la alarma fue activada

---

### HU-06: Respaldo por SMS al 123 sin internet

**Como** CIUDADANO en emergencia sin conectividad,  
**quiero** que la app envíe mis coordenadas al 123 aunque no haya internet  
**para** asegurar que mi emergencia sea atendida por el sistema institucional.

**Criterios de aceptación:**
- CA1: Si no hay internet al activar el pánico: abrir compositor de SMS con mensaje pre-redactado
- CA2: Mensaje: `"EMERGENCIA SeguroData UPZ[cod] lat:[lat] lon:[lon] [timestamp]"`
- CA3: El número destino es el 123 (NUSE)
- CA4: El mensaje incluye las coordenadas GPS con 5 decimales de precisión
- CA5: Funciona en cualquier teléfono que soporte el esquema URL `sms:`

---

### HU-07: Desactivar alarma con PIN

**Como** CIUDADANO que activó el pánico,  
**quiero** desactivar la alarma ingresando un PIN  
**para** evitar que el agresor pueda silenciarla fácilmente.

**Criterios de aceptación:**
- CA1: La única forma de desactivar la alarma es ingresar el PIN correcto en la app
- CA2: El PIN se configura en los ajustes del usuario antes de una emergencia
- CA3: Si el PIN se ingresa incorrectamente 5 veces → la alarma se mantiene y se genera un log del intento
- CA4: Al desactivar: el estado de la alarma cambia a `ATENDIDA` en Supabase
- CA5: El PIN predeterminado para nuevos usuarios es el de bloqueo del teléfono — el usuario puede cambiarlo en ajustes

---

### HU-08: Recibir alarma de pánico (COMANDANTE_CAI)

**Como** COMANDANTE_CAI suscrito a mi cuadrante,  
**quiero** recibir la alarma de pánico de un ciudadano en mi zona  
**para** responder de forma inmediata.

**Criterios de aceptación:**
- CA1: La alarma de pánico aparece en el mapa del comandante con pin rojo parpadeante diferenciado de reportes normales
- CA2: El comandante ve: tipo=PANICO, hora exacta, cuadrante, estado (ACTIVA/ATENDIDA) — NUNCA el nombre ni user_id del ciudadano (privacidad Ley 1581)
- CA3: El comandante puede marcar la alarma como `ATENDIDA`
- CA4: Si la alarma no es atendida en 10 minutos → alerta de escalada al ANALISTA_SDSCJ

---

## Dependencias técnicas

```
HU-01 (Reportar)
  ├── Auth + Roles (Ideas 1+2) — user_id válido para el reporte
  ├── F4 Cuadrantes en PostGIS [pre-mortem T7] — spatial lookup server-side
  └── Supabase Realtime — propagación <1s

HU-04 (Alerta cluster)
  ├── HU-01 (Reportar) — necesita reportes existentes
  └── PostgreSQL Trigger o FastAPI Cron — verificar umbral en cada INSERT

HU-05 (Botón pánico)
  ├── Auth + Roles (Ideas 1+2) — usuario autenticado
  ├── F4 Cuadrantes en PostGIS [pre-mortem T7] — spatial lookup
  ├── HU-01 schema (tabla alarmas_ciudadanas o reportes_comunidad)
  └── Wake Lock API — Chrome/Android ✅ · iOS 16.4+ ✅ (solo primer plano)

HU-07 (Desactivar PIN)
  └── HU-05 (Botón pánico activado)

HU-08 (Comandante recibe pánico)
  └── HU-05 + Supabase Realtime suscripción por cuadrante
```

## Notas de implementación (post-concurso)

- **Orden de HUs:** HU-01 → HU-02 → HU-03 → HU-04 → HU-05 → HU-06 → HU-07 → HU-08
- **Estimado:** 3-4 semanas para implementar las 8 HUs completas con Auth ya funcionando
- **Para hardware button (pantalla bloqueada):** React Native con `react-native-volume-manager` o Flutter con background service en Android. iOS es imposible en cualquier stack sin jailbreak.
- **Canales adicionales post-concurso:** Telegram Bot API (gratuito) y SendGrid email (100/día free) son los canales más accesibles en Colombia sin costo de API. WhatsApp Business API tiene costo y requiere cuenta verificada.
- **Cleanup de datos expirados:** agregar `WHERE expires_at > now()` a todas las queries de reportes. Para purga real, usar pg_cron en Supabase (disponible desde Plan Pro) o GitHub Action nocturno.
