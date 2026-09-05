# Backend Connection Guide

**Audience:** backend team integrating the university API/DB with the AI layer  
**Goal:** call AI correctly, map responses to persistence, handle errors  
**Overview:** [SYSTEM_OVERVIEW.md](./SYSTEM_OVERVIEW.md)

---

## 1. How to connect

### Preferred: in-process Python package

```python
from ai_tutor import AIService, GradingResponseError, RubricResponseError
from ai_tutor import AnalyticsResponseError, ChatResponseError
from ai_tutor.models import (
    RubricSuggestRequest,
    RubricRefineRequest,
    GradeSubmissionRequest,
    RubricCriteriaItem,
    SocraticChatRequest,
    LabAssistantChatRequest,
    CohortAnalyticsRequest,
    CohortGradeSnapshot,
    CohortCodeReviewSnapshot,
    CohortCriterionSnapshot,
)

ai = AIService()  # reads env / Config; uses mock if no API keys
```

Install / path: keep the `AI-Service` root (or the `ai_tutor` package) on `PYTHONPATH`, or install the package when you publish it.

### Not recommended for production

- Calling demo FastAPI routes in `app.py` as the system of record  
- Importing `evaluator.py` internals instead of `AIService`  
- Putting role checks inside AI calls  

### Optional: HTTP demo only

`app.py` exposes `/api/suggest-rubric`, `/api/grade-submission`, etc. for the local dashboard. Production backend should own HTTP and call `AIService` from your API layer.

---

## 2. Ownership split (checklist)

| Responsibility | Backend | AI Service |
|----------------|---------|------------|
| Authenticate user / enforce professor vs TA vs student | ✅ | ❌ |
| Load/store `TASKS`, `SUBMISSIONS`, `RUBRICS`, `FILES` | ✅ | ❌ |
| Extract text from uploaded files (or use AI parsers) | ✅ (or use helpers) | Helpers in `ai_tutor.parsers` |
| Call `AIService.*` with prepared text | ✅ | ✅ execute |
| Persist `ai_suggested_grade`, reviews, `ai_metadata` | ✅ | ❌ |
| Confirm final grade (`staff_confirmed`) | ✅ professor only | ❌ |
| Anonymize cohort data before analytics | ✅ | ❌ |
| Generate rubrics / grades / chat / cohort insights | ❌ | ✅ |

---

## 3. Error → HTTP mapping

Catch in this order (specific errors before generic):

| Exception | Suggested HTTP | Meaning |
|-----------|----------------|---------|
| `ValueError` | **400** | Bad/missing input (empty spec, empty cohort payload, etc.) |
| `RubricResponseError` | **502** | LLM rubric JSON invalid / failed validation |
| `GradingResponseError` | **502** | LLM grading JSON invalid / failed validation |
| `ChatResponseError` | **502** | Chat LLM call failed |
| `AnalyticsResponseError` | **502** | Cohort analytics JSON invalid / failed validation |
| `RuntimeError` | **503** | All LLM providers unavailable |

Example:

```python
try:
    result = ai.grade_submission(req)
except ValueError as e:
    raise HTTPException(400, str(e))
except GradingResponseError as e:
    raise HTTPException(502, str(e))
except RuntimeError as e:
    raise HTTPException(503, str(e))
```

---

## 4. API methods

### 4.1 Suggest rubric

```python
result = ai.suggest_rubric(
    RubricSuggestRequest(
        task_title="Lab 1: BST",
        task_type="lab",  # lab | assignment | project (also coding/essay guidance supported)
        task_description="...",
        reference_text="<extracted spec text>",
        request_metadata={"task_id": 12},  # optional audit ids
    )
)
```

**Persist:**

| Response field | DB |
|----------------|-----|
| — | `RUBRICS.source = 'ai_suggested'`, `status = 'pending'`, bump `version` |
| `criteria[].name/description/max_points/sort_order` | `RUBRIC_CRITERIA` rows |
| `total_max_points` / `rationale` | optional columns or notes |
| `ai_metadata` | audit/log JSON |
| `warnings` | show to staff / log |

### 4.2 Refine rubric

```python
result = ai.refine_rubric(
    RubricRefineRequest(
        task_title="Lab 1: BST",
        task_type="lab",
        reference_text="<spec>",
        previous_criteria=previous,  # List[RubricCriteriaItem]
        staff_feedback="Make each criterion 20 points",
    )
)
```

Staff feedback overrides prior structure. Store as a **new** rubric version (`pending`), do not overwrite accepted history.

### 4.3 Grade submission

```python
result = ai.grade_submission(
    GradeSubmissionRequest(
        task_title="Lab 1: BST",
        task_type="coding",
        reference_text="<task spec — student-facing>",
        rubric_criteria=[
            RubricCriteriaItem(
                name="Correctness",
                description="Insert/search work",
                max_points=50,
                sort_order=1,
            ),
        ],
        submission_text="<report or extracted text>",
        code_files={"main.py": "...", "bst.cpp": "..."},
        grading_key="<TA model answers — optional, never shown to students>",
        request_metadata={
            "task_id": 12,
            "submission_id": 99,
            "rubric_id": 5,
            "attempt_number": 1,
        },
    )
)
```

**Rules:**

- Require non-empty `reference_text` and some submission content (`submission_text` and/or `code_files`).
- Keep **spec** and **grading_key** separate (key is internal verification only).
- Prefer accepted rubric criteria from DB.

**Persist:**

