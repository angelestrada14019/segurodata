# Schema de Supabase y decisiones de diseño

> Referencia técnica del backbone de datos de SeguroData — PostgreSQL 17 + PostGIS + pgvector, proyecto `segurodata` (`pluxaelenhkdaakxdrpm`, `us-east-1`). Verificado contra la base de datos en producción el 11-jul-2026 (19 migraciones aplicadas, `supabase/migrations/`).

---

## Por qué Supabase

Un solo servicio cubre Postgres + PostGIS (geometrías UPZ/cuadrantes/infraestructura) + pgvector (embeddings del corpus GraphRAG) + Auth (magic link, sin contraseñas) + Realtime (notificaciones de nuevos datos) + RLS (control de acceso a nivel de fila). Evita coordinar 3-4 servicios separados para un equipo pequeño con plazo fijo. El free tier cubre el volumen del concurso; el plan del proyecto no requiere el tier de pago.

**Decisión relacionada:** la tabla Silver completa (`silver_upz_mes` a nivel de evento, ~111,606 filas) se calcula y versiona **localmente** (`datos/procesados/`, `scripts/train_model.py`) — Supabase solo recibe los *outputs* del pipeline: predicciones, SHAP, geometrías y el corpus de embeddings. Esto sigue el patrón FTI (Feature/Training/Inference): Supabase es la capa de **serving**, no el almacén de trabajo del pipeline de entrenamiento.

---

## Tablas (`public`, 11 tablas + 1 de sistema PostGIS)

| Tabla | Filas | RLS | Rol |
|---|---:|:---:|---|
| `upz_geometrias` | 112 | ✅ | Geometría MultiPolygon de las 112 UPZs (F2 IDECA) — base espacial |
| `predicciones` | 1,918 | ✅ | Output de `scripts/train_model.py` — `nivel_riesgo` + probabilidades por UPZ×mes |
| `shap_values` | 34,524 | ✅ | SHAP pre-computado, formato largo (UPZ×mes×feature) — 1,918 × 18 exacto |
| `cuadrantes_geom` | 599 | ✅ | Cuadrantes MEBOG (F4) — polígono + `nom_cai` + `telefono` + `upz_codes[]` pre-computado |
| `transmilenio_geom` | 153 | ✅ | Estaciones TransMilenio (F8), geometría punto |
| `camaras_geom` | 92 | ✅ | Cámaras Salvavidas SDM (F13), geometría punto |
| `upz_infraestructura` | 112 | ✅ | Tabla plana: `n_camaras_upz`, `luminarias_led_upz` (F14) por UPZ |
| `change_points` | — | ✅ | Rupturas estructurales (`ruptures` PELT sobre F1 DAI 2018–2026) |
| `documents_corpus` | — | ✅ | Corpus GraphRAG — noticias RSS (F10) + embedding `vector(384)` (pgvector) |
| `user_profiles` | 1 | ✅ | Perfil de usuario: `rol`, `cuadrante_asignado`, `aprobado` |
| `silver_upz_mes` | — | ✅ | Solo columnas agregadas útiles para el frontend (Realtime) — **no** la Silver completa |
| `spatial_ref_sys` | — | ❌ | Tabla de sistema de **PostGIS** (catálogo estándar de proyecciones EPSG) — no contiene datos del proyecto |

**Nota de seguridad transparente:** el advisor de Supabase marca `spatial_ref_sys` sin RLS como hallazgo "crítico" — es el catálogo estándar que instala la extensión PostGIS en cualquier proyecto (definiciones públicas de sistemas de referencia espacial, no datos de la aplicación ni información sensible). Es una tabla de sistema, no algo que el proyecto haya creado; habilitar RLS ahí no protege ningún dato propio. Se documenta aquí para que quede explícito, en vez de "silenciarlo" sin mencionarlo.

### `silver_upz_mes` — columnas (agregado UPZ×mes, no evento)

