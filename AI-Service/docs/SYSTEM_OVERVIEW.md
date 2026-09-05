# System Overview — AI Evaluation Service

**Package:** `ai_tutor` (`AI-Service/`)  
**Backend entry point:** `from ai_tutor import AIService`  
**Integration details:** [BACKEND_CONNECTION.md](./BACKEND_CONNECTION.md)

---

## 1. How to run pytest

All tests live under `AI-Service/tests/`. Config is in `pytest.ini`:

```ini
[pytest]
testpaths = tests
pythonpath = .
```

### Steps

1. Open a terminal in the **AI-Service** folder (not the parent `AI-TUTOR` folder):

```bash
cd AI-Service
```

2. Install dependencies if needed:

```bash
pip install -r requirements.txt
```

3. Run the suite:

```bash
pytest -v
```

or:

```bash
python -m pytest -v
```

### Useful variants

| Command | What it does |
|---------|----------------|
| `pytest` | Run all tests in `tests/` |
| `pytest -v` | Verbose (one line per test) |
| `pytest tests/test_ai_service.py` | One file |
| `pytest tests/test_ai_service.py::test_ai_service_cohort_analytics_mock` | One test |
| `pytest -k "grade"` | Tests whose names contain `grade` |
| `pytest --tb=short` | Shorter failure traces |

### Notes

- Run from `AI-Service/` so `pythonpath = .` puts the project root on the import path (`app`, `ai_tutor`, shims).
- Tests use **mock mode** where needed — no API keys required for the suite.
- You should see all tests **passed** (currently 41+ including cohort analytics).

---

## 2. What this system is

University **AI compute layer** for labs, assignments, and projects. It generates rubrics, grades submissions (with code review), runs student tutor/lab chat, and produces **class-wide** teaching analytics.

It does **not** own auth, the database, or final grade confirmation — that is the backend’s job.

```text
Backend (auth, DB, files, gradebook)
        │  typed requests
        ▼
AIService  →  engine + prompts + parsers + metrics
        │
        ▼
Groq (primary) / Gemini (fallback) / mock mode
```

---

## 3. Features (current)

### 3.1 Rubric suggestion

- Input: task title, type, description, reference/spec text (from PDF/DOCX/TXT or paste).
- Output: structured criteria (`name`, `description`, `max_points`, `sort_order`), total points, rationale, `warnings`, `ai_metadata`.
- Task-type guidance for lab / assignment / project / experiment / coding / essay.

**API:** `AIService.suggest_rubric(RubricSuggestRequest)`

### 3.2 Rubric refinement

- Staff natural-language feedback overrides the previous rubric (points, structure, subtasks).
- Returns a new suggested criteria set for staff review.

**API:** `AIService.refine_rubric(RubricRefineRequest)`

### 3.3 Submission grading + code review

- Requires task **spec** (`reference_text`) and submission content (`submission_text` and/or `code_files`).
- Optional separate **`grading_key`** (TA model answers — internal only, not student-facing).
- Output: `ai_suggested_grade`, percentage, summary feedback, per-criterion scores + reasoning, code review findings (`info` / `warning` / `critical`), `warnings`, `ai_metadata`.
- Validates/normalizes scores (cap to max, recompute totals, flag missing criteria).
- Context budgeting truncates long specs/code safely and records truncation warnings.

**API:** `AIService.grade_submission(GradeSubmissionRequest)`

### 3.4 File / ZIP parsing helpers

- Extract text from PDF, DOCX, and plain/code files.
- ZIP/directory extraction skips junk paths (`node_modules`, `venv`, `.git`, `__pycache__`, …).
- `prepare_submission_for_grading` standardizes text + code map (also used inside grading).

**API:** `ai_tutor.parsers` (`extract_text_from_file`, `extract_submission_content`, …)

### 3.5 Socratic student tutor chat

- Helps students with task context without dumping full solutions.
- Takes reference text, chat history, and the new student message.
- **Continue later:** backend loads `CHAT_MESSAGES` for a session and passes them as `persisted_messages` or `chat_history`.
- **Scoped context:** pass `session` (`session_id`, `task_id`, `submission_id`) so the turn stays tied to the right task/submission; ids are echoed on the response and in `ai_metadata.extra`.

**API:** `AIService.socratic_chat(SocraticChatRequest)` → `reply`, optional `session_id`  
**Helper:** `AIService.build_chat_history(persisted_messages)` maps DB `sender_type` → AI roles.

### 3.6 Lab assistant chat

