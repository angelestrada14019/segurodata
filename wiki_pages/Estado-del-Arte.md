# ESTADO_DEL_ARTE.md — Sistemas de Predicción de Crimen: Revisión Global

> Documento de referencia para el Notebook 01 (Business Understanding) y la sustentación oral.
> Cubre 20+ sistemas en 15+ países, 5 sistemas colombianos, 18 papers clave, y la diferenciación explícita de este proyecto vs todos los sistemas revisados.

---

## 1. Sistemas internacionales de predicción de crimen

### América del Norte

| Sistema | País | Tipo | Resultado verificado | Estado |
|---------|------|------|---------------------|--------|
| **PredPol → Geolitica** | EE.UU. | Hawkes process espacial (SEPP) | < 0.5% precisión en 23K predicciones auditadas (The Markup, 2023). LAPD lo discontinuó en 2022. Discriminación racial documentada: 2x más patrullaje en barrios de mayoría negra. | ❌ Discontinuado / desacreditado |
| **ShotSpotter** | EE.UU. | Detección de disparos — sensores IoT + ML | 89% de alertas no derivaron en arresto ni evidencia (Chicago OIG, 2021). Costo: ~$10M/año por ciudad. Análisis de RAND Corp: sin impacto en homicidios. | ⚠️ Controversia activa — varios contratos cancelados |
| **Palantir Predictive Policing** | EE.UU. | Graph analytics + ML sobre registros policiales | Usado por LAPD, New Orleans (cancelado 2021), otras. Sin transparencia sobre funcionamiento. Documentado uso para rastreo de manifestantes BLM. | ⚠️ Uso limitado, sin publicación de resultados |
| **Chicago Strategic Subject List ("heat list")** | EE.UU. | ML — lista de individuos en riesgo | 400+ individuos en la lista fueron víctimas de violencia pero la lista no redujo crimen. ACLU demandó por violación de privacidad. Cancelado 2020. | ❌ Cancelado |

### Europa

| Sistema | País | Tipo | Resultado verificado | Estado |
|---------|------|------|---------------------|--------|
| **National Data Analytics Solution (NDAS)** | Reino Unido | ML multi-variable (predice reincidencia individual) | Suspendido por ICO (regulador de datos UK) en 2020 por violaciones de privacidad y falta de base legal. Nunca desplegado en producción. | ❌ Suspendido |
| **Precobs** | Alemania / Suiza / Austria | Software de predictive policing sobre datos históricos | **⚠️ HITO ÉTICO CRÍTICO:** El Tribunal Constitucional Federal de Alemania declaró el predictive policing INCONSTITUCIONAL en febrero 2023. Razón: viola el derecho fundamental de los ciudadanos al perfilarlos algorítmicamente sin causa probable. Esto define el marco ético de TODA Europa. | ❌ Prohibido en Alemania — otros países en revisión |
| **PAS — Predictive Analytics System** | Países Bajos | Riesgo de reincidencia + predicción de delitos futuros | Suspendido por el tribunal de derechos humanos en 2020. Declarado discriminatorio por el Comité de la ONU. | ❌ Suspendido |
| **EU AI Act (vigente 2024-2025)** | Unión Europea | Marco regulatorio | **Prohíbe explícitamente** el risk assessment individual para predicción de crimen (Art. 5 — Prohibited AI Practices). Lo que SÍ permite: predicción de zonas (zone-level) sin perfilamiento individual. **El enfoque UPZ de este proyecto ES COMPATIBLE con el EU AI Act.** | ✅ Marco legal de referencia |
| **BriefCam + video analytics** | Europa (Varios) | Video analytics IA en red CCTV | Usado en varios países europeos (incluida Nueva Zelanda). Reconocimiento facial para perfilamiento. Sin resultados publicados de impacto en crimen. Regulado por el EU AI Act en 2024. | ⚠️ Uso limitado por regulación |

### Asia-Pacífico