`id · upz_cod · anio · mes · tipo_crimen · es_crimen · n_delitos · n_delitos_upz_4sem · n_delitos_upz_8sem · cod_localidad · nom_localidad · temperatura_c · precipitacion_mm_mes · n_incidentes_nuse · ratio_tipo_nuse_total · estrato_promedio_upz · cuadrantes_por_km2 · area_upz_km2 · n_estaciones_tm · dist_tm_metros · es_mitad_anio · km_via_intervenida_upz · n_camaras_upz · luminarias_led_upz`

### `predicciones` — columnas

`upz_cod · anio · mes · nivel_riesgo · prob_critico · prob_alto · prob_medio · prob_bajo · origen · updated_at · metadata (jsonb: model_version, pipeline_run_date, features)`

### `shap_values` — columnas

`upz_cod · anio · mes · feature · valor · origen · metadata (jsonb)` — formato largo: una fila por (UPZ, mes, variable), 18 filas por predicción.

### `user_profiles` — columnas

`user_id (uuid, FK a auth.users) · email · rol · cuadrante_asignado (nullable) · aprobado · created_at`

---

## RLS — matriz real por tabla

| Tabla | Política | Regla |
|---|---|---|
| `upz_geometrias`, `transmilenio_geom`, `camaras_geom`, `upz_infraestructura`, `change_points` | `*_lectura_publica` | `USING (true)`, `TO anon, authenticated` — lectura pública sin excepción |
| `cuadrantes_geom` | `cuadrantes_autenticados` | `USING (true)`, `TO authenticated` únicamente — expone `nom_cai` + `telefono`, decisión deliberada de no publicarlo a anon |
| `documents_corpus`, `shap_values`, `silver_upz_mes` | `*_autenticados` | `TO authenticated` — el chatbot (Módulo 4) requiere sesión, aunque sea CIUDADANO básico |
| `predicciones` | `predicciones_por_rol` | Ver detalle abajo — la única política con lógica condicional real |
| `user_profiles` | `perfil_propio_o_admin` (lectura), `admin_edita_perfiles` (escritura), `auth_admin_lee_perfiles` | Un usuario lee su propio perfil; `ADMIN` lee/edita cualquiera; el rol interno `supabase_auth_admin` puede leer todos (lo necesita el JWT hook) |

### `predicciones_por_rol` — la política con más lógica del proyecto

```sql
USING (
  (auth.jwt()->>'rol') IN ('ANALISTA_SDSCJ', 'ADMIN', 'CIUDADANO')
  OR (
    (auth.jwt()->>'rol') = 'COMANDANTE_CAI'
    AND upz_cod IN (
      SELECT unnest(cg.upz_codes) FROM cuadrantes_geom cg
      WHERE cg.cuadrante_id = auth.jwt()->>'cuadrante_asignado'
    )
  )
)
```

`COMANDANTE_CAI` solo lee filas de `predicciones` de las UPZs de su propio cuadrante — el resto de roles ve todo. Esta política protege la tabla base; **las RPCs de mapa la replican manualmente** en vez de heredarla (ver siguiente sección) porque corren `SECURITY DEFINER`.

---

## Funciones (RPCs) — 12 funciones custom

| Función | `SECURITY` | Grant a `anon` | Propósito |
|---|:---:|:---:|---|
| `upz_geojson(p_anio, p_mes)` | DEFINER | ✅ | GeoJSON de las 112 UPZs + `nivel_riesgo` del período — Módulo 1 |
| `localidades_geojson(p_anio, p_mes)` | DEFINER | ✅ | Igual, agregado por localidad (zoom < 12) |
| `transmilenio_geojson()` | INVOKER | ✅ | Puntos TransMilenio — pública desde migración 0018 |
| `camaras_geojson()` | INVOKER | ✅ | Puntos Cámaras Salvavidas — pública desde migración 0018 |
| `alumbrado_geojson()` | INVOKER | ✅ | Choropleth de luminarias por UPZ — pública desde migración 0018 |
| `cuadrantes_geojson()` | INVOKER | ❌ | Polígonos de cuadrantes — solo `authenticated` (expone CAI + teléfono) |
| `periodo_mas_reciente()` | DEFINER | ✅ | Resuelve el último (anio, mes) con datos en `predicciones` |
| `match_documents(...)` | INVOKER | ✅ | Búsqueda por similitud coseno en `documents_corpus` (pgvector) — retrieval del GraphRAG |
| `custom_access_token_hook(event)` | INVOKER | solo `supabase_auth_admin` | Inyecta `rol`/`cuadrante_asignado` en el JWT — Auth Hook de Supabase |
| `handle_new_user()` | DEFINER | trigger interno | Autoprovisiona `user_profiles` al crear un `auth.users` nuevo |
| `upsert_transmilenio_geom(...)`, `upsert_camara_geom(...)` | DEFINER | solo `service_role` | Escritura de geometrías puntuales — únicamente `scripts/seed_supabase.py` las usa |

