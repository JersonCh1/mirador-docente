# Mirador Docente — imagen única (un solo servicio Railway).
# Etapa 1: build del frontend. Etapa 2: runtime backend (FastAPI + ffmpeg)
# que también sirve el dist del frontend desde frontend/dist.

# ---------- Etapa 1: build del frontend ---------- #
FROM node:20-slim AS frontend
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
# Producción: el cliente usa el API same-origin (/api), nunca modo mock.
ENV VITE_API_BASE=""
RUN npm run build

# ---------- Etapa 2: runtime backend ---------- #
FROM python:3.11-slim
# ffmpeg para extraer audio en el pipeline (punto que suele romper el deploy).
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/backend
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./

# main.py busca el dist en <repo_root>/frontend/dist, es decir /app/frontend/dist
COPY --from=frontend /build/dist /app/frontend/dist

# Railway inyecta $PORT; default 8000 en local.
ENV PORT=8000
EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
