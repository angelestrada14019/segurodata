# Concurso Datos al Ecosistema 2026

> **Concurso:** MinTIC · "Datos al Ecosistema 2026: IA para Colombia"  
> **Reto:** #2 Seguridad Ciudadana y Justicia · Nivel Medio  
> **Competencia:** 349 equipos / 1,096 participantes (al 19 mayo 2026)  
> **Competidor directo identificado:** "Atlas del Crimen" ganó Datos al Ecosistema 2025 — análisis descriptivo sin modelo predictivo ni capa prescriptiva.
>
> **⚠️ ALERTA DE FECHA:** El evento final es **GovCamps 2026 (primera semana de agosto 2026)**. Verificar fecha exacta de registro en datos.gov.co antes de planificar entrega final.

---

## Criterios que evalúa el jurado técnico

| Criterio | Peso | Qué buscan |
|----------|------|-----------|
| Calidad del análisis | Alto | EDA profundo, ingeniería de features justificada, comparación de modelos |
| Uso de datos abiertos | Alto | Variedad de fuentes, correcta atribución, preferencia por datos.gov.co |
| Rigor técnico | Alto | Validación temporal correcta, métricas apropiadas, explicabilidad (SHAP) |
| Propuesta de valor | Alto | ¿Qué problema resuelve? ¿Quién lo usaría? ¿Cómo cambia la decisión operacional? |
| Estrategias de prevención | Medio-Alto | La mayoría de equipos ignora esto — ventaja diferencial |
| Generalización / escalabilidad | Medio | ¿Puede replicarse en otra ciudad? (argumentarlo, no necesariamente construirlo) |
| Presentación oral | Medio | Claridad, seguridad ante preguntas difíciles, 10 minutos + preguntas |

---

## Checklist de entrega

> Verificar fecha exacta en datos.gov.co — final GovCamps confirmado primera semana de agosto 2026

- [ ] Repositorio GitHub público con todos los archivos
- [ ] 6 notebooks `SeguroData_01` a `SeguroData_06` completos y ejecutables
- [ ] README.md con instrucciones de instalación + URL Vercel (frontend) + URL Railway (backend)
- [ ] **Aplicación React + deck.gl** desplegada en Vercel — URL pública, 4 módulos funcionando
- [ ] Mapa con zoom adaptativo (Localidades → UPZs) + modal 5 pestañas por UPZ operativo
- [ ] Módulo 2: proyección temporal +4 semanas visible en panel de predicción con banda de confianza
- [ ] **FastAPI en Railway** desplegado y respondiendo — `/predict`, `/graphrag` y `/prescribe` operativos
- [ ] Supabase Auth configurado — 4 roles operativos (CIUDADANO / COMANDANTE_CAI / ANALISTA_SDSCJ / ADMIN)
- [ ] RLS activa en tablas de predicciones y SHAP — test de aislamiento por cuadrante verificado
- [ ] **Supabase** configurado — Silver table + predicciones + SHAP pre-computados + pgvector cargados
- [ ] Módulo 3 Prescriptivo: tabla ontológica documentada en Notebook 03 + LLM operacional (nombre CAI incluido)
- [ ] SHAP values pre-computados en Notebook 04 + cargados en Supabase
- [ ] Análisis de sesgo por estrato en Notebook 04
- [ ] `ruptures` — change points detectados y guardados en Supabase tabla `change_points`
- [ ] Enlace registrado en datos.gov.co en la sección "Usos" — **OBLIGATORIO para no ser descalificado**
- [ ] Video pitch de 3 minutos grabado y subido
- [ ] Presentación de 10 minutos preparada
- [ ] Auditoría de git history para API keys: `git log --all -p | grep -iE "api.key|token|secret"`
- [ ] Respuestas para preguntas difíciles ensayadas (ver sección abajo)

---

## Preguntas difíciles del jurado — respuestas preparadas

**"¿Su modelo discrimina por estrato?"**
→ Sí lo analizamos explícitamente. El Notebook 04 incluye análisis de sesgo por estrato socioeconómico: comparación de predicciones por estrato (1-6), verificando que los falsos negativos no estén concentrados en estratos bajos, y SHAP interaction plots. PredPol en EE.UU. fue discontinuado por este problema — nosotros lo prevenimos por diseño.

**"¿Qué pasa con el subregistro?"**
→ Lo mitigamos de dos formas: (1) cruzamos el Delito de Alto Impacto (SIEDCO) con NUSE 123 para calcular el ratio llamadas/denuncias formales por UPZ — ese ratio mismo es un proxy del nivel de subregistro por zona. (2) El feature `ratio_nuse_criminal_upz` entra directamente al XGBoost como variable explicativa. Barrera et al. (Uniandes 2023) es la referencia metodológica.

**"¿Cómo escala esto a otra ciudad?"**
→ La arquitectura es modular. Para Medellín: sustituir el dataset CKAN por SISC via MEData, reemplazar los shapefiles UPZ por comunas, reentrenar. ~2 semanas de ingeniería. Para Barranquilla se puede usar transfer learning preentrenado en Bogotá (paper: PLOS ONE 2024). Documentado en [[Replicacion]].

**"¿Cómo previenen el crimen, no solo lo predicen?"**
→ La capa prescriptiva diagnostica la causa raíz — si es temporal, estructural o urbanística — y mapea cada diagnóstico a la entidad distrital responsable: MEBOG para patrullaje, UAESP para iluminación, IDU para obras, SDIS para programas sociales. No es "más policías en zonas pobres" (el error de PredPol). Es identificar qué intervención específica necesita cada zona y quién debe ejecutarla.

**"¿Qué diferencia esto del Atlas del Crimen que ganó en 2025?"**
→ El Atlas del Crimen es análisis descriptivo — explica qué ha pasado históricamente. Este sistema tiene tres capas operacionales: descriptivo (mapa deck.gl en tiempo real), predictivo (XGBoost + SHAP + ruptures para cambios estructurales por UPZ), y prescriptivo real (tabla ontológica SHAP→entidad→acción con nombre del CAI). El Atlas operó a nivel departamental sin modelo ML ni capa prescriptiva. Este proyecto opera a nivel UPZ con API REST pública (FastAPI + Railway, serverless).

**"¿Por qué XGBoost y no una red neuronal más avanzada?"**
→ XGBoost es el estándar de oro para datos tabulares con menos de 200K filas de entrenamiento — supera consistentemente a redes neuronales en este escenario (benchmark de Kaggle Tabular Playground 2021-2024). La verdadera innovación es la capa prescriptiva sobre SHAP, que requiere interpretabilidad local por UPZ — algo que XGBoost con SHAP da de forma nativa y que una red neuronal no daría sin costo adicional.
