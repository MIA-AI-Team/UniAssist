# Database setup — Postgres + pgvector

**Image:** `pgvector/pgvector:pg16` (via root `docker-compose.yml`)  
**Driver:** SQLAlchemy async + `asyncpg`

---

## 1. Start Postgres

From the **repo root** (`AI-TUTOR/`):

```bash
docker compose up -d db
```

Defaults:

| Variable | Default |
|----------|---------|
| User | `uniassist` |
| Password | `uniassist` |
| Database | `uniassist` |
| Port | `5432` |

`CREATE EXTENSION vector` runs automatically from `docker/postgres/init/01-pgvector.sql` on first volume init.

---

## 2. Backend `.env`

```bash
cd backend
cp .env.example .env
```

```env
DATABASE_URL=postgresql+asyncpg://uniassist:uniassist@localhost:5432/uniassist
```

Inside Docker Compose, the backend service overrides host to `db` automatically.

---

## 3. Install & migrate

```bash
cd backend
pip install -r requirements.txt

# PYTHONPATH must include backend root and ai-service (for ai_tutor)
# PowerShell:
$env:PYTHONPATH = "$PWD;$PWD\..\ai-service"

alembic upgrade head
```

If you are migrating from an old **MySQL** database: use a **fresh Postgres** volume and run migrations from scratch. Do not reuse MySQL data files.

---

## 4. Run backend locally

```bash
cd backend
$env:PYTHONPATH = "$PWD;$PWD\..\ai-service"
uvicorn backend.main:app --reload --port 8001
```

Health: `http://127.0.0.1:8001/health`

---

## 5. Full stack with Compose

```bash
# from AI-TUTOR/
cp .env.example .env
cp backend/.env.example backend/.env
cp ai-service/.env.example ai-service/.env

docker compose up --build
```

| Service | URL |
|---------|-----|
| AI service | http://localhost:8000 |
| Backend API | http://localhost:8001 |
| Postgres | localhost:5432 |
| Swagger (backend) | http://localhost:8001/docs |

---

## Notes

- Most SQLAlchemy models are portable; only the connection URL/driver changed from MySQL.
- Embeddings currently store text chunks + placeholder `vector_id`. Real `vector` columns can be added later with pgvector.
- Old MySQL-specific Alembic revisions that import `sqlalchemy.dialects.mysql` may need a clean Postgres baseline if `upgrade head` fails — prefer a new empty DB.
