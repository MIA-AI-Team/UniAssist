# UniAssist Backend — FastAPI + Postgres
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app:/ai-service

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Backend package + migrations
COPY backend/backend /app/backend
COPY backend/migrations /app/migrations
COPY backend/alembic.ini /app/alembic.ini

# AI package (in-process import: from ai_tutor import AIService)
COPY AI-Service/ai_tutor /ai-service/ai_tutor

RUN mkdir -p /app/uploads

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
