# Guía de Instalación

## Requisitos

- Python 3.10 o superior
- Git
- ~2 GB de espacio en disco (datos Bronze)
- Clave API de Anthropic (solo para Módulos 3 y 4)

## Instalación local

```bash
# 1. Clonar el repositorio
git clone https://github.com/angelestrada14019/segurodata.git
cd segurodata

# 2. Crear entorno virtual
python -m venv .venv

# Linux/Mac:
source .venv/bin/activate

# Windows:
.venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env
# Editar .env:
#   ANTHROPIC_API_KEY=sk-ant-...   (solo para Módulos 3 y 4)
```

## Descarga de datos Bronze

```bash
# Ver qué se descargaría sin ejecutar
python src/pipeline.py --dry-run

# Descargar todas las fuentes (solo lo nuevo)
python src/pipeline.py

# Verificar estado
python src/pipeline.py --status
```

## Generar tabla Silver

```bash
# Transformar Bronze → Silver (requiere que Bronze esté completo)
python src/transform.py

# Verificar resultado
python -c "import polars as pl; df = pl.read_parquet('datos/procesados/silver_upz_mes.parquet'); print(df.shape, df.columns)"
# Esperado: (111606, 20)
```

## Ejecutar en Google Colab

```python
!git clone https://github.com/angelestrada14019/segurodata.git
%cd segurodata
!pip install -r requirements.txt -q
!python src/pipeline.py
!python src/transform.py
```

⚠️ **Advertencia Colab:** El paso `f7` (estratificación, ~115K polígonos) puede agotar la RAM gratuita. Ver `docs/TRANSFORMACION.md` para opciones de optimización.

## Levantar el dashboard

```bash
# Cuando esté implementado (Fase 3):
streamlit run app.py
# Abre automáticamente en http://localhost:8501
```

## Variables de entorno necesarias

| Variable | Requerida para | Cómo obtener |
|----------|--------------|-------------|
| `ANTHROPIC_API_KEY` | Módulos 3 y 4 (Claude API) | console.anthropic.com |
| Ninguna otra | — | Open-Meteo, CKAN, Socrata son públicos |