| Sistema | País | Tipo | Resultado verificado | Estado |
|---------|------|------|---------------------|--------|
| **Crime Nabi** | Japón → América Latina | ML + datos históricos + clima + socioeconómicos + redes sociales | 50% más efectivo que métodos convencionales (claim del proveedor — Singular Perturbations Inc., sin auditoría independiente). Desplegado en Tokyo pre-Olimpiadas 2020. Expandido a Belo Horizonte (Brasil) en diciembre 2023 — primero de ALC en adoptar el sistema. En 2023 añadió soporte de cámaras de vigilancia. | ✅ Desplegado en producción en 2 países |
| **CMAPS — Crime Mapping Analytics and Predictive System** | India (Delhi Police) | Hotspot mapping automatizado + asignación de patrullas | Primera implementación gubernamental de hotspot mapping automatizado en India. Usa datos Dial 100 (llamadas a emergencias) + FIR/CCTNS (sistema de registros de crimen). Adoptado progresivamente en múltiples estados indios. Paper de evaluación en colaboración con Delhi Police (2026). | ✅ Desplegado — más adoptado en India |
| **Singapore Police Force (SPF) Data Analytics** | Singapur | Data analytics + video analytics IA en red CCTV nacional | SPF Police Intelligence Department usa analytics para detección de patrones de crimen y asignación de recursos. Sin resultados publicados (sistema cerrado). Singapur tiene una de las redes CCTV más densas del mundo (~90K cámaras). | ✅ Operacional (cerrado — sin transparencia) |
| **China: Hikvision, Dahua, SenseTime** | China → exportado a 60+ países | Visión computacional + reconocimiento facial + patrones de comportamiento | Sistema "pre-crimen" basado en anticipación de patrones de conducta. Vendido a países en América Latina, África, y Sudeste Asiático. **No es modelo predictivo ML clásico — es vigilancia masiva con reconocimiento facial.** No replicable en Colombia: viola Ley 1581/2012. | ⚠️ No replicable — vigilancia masiva |
| **ProMap — Australian Institute of Criminology** | Australia | Kernel density + spatial risk scoring | AIC evaluó ProMap en 2023 (Technical Report 666): genera valores de intensidad de riesgo basados en distribución espacial histórica. Preocupación clave del informe: riesgo de over-policing de áreas ya sobre-vigiladas (efecto feedback). | ⚠️ Evaluado — no adoptado masivamente |
| **NZ Police Intelligence Tools** | Nueva Zelanda | ML + análisis de redes + biometría | NZ Police usa herramienta de análisis de redes para mapeo de conexiones entre personas de interés. También usa Cellebrite (extracción de datos de dispositivos móviles) y BriefCam (video analytics + reconocimiento facial). Sin marco legal específico para IA predictiva (2023). | ⚠️ Operacional sin marco regulatorio |

### África

| Sistema | País | Tipo | Resultado verificado | Estado |
|---------|------|------|---------------------|--------|
| **PIVA — Pugnabit Identity Verification Application** | Sudáfrica | Biometría — deep learning (huella, facial, iris) | Verificó identidad de 1,081,688 personas acusadas en 2023/24. Integrado al sistema de justicia criminal de SAPS (South African Police Service). | ✅ Desplegado en producción |
| **MeMeZa** | Sudáfrica | Community policing ML | Desplegado en barrios de bajos ingresos para anticipar puntos de conflicto. Usa datos históricos de incidentes + factores contextuales. Oxford paper sobre reducción de violencia de pandillas en Cape Town. | ✅ Desplegado en producción |

### América Latina

