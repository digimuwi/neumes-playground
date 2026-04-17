FROM python:3.11-slim AS builder

# Build dependencies for kraken / Pillow / shapely
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first (layer cache)
COPY pyproject.toml ./
RUN pip install --no-cache-dir . \
    && pip install --no-cache-dir gunicorn

# ---- runtime stage ----
FROM python:3.11-slim

# git is needed at runtime for git-backed storage
RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application source
COPY src/ src/

# Copy static data files
COPY patterns/ patterns/
COPY neume_classes.yaml .

# Models: baked in by default (~35 MB active).
# To use a volume mount instead, omit the models/ dir and mount at /app/models.
COPY models/neume_detector.pt models/neume_detector.pt
COPY models/seg_model.mlmodel models/seg_model.mlmodel
COPY models/Tridis_Medieval_EarlyModern.mlmodel models/Tridis_Medieval_EarlyModern.mlmodel

# Contributions directory — mount as a volume for persistence
RUN mkdir -p contributions
VOLUME /app/contributions

EXPOSE 8000

# Use gunicorn with uvicorn workers for production
CMD ["gunicorn", "htr_service.api:app", \
     "-k", "uvicorn.workers.UvicornWorker", \
     "-b", "0.0.0.0:8000", \
     "--workers", "2", \
     "--timeout", "300"]
