# ESTADO_DEL_ARTE.md — Sistemas de Predicción de Crimen: Revisión Global

> Revisión de literatura y estado del arte en predicción de crimen con datos abiertos.
> Cubre 20+ sistemas en 15+ países, 6 sistemas colombianos, 18 papers clave, y la diferenciación explícita de este proyecto vs todos los sistemas revisados.

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
| Modelo | SEPP Hawkes | ML + imagen + clima + RRSS | Sin modelo publicado | SEPP Hawkes (CAP-AUC=0.8) | **XGBoost + SHAP + ruptures (cambios estructurales)** |
| Interpretabilidad | ❌ No (caja negra) | ❌ No | ❌ No | ❌ No publicado | **✅ SHAP values por UPZ (pre-computados)** |
| Capa prescriptiva | ❌ No | ❌ No | ❌ No | ❌ No | **✅ Tabla ontológica + diagnóstico causal + entidades responsables** |
| API operacional | Propietaria (SaaS) | SaaS (licencia $) | ❌ No | ❌ No | **✅ API REST pública (FastAPI + Railway)** |
| Sesgo documentado | ❌ No (lo hundió) | ⚠️ Sin publicar | ❌ No aplica | ❌ No publicado | **✅ `scripts/train_model.py` — análisis estrato** |
| Compatible EU AI Act | ❌ No (perfilamiento individual) | ⚠️ Zona-level pero con cámaras | N/A | ⚠️ Punto geoespacial | **✅ Zone-level, sin perfilamiento individual** |
| Datos abiertos | ❌ No (propietarios) | ❌ No | ✅ Sí (nacional) | ⚠️ Parcial | **✅ 12 fuentes verificadas, 100% abiertas** |
| LLM / Generativa | ❌ No | ❌ No | Chatbot básico | ❌ No | **✅ Reporte operacional en lenguaje natural** |
| Multi-ciudad | ❌ No (licencias por ciudad) | ✅ Sí (SaaS $) | ❌ No | ❌ No | **✅ Arquitectura modular (Medellín, Cali documentados)** |
| Hardware / IoT | ❌ No (PredPol) | ✅ Cámaras desde dic 2023 | ❌ No | ❌ No | Roadmap futuro — fuera de scope v1 |

**Conclusión crítica:** ninguno de los 20+ sistemas internacionales y colombianos revisados combina las 4 capas de este proyecto — predicción (XGBoost + detección de cambios estructurales con ruptures) + interpretabilidad causal (SHAP) + prescripción real (tabla ontológica SHAP→entidad→acción + GraphRAG causal) + operacionalización (API REST pública + datos 100% abiertos + 12 fuentes). Esta combinación es genuinamente nueva en el contexto latinoamericano.

---

## 4. Papers clave a citar (este documento y README)

1. **Mohler et al. (2011)** — "Self-exciting point process modeling of crime" — *Journal of the American Statistical Association* — Paper fundacional de todos los modelos Hawkes para crimen. Base teórica del SEPP.

2. **Riascos & Mateo (2019)** — "Crime prediction using self-exciting point processes" — *NeurIPS LatinX Workshop* / *SIAM News 2019* — Aplicación Bogotá, CAP-AUC=0.8. El benchmark colombiano más sólido. Financiado por Colciencias.

3. **Barrera et al. (2023)** — "Modelling underreported spatio-temporal crime events" — *PMC/NCBI* — Uniandes+UNAL — Primer paper colombiano que modela el sesgo de subregistro explícitamente.

4. **D'Angelo et al. (2022/2024)** — "Self-exciting point process modelling of crimes on linear networks" — *Journal of the Royal Statistical Society / SAGE Journals* — Hawkes en red lineal de calles aplicado a Bucaramanga. Mejora de precisión espacial.

5. **Urvio (2022)** — "Prediciendo el crimen en ciudades intermedias: un modelo de machine learning en Bucaramanga" — *FLACSO/URVIO Revista Latinoamericana de Estudios de Seguridad* — Resultado clave: spatial graph semanal supera KDE y RF. Primer paper colombiano de ML urbano comparativo.

6. **ST-GNN Chicago study (2024)** — "Research on crime spatiotemporal prediction integrating Informer and ST-GCN" — *MDPI Big Data & Cognitive Computing* — F1=71% en 320K registros. Estado del arte académico 2024-2025.

7. **Uncertainty-Aware ST-GNN (2024)** — arXiv 2408.04193 — Cuantificación de incertidumbre en predicción de crimen, referencia metodológica para documentar los límites del modelo.

8. **PMC study on alcohol establishments (2012)** — "The Association between Density of Alcohol Establishments and Violent Crime" — *PMC* — Justificación cuantitativa de la FUENTE 15 (uso económico manzana) y FUENTE 19 (OSM POI de bares).

9. **Transfer Learning cross-city (2024)** — "Leveraging transfer learning with deep learning for crime prediction" — *PLOS ONE* — NYC+Chicago. Base para extensión del modelo a Medellín/Cali.

10. **Network-Based Transfer Learning (2024)** — arXiv 2406.06645 — 4 ciudades EEUU (Austin+Baltimore→Chicago+Minneapolis). Técnica más avanzada de transfer learning para crimen.

11. **AIC Technical Report 666 (2023)** — "Predictive policing in an Australian context" — *Australian Institute of Criminology* — Evaluación independiente de ProMap. Documenta el riesgo de over-policing (efecto feedback amplificador de sesgo).

12. **Systematic Review (2024)** — "Effectiveness of Big Data and Predictive Policing" — *Taylor & Francis / Policing & Society* — Revisión global de 30+ sistemas en EE.UU., Europa y Asia. Conclusión: impacto en crimen es marginal sin cambios operacionales.

13. **EU AI Act 2024** — "Prohibited AI Practices" (Art. 5) — *Future of Privacy Forum analysis* — Marco legal que prohíbe el perfilamiento individual para predicción de crimen. El enfoque UPZ-level de este proyecto es compatible.

14. **BID Blog (2024)** — "Combatir el crimen con IA" — *iadb.org* — El crimen cuesta 3.4% del PIB regional en ALC. Inversión $2.5B 2024-2027. Contexto regional que justifica la urgencia del problema.

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