| Sistema | País | Tipo | Resultado verificado | Estado |
|---------|------|------|---------------------|--------|
| **Plataforma IA Seguridad "Unidad IA Seguridad"** | Argentina | ML + reconocimiento facial + monitoreo redes sociales | Anunciada por gobierno Milei (2024): ML sobre históricos de crimen + reconocimiento facial en cámaras + monitoreo de redes sociales. Amplia controversia ("Minority Report real"). Sin resultados publicados ni auditoría independiente. | ⚠️ Controversia activa — sin resultados |
| **Sistema ML crimen organizado** | Ecuador | ML para predicción de crimen organizado | Sistema nuevo desplegado en 2024 para guiar patrullaje en áreas de mayor riesgo de violencia organizada. Ecuador atraviesa crisis de seguridad severa (2023-2024). | ⚠️ En implementación — sin resultados publicados |
| **Crime Nabi — Belo Horizonte** | Brasil | ML + cámaras (versión Crime Nabi con soporte visual) | Primera ciudad latinoamericana en adoptar Crime Nabi con soporte de cámaras (diciembre 2023). Pilotos adicionales en Rio de Janeiro y Fortaleza (solo ML sin cámaras). | ⚠️ Piloto activo — resultados pendientes |
| **BID — Plataforma regional de seguridad ciudadana** | América Latina y Caribe | Evidence-based interventions platform | BID lanzó plataforma con 90 tipos de soluciones y 700+ ejemplos de intervenciones evaluadas. Compromiso de $2.5B en préstamos 2024-2027 para seguridad ciudadana en ALC. El crimen cuesta el **3.4% del PIB regional** (vs 1.9% promedio mundial). | ✅ Referencia para contextualización |

### Académico / Estado del Arte Técnico

| Sistema | Tipo | Resultado | Referencia |
|---------|------|-----------|-----------|
| **ST-GNN / Informer+ST-GCN** | Graph Neural Network + Transformer | F1=71% en 320K registros Chicago 2015-2020. MAE: assault=0.73, theft=1.36. Estado del arte académico 2024-2025. | MDPI Big Data & Cognitive Computing, 2024 |
| **Uncertainty-Aware ST-GNN** | GNN con cuantificación de incertidumbre | Predice intervalos de confianza por zona — crucial para decisiones policiales. | arXiv 2408.04193, 2024 |
| **ConvLSTM** | CNN + LSTM sobre grilla espacial | Supera KDE y Random Forest en múltiples ciudades. Requiere datos en formato grilla. | Multiple papers 2020-2024 |
| **Transfer Learning cross-city** | Deep Learning + domain adaptation | NYC→Chicago (PLOS ONE 2024). Austin+Baltimore→Chicago+Minneapolis (arXiv 2024). Toronto+Vancouver→Halifax (PMC 2021). | Ver Papers clave #9 y #10 |
| **Risk Terrain Modeling (RTM) + OSM** | Regresión espacial + POI OpenStreetMap | F1 superior a KDE en 3 ciudades europeas usando POIs de OSM como features. Valida FUENTE 19 del proyecto. | Springer 2024 |

---

## 2. Sistemas colombianos identificados

| Sistema | Entidades | Datos usados | Resultado | Referencia |
|---------|-----------|-------------|-----------|-----------|
| **Modelo Hawkes Bogotá** (2019) | Secretaría de Seguridad Bogotá + UNAL + Quantil | SIEDCO, NUSE 123, Google Street View | CAP-AUC = 0.8. Financiado por Colciencias (3B COP). Objetivo: optimizar patrullaje, no predecir arrestos. Desplegado operacionalmente en Bogotá. | Riascos & Mateo, NeurIPS LatinX 2019; SIAM News 2019 |
| **Atlas del Crimen** (ganador 2025) | Participante concurso Datos al Ecosistema 2025 | Datos Policía Nacional + variables culturales (bibliotecas, equipamientos) | Análisis descriptivo + chatbot comunitario. Enfoque: departamento de Santander (Gobernación). **Sin modelo predictivo.** | herramientas.datos.gov.co/usos/atlas-del-crimen |
| **Modelo Bucaramanga** (2022) | Investigación académica (FLACSO / Urvio) | Signal graph processing + TF-IDF sobre datos Policía Nacional | Spatial graph semanal = mejor resultado. Primera publicación colombiana comparando modelos ML para crimen urbano en ciudad intermedia. | URVIO Revista Latinoamericana de Estudios de Seguridad, 2022 |
| **Medellín ML** (2022) | UNAL | Datos Policía Nacional 2018-2022 | Clustering neural en 4 grupos departamentales + forecasting. Nivel de análisis: comunas de Medellín. | Repositorio UNAL, 2022 |
| **Barrera et al.** (2023) | Uniandes + UNAL | Crimen con subregistro modelado explícitamente | Primer paper colombiano que modela el sesgo de subregistro de forma explícita. Propone estimador de crimen real a partir de crimen reportado + proxies de victimización. | PMC / NCBI 2023 |
| **D'Angelo et al. — Bucaramanga SEPP** (2022/2024) | SAGE Journals | SIEDCO / datos Policía + red lineal de calles | Hawkes process en red lineal de calles — mejora precisión espacial al seguir la geometría real de las vías. | Journal of the Royal Statistical Society, 2022; SAGE Journals 2024 |

