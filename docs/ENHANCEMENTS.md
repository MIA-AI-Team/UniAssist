# AI Layer Enhancements

This document describes the AI-focused improvements applied to the project, how the backend team should integrate, and an assessment of the current project structure.

**AI Engine Version:** `1.4.0`  
**Prompt Bundle Version:** `2.0.0`  
**Last updated:** 2026-09-01

---

## v1.4.0 — Package folder structure (`ai_tutor/`)

The AI layer was moved into an installable package so the backend team can import a single namespace instead of flat root modules.

### New layout

```
AI-TUTOR/
├── ai_tutor/                    # ★ AI package — backend imports from here
│   ├── __init__.py              # exports AIService, AIEvaluationEngine, Config, errors
│   ├── service.py               # AIService facade (was ai_service.py)
│   ├── metrics.py               # AIMetricsCollector (was ai_metrics.py)
│   ├── config.py
│   ├── engine/
│   │   ├── evaluator.py         # Core LLM engine (was evaluator.py)
│   │   └── exceptions.py        # GradingResponseError, RubricResponseError, ChatResponseError
│   ├── models/                  # Pydantic schemas split by domain
│   │   ├── metadata.py
│   │   ├── rubric.py
│   │   ├── grading.py
│   │   ├── chat.py
│   │   ├── lab.py
│   │   └── requests.py
│   ├── prompts/
│   │   └── templates.py         # Prompt templates + task-type guidance
│   └── parsers/
│       └── submission.py        # PDF/DOCX/ZIP/code extraction (was file_parser.py)
├── app.py                       # FastAPI demo (imports from ai_tutor)
├── tests/                       # pytest suite (was test_*.py at root)
├── static/
├── data/
├── config.py                    # shim → ai_tutor.config
├── models.py                    # shim → ai_tutor.models
├── evaluator.py                 # shim → ai_tutor.engine
├── ai_service.py                # shim → ai_tutor.service
├── ai_metrics.py                # shim → ai_tutor.metrics
├── file_parser.py               # shim → ai_tutor.parsers
└── prompts.py                   # shim → ai_tutor.prompts
```

### What changed

| Change | Why |
|--------|-----|
| **`ai_tutor/` package** | Clear boundary for backend integration; easier to version and publish |
| **Models split into submodules** | Smaller files, easier navigation as schemas grow |
| **Engine exceptions extracted** | `engine/exceptions.py` keeps error types importable without loading the full evaluator |
| **Tests moved to `tests/`** | Standard Python layout; `pytest.ini` sets `testpaths = tests` |
| **Root shims retained** | Existing `from models import ...` and `from evaluator import ...` still work during migration |
| **`app.py` imports `ai_tutor` directly** | Demo API uses the same import path the backend should use |

### Backend import (preferred)

```python
from ai_tutor import AIService, GradingResponseError, RubricResponseError
from ai_tutor.models import GradeSubmissionRequest, RubricCriteriaItem

ai = AIService()
```

Legacy root imports (`from ai_service import AIService`) still work via thin shim files.

---

## What Was Done

### P0 — Backend integration readiness

| Enhancement | Description |
|-------------|-------------|
| **`AIService` facade** | `ai_tutor/service.py` is the single entry point for all AI operations. Backend should call this instead of FastAPI routes or the engine directly. |
| **Typed request models** | `RubricSuggestRequest`, `RubricRefineRequest`, `GradeSubmissionRequest`, `SocraticChatRequest`, `LabAssistantChatRequest` in `ai_tutor/models/`. |
| **Unified error handling** | No silent mock fallback in production flows. Errors: `ValueError` (400), `RubricResponseError` / `GradingResponseError` / `ChatResponseError` (502), provider failure (503 via `RuntimeError`). |
| **`grading_key` separation** | Model answers are passed separately from the task spec so grading does not treat the answer key as the student-facing specification. |
| **`prepare_submission_for_grading()`** | Standardizes `submission_text` + `code_files` before grading. Lab submissions now store `code_files` from ZIP uploads. |
| **`AIMetadata` on all responses** | Every AI response includes `ai_metadata` (provider, model, latency, truncation, version info) for backend persistence and audits. |

### P1 — AI quality and safety

| Enhancement | Description |
|-------------|-------------|
| **Rubric validation** | `_normalize_rubric_response()` enforces criteria count bounds and recalculates `total_max_points` from criteria. |
| **Grading validation** | Extended `_normalize_grading_response()`: caps scores, recomputes totals, detects missing criteria, flags empty reasoning. |
| **Task-type-aware prompts** | `get_task_type_guidance()` in `ai_tutor/prompts/templates.py` adds lab/assignment/project/experiment/coding/essay guidance to rubric and grading prompts. |
| **Context budgeting** | `_allocate_grading_context()` distributes character budget across spec, submission, code files, and grading key (configurable ratios). |
| **Lab anti-leak guardrails** | `_sanitize_lab_reply()` blocks obvious solution leaks and long verbatim copies from TA model answers. |

### AI evaluation metrics

| Component | Description |
|-----------|-------------|
| **`ai_tutor/metrics.py`** | `AIMetricsCollector` tracks latency, provider, model, parse success, truncation, score adjustments per operation. |
| **`GET /api/ai/metrics`** | Returns summary + recent metrics for observability. |
| **`GET /api/ai/health`** | Returns mock mode, provider, engine and prompt versions. |
| **Logging** | Each AI operation logs structured metrics to the `AIMetrics` logger. |

### Bug fixes included

