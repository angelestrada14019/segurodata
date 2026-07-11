# CLAUDE.md — Frontend SeguroData (Fase 3)

> Dashboard React del sistema **SeguroData Bogotá**. Lo construye el agente **`frontend-builder`**.
> Lee también el `CLAUDE.md` de la raíz (visión, módulos, decisiones) y las skills `backend-segurodata`
> (contrato de la API) y `supabase-segurodata` (tablas).

## Estado: en producción

- **Frontend:** https://segurodata-frontend.vercel.app
- **Backend:** https://segurodata-api-production.up.railway.app

Los 4 módulos + modal de 5 pestañas + Panel Admin están construidos y desplegados. Pendiente,
deliberadamente fuera de alcance por ahora: heatmap día×hora (Plotly) y el backfill del mapeo
UPZ→Localidad de Bogotá (sin eso, la capa de rupturas estructurales no tiene con qué hacer join).

## Stack

**React + Vite + Tailwind v4 + deck.gl + supabase-js** → deploy en **Vercel**. Dashboard dark por
defecto, estilo C4 / Palantir Gotham.

## Comandos

```bash
npm install
npm run dev      # http://localhost:5173
npm run build    # build de producción
npm run lint     # o: npx tsc --noEmit
```

## Variables de entorno (`frontend/.env.local`)

| Variable | Valor |
|----------|-------|
| `VITE_SUPABASE_URL` | `https://pluxaelenhkdaakxdrpm.supabase.co` |
| `VITE_SUPABASE_ANON_KEY` | anon / publishable key de Supabase (NUNCA la service key) |
| `VITE_API_URL` | URL pública del backend FastAPI (Railway) |

## Skills disponibles (vendorizadas en `.claude/skills/` — ver `.claude/skills/VENDORED.md`)

| Skill | Para qué |
|-------|----------|
| **frontend-design** (Anthropic) | Estética no-genérica. Invócala antes de construir UI nueva. |
| **react-patterns** | React 19: composición, evitar waterfalls y re-renders. |
| **tailwind-theme-builder** | Tailwind v4 + tokens + dark mode (montar el theme primero). |
| **shadcn-ui** | Componentes accesibles (modal, tabs, tablas, forms). |
| **design-review** | Revisión visual antes de cerrar una vista. |
| **vercel-react-best-practices** | Performance (ya estaba en el repo). |

El agente **`frontend-builder`** orquesta estas skills aplicándolas al contrato del proyecto.
Lectura adicional (no vendorizada): [wilwaldon/Claude-Code-Frontend-Design-Toolkit](https://github.com/wilwaldon/Claude-Code-Frontend-Design-Toolkit).

## Módulos y su fuente de datos (detalle en la skill `backend-segurodata`)

- **Módulo 1 — Diagnóstico**: Supabase directo (`silver_upz_mes` vía Realtime, `change_points`) + mapa deck.gl.
- **Módulo 2 — Predicción**: FastAPI `/predict` + `/explain`.
- **Módulo 3 — Prescriptivo**: FastAPI `/prescribe`.
- **Módulo 4 — Chatbot**: FastAPI `/graphrag`.

**Texto generado por LLM (Módulos 3 y 4):** `recomendacion_llm` (`/prescribe`) y las respuestas del
chatbot (`/graphrag`) se renderizan con `<TextoMarkdown>` (`components/shared/texto-markdown.tsx`,
`react-markdown` + `remark-breaks`) — OpenRouter suele devolver `**negrita**`/listas aunque el prompt
no lo pida, y antes se mostraban los asteriscos crudos en pantalla. En `chat-panel.tsx` solo aplica al
mensaje del bot; el mensaje del usuario se muestra como texto plano tal cual lo escribió.

## El mapa (deck.gl)

`GeoJsonLayer` (NO `PolygonLayer` — `upz_geometrias.geom` es `MultiPolygon`, supabase-js no parsea
WKB, por eso las RPCs `upz_geojson`/`localidades_geojson`/`cuadrantes_geojson` devuelven GeoJSON ya
construido) con 112 UPZs · paleta **CRÍTICO=morado · ALTO=rojo · MEDIO=naranja · BAJO=verde** ·
zoom adaptativo Localidades(zoom<12)→UPZs(zoom≥12) · hover · slider temporal (navega meses
históricos de `predicciones`, con spinner puntual vía `isFetching` mientras trae el período nuevo —
`placeholderData: keepPreviousData` evita el parpadeo pero necesitaba esa señal aparte) · panel de
5 capas toggleables, todas con geometría real (Cuadrantes, Cambios estructurales, TransMilenio F8,
Cámaras Salvavidas F13, Alumbrado F14). Solo Cuadrantes sigue siendo `authenticated`-only (RPC
`cuadrantes_geojson`, expone CAI + teléfono — decisión deliberada, panel muestra candado sin
sesión); las otras 4 son de lectura pública desde la migración 0018 · modal de 5 pestañas por UPZ
(Descripción · Predicción · Sugerencia · Fuentes · Chatbot), compartido como punto de entrada desde
Módulo 1 y Módulo 2.

## Regla de documentación (INAMOVIBLE)

Tras cualquier cambio significativo, **preguntar al usuario si desea actualizar la documentación**
(este archivo, `wiki_pages/`, `README.md`, `CLAUDE.md` raíz, `CRONOGRAMA.md`) antes de cerrar la tarea.
