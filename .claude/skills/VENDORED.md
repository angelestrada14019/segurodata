# Skills vendorizadas (terceros)

Estas skills de `.claude/skills/` fueron **copiadas (vendorizadas)** desde repositorios públicos de
terceros para que viajen con el repo y estén disponibles al clonar (igual que `vercel-react-best-practices`
y `supabase`). Todas bajo licencia **MIT**. Vendorizadas el **2026-06-17**.

| Skill | Origen | Ruta original | Licencia |
|-------|--------|---------------|----------|
| `frontend-design` | [anthropics/claude-code](https://github.com/anthropics/claude-code) | `plugins/frontend-design/skills/frontend-design/` | MIT |
| `react-patterns` | [jezweb/claude-skills](https://github.com/jezweb/claude-skills) `@0aa0f44` | `plugins/frontend/skills/react-patterns/` | MIT |
| `design-review` | jezweb/claude-skills `@0aa0f44` | `plugins/frontend/skills/design-review/` | MIT |
| `shadcn-ui` | jezweb/claude-skills `@0aa0f44` | `plugins/frontend/skills/shadcn-ui/` (+ `references/`) | MIT |
| `tailwind-theme-builder` | jezweb/claude-skills `@0aa0f44` | `plugins/frontend/skills/tailwind-theme-builder/` (+ `assets/`, `references/`) | MIT |

## Notas

- **No editar estas skills localmente** — son copias upstream. El conocimiento específico del proyecto
  (contrato de API, deck.gl, paleta de riesgo) vive en el agent `frontend-builder` y en `CLAUDE.md`, no aquí.
- **Para actualizar**: re-descargar el `SKILL.md` (y `assets/`/`references/`) desde la rama `HEAD` de cada repo.
- Otras skills de terceros ya presentes en el repo desde antes: `vercel-react-best-practices`, `supabase`,
  `supabase-postgres-best-practices`, `tdd`, `diagnose`, `to-prd`, `github-actions-docs`, etc.