- Modes: experiment guide vs coding hints (`detected_mode`).
- Uses lab steps/theory + optional model answers (anti-leak sanitization blocks obvious solution dumps).
- Same **CHAT_SESSIONS / CHAT_MESSAGES** continue-later + task scoping as Socratic chat.

**API:** `AIService.lab_assistant_chat(LabAssistantChatRequest)`

### 3.7 Cohort analytics (all students on a task)

- Staff-facing class patterns: shared errors, misconceptions, teaching focus.
- Backend aggregates/anonymizes grades + code-review stats (+ optional criterion stats), then calls AI.
- Warns when cohort size is too small for reliable patterns.

**API:** `AIService.analyze_cohort_patterns(CohortAnalyticsRequest)`  
**Output:** `summary`, `common_issues[]`, `misconceptions[]`, `teaching_focus[]`, `warnings`, `ai_metadata`

### 3.8 AI metadata & ops metrics

- Every AI response can include **`ai_metadata`**: engine/prompt version, operation, provider, model, latency, truncation/sanitize flags, warnings count.
- In-process collector: `AIService.metrics_summary()` / `recent_metrics()`.
- Demo health/metrics routes exist on `app.py` (`/api/ai/health`, `/api/ai/metrics`).

### 3.9 Demo FastAPI app + dashboard (local)

- `app.py` + `static/index.html`: temporary UI for labs, uploads, rubric, grading, chat.
- JSON under `data/` for local persistence — **not** production storage.
- Backend should call **`AIService` directly**, not treat demo routes as the permanent contract.

### 3.10 Reliability behaviors

| Behavior | Detail |
|----------|--------|
| No silent fake grades on bad JSON | Raises `GradingResponseError` / `RubricResponseError` / etc. |
| Provider fallback | Groq primary → Groq fallback model → Gemini → Gemini fallback |
| Mock mode | Deterministic responses when `MOCK_MODE=true` or no API keys |
| Unified facade | All capabilities go through `AIService` |

---

## 4. Package layout

```text
AI-Service/
├── ai_tutor/
│   ├── service.py           # AIService — call this
│   ├── config.py
│   ├── metrics.py
│   ├── engine/              # evaluator + exceptions
│   ├── models/              # requests/responses (rubric, grading, chat, analytics, …)
│   ├── prompts/templates.py
│   └── parsers/submission.py
├── app.py                   # demo HTTP + dashboard
├── tests/                   # pytest suite
├── static/                  # demo UI
├── data/                    # demo JSON store
├── pytest.ini
├── .env.example
└── docs/
    ├── SYSTEM_OVERVIEW.md   # this file
    └── BACKEND_CONNECTION.md
```

Root shims (`ai_service.py`, `evaluator.py`, …) re-export the package for older imports.

---

## 5. Who does what

| Concern | Owner |
|---------|--------|
| Login, roles (professor / TA / student), authorize staff APIs | **Backend** |
| Tasks, submissions, rubrics, files, final grade confirmation | **Backend** |
| `CHAT_SESSIONS` / `CHAT_MESSAGES` create, load, append | **Backend** |
| Extract/prepare text, call `AIService`, save AI outputs | **Backend** |
| Rubric/grade/chat/cohort generation + validation | **AI Service** |
| Convert stored chat rows → `chat_history` helpers | **AI Service** (optional helper) |
| Cohort anonymization before analytics | **Backend** |

---

## 6. Errors the backend should map

| Exception | Typical HTTP |
|-----------|--------------|
| `ValueError` | 400 |
| `RubricResponseError` | 502 |
| `GradingResponseError` | 502 |
| `ChatResponseError` | 502 |
| `AnalyticsResponseError` | 502 |
| `RuntimeError` (providers down) | 503 |

---

## 7. Configuration

Copy `.env.example` → `.env`:

- `PRIMARY_PROVIDER` = `groq` or `gemini`
- `GROQ_API_KEY` / `GEMINI_API_KEY`
- `MOCK_MODE` = `true` for offline
- `AI_ENGINE_VERSION` / `PROMPT_VERSION` (copied into `ai_metadata`)
- Context budget variables for long documents
- `MAX_CHAT_HISTORY_MESSAGES` (default 40) — how many prior messages are sent to the model

---

## 8. Quick start (beyond tests)

```bash
cd AI-Service
pip install -r requirements.txt
# optional: copy .env.example → .env and set keys
uvicorn app:app --reload
```

Dashboard: open the URL printed by Uvicorn (usually `http://127.0.0.1:8000`).

Backend integration examples: see [BACKEND_CONNECTION.md](./BACKEND_CONNECTION.md).
