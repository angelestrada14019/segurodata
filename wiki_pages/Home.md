# SeguroData Bogotá

> Sistema de predicción y prescripción de crimen urbano para Bogotá D.C., construido sobre datos abiertos, XGBoost y Claude API.

**Concurso:** Datos al Ecosistema 2026 — MinTIC · Reto #2 Seguridad Ciudadana · Nivel Medio  
**Repositorio:** https://github.com/angelestrada14019/segurodata  
**Estado:** Fases 1A y 1B completadas (Bronze + Silver) — En progreso Fase 2 (Gold + Modelo)

---

## Las 4 preguntas que responde

| # | Pregunta | Módulo | Tecnología |
|---|---------|--------|-----------|
| 1 | ¿Qué está pasando? | Diagnóstico | GeoPandas + Folium + Plotly |
| 2 | ¿Qué va a pasar? | Predicción | XGBoost + SHAP |
| 3 | ¿Qué hacer? | Recomendación | Claude API (Anthropic) |
| 4 | ¿Por qué? | Chatbot causal | Claude API + GraphRAG |

## El diferenciador clave

> *"SeguroData no solo predice dónde habrá delitos — le dice exactamente a qué cuadrante de la Policía tiene que ir y por qué. Ese es el puente que hoy no existe entre los datos abiertos de Bogotá y la acción institucional."*

El **Módulo 3 (Recomendación)** usa SHAP para identificar la causa dominante del riesgo (¿es el clima? ¿es la obra del IDU? ¿es el subregistro policial?) y conecta directamente con el CAI responsable. El **Módulo 4 (Chatbot causal)** usa GraphRAG + Claude API para responder preguntas como "¿por qué está subiendo el hurto en Kennedy?" con contexto de boletines SCJ, noticias y el Plan de Desarrollo.

## Navegación

- [[Fuentes de Datos]] — 10 fuentes activas + 2 planificadas
- [[Arquitectura]] — Medallion Architecture + GraphRAG
- [[Modulos]] — Los 4 módulos del dashboard
- [[Metodologia]] — CRISP-ML, validación temporal, análisis de sesgo
- [[Replicacion]] — Cómo usar SeguroData en otra ciudad
- [[Instalacion]] — Guía paso a paso

### Documentación técnica

- [[Transformacion]] — Capa Silver: esquema 20 cols, comandos, advertencia RAM F7
- [[Estado-del-Arte]] — 20+ sistemas internacionales, 18 papers, diferenciación
- [[Provenance]] — URLs verificadas, licencias, tabla causal, cumplimiento concurso
- [[Investigacion-Fuentes]] — Catálogo 20 fuentes, IDs descartados, snippets ETL
- [[Reglas-Concurso]] — Checklist obligatorios, preguntas del jurado, decisiones de diseño