---

## 3. Diferenciación de este proyecto vs todos los sistemas revisados

**Tabla comparativa global — dimensiones clave:**

| Dimensión | PredPol (EE.UU.) ❌ | Crime Nabi (Japón) ✅ | Atlas del Crimen (Col. 2025) | Riascos et al. (Col. 2019) | **Este proyecto** |
|-----------|-------------------|---------------------|------------------------------|---------------------------|-------------------|
| Objetivo | Zonas de riesgo para patrullaje | Rutas de patrullaje optimizadas | Descripción + chatbot comunitario | Predicción de crimen en Bogotá | Predicción + diagnóstico causal + intervención |
| Granularidad | Manzana (~100m) | Zona urbana | Municipal (Santander) | Punto geoespacial (lat/lon) | **UPZ (112 zonas Bogotá)** |
| Tipo de análisis | Predictivo (caja negra) | Predictivo + routing | **Solo descriptivo** | Predictivo | Predictivo + **prescriptivo** |
| Modelo | SEPP Hawkes | ML + imagen + clima + RRSS | Sin modelo publicado | SEPP Hawkes (CAP-AUC=0.8) | **XGBoost + Hawkes + SHAP** |
| Interpretabilidad | ❌ No (caja negra) | ❌ No | ❌ No | ❌ No publicado | **✅ SHAP values por UPZ** |
| Capa prescriptiva | ❌ No | ❌ No | ❌ No | ❌ No | **✅ Diagnóstico causal + entidades responsables** |
| API operacional | Propietaria (SaaS) | SaaS (licencia $) | ❌ No | ❌ No | **✅ FastAPI pública (abierta)** |
| Sesgo documentado | ❌ No (lo hundió) | ⚠️ Sin publicar | ❌ No aplica | ❌ No publicado | **✅ Notebook 05 — análisis estrato** |
| Compatible EU AI Act | ❌ No (perfilamiento individual) | ⚠️ Zona-level pero con cámaras | N/A | ⚠️ Punto geoespacial | **✅ Zone-level, sin perfilamiento individual** |
| Datos abiertos | ❌ No (propietarios) | ❌ No | ✅ Sí (nacional) | ⚠️ Parcial | **✅ 20 fuentes verificadas, 100% abiertas** |
| LLM / Generativa | ❌ No | ❌ No | Chatbot básico | ❌ No | **✅ Reporte operacional en lenguaje natural** |
| Multi-ciudad | ❌ No (licencias por ciudad) | ✅ Sí (SaaS $) | ❌ No | ❌ No | **✅ Arquitectura modular (Medellín, Cali documentados)** |
| Hardware / IoT | ❌ No (PredPol) | ✅ Cámaras desde dic 2023 | ❌ No | ❌ No | Roadmap futuro — fuera de scope v1 |

**Conclusión crítica:** ninguno de los 20+ sistemas internacionales y colombianos revisados combina las 4 capas de este proyecto — predicción (Hawkes+XGBoost) + interpretabilidad causal (SHAP) + prescripción (diagnóstico con entidades responsables) + operacionalización (FastAPI pública + datos 100% abiertos). Esta combinación es genuinamente nueva en el contexto latinoamericano.

---

## 4. Papers clave a citar (Notebook 01 y README)

1. **Mohler et al. (2011)** — "Self-exciting point process modeling of crime" — *Journal of the American Statistical Association* — Paper fundacional de todos los modelos Hawkes para crimen. Base teórica del SEPP.

