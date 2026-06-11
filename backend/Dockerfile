# SeguroData API — imagen para Railway
# Multi-stage: builder instala deps (torch CPU-only), runtime queda slim.
# El modelo de embeddings se HORNEA en la imagen: Railway no descarga nada al arrancar.

FROM python:3.12-slim AS builder

WORKDIR /build
COPY requirements.txt .
# torch CPU-only: el wheel CUDA pesa >5GB y Railway no tiene GPU
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt \
    --extra-index-url https://download.pytorch.org/whl/cpu


FROM python:3.12-slim

# Usuario no-root
RUN useradd --create-home --shell /usr/sbin/nologin segurodata
WORKDIR /app

COPY --from=builder /install /usr/local

# Hornear el modelo all-MiniLM-L6-v2 (384 dims) en la imagen — línea load-bearing:
# sin esto, el primer /graphrag descargaría ~90MB desde HuggingFace en producción.
ENV HF_HOME=/app/.hf_cache
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')" \
    && chown -R segurodata:segurodata /app

COPY --chown=segurodata:segurodata app ./app

USER segurodata
EXPOSE 8000

# 1 worker: el modelo de embeddings no se duplica en RAM (Railway escala vertical)
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1
