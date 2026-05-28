# Los 4 Módulos del Dashboard

El dashboard Streamlit tiene 4 pestañas, cada una respondiendo una pregunta diferente.

## Módulo 1 — Diagnóstico ("¿Qué está pasando?")

**Usuario:** Secretaría de Seguridad, ciudadano informado  
**Tecnología:** GeoPandas + Folium + Plotly

- Mapa coroplético de Bogotá: riesgo por UPZ, calor de incidentes
- Series temporales: tendencia por localidad y tipo de crimen
- Comparación entre UPZs: ranking de más/menos violentas
- Filtros: mes, año, tipo de crimen, localidad

## Módulo 2 — Predicción ("¿Qué va a pasar?")

**Usuario:** Comandante de CAI, planeación policial  
**Tecnología:** XGBoost + SHAP

- Predicción: nivel de riesgo ALTO/MEDIO/BAJO para la próxima semana por UPZ
- SHAP values: las 3 variables que más explican el riesgo en esa UPZ
- Validación: entrenado en 2022–2024, testeado en 2025 (validación temporal)
- Análisis de sesgo: ¿predice igual para estratos 1 y 6?

## Módulo 3 — Recomendación ("¿Qué hacer?")

**Usuario:** Comandante de CAI  
**Tecnología:** Claude API + SHAP + GraphRAG

Combina la predicción XGBoost con contexto causal para dar una **recomendación operacional**:

> *"UPZ 44 (Kennedy Sur) — RIESGO ALTO la próxima semana. Causa principal: obra IDU en Av. 1° de Mayo (SHAP +0.31) + temperatura > 22°C (SHAP +0.18). CAI Kennedy (Cra 80 con Calle 42) debe reforzar patrullaje a pie en franja 18:00–22:00. Historial SCJ: misma zona registró +23% hurto en feb/2025 durante obra similar."*

El módulo no solo dice "hay riesgo" — dice **quién debe actuar, cuándo y por qué**.

## Módulo 4 — Chatbot Causal ("¿Por qué?")

**Usuario:** Ciudadano, periodista, funcionario distrital  
**Tecnología:** Claude API + GraphRAG (nano-graphrag, networkx)

Permite preguntas en lenguaje natural sobre causas del crimen:
- "¿Por qué aumentó el hurto en Chapinero en 2025?"
- "¿Qué UPZs tienen más subregistro policial?"
- "¿Cómo va Bogotá en las metas de seguridad del Plan de Desarrollo?"

Claude responde usando el grafo de conocimiento construido de boletines SCJ, noticias y el Plan de Desarrollo Bogotá 2024-2027.
