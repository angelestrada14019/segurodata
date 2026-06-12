# SeguroData Bogotá

> Sistema de predicción y prescripción de crimen urbano para Bogotá D.C., construido sobre datos abiertos, XGBoost y OpenRouter.

**Concurso:** Datos al Ecosistema 2026 — MinTIC · Reto #2 Seguridad Ciudadana · Nivel Medio  
**Repositorio:** https://github.com/angelestrada14019/segurodata  
**Estado:** Bronze + Silver + EDA completados — En progreso Fase 2 (Gold + Modelo + Supabase)

---

## Las 4 preguntas que responde

| # | Pregunta | Módulo | Tecnología |
|---|---------|--------|-----------|
| 1 | ¿Qué está pasando? | Diagnóstico | React + deck.gl + Supabase Realtime |
| 2 | ¿Qué va a pasar? | Predicción | XGBoost + SHAP + ruptures |
| 3 | ¿Qué hacer? | Prescriptivo | Tabla ontológica + OpenRouter (Gemini Flash) |
| 4 | ¿Por qué? | Chatbot causal | FastAPI (Railway) + pgvector + OpenRouter |
| 5 | ¿Cómo participo? | Plataforma Ciudadana | Supabase Auth + Realtime + React PWA |

## El diferenciador clave

> *"SeguroData no solo predice dónde habrá delitos — le dice exactamente a qué cuadrante de la Policía tiene que ir y por qué. Ese es el puente que hoy no existe entre los datos abiertos de Bogotá y la acción institucional."*

El **Módulo 3 (Prescriptivo)** combina SHAP values + detección de cambios estructurales (`ruptures`) + tabla ontológica de intervenciones → OpenRouter (Gemini Flash vía `LLM_MODEL`) genera la recomendación en lenguaje operacional para el comandante de CAI. El **Módulo 4 (Chatbot causal)** usa GraphRAG (FastAPI + Supabase pgvector + OpenRouter) para responder preguntas como "¿por qué está subiendo el hurto en Kennedy?" con citas de boletines SCJ, noticias y el Plan de Desarrollo.

## Navegación

- [[Fuentes de Datos]] — 10 fuentes activas + 2 planificadas
- [[Arquitectura]] — Medallion Architecture + GraphRAG + Autenticación
- [[Modulos]] — Los 5 módulos del sistema + matriz de acceso por rol
- [[Plataforma-Ciudadana]] — Roles, mapa interactivo, roadmap y features ciudadanas
- [[Metodologia]] — CRISP-ML, validación temporal, análisis de sesgo
- [[Replicacion]] — Cómo usar SeguroData en otra ciudad
- [[Instalacion]] — Guía paso a paso

### Documentación técnica

- [[Transformacion]] — Capa Silver: esquema 20 cols, comandos, advertencia RAM F7
- [[Estado-del-Arte]] — 20+ sistemas internacionales, 18 papers, diferenciación
- [[Provenance]] — URLs verificadas, licencias, tabla causal, cumplimiento concurso
- [[Investigacion-Fuentes]] — Catálogo 20 fuentes, IDs descartados, snippets ETL
- [[Reglas-Concurso]] — Checklist obligatorios, preguntas del jurado, decisiones de diseño
