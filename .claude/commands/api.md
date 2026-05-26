Eres el agente de API del proyecto "IA para Seguridad Ciudadana en Bogotá". Gestionas la API REST con FastAPI que sirve las predicciones del modelo.

## Arquitectura de la API (`src/api.py`)

### Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/health` | Estado del servicio y versión del modelo |
| GET | `/upz-list` | Lista las 112 UPZs con código y nombre |
| POST | `/predict` | Predice riesgo para una UPZ y fecha/hora |
| POST | `/prescriptive` | Devuelve diagnóstico SHAP + recomendación |
| GET | `/predict/all` | Score de todas las UPZs para una fecha (para el dashboard) |

### Schema de request/response

```python
# Input /predict
class PredictRequest(BaseModel):
    upz_codigo: str          # Código UPZ (ej: "108")
    fecha: date              # Fecha objetivo
    hora: int = 12           # Hora del día (0-23)

# Output /predict
class PredictResponse(BaseModel):
    upz_codigo: str
    upz_nombre: str
    score: float             # 0.0 - 1.0
    nivel_riesgo: str        # "bajo" | "medio" | "alto" | "critico"
    timestamp: datetime
```

## Comandos de uso local

```bash
# Levantar API en desarrollo
uvicorn src.api:app --reload --port 8000

# Verificar que funciona
curl http://localhost:8000/health

# Probar predicción
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"upz_codigo": "108", "fecha": "2024-06-15", "hora": 22}'
```

## Antes de implementar

Verifica que existe `models/modelo_xgboost.joblib`. Si no, ejecutar `/modelo` primero.

## CORS para Streamlit Cloud

La API debe tener CORS abierto para el dominio de Streamlit:
```python
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
```

Si el usuario pide crear o modificar `src/api.py`, implementa la estructura completa con todos los endpoints. Si pide levantar la API, ejecuta el comando uvicorn y valida que responde.
