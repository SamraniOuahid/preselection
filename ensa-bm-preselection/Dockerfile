# ──────────────────────────────────────────────────────────────────────
# Dockerfile — Backend Django (Gunicorn + Daphne ASGI)
# ──────────────────────────────────────────────────────────────────────
FROM python:3.12-slim AS backend

# Prevent Python from buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# System dependencies (Tesseract OCR, Poppler for pdf2image, PostgreSQL client)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    tesseract-ocr \
    tesseract-ocr-fra \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (Docker layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy project source code
COPY . .

# Create directories for static files, media, and logs
RUN mkdir -p /app/staticfiles /app/media /app/logs

# Collect static files (uses dummy SECRET_KEY if not set)
RUN SECRET_KEY=build-placeholder \
    DEBUG=False \
    ALLOWED_HOSTS=localhost \
    python manage.py collectstatic --noinput 2>/dev/null || true

# Expose port
EXPOSE 8000

CMD ["gunicorn", "config.asgi:application", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-"]
