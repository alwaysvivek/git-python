# Stage 1: Build Frontend
FROM node:18-alpine as frontend-builder

WORKDIR /app/ui
COPY src/ui/package*.json ./
RUN npm install
COPY src/ui ./
# Build output will be in /app/ui/dist
RUN npm run build

# Stage 2: Backend Runtime
FROM python:3.9-slim

WORKDIR /app

# Install git and system deps
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Copy backend deps
COPY pyproject.toml .
# No lock file handling for simplicity in this demo, just install dev deps or main deps
# We will just install main deps via pip
RUN pip install "fastapi[standard]" uvicorn

# Copy entire src
COPY src ./src

# Copy frontend build from Stage 1
COPY --from=frontend-builder /app/ui/dist ./src/ui/dist

# Env vars
ENV PYTHONPATH=/app
ENV GIT_DIR=.git
ENV PORT=8000

# Expose port
EXPOSE 8000

# Run
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
