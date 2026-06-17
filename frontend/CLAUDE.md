# CLAUDE.md — Frontend SeguroData (Fase 3)

> Dashboard React del sistema **SeguroData Bogotá**. Lo construye el agente **`frontend-builder`**.
> Lee también el `CLAUDE.md` de la raíz (visión, módulos, decisiones) y las skills `backend-segurodata`
> (contrato de la API) y `supabase-segurodata` (tablas).

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

## El mapa (deck.gl)

`PolygonLayer` con 112 UPZs · paleta **CRÍTICO=morado · ALTO=rojo · MEDIO=naranja · BAJO=verde** ·
zoom adaptativo Localidades(zoom<12)→UPZs(zoom≥12) · hover · slider temporal · capas toggleables ·
modal de 5 pestañas por UPZ (Descripción · Predicción · Sugerencia · Fuentes · Chatbot).

## Regla de documentación (INAMOVIBLE)

Tras cualquier cambio significativo, **preguntar al usuario si desea actualizar la documentación**
(este archivo, `wiki_pages/`, `README.md`, `CLAUDE.md` raíz, `CRONOGRAMA.md`) antes de cerrar la tarea.