2. **Riascos & Mateo (2019)** — "Crime prediction using self-exciting point processes" — *NeurIPS LatinX Workshop* / *SIAM News 2019* — Aplicación Bogotá, CAP-AUC=0.8. El benchmark colombiano más sólido. Financiado por Colciencias.

3. **Barrera et al. (2023)** — "Modelling underreported spatio-temporal crime events" — *PMC/NCBI* — Uniandes+UNAL — Primer paper colombiano que modela el sesgo de subregistro explícitamente. Citar en Notebook 05.

4. **D'Angelo et al. (2022/2024)** — "Self-exciting point process modelling of crimes on linear networks" — *Journal of the Royal Statistical Society / SAGE Journals* — Hawkes en red lineal de calles aplicado a Bucaramanga. Mejora de precisión espacial.

5. **Urvio (2022)** — "Prediciendo el crimen en ciudades intermedias: un modelo de machine learning en Bucaramanga" — *FLACSO/URVIO Revista Latinoamericana de Estudios de Seguridad* — Resultado clave: spatial graph semanal supera KDE y RF. Primer paper colombiano de ML urbano comparativo.

6. **ST-GNN Chicago study (2024)** — "Research on crime spatiotemporal prediction integrating Informer and ST-GCN" — *MDPI Big Data & Cognitive Computing* — F1=71% en 320K registros. Estado del arte académico 2024-2025.

7. **Uncertainty-Aware ST-GNN (2024)** — arXiv 2408.04193 — Cuantificación de incertidumbre en predicción de crimen. Importante para comunicar limitaciones al jurado.

8. **PMC study on alcohol establishments (2012)** — "The Association between Density of Alcohol Establishments and Violent Crime" — *PMC* — Justificación cuantitativa de la FUENTE 15 (uso económico manzana) y FUENTE 19 (OSM POI de bares).

9. **Transfer Learning cross-city (2024)** — "Leveraging transfer learning with deep learning for crime prediction" — *PLOS ONE* — NYC+Chicago. Base para extensión del modelo a Medellín/Cali.

10. **Network-Based Transfer Learning (2024)** — arXiv 2406.06645 — 4 ciudades EEUU (Austin+Baltimore→Chicago+Minneapolis). Técnica más avanzada de transfer learning para crimen.

11. **AIC Technical Report 666 (2023)** — "Predictive policing in an Australian context" — *Australian Institute of Criminology* — Evaluación independiente de ProMap. Documenta el riesgo de over-policing (efecto feedback amplificador de sesgo).

12. **Systematic Review (2024)** — "Effectiveness of Big Data and Predictive Policing" — *Taylor & Francis / Policing & Society* — Revisión global de 30+ sistemas en EE.UU., Europa y Asia. Conclusión: impacto en crimen es marginal sin cambios operacionales.

13. **EU AI Act 2024** — "Prohibited AI Practices" (Art. 5) — *Future of Privacy Forum analysis* — Marco legal que prohíbe el perfilamiento individual para predicción de crimen. El enfoque UPZ-level de este proyecto es compatible. Citar en Notebook 01 y Notebook 05.

14. **BID Blog (2024)** — "Combatir el crimen con IA" — *iadb.org* — El crimen cuesta 3.4% del PIB regional en ALC. Inversión $2.5B 2024-2027. Referencia para la apertura de la sustentación oral.

15. **Romero et al. (2025)** — "Artificial Intelligence and Crime in Latin America: A Multilingual Bibliometric Review (2010–2025)" — *MDPI Information 16(11):1001* — 146 papers revisados; Colombia entre los hubs principales de publicación sobre IA y crimen; publicaciones aceleran desde 2018.

16. **Springer 2024** — "Predicting Public Violent Crime Using Register and OpenStreetMap Data: A Risk Terrain Modeling Approach Across Three Cities" — Valida el uso de OSM POI como feature predictora de crimen en 3 ciudades europeas. Justificación directa de FUENTE 19.

