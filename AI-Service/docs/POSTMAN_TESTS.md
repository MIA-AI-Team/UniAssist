# Postman test cases — AI Service FastAPI

Use these requests against the running container or local server.

**Base URL:** `http://localhost:8000`

**Tip:** Set `MOCK_MODE=true` in `.env` (Dockerfile default) so Postman works without API keys.

---

## 0. Run the API (Docker)

From `ai-service/`:

```bash
# Build image
docker build -t ai-tutor-service .

# Run (mock mode by default)
docker run --rm -p 8000:8000 ai-tutor-service

# Or with your .env (real Groq/Gemini keys)
docker run --rm -p 8000:8000 --env-file .env -e MOCK_MODE=false ai-tutor-service

# or: docker compose up --build
```

Open `http://localhost:8000/docs` for Swagger. There is **no web dashboard** — APIs only.

`GET /` returns JSON service info (`docs`, `health`, `metrics`).

---

## 1. Health check

| Field | Value |
|-------|--------|
| Method | `GET` |
| URL | `{{baseUrl}}/api/ai/health` |
| Body | none |

**Expect (200):**

```json
{
  "status": "ok",
  "mock_mode": true,
  "provider": "groq",
  "ai_engine_version": "1.4.0",
  "prompt_version": "2.0.0"
}
```

**Postman Tests tab:**

```javascript
pm.test("Status 200", () => pm.response.to.have.status(200));
pm.test("Healthy", () => pm.expect(pm.response.json().status).to.eql("ok"));
```

---

## 2. AI metrics

| Field | Value |
|-------|--------|
| Method | `GET` |
| URL | `{{baseUrl}}/api/ai/metrics` |

**Expect (200):** `summary` + `recent` array.

```javascript
pm.test("Has summary", () => pm.expect(pm.response.json()).to.have.property("summary"));
```

---

## 3. Suggest rubric (form-data)

| Field | Value |
|-------|--------|
| Method | `POST` |
| URL | `{{baseUrl}}/api/suggest-rubric` |
| Body | `form-data` |

| Key | Type | Value |
|-----|------|--------|
| `task_title` | Text | `Lab 1: Binary Search Tree` |
| `task_type` | Text | `coding` |
| `task_description` | Text | `Implement insert and search` |
| `spec_text_override` | Text | `Students must implement a BST with insert and search. Handle empty tree and duplicates.` |

(Optional) `spec_file` = File → upload a PDF/DOCX instead of `spec_text_override`.

**Expect (200):** `criteria` array, `total_max_points`, `ai_metadata`.

```javascript
const j = pm.response.json();
pm.test("Status 200", () => pm.response.to.have.status(200));
pm.test("Has criteria", () => pm.expect(j.criteria.length).to.be.above(0));
pm.test("Has metadata", () => pm.expect(j.ai_metadata).to.be.ok);
// Save rubric for next requests
pm.collectionVariables.set("rubric_json", JSON.stringify(j.criteria));
```

---

## 4. Refine rubric (form-data)

| Field | Value |
|-------|--------|
| Method | `POST` |
| URL | `{{baseUrl}}/api/refine-rubric` |
| Body | `form-data` |

| Key | Type | Value |
|-----|------|--------|
| `task_title` | Text | `Lab 1: Binary Search Tree` |
| `task_type` | Text | `coding` |
| `task_description` | Text | `Implement insert and search` |
| `spec_text_override` | Text | `Students must implement a BST with insert and search.` |
| `rubric_json` | Text | `{{rubric_json}}` (from suggest step) or paste criteria JSON array |
| `staff_feedback` | Text | `Make each criterion worth 25 points` |

**Example `rubric_json` if variable empty:**

```json
[
  {"name": "Correctness", "description": "Insert and search work", "max_points": 50, "sort_order": 1},
  {"name": "Style", "description": "Readable code", "max_points": 50, "sort_order": 2}
]
```

**Expect (200):** refined `criteria`.

---

## 5. Grade submission (form-data)

| Field | Value |
|-------|--------|
| Method | `POST` |
| URL | `{{baseUrl}}/api/grade-submission` |
| Body | `form-data` |

| Key | Type | Value |
|-----|------|--------|
| `task_title` | Text | `Lab 1: Binary Search Tree` |
| `task_type` | Text | `coding` |
| `spec_text_override` | Text | `Implement BST insert and search. Handle empty tree.` |
| `submission_text_override` | Text | `class Node:\n  def __init__(self, v):\n    self.v=v; self.left=None; self.right=None\n# insert and search implemented` |
| `rubric_json` | Text | see JSON below |
| `student_name` | Text | `Ada Lovelace` (optional) |
| `student_id` | Text | `STU-100` (optional — saves into demo store) |

**`rubric_json`:**

```json
[
  {"name": "Correctness", "description": "Operations work", "max_points": 70, "sort_order": 1},
  {"name": "Code quality", "description": "Clear structure", "max_points": 30, "sort_order": 2}
]
```

