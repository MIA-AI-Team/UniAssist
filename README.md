# UniAssist

A bilingual, human-supervised university task and assessment workspace.

```text
frontend/     Next.js 16 / Node.js 24, English + Arabic RTL
backend/      FastAPI, SQLAlchemy, Alembic, PostgreSQL
AI-Service/   In-process AI package and separate demo API
docker/       PostgreSQL initialization
```

Students submit text/files, staff evaluate against versioned rubrics, and professors explicitly
release grades. Students can use private task-linked AI tutoring in English or Arabic, with saved
conversations and clearly labeled mock replies. Students can share/revoke previewed snapshots with
selected teaching staff; staff can configure lab guidance mode. Staff can also save private versioned
grading guidance and view released-only teaching insights with saved English/Arabic AI suggestions.
Project teams now support student invitations/consent, TA/professor roster approval and individually
graded team-context submissions in English/Arabic. First submission locks the roster. Legacy teams
remain review-blocked; no historical consent is invented. Approved teams can propose public GitHub
repositories, obtain staff approval, sync recent commits and submit private commit-pinned archive
evidence. Attribution is staff-reviewed, never an effort score. Profiles and limited account/operations
administration are implemented. Email remains deferred; see the integration checkpoint.

### Public GitHub evidence

On an approved team page, open **Public GitHub repositories**. A member proposes a public
`https://github.com/owner/repository` link; a TA/professor approves it and can correct commit
attribution. Sync is explicit and reads at most 100 recent default-branch commits per request.
A student selects or enters a full commit SHA, saves its archive, then chooses **Use snapshot in
my submission**. Text may accompany a snapshot; an uploaded file and snapshot cannot be combined.
Evaluation uses the saved bytes, not the current branch. Normal text/file submission remains available.

GitHub access is unauthenticated and public-only: no GitHub token or plugin is needed. Network/rate
limits are shown as failures, not successful syncs. Archives are bounded to 25 MiB compressed,
100 MiB expanded and 1,000 files, and are never executed or extracted to disk. Supported UTF-8
text/code enters bounded evaluation; the saved manifest identifies initial omissions. Submodules
and external large-file objects are not fetched separately. Archives remain in PostgreSQL, including
staged snapshots: include them in backup/capacity planning; automatic retention cleanup is not implemented.

Only `docker-compose.test.yml` enables `GITHUB_FIXTURE_MODE=true` (requires `MOCK_MODE=true`).
It uses deterministic `uniassist-fixtures/demo` and `uniassist-fixtures/replacement` data, visibly
labeled as test evidence. Normal Compose uses real public GitHub even with mock AI. Never use
fixture output as genuine repository evidence. Legacy links require new reviewed proposals; duplicate
historical commits stop migration for manual review without deleting records.

## Docker quick start

Prerequisites: Docker Compose v2 and an available Docker engine.

1. Copy `.env.example` to `.env` if you do not already have one. Preserve existing database credentials.
2. Set POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB, SECRET_KEY and SESSION_SECRET.
   Generate two different persistent secrets; SESSION_SECRET must be at least 32 characters.
3. Keep MOCK_MODE=true for the demo. Mock assessment is labeled in the UI.
4. Run:

```powershell
docker compose up --build -d
docker compose ps
```

Generate a secret locally (run twice and put outputs in the appropriate .env fields):

```powershell
node -e "console.log(require('node:crypto').randomBytes(32).toString('hex'))"
```

Do not overwrite an existing .env or rotate secrets inadvertently. Rotating SESSION_SECRET signs users out.
Optional provider configuration may be placed in `backend/.env` and `AI-Service/.env`.
The backend imports the AI package in-process; its MOCK_MODE setting controls product evaluations.
It also controls tutor responses. Mock tutoring demonstrates the workflow, not real reasoning.
Optional backend settings: TUTOR_TIMEOUT_SECONDS (default 90, maximum 120) and
TUTOR_TURNS_PER_MINUTE (default 10). Put these in backend/.env if changing them in root Compose.

| Service                  | Default local address                       |
| ------------------------ | ------------------------------------------- |
| Frontend                 | http://localhost:3000/en/login or /ar/login |
| Backend / OpenAPI        | http://localhost:8001/docs                  |
| AI demo, not product API | http://localhost:8000                       |
| PostgreSQL               | localhost:5432                              |

The database healthcheck gates the one-shot migration service, which gates backend startup.
The frontend waits for backend health. Migrations upgrade existing schemas without recreating
databases or deleting volumes. Do not use `docker compose down -v` on a database you need.

Runtime variables for frontend: BACKEND_INTERNAL_URL (server-only), APP_URL (browser origin),
SESSION_SECRET, optional BACKEND_TIMEOUT_MS (default 180000), FRONTEND_PORT (Compose mapping).
Changing the frontend port also requires APP_URL to match the browser origin.

The production frontend uses a multi-stage build and a non-root standalone Node runtime.
Arabic fonts are bundled; no external font service is needed.