17. **ScienceDirect 2025** — "Brighter Nights, safer cities? Exploring spatial link between VIIRS nightlight and urban crime risk" — Correlación negativa estadísticamente significativa entre radiancia nocturna satelital y crimen urbano. Justificación directa de FUENTE 20.

18. **Liu et al. (2023)** — "Big data in crime statistics: Using Google Trends to measure victimization" — *SAGE Journals* — Google Trends como proxy de victimización percibida. Referencia si se decide usar Google Trends como feature adicional.

---

## 5. Extensión multi-ciudad Colombia: Medellín, Cali, Barranquilla

La arquitectura es modular por diseño. Replicar en otra ciudad colombiana requiere sustituir 3 componentes:

| Componente | Bogotá | Medellín | Cali | Barranquilla |
|-----------|--------|---------|------|-------------|
| **Portal datos** | datosabiertos.bogota.gov.co (CKAN) | medata.gov.co (descarga CSV/JSON — no CKAN/Socrata) | datos.cali.gov.co + IDESC ArcGIS | datos.gov.co nacional + Gobernación Atlántico |
| **Dataset crimen** | Delito de Alto Impacto + NUSE 123 | SISC por comunas (MEData, anual, desde 2003) | Observatorio Seguridad Cali (semestral, homicidios+comparendos, ArcGIS) | Datos nacionales Policía filtrados + "Creciendo en la Sombra" |
| **Unidad geográfica** | 112 UPZs | 16 comunas + 5 corregimientos | 22 comunas | 5 localidades (nivel grueso) |
| **Shapefile** | IDECA CKAN ✅ | Portal Metropol / IDECA Medellín ✅ | Geoportal IDESC Cali ✅ | Dato menos maduro ⚠️ |
| **Datos clima** | Open-Meteo (lat 4.6, lon -74.0) | Open-Meteo (lat 6.2, lon -75.5) | Open-Meteo (lat 3.4, lon -76.5) | Open-Meteo (lat 10.9, lon -74.7) |
| **Madurez datos** | ★★★★★ | ★★★★ | ★★★ | ★★ |

**Estrategia de extensión:**
- **Medellín**: Dataset más maduro después de Bogotá gracias al SISC (desde 2003, por comunas). ~2 semanas de ingeniería para adaptar el pipeline.
- **Cali**: Datos disponibles pero fragmentados entre diferentes portales. Requiere trabajo de integración adicional.
- **Barranquilla**: Usar transfer learning (preentrenar en Bogotá, afinar con datos nacionales Policía filtrados por municipio). Granularidad solo a nivel de localidades.

**Advertencia:** No implementar la extensión en el concurso — el jurado no puntúa por número de ciudades sino por profundidad del análisis. Documentar como "escalabilidad planificada" en Notebook 06 y README.

---

## 6. Lecciones aprendidas de sistemas internacionales

**Para Notebook 01 (Business Understanding) y la sustentación oral:**

### 1. No replicar el error de PredPol
El sistema predice zonas de alto riesgo, **no perfila individuos**. Las intervenciones recomendadas son urbanísticas/sociales, no solo policiales masivas. El Tribunal Constitucional alemán (2023) y el EU AI Act (2024-2025) validan que el enfoque de zona (UPZ) es el éticamente correcto.

### 2. El Tribunal Constitucional alemán es el marco ético de referencia
La sentencia de febrero 2023 articula con precisión qué viola derechos fundamentales (individual profiling) y qué no (zone-level prediction + crime prevention). Citar en Notebook 01 y Notebook 05: "el diseño de este proyecto fue pensado con base en los más altos estándares internacionales de derechos".

### 3. El análisis de sesgo es obligatorio y diferenciador
Documentar explícitamente en Notebook 05 que el modelo no discrimina sistemáticamente por estrato socioeconómico. PredPol fue discontinuado por esto (2x más patrullaje en barrios negros). Argentina 2024 ya genera controversia similar. El análisis de bias es diferenciador ético, no solo técnico — y el jurado lo valorará.

