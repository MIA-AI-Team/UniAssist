# UniAssist

Monorepo layout:

```text
AI-TUTOR/
├── docker-compose.yml      # db + ai-service + backend
├── docker/postgres/init/   # enables pgvector extension
├── ai-service/             # AI LLM package + demo FastAPI
├── backend/                # UniAssist API + Alembic + Postgres
└── .env.example
```

## Quick start (Docker)

```bash
cp .env.example .env
cp ai-service/.env.example ai-service/.env
cp backend/.env.example backend/.env

docker compose up --build
```

| Service | Port |
|---------|------|
| Postgres (pgvector/pg16) | 5432 |
| AI service | 8000 |
| Backend API | 8001 |

## Docs

- AI: `ai-service/docs/SYSTEM_OVERVIEW.md`, `BACKEND_CONNECTION.md`, `POSTMAN_TESTS.md`
- Backend DB: `backend/docs/DATABASE_INITIATION.md`