## Development

### Admin bootstrap and profiles

Open **My profile** to edit your name (and a student's GitHub username). Academic identity remains
read-only to its owner. Admin self-registration is disabled. After Docker startup, an operator can run:

```powershell
docker compose exec backend python -m backend.bootstrap_admin
```

The interactive command prompts for name/email and a hidden, confirmed password of at least 12
characters. It refuses an existing email and never converts or overwrites an account. For local
development, use the configured backend environment and, from backend, run:

```powershell
..\.venv\Scripts\python.exe -m backend.bootstrap_admin
```

Never put real passwords in command arguments or commit them.

Sign in as that admin at `/en/login` or `/ar/login`. The admin workspace supports account search,
version-checked corrections, suspension/reactivation, TA↔professor changes, content-free audit history
and aggregate AI operations. No account deletion, student↔staff conversion, password reset or academic
content access is exposed. Suspension blocks existing JWTs on their next request; reactivation permits
still-valid JWTs again. The last active admin cannot be suspended. Historical snapshots are preserved.

Migration f8a20260919 preserves existing users as active and creates empty audit/AI-operation tables;
no historical activity is fabricated. Review existing admins created under the prior public demo policy
before deployment. Operational counts cover new application AI calls, not billing/internal retries.
No prompts, replies, provider exception bodies or private transcripts are logged in these records.
Include account/audit/operations tables in PostgreSQL backups; automatic retention cleanup is not implemented.

### Development commands

Docker hot reload:

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

The frontend source is bind-mounted; node_modules and .next have separate container volumes.
After dependency changes, rebuild and run npm ci in the development container if its dependency volume is stale.

Local frontend (Node 24):

```powershell
cd frontend
Copy-Item .env.example .env.local
# Set SESSION_SECRET in .env.local; backend URL defaults to http://localhost:8001.
npm.cmd ci
npm.cmd run dev
```

Use npm.cmd/npx.cmd when PowerShell blocks npm.ps1. On Linux/macOS, npm/npx work normally.
The backend can remain in Docker.

Local backend, from repository root after starting PostgreSQL:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt httpx
$env:PYTHONPATH="$PWD\backend;$PWD\AI-Service"
$env:DATABASE_URL="postgresql+asyncpg://USER:PASSWORD@localhost:5432/DATABASE"
$env:SECRET_KEY="your-persistent-backend-secret"
$env:MOCK_MODE="true"
cd backend
..\.venv\Scripts\python.exe -m alembic upgrade head
..\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 0.0.0.0 --port 8001
```

Use URL-safe/encoded database credentials in DATABASE_URL.

## Verification

Frontend checks:

```powershell
cd frontend
npm.cmd run typecheck
npm.cmd run lint
npm.cmd test
npm.cmd run build
```

Real PostgreSQL + mock-AI acceptance stack, isolated from normal data:

```powershell
docker compose -p uniassist-verify -f docker-compose.test.yml up --build -d
.\.venv\Scripts\python.exe -m pytest backend/tests -q
cd frontend
npx.cmd playwright install chromium
npm.cmd run test:e2e
```

Acceptance ports: frontend 13000, backend 18001, PostgreSQL 15432.
If Microsoft Edge is already installed, you can skip the Chromium download and set
`$env:E2E_CHANNEL='msedge'` before running the browser tests.
Tests create uniquely named demo users/tasks. The migration test creates a uniquely named
verification database, upgrades the former head with historical rows, and checks preservation.
Verification volumes/databases remain available for inspection; no automatic destructive cleanup.

Generate API contracts with the main backend on port 8001:

```powershell
cd frontend
npm.cmd run api:types
```

For the acceptance backend, set `$env:API_SCHEMA_URL='http://localhost:18001/openapi.json'` first.

## Demo limitations and operational notes

- Student, TA and professor self-registration is intentional for this local/demo release.
  Institutional role assignment, rate limiting, reviewed admin provisioning, backups and deployment hardening
  must precede a public production release.
- Uploaded files are limited to 25 MiB; student code is parsed, not executed.
- Task deletion removes linked academic/file records; physical upload bytes remain on disk pending
  an explicit retention/cleanup policy.
- Existing missing text, original filenames and AI provenance cannot be recovered by migration.
- Logout clears the frontend session, not already-issued backend JWTs.
- Provider-backed AI is synchronous; configure timeouts and keep staff review mandatory.
- The root .gitignore currently excludes AGENTS.md (an existing local choice); share that file explicitly
  if other agents/developers need it through Git.

## Documentation

- [Product and UX rules](AGENTS.md)
- [Frontend API contract](backend/docs/FRONTEND_API_GUIDE.md)
- [Implementation plan](plan.md)
- [Active backend/UI integration plan and resume checkpoint](backend/docs/BACKEND_UI_INTEGRATION_PLAN.md)
- [Verification results and coverage limits](backend/docs/VERIFICATION.md)
- [AI package overview](AI-Service/docs/SYSTEM_OVERVIEW.md)