### 4. La capa prescriptiva como diferenciador ético y práctico
En lugar de "más policías en zonas pobres" (error sistémico de todos los sistemas que fueron cancelados), el modelo identifica qué tipo de intervención (iluminación, empleo, espacio público) reduce el riesgo estructuralmente. **Ninguno de los 20+ sistemas internacionales revisados tiene esta capa.** Es el diferenciador genuino.

### 5. El subregistro es una limitación universal
Todos los papers colombianos lo documentan. Barrera et al. (2023) es la referencia local. FUENTE 16 y FUENTE 17 (Medicina Legal) son las fuentes de datos para cuantificarlo. El ratio NUSE_123/delitos_formales_por_UPZ (FUENTE 1) es el segundo proxy.

### 6. El contexto latinoamericano es el argumento de urgencia
El crimen cuesta **3.4% del PIB regional** en ALC (BID 2023), vs 1.9% mundial. Tasa de homicidios: 18 por 100K en ALC vs 5.6 mundial (UNODC). Bogotá concentra una fracción desproporcionada de los delitos de Colombia. Este contexto justifica la urgencia en los primeros 60 segundos de la sustentación.

### 7. La combinación de las 4 capas es genuinamente nueva
Revisados 20+ sistemas en 15+ países y 5 sistemas colombianos: **ninguno** combina Hawkes (auto-excitación temporal) + SHAP (interpretabilidad causal) + prescripción (diagnóstico causal con mapeo a entidades responsables) + operacionalización (FastAPI pública + datos 100% abiertos). Esto es genuinamente nuevo en el estado del arte global del predictive policing con datos abiertos.

---

## 7. Preguntas difíciles del jurado — respuestas con sustento de estado del arte

**"¿Su modelo discrimina por estrato?"**
→ Sí lo analizamos explícitamente en Notebook 05. Usamos SHAP values para verificar que el peso del estrato en las predicciones es proporcional a su correlación real con el crimen, y no produce predicciones sistemáticamente más altas para zonas de estrato bajo. PredPol en EE.UU. fue discontinuado por este problema — nosotros lo prevenimos por diseño.

**"¿Qué pasa con el subregistro?"**
→ Lo mitigamos de dos formas. Primero, cruzamos el Delito de Alto Impacto (SIEDCO) con NUSE 123 (FUENTE 1) para calcular el ratio llamadas/denuncias_formales por UPZ — ese ratio mismo es un proxy del nivel de subregistro por zona. Segundo, incorporamos datos de Medicina Legal (FUENTE 16 y 17) para capturar lesiones que llegan a urgencias pero no siempre a la policía. Barrera et al. (2023) de Uniandes es la referencia metodológica.

**"¿Cómo escala esto a otra ciudad?"**
→ La arquitectura es modular. Para Medellín: sustituir el dataset Socrata/CKAN por SISC via MEData, reemplazar los shapefiles de UPZ por los de comunas, y reentrenar el modelo. ~2 semanas de ingeniería. Para Barranquilla se puede usar transfer learning preentrenando en Bogotá (paper: PLOS ONE 2024, arXiv 2406.06645). Documentado en Notebook 06.

**"¿Cómo previenen el crimen, no solo lo predicen?"**
→ La capa prescriptiva diagnostica la causa raíz del riesgo — si es temporal (evento próximo), estructural (desempleo, hacinamiento) o urbanística (iluminación, espacio público) — y mapea cada diagnóstico a la entidad distrital responsable de la intervención. No es "más policías en zonas pobres" (el error de PredPol). Es identificar qué tipo de intervención específica necesita cada zona y quién debe ejecutarla. Ninguno de los sistemas internacionales revisados tiene esta capa.

**"¿Qué diferencia esto del Atlas del Crimen que ganó en 2025?"**
→ El Atlas del Crimen es análisis descriptivo — explica qué ha pasado históricamente. Este sistema es predictivo y prescriptivo — predice qué va a pasar y recomienda qué hacer. Adicionalmente, el Atlas operó a nivel departamental (Santander) sin modelo ML. Este proyecto opera a nivel UPZ en Bogotá con XGBoost + Proceso de Hawkes + SHAP + FastAPI operacional.
