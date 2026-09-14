# UniAssist API — Frontend Integration Guide

**Base URL:** `http://localhost:8000` (development)  
**Auth:** All endpoints except `/auth/register` and `/auth/login` require a Bearer token. Check [Authentication README](AUTHENTICATION_CONNECTION)

```
Authorization: Bearer <access_token>
```

---

## Table of Contents

1. [Authentication](#1-authentication)
2. [Files](#2-files)
3. [Tasks](#3-tasks)
4. [Rubrics](#4-rubrics)
5. [Submissions](#5-submissions)
6. [Chat](#6-chat)
7. [Analytics](#7-analytics)
8. [Full Flows](#8-full-flows)
9. [Role Permission Summary](#9-role-permission-summary)
10. [Error Reference](#10-error-reference)

---

## 1. Authentication

### Register
**`POST /auth/register`**

Role determines which extra fields are required.

**Student:**
```json
{
  "name": "Ahmed Mostafa",
  "email": "ahmed@uni.edu",
  "password": "password123",
  "role": "student",
  "student_number": "S001",
  "cohort_year": 2027,
  "major": "Computer Engineering"
}
```

**Professor:**
```json
{
  "name": "Dr. Sara Ali",
  "email": "sara@uni.edu",
  "password": "password123",
  "role": "professor",
  "staff_role": "professor",
  "department": "Computer Science"
}
```

**Teaching Assistant:**
```json
{
  "name": "TA Mona",
  "email": "mona@uni.edu",
  "password": "password123",
  "role": "teaching_assistant",
  "staff_role": "teaching_assistant",
  "department": "Computer Science"
}
```

**Response `201`:**
```json
{
  "id": 1,
  "name": "Ahmed Hassan",
  "email": "ahmed@uni.edu",
  "role": "student",
  "message": "Account created successfully."
}
```

---

### Login
**`POST /auth/login`**

```json
{
  "email": "ahmed@uni.edu",
  "password": "password123"
}
```

**Response `200`:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_id": 1,
  "role": "student",
  "name": "Ahmed Hassan"
}
```

> Save the `access_token` and attach it to every subsequent request header.

---

## 2. Files

File upload is always the **first step** before creating a lab task or a submission. You upload the file, get back a `file_id`, then use that `file_id` in the next request.

### Upload a File
**`POST /files/upload`**  
Content-Type: `multipart/form-data`

| Field | Type | Required | Description |
|---|---|---|---|
| `file` | File | ✅ | The actual file (PDF, ZIP, etc.) |
| `purpose` | string | ✅ | `reference` \| `submission` \| `other` |
| `task_id` | int | ❌ | Optionally link to a task at upload time |
| `submission_id` | int | ❌ | Optionally link to a submission at upload time |

> For lab reference PDFs: upload with `purpose=reference` and no `task_id` yet. You will link it when creating the task.  
> For submission files: upload with `purpose=submission` and no `submission_id` yet. You will link it when creating the submission.

```js
const formData = new FormData();
formData.append("file", fileInput.files[0]);
formData.append("purpose", "reference");

const res = await fetch("/files/upload", {
  method: "POST",
  headers: { "Authorization": `Bearer ${token}` },
  body: formData,
});
const { file_id } = await res.json();
// save file_id — you need it for the next step
```

**Response `201`:**
```json
{
  "file_id": 5,
  "file_name": "lab1_spec.pdf",
  "file_type": "pdf",
  "purpose": "reference",
  "storage_path": "uploads/reference/abc123.pdf",
  "uploaded_at": "2026-09-10T10:00:00Z"
}
```

---

### Get File Metadata
**`GET /files/{file_id}`**

Returns info about a file — not the file content itself.

**Response `200`:**
```json
{
  "file_id": 5,
  "file_type": "pdf",
  "purpose": "reference",
  "task_id": 3,
  "submission_id": null,
  "storage_path": "uploads/reference/abc123.pdf",
  "uploaded_at": "2026-09-10T10:00:00Z"
}
```

---

### Download a File
**`GET /files/{file_id}/download`**

Returns the raw file. The browser will prompt a download.

**Access rules:**
- Students can download their own files and any `reference` file (lab PDFs)
- Students cannot download other students' submission files
- Staff can download everything

---

## 3. Tasks

### ⚠️ Lab Task — Two-Step Flow

Lab tasks require a reference PDF (the lab spec/instructions). You must upload the PDF first to get a `file_id`, then include it when creating the task.

```
Step 1: POST /files/upload  (purpose=reference)  →  get file_id
Step 2: POST /tasks/        (include reference_file_id)  →  task created
```

Assignment and project tasks do not require a file — you can create them directly.

---

### Create a Task
**`POST /tasks/`**  
🔒 Professor or TA only

**Lab (requires file upload first):**
```json
{
  "type": "lab",
  "title": "Lab 1: Linked Lists",
  "description": "Implement a singly linked list in C.",
  "due_date": "2026-10-01T23:59:00",
  "target_cohort_year": 2024,
  "target_major": "Computer Science",
  "reference_file_id": 5,
  "scheduled_date": "2026-09-20T10:00:00"
}
```

**Assignment (no file needed):**
```json
{
  "type": "assignment",
  "title": "Assignment 1: Sorting",
  "description": "Implement merge sort and quick sort.",
  "due_date": "2026-10-10T23:59:00",
  "target_cohort_year": 2024,
  "target_major": null,
  "allowed_file_types": ["pdf", "zip"],
  "allow_late": false
}
```

**Project (no file needed):**
```json
{
  "type": "project",
  "title": "Final Project: Database Design",
  "description": "Design and implement a relational database.",
  "due_date": "2026-12-01T23:59:00",
  "target_cohort_year": 2024,
  "target_major": null,
  "require_team": true,
  "default_repo_provider": "github"
}
```

> `target_major: null` means the task is visible to **all majors** in that cohort year.

**Response `201`:**
```json
{
  "id": 3,
  "type": "lab",
  "title": "Lab 1: Linked Lists",
  "due_date": "2026-10-01T23:59:00Z",
  "created_at": "2026-09-10T10:00:00Z"
}
```

---

### List Tasks
**`GET /tasks/`**  
🔒 All authenticated users

| Query Param | Type | Description |
|---|---|---|
| `cohort_year` | int | Filter by cohort — auto-applied for students |
| `major` | string | Filter by major — auto-applied for students |
| `task_type` | string | `lab` \| `assignment` \| `project` |
| `filter_due_tasks` | bool | `true` = show only tasks not yet past due date |

> Students automatically get their own `cohort_year` and `major` applied. No need to pass them manually from the frontend for student users.

```
GET /tasks/
GET /tasks/?task_type=lab
GET /tasks/?filter_due_tasks=true
GET /tasks/?task_type=assignment&filter_due_tasks=true
```

**Response `200`:**
```json
[
  {
    "id": 3,
    "type": "lab",
    "title": "Lab 1: Linked Lists",
    "description": "Implement a singly linked list in C.",
    "due_date": "2026-10-01T23:59:00Z",
    "target_cohort_year": 2024,
    "target_major": "Computer Science",
    "reference_file_id": 5
  }
]
```

---

### Get Single Task
**`GET /tasks/{task_id}`**  
🔒 All authenticated users

**Response `200`:**
```json
{
  "id": 3,
  "type": "lab",
  "title": "Lab 1: Linked Lists",
  "description": "Implement a singly linked list in C.",
  "due_date": "2026-10-01T23:59:00Z",
  "target_cohort_year": 2024,
  "target_major": "Computer Science",
  "reference_file_id": 5,
  "created_by": 1,
  "created_at": "2026-09-10T10:00:00Z",
  "lab_details": {
    "scheduled_date": "2026-09-20T10:00:00Z"
  },
  "assignment_details": null,
  "project_details": null
}
```

> `lab_details`, `assignment_details`, `project_details` — only the matching type will be populated. The other two will be `null`.

---

### Delete a Task
**`DELETE /tasks/{task_id}`**  
🔒 Professor only — TAs cannot delete

Deletes the task and everything linked to it: rubrics, submissions, files, chat sessions.

**Response `204` — no body**

---

## 4. Rubrics

Rubrics must exist and be **accepted** before any submission can be graded. The flow is: suggest → professor reviews → accept or refine → accept.

### Option A — AI Suggests Rubric
**`POST /tasks/{task_id}/rubrics/suggest`**  
🔒 Professor or TA

AI reads the task spec and suggests criteria automatically. Saved as `pending`.

**Response `201`:**
```json
{
  "rubric_id": 1,
  "version": 1,
  "status": "pending"
}
```

---

### Option B — Staff Creates Rubric Manually
**`POST /tasks/{task_id}/rubrics/create`**  
🔒 Professor or TA

```json
{
  "criteria": [
    {
      "name": "Correctness",
      "description": "Insert, delete, and search work correctly for all cases.",
      "max_points": 50,
      "sort_order": 1
    },
    {
      "name": "Edge Cases",
      "description": "Handles empty list, single element, and duplicate values.",
      "max_points": 30,
      "sort_order": 2
    },
    {
      "name": "Code Quality",
      "description": "Clean, readable code with no memory leaks.",
      "max_points": 20,
      "sort_order": 3
    }
  ]
}
```

**Response `201`:**
```json
{
  "rubric_id": 1,
  "version": 1,
  "status": "pending",
  "criteria": [...]
}
```

---

### Refine Rubric with AI
**`POST /tasks/{task_id}/rubrics/refine`**  
🔒 Professor or TA

Pass feedback and AI generates a new improved version. The previous version is kept — never overwritten.

You can target a specific rubric by `rubric_id` or `version` as query params:

```
POST /tasks/3/rubrics/refine?rubric_id=1
POST /tasks/3/rubrics/refine?version=1
```

**Body:**
```json
{
  "staff_feedback": "Break correctness into 3 sub-criteria worth 20 points each"
}
```

**Response `201`:**
```json
{
  "rubric_id": 2,
  "version": 2,
  "status": "pending"
}
```

---

### Accept or Reject a Rubric
**`PATCH /tasks/{task_id}/rubrics/status`**  
🔒 Professor only

Target by `rubric_id` or `version` as query params:

```
PATCH /tasks/3/rubrics/status?rubric_id=2
PATCH /tasks/3/rubrics/status?version=2
```

**Body:**
```json
{
  "status": "accepted"
}
```

Valid values: `accepted` | `rejected`

> Accepting a rubric automatically marks any previously accepted rubric for this task as `replaced`. Only one rubric can be `accepted` at a time.

**Response `200`:**
```json
{
  "rubric_id": 2,
  "version": 2,
  "status": "accepted"
}
```

---

### List All Rubric Versions
**`GET /tasks/{task_id}/rubrics`**  
🔒 Professor or TA

Returns all rubric versions for a task in descending order (latest first).

**Response `200`:**
```json
[
  {
    "id": 2,
    "version": 2,
    "source": "ai_suggested",
    "status": "accepted",
    "reviewed_at": "2026-09-10T11:00:00Z",
    "criteria": [
      {
        "name": "Correctness",
        "description": "Insert and search work correctly",
        "max_points": 50,
        "sort_order": 1
      }
    ]
  },
  {
    "id": 1,
    "version": 1,
    "source": "ai_suggested",
    "status": "replaced",
    "reviewed_at": null,
    "criteria": [...]
  }
]
```

---

## 5. Submissions

### ⚠️ Submission with File — Two-Step Flow

If the student is submitting a file (code, PDF, ZIP), upload the file first to get a `file_id`, then create the submission with that `file_id`.

```
Step 1: POST /files/upload  (purpose=submission)  →  get file_id
Step 2: POST /submissions/  (include file_id)      →  submission created
```

If the student is submitting text only (no file), skip step 1 and just send `submission_text` directly.

---

### Submit Work
**`POST /submissions/`**  
🔒 Student only

**Text-only submission:**
```json
{
  "task_id": 3,
  "submission_text": "I implemented insert, delete, and search. Time complexity is O(n)...",
  "file_id": null,
  "team_id": null
}
```

**File submission (after uploading file first):**
```json
{
  "task_id": 3,
  "submission_text": "",
  "file_id": 8,
  "team_id": null
}
```

**Both text and file:**
```json
{
  "task_id": 3,
  "submission_text": "See the attached file for my implementation.",
  "file_id": 8,
  "team_id": null
}
```

> At least one of `submission_text` or `file_id` must be provided.  
> Resubmissions are supported — each new submission for the same task gets the next `attempt_number`. Only the latest attempt is graded.

**Response `201`:**
```json
{
  "submission_id": 10,
  "task_id": 3,
  "attempt_number": 1,
  "status": "pending",
  "submitted_at": "2026-09-10T12:00:00Z"
}
```

---

### View My Submissions
**`GET /submissions/my/{task_id}`**  
🔒 Student only

Returns all attempts for the logged-in student on a specific task.

**Response `200`:**
```json
[
  {
    "id": 10,
    "attempt_number": 1,
    "is_latest": true,
    "status": "ai_graded",
    "submitted_at": "2026-09-10T12:00:00Z",
    "ai_suggested_grade": 78.5,
    "final_grade": null,
    "feedback": "Good implementation. Missing edge case for empty list."
  }
]
```

---

### Trigger AI Grading
**`POST /submissions/{submission_id}/grade`**  
🔒 Professor or TA

The task must have an accepted rubric before this will work.

**Response `200`:**
```json
{
  "submission_id": 10,
  "status": "ai_graded",
  "ai_suggested_grade": 78.5,
  "feedback": "Good implementation. Missing edge case for empty list."
}
```

---

### Confirm Final Grade
**`PATCH /submissions/{submission_id}/confirm`**  
🔒 Professor only — TAs cannot confirm grades

Professor can accept the AI grade or override it with a different value.

```json
{
  "final_grade": 80.0
}
```

**Response `200`:**
```json
{
  "submission_id": 10,
  "status": "staff_confirmed",
  "final_grade": 80.0,
  "confirmed_by": 1,
  "confirmed_at": "2026-09-10T14:00:00Z"
}
```

---

### Get Submission Details
**`GET /submissions/{submission_id}`**  
🔒 Staff see all; students see only their own

**Response `200`:**
```json
{
  "id": 10,
  "task_id": 3,
  "student_id": 5,
  "team_id": null,
  "file_id": 8,
  "submission_text": "See the attached file for my implementation.",
  "attempt_number": 1,
  "is_latest": true,
  "status": "staff_confirmed",
  "ai_suggested_grade": 78.5,
  "final_grade": 80.0,
  "feedback": "Good implementation. Missing edge case for empty list.",
  "confirmed_by": 1,
  "confirmed_at": "2026-09-10T14:00:00Z",
  "submitted_at": "2026-09-10T12:00:00Z"
}
```

---


---
## 6. API Endpoints Reference

| Method | Endpoint | Auth | Role | Description |
|---|---|---|---|---|
| **GENERAL** |
| |
| **AUTH** |
| POST | `/auth/register` | ❌ | Any | Create a new account |
| POST | `/auth/login` | ❌ | Any | Login and get JWT token |
| **FILES** |
| POST | `/files/upload` | ✅ | Any | Upload a file — returns `file_id` |
| GET | `/files/{file_id}` | ✅ | Any | Get file metadata |
| GET | `/files/{file_id}/download` | ✅ | Any* | Download the actual file |
| **TASKS** |
| POST | `/tasks/` | ✅ | Staff | Create a task (lab / assignment / project) |
| GET | `/tasks/` | ✅ | Any | List tasks — students auto-filtered by cohort + major |
| GET | `/tasks/{task_id}` | ✅ | Any | Get a single task with full details |
| DELETE | `/tasks/{task_id}` | ✅ | Professor | Delete a task and all linked data |
| **RUBRICS** |
| POST | `/tasks/{task_id}/rubrics/suggest` | ✅ | Staff | AI suggests a rubric from the task spec |
| POST | `/tasks/{task_id}/rubrics/create` | ✅ | Staff | Staff manually creates a rubric |
| POST | `/tasks/{task_id}/rubrics/refine` | ✅ | Staff | AI refines an existing rubric based on staff feedback |
| PATCH | `/tasks/{task_id}/rubrics/status` | ✅ | Professor | Accept or reject a rubric |
| GET | `/tasks/{task_id}/rubrics` | ✅ | Staff | List all rubric versions for a task |
| **SUBMISSIONS** |
| POST | `/submissions/` | ✅ | Student | Submit work for a task (text or file) |
| GET | `/submissions/my/{task_id}` | ✅ | Student | View all own submissions for a task |
| PATCH | `/submissions/{submission_id}/confirm` | ✅ | Professor | Confirm or override the final grade |
| GET | `/submissions/{submission_id}` | ✅ | Any* | Get full submission details |


> \* Students have restricted access — they can only view their own files and submissions.


## 7. Role Permission Summary

| Action | Student | TA | Professor |
|---|---|---|---|
| Register / Login | ✅ | ✅ | ✅ |
| Upload file | ✅ | ✅ | ✅ |
| Download reference file | ✅ | ✅ | ✅ |
| Download own submission file | ✅ | ✅ | ✅ |
| Download any file | ❌ | ✅ | ✅ |
| Create task | ❌ | ✅ | ✅ |
| Delete task | ❌ | ❌ | ✅ |
| Suggest rubric (AI) | ❌ | ✅ | ✅ |
| Create rubric manually | ❌ | ✅ | ✅ |
| Refine rubric (AI) | ❌ | ✅ | ✅ |
| Accept / Reject rubric | ❌ | ❌ | ✅ |
| Submit work | ✅ | ❌ | ❌ |
| View own submissions | ✅ | ❌ | ❌ |
| Trigger AI grading | ❌ | ✅ | ✅ |
| Confirm final grade | ❌ | ❌ | ✅ |
| Use chatbot | ✅ | ❌ | ❌ |
| View analytics | ❌ | ✅ | ✅ |

---

## 8. Error Reference

| Status | Meaning | Common Cause |
|---|---|---|
| `400` | Bad request | Invalid task type, empty file, missing content |
| `401` | Unauthorized | Token missing, expired, or invalid |
| `403` | Forbidden | Your role cannot perform this action |
| `404` | Not found | Task, file, submission, or rubric ID does not exist |
| `422` | Validation error | Missing required field (e.g. `reference_file_id` for a lab, `student_number` for a student) |
| `502` | AI error | LLM returned an invalid response — retry |
| `503` | AI unavailable | All LLM providers are down — retry later |
