# Arquitectura del Sistema

## Medallion Architecture

SeguroData sigue la arquitectura Medallion (Bronze → Silver → Gold → Model):

```
Bronze  datos/raw/          src/pipeline.py   ← 10 fuentes, descarga incremental
Silver  datos/procesados/   src/transform.py  ← tabla silver_upz_mes.parquet (111,606 × 20)
Gold    datos/features/     Notebook 03       ← 14 variables + tabla maestra
Model   datos/modelos/      Notebook 04       ← XGBoost + SHAP values
```

## La tabla Silver

La tabla Silver tiene una fila por cada combinación **UPZ × mes × tipo de incidente** (86 tipos):

- **Genera filas**: F5 NUSE (128,314 registros raw → 111,606 filas silver)
- **Agrega columnas**: F3 (clima), F4 (cuadrantes), F7 (estrato), F8 (TransMilenio)
- **No entra al JOIN**: F1 (solo localidad), F6 (solo municipio)
- **Base geométrica**: F2 UPZ (spatial join)

**Resultado: 111,606 filas × 20 columnas, 120 UPZs, 86 tipos NUSE, 19 localidades**

## GraphRAG (Fase 3)

Los datos no estructurados (F9 PDFs + F10 RSS + F12 Plan Desarrollo) se integran como un **Knowledge Graph** usando `nano-graphrag`:

```
F9 PDF → pdfplumber → graph.insert(texto)   ← boletines SCJ
F10 RSS → feedparser → graph.insert(texto)  ← noticias seguridad
F12 PDF → pdfplumber → graph.insert(texto)  ← Plan Desarrollo
           ↓
    datos/grafo/ (nano-graphrag, networkx)
           ↓
    graph.query("¿causas del riesgo en UPZ 44?")
           ↓
    Claude API → respuesta operacional al comandante de CAI
```

**Ventaja del GraphRAG sobre corpus plano**: Claude recibe un subgrafo contextualizado con relaciones explícitas (UPZ → OBRA_ACTIVA → HURTO_ALTA → BOLETIN_MENCIONA), no solo chunks de texto desconectados.

## Diagrama SVG

Ver el diagrama completo de fuentes en: [docs/diagrama_arquitectura.svg](https://github.com/angelestrada14019/segurodata/blob/main/docs/diagrama_arquitectura.svg)