| Response field | DB |
|----------------|-----|
| `ai_suggested_grade` | `SUBMISSIONS.ai_suggested_grade` |
| `summary_feedback` | `SUBMISSIONS.feedback` |
| — | `SUBMISSIONS.status = 'ai_graded'`, set `rubric_id` |
| `criterion_evaluations[]` | **Recommended:** store per-criterion scores (table or JSON) for analytics |
| `code_reviews[]` | `CODE_REVIEWS` (`severity`: `info\|warning\|critical`, `file_path`, `line_number`, `finding`) |
| `warnings`, `ai_metadata` | log / UI |

`final_grade` / `confirmed_by` / `staff_confirmed` are **backend-only** after professor action.

### 4.4 Socratic student chat

```python
result = ai.socratic_chat(
    SocraticChatRequest(
        task_title="Lab 1",
        reference_text="<spec excerpts or retrieved chunks>",
        chat_history=[{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}],
        student_message="I'm stuck on insert",
    )
)
# result.reply
```

Backend loads/saves history if you use `CHAT_SESSIONS` / `CHAT_MESSAGES`.

### 4.5 Lab assistant chat

```python
result = ai.lab_assistant_chat(
    LabAssistantChatRequest(
        lab_title="RC Circuit Lab",
        lab_type="experiment",  # or coding
        steps_and_theory="<procedure>",
        model_answers="<TA key — never leak>",
        chat_history=[],
        student_message="What do I measure in step 2?",
    )
)
# result.reply, result.detected_mode
```

Anti-leak sanitization runs on the AI side; still never send model answers to the student UI.

### 4.6 Cohort analytics (class-wide)

Backend aggregates **latest** attempts for a task (`is_latest = true`), **strips names/ids**, then:

```python
result = ai.analyze_cohort_patterns(
    CohortAnalyticsRequest(
        task_title="Lab 3: Recursion",
        task_type="coding",
        rubric_criteria_names=["Correctness", "Base cases"],
        grades=[
            CohortGradeSnapshot(grade=40, max_grade=100, feedback="Missed base case"),
            CohortGradeSnapshot(grade=55, max_grade=100, feedback="Wrong recursive call"),
        ],
        code_reviews=[
            CohortCodeReviewSnapshot(
                severity="critical",
                finding="Missing recursion base case",
                file_path="solution.py",
                count=6,
            )
        ],
        criterion_stats=[
            CohortCriterionSnapshot(
                criterion_name="Base cases",
                average_score=8,
                max_points=25,
                low_score_count=5,
            )
        ],
    )
)
```

**Response for staff UI:** `summary`, `common_issues[]`, `misconceptions[]`, `teaching_focus[]`, `warnings`, `ai_metadata`.

Auth: professor/TA only. Do not expose to students.

---

## 5. File parsing helpers

Optional utilities (backend may use its own pipeline instead):

```python
from ai_tutor.parsers import extract_text_from_file, extract_submission_content, prepare_submission_for_grading
```

- Skips junk paths (`node_modules`, `venv`, `.git`, `__pycache__`, …) inside ZIPs/directories.
- `prepare_submission_for_grading` is already invoked inside `AIService.grade_submission`.

---

## 6. Suggested `request_metadata` keys

Not required by AI logic; useful for your logs / tracing. May appear in metrics extras:

```json
{
  "task_id": 12,
  "submission_id": 99,
  "rubric_id": 5,
  "rubric_version": 2,
  "attempt_number": 1,
  "commit_id": null,
  "request_id": "uuid"
}
```

---

## 7. Persistence recommendations

| AI output | Minimum MVP store | Better for analytics |
|-----------|-------------------|----------------------|
| Rubric criteria | `RUBRIC_CRITERIA` | Keep all `RUBRICS` versions |
| Overall grade + feedback | `SUBMISSIONS` | — |
| Criterion breakdown | optional JSON | Dedicated score rows |
| Code reviews | `CODE_REVIEWS` | Link `commit_id` for projects |
| `ai_metadata` | JSON column / audit table | Searchable by `operation` |
| Cohort insights | cache or recompute | Optional staff notes table |

---

## 8. Environment the AI process needs

Copy `AI-Service/.env.example` → `.env` on the host that runs AI calls:

```env
PRIMARY_PROVIDER=groq
MOCK_MODE=false
GROQ_API_KEY=...
GEMINI_API_KEY=...
AI_ENGINE_VERSION=1.4.0
PROMPT_VERSION=2.0.0
```

Health/ops (demo app): `GET /api/ai/health`, `GET /api/ai/metrics` — or call `ai.metrics_summary()` from your own admin route.

---

## 9. Integration smoke test

```python
ai = AIService()
ai.engine.mock_mode = True

r = ai.suggest_rubric(
    RubricSuggestRequest(task_title="Smoke", reference_text="Build a linked list.")
)
assert r.criteria and r.ai_metadata

g = ai.grade_submission(
    GradeSubmissionRequest(
        task_title="Smoke",
        reference_text="Build a linked list.",
        rubric_criteria=r.criteria,
        submission_text="I implemented insert and delete.",
    )
)
assert g.ai_suggested_grade is not None
```

Full automated coverage: from `AI-Service/` run `pytest -v`.

---

## 10. Quick FAQ

**Q: Do we need chat tables for MVP?**  
A: Not for grading. Add `CHAT_SESSIONS` / `CHAT_MESSAGES` only if you persist tutor conversations.

**Q: Who anonymizes cohort analytics?**  
A: Backend, before calling `analyze_cohort_patterns`.

**Q: Can TAs confirm grades?**  
A: No — schema/product rule: professors only. Enforce in backend.

**Q: Same package for labs, assignments, projects?**  
A: Yes. Pass `task_type` and the right `reference_text` / `code_files` / optional `grading_key`.
