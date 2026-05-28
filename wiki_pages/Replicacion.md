# Cómo Replicar SeguroData en Otra Ciudad

SeguroData está diseñado para ser replicable en cualquier ciudad colombiana con datos abiertos disponibles.

## Lo que cambia (3 pasos)

### Paso 1 — Cambiar el shapefile de UPZ
```python
# En src/pipeline.py, cambiar:
URL_F2_UPZ = "https://serviciosgis.catastrobogota.gov.co/..."  # Bogotá
# Por el equivalente de la ciudad destino, por ejemplo Medellín:
URL_F2_UPZ = "https://geomedellin.gov.co/..."  # Barrios de Medellín
```

### Paso 2 — Cambiar los IDs de datasets
```python
# En src/pipeline.py, cambiar los Resource IDs de CKAN/Socrata:
# F1 (delitos): buscar dataset equivalente en datosabiertos de la ciudad
# F5 (incidentes NUSE/123): buscar dataset de llamadas al 123
# F4 (cuadrantes): shapefile de cuadrantes policiales
```

### Paso 3 — Ajustar coordenadas de Open-Meteo
```python
# En src/pipeline.py, cambiar:
LAT_BOGOTA, LON_BOGOTA = 4.711, -74.072  # Bogotá
# Por las coordenadas de la ciudad destino:
LAT_MEDELLIN, LON_MEDELLIN = 6.244, -75.574  # Medellín
```

## Lo que NO cambia

- La arquitectura Medallion completa (Bronze → Silver → Gold → Model)
- El modelo XGBoost y su estructura de 14 variables
- El pipeline de GraphRAG (apuntar F9/F10 a fuentes locales)
- El dashboard Streamlit y los 4 módulos
- Los notebooks CRISP-ML

## Ciudades con datos abiertos en Colombia

| Ciudad | Portal | Equivalente F5 (incidentes) | Equivalente F1 (delitos) |
|--------|--------|---------------------------|--------------------------|
| Medellín | datosabiertos.medellin.gov.co | Centro de Comando Medellín | Secretaría de Seguridad Medellín |
| Cali | datos.cali.gov.co | Línea 123 Cali | Secretaría de Seguridad y Justicia |
| Barranquilla | datosabiertos.barranquilla.gov.co | Verificar disponibilidad | Secretaría del Interior |
| Nacional | datos.gov.co (Socrata) | — | Policía Nacional (granularidad municipio) |

## Limitaciones de replicación

- La granularidad UPZ es única de Bogotá. En otras ciudades, usar la división administrativa equivalente (comunas en Medellín, corregimientos en Cali)
- La calidad del modelo depende de que exista un dataset de incidentes/llamadas de emergencia con granularidad subnivel ciudad
- El corpus SCJ (F9) es específico de Bogotá — para otras ciudades, usar los boletines de la Secretaría de Seguridad local