- Removed duplicate code in `file_parser.py`
- Fixed missing `logger` in `app.py` batch grading
- Lab grading now passes `code_files` and uses separate `grading_key`
- Batch grading returns per-submission `errors` list

---

## Backend Integration Guide

### Call the AI layer

```python
from ai_tutor import AIService, GradingResponseError, RubricResponseError
from ai_tutor.models import GradeSubmissionRequest, RubricCriteriaItem

ai = AIService()

result = ai.grade_submission(
    GradeSubmissionRequest(
        task_title="Lab 1: BST",
        task_type="coding",
        reference_text="<parsed spec text>",
        rubric_criteria=[RubricCriteriaItem(name="Correctness", description="...", max_points=100, sort_order=1)],
        submission_text="<student text>",
        code_files={"main.py": "..."},
        grading_key="<TA model answers — optional>",
    )
)

# Persist for audit trail
db.save_grade(
    submission_id=...,
    ai_grade=result.ai_suggested_grade,
    ai_metadata=result.ai_metadata.model_dump(),
    warnings=result.warnings,
)
```

### Error handling contract

| Exception | HTTP | Meaning |
|-----------|------|---------|
| `ValueError` | 400 | Missing spec, empty submission, invalid input |
| `RubricResponseError` | 502 | AI returned invalid rubric JSON |
| `GradingResponseError` | 502 | AI returned invalid grading JSON |
| `ChatResponseError` | 502 | AI chat call failed |
| `RuntimeError` | 503 | All LLM providers unavailable |

### What backend provides vs what AI provides

| Backend team | AI layer |
|--------------|----------|
| File upload & storage | Text/code extraction helpers (`ai_tutor/parsers/submission.py`) |
| User auth, roles | — |
| Database, task/submission IDs | Optional `request_metadata` dict on requests |
| Persist `ai_metadata`, grades, warnings | Generate grades, rubrics, chat replies |
| Professor confirmation workflow | Suggested grades only |

---

## Project Structure Assessment

### Current layout (v1.4.0)

```
AI-TUTOR/
├── ai_tutor/              # ★ Backend integration package
│   ├── service.py         # AIService facade
│   ├── metrics.py         # Observability / metrics collector
│   ├── engine/evaluator.py
│   ├── prompts/templates.py
│   ├── models/            # Pydantic schemas
│   ├── config.py
│   └── parsers/submission.py
├── app.py                 # FastAPI demo + lab JSON store (temporary)
├── tests/                 # Test suite
├── static/index.html      # Demo dashboard UI
├── data/                  # Temporary JSON persistence (replace with DB)
├── DATABASE_DESIGN.md     # Target schema (backend team)
├── README.md              # Product overview
└── ENHANCEMENTS.md        # This file
```

Root-level `config.py`, `models.py`, `evaluator.py`, etc. are **backward-compatible shims** that re-export from `ai_tutor/`. New code should import from `ai_tutor` only.

### Is the structure good?

**Good for an AI MVP / integration prototype:**

| Strength | Why |
|----------|-----|
| Clear AI boundary | `ai_tutor/service.py` separates AI from HTTP and storage |
| Typed contracts | Pydantic models define inputs/outputs for backend |
| Testable engine | `ai_tutor/engine/evaluator.py` can be tested without FastAPI |
| Prompts isolated | `ai_tutor/prompts/` is easy to version and review |
| Metrics built in | Ready for backend observability pipeline |

**Needs improvement before production:**

| Issue | Recommendation |
|-------|----------------|
| `app.py` is large (~680 lines) | Split into `routes/rubric.py`, `routes/labs.py`, `routes/grading.py` when backend takes over HTTP |
| `static/index.html` is a monolith | Split JS or replace with a proper frontend framework |
| `data/*.json` is temporary | Backend replaces with Postgres per `DATABASE_DESIGN.md` |
| `evaluator.py` is growing | Split further inside `ai_tutor/engine/` (e.g. `llm_client.py`, `grading_engine.py`) |
| No `httpx` in requirements | Add explicitly if using TestClient in CI |

### Verdict

**Structure is good for the current phase** — AI logic lives in `ai_tutor/` and is backend-ready. The main technical debt is in the **demo layer** (`app.py`, `static/`, JSON files), which the backend team will replace. **Do not merge DB logic into the engine**; keep calling `AIService` from the backend API layer.

---

## Configuration

See `.env.example` for all settings. Key new variables:

```env
AI_ENGINE_VERSION=1.4.0
PROMPT_VERSION=2.0.0
MAX_TOTAL_PROMPT_CHARS=48000
BUDGET_REFERENCE_RATIO=0.40
BUDGET_SUBMISSION_RATIO=0.35
BUDGET_CODE_RATIO=0.10
MAX_GRADING_KEY_CHARS=6000
```

---

## Running Tests

```bash
pytest -v
```

Key test files:

| File | Covers |
|------|--------|
| `tests/test_ai_service.py` | AIService facade, error contracts, metrics |
| `tests/test_evaluator.py` | Engine normalization, anti-leak, grading rules |
| `tests/test_app.py` | HTTP endpoints, health, metrics |
| `tests/test_file_parser.py` | ZIP extraction, junk folder skipping |

---

## Next Steps (after backend DB integration)

1. Backend calls `AIService` from their API layer (not `app.py` JSON routes)
2. Persist `ai_metadata` and `warnings` on every AI operation
3. Add RAG for long PDF specs (optional, post-MVP)
4. Professor confirmation workflow (backend-owned, not AI)
5. GitHub code sync → pass `code_files` into `GradeSubmissionRequest`