**Por qué `upz_geojson`/`localidades_geojson` son `SECURITY DEFINER` con la lógica de rol *escrita a mano dentro de la función*, en vez de heredar la RLS de `predicciones`:** al ser `SECURITY DEFINER`, la función corre con los privilegios de su dueño y **no** respeta la RLS de las tablas que consulta — así que replican manualmente el mismo filtro (`v_rol`/`v_cuadrante` leídos de `auth.jwt()`) dentro del `LEFT JOIN`. Esto fue necesario porque estas RPCs unen varias fuentes (`upz_geometrias` + `predicciones`) y devuelven un JSON ya armado — RLS por sí sola no puede filtrar *después* del `jsonb_agg`. Ver migración `20260711_0019` para el detalle de por qué el filtro de cuadrante se quitó de estas dos funciones específicamente (Módulo 1 es diagnóstico público para todos los roles; la restricción de cuadrante es correcta solo para `/predict`/`/prescribe`, no para el mapa).

---

## Autenticación

- **Método:** magic link (Supabase Auth, sin contraseñas) — `frontend/src/routes/login.tsx`, `supabase.auth.signInWithOtp()`.
- **Firma del JWT:** ES256/JWKS (no HS256 legacy) — claves rotables sin invalidar sesiones activas.
- **Autoprovisioning por dominio** (`handle_new_user()`, trigger `on_auth_user_created` en `auth.users`):

  | Dominio del correo | `rol` asignado | `aprobado` |
  |---|---|:---:|
  | `@policia.gov.co` | `COMANDANTE_CAI` | `true` |
  | `@sdscj.gov.co` | `ANALISTA_SDSCJ` | `true` |
  | cualquier otro | `CIUDADANO` | `false` |

  `cuadrante_asignado` **nunca** se autoprovisiona — llega `NULL` para todo `COMANDANTE_CAI` nuevo. Un `ADMIN` lo asigna después vía `PATCH /admin/usuarios/{id}/cuadrante` (`frontend/src/routes/admin-usuarios.tsx` → `/admin/usuarios`, desplegable con la lista real de cuadrantes). El rol `ADMIN` en sí **tampoco** tiene autoprovisioning por dominio — se asigna únicamente por SQL/Dashboard manual (mismo mecanismo que existía para `cuadrante_asignado` antes de que se construyera ese endpoint).

- **Claims del JWT:** `custom_access_token_hook()` lee `user_profiles` por `user_id` e inyecta `rol` y `cuadrante_asignado` en cada token nuevo. Se habilita manualmente en el Dashboard (Authentication → Auth Hooks) — no hay forma de activarlo por migración SQL.

---

## Realtime

`silver_upz_mes` tiene Realtime habilitado (`ALTER PUBLICATION supabase_realtime ADD TABLE silver_upz_mes`, migración `0009`) — el frontend se suscribe a INSERTs nuevos para la UPZ que el usuario tiene abierta en el modal (`use-silver-realtime.ts`) y muestra un toast informativo, sin refetch automático.

---

## Extensiones habilitadas

`postgis` (geometrías UPZ/cuadrantes/infraestructura, `ST_AsGeoJSON`, `ST_Union` para agregados por localidad) · `pgvector` (`vector(384)`, embeddings `all-MiniLM-L6-v2` del corpus GraphRAG, búsqueda por similitud coseno en `match_documents`).

---

*Ver también: [[Arquitectura]] (vista general del stack), [[Modulos]] (matriz de acceso por rol y módulo), `supabase/migrations/` (las 19 migraciones, fuente de verdad literal del schema).*