**Expect (200):** `ai_suggested_grade`, `criterion_evaluations`, `summary_feedback`, `ai_metadata`.

**Negative case — missing submission:** omit both `submission_file` and `submission_text_override` → expect **400**.

**Negative case — missing spec:** omit both `spec_file` and `spec_text_override` → expect **400**.

```javascript
pm.test("Graded", () => {
  pm.response.to.have.status(200);
  const j = pm.response.json();
  pm.expect(j).to.have.property("ai_suggested_grade");
  pm.expect(j.criterion_evaluations.length).to.be.above(0);
});
```

---

## 6. Student Socratic chat (JSON)

| Field | Value |
|-------|--------|
| Method | `POST` |
| URL | `{{baseUrl}}/api/student-chat` |
| Headers | `Content-Type: application/json` |
| Body | raw JSON |

```json
{
  "task_title": "Lab 1: Binary Search Tree",
  "reference_text": "Implement insert and search on a BST. Do not ask for the full solution.",
  "chat_history": [
    {"role": "user", "content": "Where should I start?"},
    {"role": "assistant", "content": "What happens when the tree is empty?"}
  ],
  "student_message": "How do I handle an empty tree without giving me the full code?"
}
```

**Expect (200):** `{ "reply": "...", "ai_metadata": {...} }`

```javascript
pm.test("Got reply", () => {
  pm.response.to.have.status(200);
  pm.expect(pm.response.json().reply.length).to.be.above(0);
});
```

---

## 7. List labs

| Field | Value |
|-------|--------|
| Method | `GET` |
| URL | `{{baseUrl}}/api/labs` |

**Expect (200):** JSON array (may be empty on fresh container).

---

## 8. Create lab (form-data)

| Field | Value |
|-------|--------|
| Method | `POST` |
| URL | `{{baseUrl}}/api/create-lab` |
| Body | `form-data` |

| Key | Type | Value |
|-----|------|--------|
| `title` | Text | `RC Circuit Lab` |
| `lab_type` | Text | `experiment` |
| `description` | Text | `Measure RC time constant` |
| `steps_and_theory_text` | Text | `Step 1: Wire R and C. Step 2: Measure tau.` |
| `model_answers_text` | Text | `tau = R * C` |
| `rubric_json` | Text | `[]` |

**Expect (200):** lab object with `id` like `lab-1`.

```javascript
pm.test("Lab created", () => {
  pm.response.to.have.status(200);
  const j = pm.response.json();
  pm.expect(j).to.have.property("id");
  pm.collectionVariables.set("lab_id", j.id);
});
```

---

## 9. Lab chat (JSON) — needs existing lab

| Field | Value |
|-------|--------|
| Method | `POST` |
| URL | `{{baseUrl}}/api/lab-chat` |
| Headers | `Content-Type: application/json` |

```json
{
  "lab_id": "{{lab_id}}",
  "student_message": "What should I do in step 1?",
  "chat_history": []
}
```

**Expect (200):** `reply`, `detected_mode`.  
**Expect (404):** unknown `lab_id`.

---

## 10. Student feedback shield

| Field | Value |
|-------|--------|
| Method | `GET` |
| URL | `{{baseUrl}}/api/student-feedback/STU-100` |

**Expect (200):** array of submissions for that student; if graded, `criterion_evaluations` and `code_reviews` should be empty arrays (shielded).

---

## Suggested Postman collection setup

1. Create collection **AI-Tutor Service**
2. Collection variable: `baseUrl` = `http://localhost:8000`
3. Add requests **1 → 6** in order (health → suggest → grade → chat)
4. Paste the **Tests** scripts above into each request’s Tests tab
5. Run **Collection Runner** once with mock mode

### Import as curl (Postman: Import → Raw text)

```bash
curl -s http://localhost:8000/api/ai/health

curl -s -X POST http://localhost:8000/api/suggest-rubric \
  -F "task_title=Lab 1: BST" \
  -F "task_type=coding" \
  -F "task_description=Implement insert and search" \
  -F "spec_text_override=Implement a BST with insert and search. Handle empty trees."

curl -s -X POST http://localhost:8000/api/student-chat \
  -H "Content-Type: application/json" \
  -d "{\"task_title\":\"Lab 1\",\"reference_text\":\"BST lab\",\"chat_history\":[],\"student_message\":\"What is a base case?\"}"
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Connection refused | Container not running / wrong port mapping `-p 8000:8000` |
| 502 on AI calls | Provider/API key issue — set `MOCK_MODE=true` |
| 400 on grade | Must send spec **and** submission (file or text override) |
| Form fields ignored | Use Body → **form-data**, not raw JSON, for rubric/grade routes |
| Chat 422 | Use **raw JSON** + `Content-Type: application/json` for `/api/student-chat` |
