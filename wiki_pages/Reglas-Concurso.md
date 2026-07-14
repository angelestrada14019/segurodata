# Concurso Datos al Ecosistema 2026

> **Concurso:** MinTIC · "Datos al Ecosistema 2026: IA para Colombia"  
> **Reto:** #2 Seguridad Ciudadana y Justicia · Nivel Medio  
> **Competencia:** 349 equipos / 1,096 participantes (al 19 mayo 2026)  
> **Competidor directo identificado:** "Atlas del Crimen" ganó Datos al Ecosistema 2025 — análisis descriptivo sin modelo predictivo ni capa prescriptiva.
>
> **Entrega confirmada: 13 de julio de 2026, antes de medianoche** (código en GitHub público + registro en datos.gov.co). **GovCamps 2026 (primera semana de agosto)** es el evento presencial posterior para los equipos finalistas seleccionados — no es la fecha de entrega.

---

## Criterios que evalúa el jurado técnico

| Criterio | Peso | Qué buscan |
|----------|------|-----------|
| Calidad del análisis | Alto | EDA profundo, ingeniería de features justificada, comparación de modelos |
| Uso de datos abiertos | Alto | Variedad de fuentes, correcta atribución, preferencia por datos.gov.co |
| Rigor técnico | Alto | Validación temporal correcta, métricas apropiadas, explicabilidad (SHAP) |
| Propuesta de valor | Alto | ¿Qué problema resuelve? ¿Quién lo usaría? ¿Cómo cambia la decisión operacional? |
| Estrategias de prevención | Medio-Alto | Capa prescriptiva que mapea causa raíz a entidad responsable, no solo predicción |
| Generalización / escalabilidad | Medio | ¿Puede replicarse en otra ciudad? (argumentarlo, no necesariamente construirlo) |
| Presentación oral | Medio | Claridad y verificabilidad en bloque de 15 minutos (10 de pitch + preguntas cortas de precisión) |

---

## Checklist de entrega

- [x] ✅ Repositorio GitHub público con todos los archivos
- [x] ✅ Metodología CRISP-ML documentada en `wiki_pages/` (plan, fuentes, análisis exploratorio, arquitectura) + `scripts/train_model.py` ejecutado y versionado
- [x] ✅ README.md con instrucciones de instalación + URL Vercel (frontend) + URL Railway (backend)
- [x] ✅ **Aplicación React + deck.gl** desplegada en Vercel — URL pública, 4 módulos funcionando
- [x] ✅ Mapa con zoom adaptativo (Localidades → UPZs) + modal 5 pestañas por UPZ operativo
- [x] ✅ Módulo 2: proyección temporal +4 semanas visible en panel de predicción con banda de confianza
- [x] ✅ **FastAPI en Railway** desplegado y respondiendo — `/predict`, `/graphrag` y `/prescribe` operativos
- [x] ✅ Supabase Auth configurado — 4 roles operativos (CIUDADANO / COMANDANTE_CAI / ANALISTA_SDSCJ / ADMIN)
- [x] ✅ RLS activa en tablas de predicciones y SHAP — test de aislamiento por cuadrante verificado
- [x] ✅ **Supabase** configurado — Silver table + predicciones + SHAP pre-computados + pgvector cargados
- [x] ✅ Módulo 3 Prescriptivo: tabla ontológica (`backend/app/data/tabla_ontologica_seed.json`) + LLM operacional (nombre CAI incluido)
- [x] ✅ SHAP values pre-computados (`scripts/train_model.py`) + cargados en Supabase
- [x] ✅ Análisis de sesgo por estrato (`scripts/train_model.py::analisis_sesgo`)
- [x] ✅ `ruptures` — change points detectados y guardados en Supabase tabla `change_points`
- [ ] Enlace registrado en datos.gov.co en la sección "Usos" — **OBLIGATORIO para no ser descalificado**
- [x] ✅ Presentación de sustentación preparada
- [ ] Video pitch grabado
- [x] ✅ Auditoría de git history para API keys — sin hallazgos
