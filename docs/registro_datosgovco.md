# Texto para el registro en datos.gov.co — sección "Usos"

> Borrador listo para pegar en el formulario de "Registrar un uso" de datos.gov.co. Ajustar solo si algún campo del formulario real no coincide exactamente con esta estructura.

---

## Título del uso

```
SeguroData Bogotá — Predicción y prescripción de crimen con IA para Bogotá D.C.
```

## Descripción corta (si el formulario pide un resumen separado)

```
Sistema que combina 12 fuentes de datos abiertos de Bogotá con un modelo XGBoost
para predecir el nivel de riesgo delictivo por UPZ y recomendar, de forma
automática, la intervención y la entidad institucional responsable de
ejecutarla — no solo predice dónde puede haber delitos, también dice qué
hacer y a quién avisar.
```

## Descripción completa

```
SeguroData Bogotá es un sistema de analítica predictiva y prescriptiva
desarrollado para el reto "Seguridad Ciudadana y Justicia" del concurso
Datos al Ecosistema 2026 (MinTIC). Integra 12 fuentes de datos abiertos de
Bogotá D.C. — delito de alto impacto, incidentes NUSE 123, cuadrantes de
Policía, estratificación socioeconómica, estaciones de TransMilenio, malla
vial, cámaras Salvavidas y alumbrado público, entre otras — con un modelo
XGBoost entrenado sobre el histórico 2018-2026 para predecir el nivel de
riesgo delictivo (crítico/alto/medio/bajo) de cada una de las 112 UPZs de
la ciudad para el mes siguiente.

A diferencia de un dashboard descriptivo, el sistema añade dos capas que no
existen en las herramientas actuales: (1) una capa predictiva explicable,
con SHAP values que muestran qué variables empujan el riesgo de cada zona,
validada con separación temporal estricta (nunca aleatoria) y con análisis
de sesgo por estrato socioeconómico incluido desde el diseño; y (2) una
capa prescriptiva que traduce ese diagnóstico en una recomendación
operacional en lenguaje humano y la conecta directamente con el cuadrante
de Policía responsable de esa zona — cerrando el vacío que hoy existe entre
el dato abierto publicado por el Distrito y la decisión operativa de un
comandante de CAI.

El sistema está desplegado en producción (frontend en Vercel, backend en
Railway, base de datos en Supabase/PostgreSQL+PostGIS) y es de código
abierto. Incluye además un chatbot causal que responde preguntas
ciudadanas citando noticias reales indexadas por similitud semántica, sin
inventar fuentes.

Arquitectura modular pensada para replicarse en otras ciudades colombianas
sustituyendo las fuentes locales equivalentes.
```

## Entidad o persona que desarrolla el uso

```
[Completar con el nombre/equipo registrado en el concurso Datos al Ecosistema 2026]
```

## Sector / categoría

```
Seguridad y Defensa · Ciencia, Tecnología e Innovación
```

## Tipo de uso

```
Aplicación web / Modelo predictivo con inteligencia artificial
```

## URL del proyecto

```
Aplicación en producción: https://segurodata-frontend.vercel.app
Repositorio de código (público):  https://github.com/angelestrada14019/segurodata
```

## Conjuntos de datos utilizados (buscar y enlazar cada uno en la plataforma)

Priorizar estos — ya están catalogados en datos.gov.co (ver `wiki_pages/Fuentes-de-Datos.md` para el detalle completo de las 12 fuentes, incluidas las que no están en este portal):

```
- Delito de Alto Impacto (Secretaría de Seguridad, Convivencia y Justicia)
- Incidentes NUSE 123 — C4
- Cuadrantes de Policía — MEBOG
- Hurto a Personas — Policía Nacional
- Estratificación socioeconómica por manzana — SDP
- Malla Vial y Obras IDU activas
- Alumbrado Público — UAESP
```

Si el formulario permite texto libre además de la búsqueda, agregar esta nota:

```
El sistema también integra datos geoespaciales abiertos que no están
catalogados en datos.gov.co (UPZ — IDECA/Catastro, estaciones TransMilenio,
cámaras Salvavidas SDM vía ArcGIS Hub, clima vía Open-Meteo) — el detalle
completo de las 12 fuentes y su rol en el modelo está documentado en el
repositorio público del proyecto.
```

## Beneficio / impacto generado

```
Convierte datos abiertos dispersos en una recomendación operativa concreta
para la Policía Nacional y la Secretaría de Seguridad: en vez de un mapa
descriptivo de "qué pasó", el sistema dice qué UPZ necesita atención el
próximo mes, por qué (variables SHAP explicables), y a qué cuadrante y
comandante específico corresponde actuar. Reduce la brecha entre la
publicación de datos abiertos por el Distrito y su uso operativo real por
las entidades responsables de la seguridad ciudadana.
```

---

## Antes de enviar el formulario real

- [ ] Confirmar que cada dataset enlazado abre correctamente en datos.gov.co (algunos IDs pueden haber cambiado desde la verificación original — ver `wiki_pages/Provenance.md`)
- [ ] Completar el campo de entidad/persona con el nombre exacto usado en la inscripción del concurso
- [ ] Verificar si el formulario pide capturas de pantalla o un video adjunto — si es así, usar el video pitch de `docs/sustentacion/` una vez grabado
