Verifica el estado de todos los datasets del proyecto "IA para Seguridad Ciudadana en Bogotá".

Ejecuta este chequeo y muestra el resultado como una tabla de estado:

```python
import os
import pandas as pd

datasets = {
    "SIEDCO (crímenes)": "data/raw/siedco_raw.csv",
    "Shapefiles UPZ": "data/raw/shapefiles/UPZ_Bogota.shp",
    "Shapefiles Localidades": "data/raw/shapefiles/Localidades_Bogota.shp",
    "Clima histórico": "data/raw/clima_bogota.json",
    "TransMilenio estaciones": "data/raw/transmilenio_estaciones.csv",
    "Estratificación": "data/raw/estratificacion.csv",
    "DANE por UPZ": "data/raw/dane_upz.csv",
    "Features procesadas": "data/processed/features.parquet",
    "Modelo entrenado": "models/modelo_xgboost.joblib",
    "Métricas": "models/metrics.json",
}

for nombre, ruta in datasets.items():
    if os.path.exists(ruta):
        size = os.path.getsize(ruta) / 1024  # KB
        # Para CSVs, contar filas
        if ruta.endswith('.csv'):
            try:
                n = sum(1 for _ in open(ruta)) - 1
                print(f"✅ {nombre}: {n:,} filas ({size:.0f} KB)")
            except:
                print(f"✅ {nombre}: {size:.0f} KB")
        else:
            print(f"✅ {nombre}: {size:.0f} KB")
    else:
        print(f"❌ {nombre}: NO ENCONTRADO — {ruta}")
```

Después de mostrar el estado:
- Si falta SIEDCO: sugerir ejecutar `/etl` inmediatamente
- Si faltan features: sugerir ejecutar el Notebook 03
- Si falta el modelo: sugerir ejecutar `/modelo`
- Mostrar la semana actual del cronograma y qué debería estar listo para esta semana
