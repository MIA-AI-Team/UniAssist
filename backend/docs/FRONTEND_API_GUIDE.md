# UniAssist frontend API guide

This is the public integration contract for the main FastAPI backend and its Next.js frontend.
Use this together with [AGENTS.md](../../AGENTS.md) for product meaning.
The generated OpenAPI snapshot is [backend/openapi.json](../openapi.json).

## Connection and authentication

Root Docker defaults: frontend http://localhost:3000, backend http://localhost:8001,
AI demo http://localhost:8000. The frontend container uses `BACKEND_INTERNAL_URL=http://backend:8000`.
Outside Docker, use `http://localhost:8001`. The AI demo is not the product API.

Direct backend clients use `Authorization: Bearer <JWT>` except for login, registration and health.
Browser code uses the same-origin Next.js layer instead:

| Frontend route               | Behavior                                                                                               |
| ---------------------------- | ------------------------------------------------------------------------------------------------------ |
| POST /api/session            | JSON email/password; backend login; sets encrypted HttpOnly session; returns identity summary, not JWT |
| GET /api/session             | Revalidates via GET /auth/me; returns identity/profile                                                 |
| DELETE /api/session          | Clears cookie; 204; does not revoke JWT                                                                |
| /api/backend/{approved-path} | Forwards only approved route/method combinations to FastAPI                                            |
| GET /api/health              | Frontend liveness                                                                                      |

Mutations require Origin to match APP_URL. Cookies are SameSite=Lax and Secure on HTTPS.
JWT expiry bounds session lifetime. Authenticated responses are private/no-store.
401 clears session and leads to localized login; 403 is a permission failure, not logout.
No automatic mutation retry. After a timeout, inspect refreshed state before repeating the action.
Downloads are proxied with authorization. Never display storage_path as a public URL.

## Agreed academic rules

- Local/demo self-registration supports student, teaching_assistant and professor only. Admins are
  operator-bootstrapped and use account/operations screens, not academic routes. Staff self-selection
  is not production account policy. All academic endpoints reject admin tokens with 403.
- Labs are visible immediately to their cohort/major. scheduled_date is informational, NOT a one-day availability window.
- Labs require reference PDF and scheduled_date; due_date must not precede scheduled_date.
- Submit until due_date, except assignments with allow_late=true may continue after due_date.
- Professor confirmation closes new attempts regardless of late policy.
- Accepted rubric required before submission. Each attempt permanently retains its rubric_id.
- Only the latest pending attempt may be graded, once. Only the latest ai_graded attempt may be confirmed.
- Individual projects use require_team=false and no team ID. Team-required projects require an
  accepted, staff-approved roster; attempts and grades remain individually owned.
- Students cannot override their cohort/major via filters or guessed IDs.
- Rubric and attempt history is preserved.
- Grading is synchronous. Competing submission/review operations return 409 while the transaction holds its lock.
- Unconfirmed student assessment fields are null; only professor confirmation releases content.

## 1. Authentication

### POST /auth/register → 201

Common JSON: name (2–150 characters), email, password (minimum 8 characters), role.

Student fields: student_number (unique), cohort_year, major; optional github_username.
Staff fields: staff_role and department. The persisted staff_role follows the authenticated role.

```json
{
  "name": "Ahmed Mostafa",
  "email": "ahmed@example.com",
  "password": "example-password",
  "role": "student",
  "student_number": "S001",
  "cohort_year": 2027,
  "major": "CS"
}
```

Staff example: role=professor, staff_role=professor, department=CS.
TA uses teaching_assistant for both role fields.
Returns id, name, email, role, message. Registration does not sign the user in.

### POST /auth/login → 200

Body: `{"email":"ahmed@example.com","password":"example-password"}`.
Direct backend response: access_token, token_type=bearer, user_id, role, name.
Do not store this token in browser-accessible storage.

### GET /auth/me → 200

```json
{
  "id": 1,
  "name": "Ahmed Mostafa",
  "email": "ahmed@example.com",
  "role": "student",
  "student_number": "S001",
  "cohort_year": 2027,
  "major": "CS",
  "department": null,
  "github_username": null,
  "profile_version": 1
}
```

No refresh-token, password-reset, email-delivery or backend logout/revocation endpoint exists.

### PATCH /auth/me → 200

JSON: expected_version (current positive profile_version), name (trimmed, 2–150 characters),
optional github_username (student only, null clears; GitHub-shaped 1–39 characters). Unknown fields
are rejected. No self-service email, academic identity or role changes. Returns IdentityResponse.
Every real change increments profile_version; no-op edits do not. Stale edits return 409 account_changed.
The profile screen preserves input on failure; refresh current state before retrying a conflict.

Login verifies password before returning 401 account_suspended. Every authenticated request checks
current database active status and role, not JWT role claims. Suspension blocks existing JWTs and
clears the frontend cookie; reactivation permits a still-valid JWT again. This is not token revocation
and does not cancel already-authorized in-flight work. Identity/role/cohort/major changes reset academic client caches.

## 2. Files

### POST /files/upload → 201

Multipart: file, purpose=reference|submission|other; optional integer task_id.
The legacy submission_id field is accepted in the schema but MUST be omitted/null:
attaching artifacts to existing attempts is rejected with 422 immutable_artifact.

- reference uploads: TA/professor only; valid PDF header and .pdf extension.
- submission uploads: student only, owner preserved; optional task must be accessible.
- Maximum file size is 25 MiB.
- Uploading is not academic submission.
- Original filename is persisted. Historical metadata uses a safe file-ID/type fallback.
- Reference extraction uses only reference uploads, not student content.
- Setting a task's reference through an upload is staff-only.

Response: file_id, file_name, file_type, purpose, size_bytes, uploaded_at.
Phase 5 removes storage_path from public upload/metadata schemas. It was never a download URL.

### GET /files/{id}

Returns file_id, file_name, file_type, purpose, task_id, submission_id, size_bytes, uploaded_at.
size_bytes is null when the stored file is missing; do not invent its size. The UI shows authorized
metadata beside downloads and never renders storage locations. Admins cannot read/download artifacts.

### GET /files/{id}/download

Returns binary attachment with original/safe fallback filename.
Students may access their own files and the designated reference of an accessible task.
Staff may access files for review. Guessing another student's ID is forbidden.

For labs, upload reference with no task_id first; pass its file_id into task creation.
For submissions, upload with purpose=submission, optionally task_id; pass file_id into the submission JSON.
Reusing an attached file is rejected; it never detaches the previous artifact.

## 3. Tasks

### POST /tasks/ → 201 — staff

Common fields: type=lab|assignment|project, title, description, due_date (timezone required),
target_cohort_year, optional target_major and reference_file_id.

```json
{
  "type": "lab",
  "title": "Binary search",
  "description": "Explain and implement binary search.",
  "due_date": "2026-10-02T23:59:00+03:00",
  "target_cohort_year": 2027,
  "target_major": "CS",
  "reference_file_id": 5,
  "scheduled_date": "2026-10-01T10:00:00+03:00"
}
```

Assignment: allowed_file_types (default pdf,zip), allow_late (default false).
Project: default_repo_provider (default github), require_team (default true).
Assignment/project do not require reference_file_id. A supplied reference must be an
unlinked reference upload owned by the creating staff user. Lab references must be PDF.

Returns id, type, title, due_date, created_at. No draft/publish state.

### GET /tasks/ → 200

Query filters: cohort_year, major, task_type, filter_due_tasks.
Student profile cohort/major always replace caller filters. Staff may filter freely.
filter_due_tasks=true means due_date >= now, not “eligible to submit”; late assignments may be omitted.

Each item: id, type, title, description, due_date, target_cohort_year, target_major,
reference_file_id, latest_submission, review_counts.

Student latest_submission is their latest attempt summary or null.
Staff review_counts maps pending/ai_graded/staff_confirmed to latest-attempt counts (missing keys mean zero).
This avoids one history request per dashboard card.

### GET /tasks/{id} → 200

Common task fields plus created_by, created_at and one matching detail object:
lab_details, assignment_details, project_details (others null).
Includes:

```json
{
  "submission_eligibility": {
    "allowed": true,
    "reason_code": null,
    "rubric_ready": true,
    "rubric_total": 25,
    "team_id": null
  }
}
```

Reason codes: student_only, team_required, team_not_approved, team_legacy_review,
grade_confirmed, deadline_passed, rubric_not_ready. team_id identifies the student's active team
when team eligibility is evaluated; an ID alone never means submission is allowed.

Task detail also returns `accepted_rubric`: null when none is accepted, otherwise
`{id, version, total, criteria: [{name, description, max_points, sort_order}]}`.
Students in the task's cohort/major can read these approved expectations before submitting.
Only the currently accepted version is exposed here; pending/rejected versions and staff version
history remain private. Criteria are student-facing content: professors must remove model answers
and private marking notes before approval. There is no automatic answer redaction.
Student task targeting is checked before returning details. Readiness/total expose no hidden answers.

### GET /tasks/{id}/submissions → 200 — staff

Query: latest_only=true (default); optional status=pending|ai_graded|staff_confirmed.
Returns attempt summaries plus student_id, student_name, student_number, newest submitted first.
Set latest_only=false to inspect history. Students receive 403.

### DELETE /tasks/{id} → 204 — professor

Deletes task and related academic records through database cascades, including attempts, rubrics,
file records and reviews. Physical upload bytes are retained; no storage cleanup policy is implied.
Require explicit confirmation in the UI. TA receives 403.

## 4. Rubrics — staff except professor approval

| Method/path                                  | Body                     | Result                                 |
| -------------------------------------------- | ------------------------ | -------------------------------------- |
| POST /tasks/{id}/rubrics/suggest             | none                     | 201 rubric_id, version, status=pending |
| POST /tasks/{id}/rubrics/create              | criteria array           | 201 same fields plus criteria          |
| POST /tasks/{id}/rubrics/refine?rubric_id=N  | staff_feedback           | 201 new pending version                |
| PATCH /tasks/{id}/rubrics/status?rubric_id=N | status accepted/rejected | 200 rubric_id, version, status         |
| GET /tasks/{id}/rubrics                      | none                     | array, newest version first            |

Criteria: name, description, max_points (positive finite number), sort_order.
Manual criteria cannot be empty. Sum max_points to obtain total.

Refine/status support version=N instead of rubric_id; version=0 selects latest for compatibility.
The chosen rubric must belong to the path's task. Prefer rubric_id in frontend code.
Only professor accepts/rejects. Acceptance marks any prior accepted version replaced.
Criteria and versions are never edited in place.

List items: id, version, source=ai_suggested|staff_created,
status=pending|accepted|rejected|replaced, reviewed_at, criteria.
AI suggestions/refinements are new versions. Pending does not mean an accepted grading standard.

## 5. Submissions

### POST /submissions/ → 201 — student

```json
{
  "task_id": 3,
  "submission_text": "My explanation...",
  "file_id": null,
  "team_id": null
}
```

submission_text is a non-null string, default empty.
file_id and team_id are integer-or-null. repository_snapshot_id is an optional positive integer;
use a saved snapshot instead of file_id, never both. The owning student can include explanation text.
Individual tasks reject non-null team_id and do not support repository snapshots.
For team-required projects, omit/null to resolve the student's own approved team, or send the
eligibility team_id; a different ID is rejected. The first successful team-linked submission locks
the roster. Failures do not lock it. Every attempt remains owned and graded individually.
Include nonblank text or a valid file. For files, upload first and retain file_id.
Combined submissions grade both inputs. Assignment extension restrictions apply on submission creation.

Returns submission_id, task_id, attempt_number, status=pending, submitted_at.
Creation and previous-is_latest changes are transactional.
Conflicts/deadlines/missing-rubric errors do not erase prior attempts.

### GET /submissions/my/{task_id} → 200 — owning student

All own attempts, oldest first. Summary fields:
id, attempt_number, is_latest, status, submitted_at, ai_suggested_grade,
final_grade, feedback, total_possible_grade.

Before confirmation, ai_suggested_grade, final_grade and feedback are null.
Status labels: pending → Submitted; ai_graded → Instructor review in progress;
staff_confirmed → Grade released.

### POST /submissions/{id}/grade → 200 — staff

Only latest pending attempt. Uses the associated rubric, not a newly accepted version.
Accepts persisted text-only, file-only and combined content; only the designated task reference
is used for task context. Persists criterion evidence, findings, warnings, total and mock-mode provenance.

Returns submission_id, status=ai_graded, ai_suggested_grade, feedback.
Fetch detail for full evidence. Competing/repeated grading returns 409, not a duplicate evaluation.
On provider/parsing failure no partial grade is released.

### PATCH /submissions/{id}/confirm → 200 — professor

Body: `{"final_grade":23}`.
Grade must be finite, nonnegative and <= the associated rubric total.
Only latest ai_graded attempt may be confirmed.

Returns submission_id, status=staff_confirmed, final_grade, confirmed_by, confirmed_at.
Overrides do not redistribute AI criterion scores. Confirmation closes further attempts.

### GET /submissions/{id} → 200

Staff or owning student (student task access also checked).
Fields: id, task_id, student_id, team_id, team_snapshot, repository_snapshot, file_id, submission_text,
attempt_number, is_latest, status, submitted_at, rubric_id, rubric_version,
total_possible_grade, rubric_criteria, artifacts, ai_suggested_grade, final_grade,
feedback, confirmed_by, confirmed_at, criterion_evaluations, code_reviews, ai_warnings, is_mock.

Artifacts: file_id, file_name, file_type; no storage paths.
team_snapshot: null for individual/historical attempts, otherwise the approved
{team_id, name, version, members: [{student_id, name, student_number, accepted_at}]} captured
at submission. Membership never authorizes another student's attempt or artifact.
Criterion evaluations: criterion_name, score_given, max_points, reasoning.
Code findings: file_path, line_number, severity, finding.

Student response before staff_confirmed: assessment fields are null, but rubric_criteria contains
the approved criteria associated with that attempt. Its rubric ID/version/criteria remain unchanged
when a newer rubric is accepted. Grading expectations are visible independently of assessment release.
Staff can see provisional evidence. After confirmation, the student sees released feedback.
is_mock=true must display a prominent demo/mock assessment notice; null means unknown historical provenance.

## 6. Error behavior

Errors preserve FastAPI detail. Business/service failures also return stable code.
Validation errors retain the standard detail array with loc/msg/type for field mapping.

| Status | Meaning / representative codes                                                                                      |
| ------ | ------------------------------------------------------------------------------------------------------------------- |
| 400    | Invalid business input, final score outside rubric total                                                            |
| 401    | Invalid/missing/expired session                                                                                     |
| 403    | permission_denied, task_forbidden, file_forbidden, submission_forbidden                                             |
| 404    | Missing record/file                                                                                                 |
| 409    | rubric_not_ready, deadline_passed, grade_confirmed, review_in_progress, attempt_not_pending, file_already_submitted |
| 413    | file_too_large                                                                                                      |
| 422    | invalid_input, empty_submission, lab_fields_required, invalid_dates, file_type_not_allowed, team_not_required, team_limit |
| 502    | ai_invalid_response                                                                                                 |
| 503    | ai_unavailable, or frontend backend_unavailable                                                                     |

Do not show raw provider diagnostics as product copy. Translate stable codes, map loc fields,
and retain a translated fallback for unknown errors. Backend unavailability may have an ambiguous
mutation outcome: refresh relevant reads before offering a retry.

## 7. Student tutoring and consent-based sharing

The session/turn routes below require a student token. Sessions are owner-only; staff/admin access is denied.
Task cohort/major access is checked for session creation and every session/turn request.
Tutoring is independent of deadlines, rubric readiness and grade confirmation.

| Method/path | Request | Response |
| --- | --- | --- |
| POST /tasks/{id}/chat-sessions | request_id UUID, language en/ar (default en), optional submission_id | 201 ChatInfo |
| GET /tasks/{id}/chat-sessions | optional before cursor, limit 1–50 (default 20) | items, next_cursor |
| GET /chat-sessions/{id} | none | ChatInfo |
| GET /chat-sessions/{id}/messages | optional before cursor, limit 1–50 (default 20) | items, next_cursor |
| POST /chat-sessions/{id}/messages | request_id UUID, content 1–4000 nonblank characters, retry boolean (default false) | ChatTurnInfo |
| GET /chat-sessions/{id}/legacy-messages | optional before cursor, limit 1–50 | items (id, sender_type, content, created_at), next_cursor |

ChatInfo: id, task_id, submission_id, title, language, created_at, updated_at.
ChatTurnInfo: id, request_id, content, reply, status (pending/completed/failed), error_code,
retryable, is_mock, context_info, ai_metadata, created_at. A messages page contains complete turns in chronological
order; `next_cursor` loads older turns. Sessions are newest-created first.

Context information lists actual materials used: task_id, optional reference_file_id/rubric_version/
submission_id, released_feedback and truncated flags, lab_mode. These are provenance, not proof of cited claims.
ai_metadata stores only provider/model/prompt/engine versions, measured latency and output_sanitized;
older provenance remains null. Legacy user/assistant messages are owner-readable and enter bounded
history; system messages and failed/pending turns do not. Legacy messages are not included in shares.
Use only task instructions, designated public reference, approved rubric and owned submission text.
Assessment feedback enters prompts only after professor confirmation. Model answers are always empty
for lab tutoring; uploaded submission files are not automatically ingested.

Reuse request_id on ambiguous transport failures. Same ID + different content/context returns 409
request_conflict. A completed duplicate replays its result. Failed duplicates do not invoke AI unless
retry=true. One active turn per session; competing turns return 409 chat_busy. Interrupted pending
turns become retryable after their lease expires. At most three attempts per turn, then send a new
question. Defaults: 90-second provider timeout (TUTOR_TIMEOUT_SECONDS, capped at 120), 10 turn attempts
per user/minute (TUTOR_TURNS_PER_MINUTE), at most 40 prior messages/16000 history characters.
Rate/retry limits return 429 chat_rate_limit/chat_retry_limit. Provider errors return 503 ai_unavailable
and leave the question saved. No auto retry or silent mock fallback is introduced by these endpoints.

UI: /{locale}/student/tasks/{id}/tutor?chat={session_id}; optional submission={id} preselects context
when creating a new conversation. Language defaults to the current UI locale at creation and remains
fixed per conversation. Actual mock engine responses are visibly labeled. Markdown/code/math render
without raw HTML, remote images or executable links.

### Snapshot sharing and lab settings

| Method/path | Permission | Request / response |
| --- | --- | --- |
| GET /chat-sessions/{id}/share-preview | Owner student | through_turn_id → completed SharedTurn[] through cutoff, at most 200 |
| POST /chat-sessions/{id}/shares | Owner student | request_id UUID, recipient_email, through_turn_id, preview_turn_ids → 201 ShareInfo |
| GET /chat-sessions/{id}/shares | Owner student | before/limit pagination; includes revoked shares |
| DELETE /chat-shares/{id} | Owner student | 204; idempotent revocation |
| GET /chat-shares | Recipient TA/professor | before/limit pagination; only active shares addressed to this user |
| GET /chat-shares/{id} | Recipient TA/professor | ShareDetail with immutable snapshot; revoked/wrong recipient → 404 |
| GET/PATCH /tasks/{id}/tutor-settings | TA/professor | lab_mode: experiment (default) or coding; labs only |

SharedTurn: id, content, reply, is_mock, created_at. ShareInfo: id, session_id, task_id, title,
student_name, recipient_name, through_turn_id, created_at, revoked_at. ShareDetail adds snapshot.
Creation requires the exact completed turn IDs shown in the preview; changed contents return 409
request_conflict and require a new preview. Requests are deduplicated by session/request_id; retrying
a revoked share does not reactivate it. Unknown/non-staff email → 404 share_recipient_missing;
invalid cutoff → 422 invalid_input; over 200 completed turns → 422 chat_share_too_large.
Recipient access never grants access to the original chat. Later messages are never auto-shared.
Revocation prevents future reads, not screenshots or copies already obtained. Staff UI polls an open
snapshot every 15 seconds; revocation does not claim instantaneous removal from another browser.
Settings apply to future turns and never introduce private model answers into tutoring.

## 8. Private grading guidance and teaching insights

All routes in this section require TA/professor authentication. Students and admins receive 403.
Private guidance is not returned by task detail, rubric or student submission responses.

| Method/path | Request | Response |
| --- | --- | --- |
| GET /tasks/{id}/grading-guidance | before cursor, limit 1–50 (default 20) | GuidanceList: items, next_cursor, newest first |
| POST /tasks/{id}/grading-guidance | request_id UUID, content string up to 12000 characters | 201 GuidanceInfo |
| GET /tasks/{id}/grading-guidance/{guidance_id} | task-scoped version ID | GuidanceInfo |
| GET /tasks/{id}/analytics | none | TaskAnalytics |
| GET /tasks/{id}/analytics/reports | before cursor, limit 1–30 (default 10) | TeachingReportList: items, next_cursor |
| POST /tasks/{id}/analytics/reports | request_id UUID, rubric_id, language en/ar (default en) | 201 TeachingReportInfo |

GuidanceInfo: id, task_id, version, content, created_by, created_at. Every save creates a new immutable
version, serialized per task. Duplicate task/request_id replays the saved version; changed author/content
returns 409 request_conflict. Empty content deliberately disables guidance for future grading. No edits
or individual deletes exist. The latest version at evaluation start is passed only via grading_key.
Submission detail adds grading_guidance_id/version for teaching staff only (null otherwise); historical
evaluations stay null. Fetch the exact task-scoped version for review, never replace it with today's latest.
Grading prompts prohibit copying private solutions into releasable fields, but professor review and
live leakage acceptance remain necessary. No automatic semantic redaction is claimed.

TaskAnalytics: task_id, minimum_group_size, released_count, excluded_count, input_fingerprint, groups.
Select the highest attempt_number confirmed attempt per student; newer pending/AI-only attempts do not
hide a historical confirmed attempt. Invalid historical final grades/totals are counted as excluded.
Groups contain rubric_id/version, student_count, eligible, average/minimum/maximum_percentage,
below_half_count, criteria, severity_counts, mock_assessment_count, unknown_provenance_count.
Minimum group size is max(3, MIN_COHORT_SIZE_FOR_PATTERNS). Below-threshold statistics are null and
generation returns 422 analytics_insufficient. Grades are normalized by associated rubric totals, not 100.
50% and 60% are descriptive bands, not configured academic pass/fail rules.

Criterion statistics: criterion_id, name, generated label (Criterion N), max_points, sample_count,
average_score, low_score_count (below 60%). Match original AI evidence only when the name is unambiguous
and point total matches. Missing/invalid evidence is excluded; means/low counts stay null until the
criterion also meets the minimum. Professor overrides do not change AI criterion scores.

TeachingReportInfo: id, task_id, rubric_id/version, language, input_fingerprint, input_snapshot (the
RubricGroup at generation), result (summary/common_issues/misconceptions/teaching_focus/warnings),
is_mock, ai_metadata, created_at, stale. Report history is immutable and newest-first. The fingerprint
covers released numeric evidence across the task; new/changed releases mark all previous reports stale,
including changes during generation. It contains no student identities or free-text feedback.
No authored task/rubric prose or individual feedback/work/chats/filenames reach analytics; generated
criterion labels map back to staff-visible names in the statistics table. Actual mock report provenance
and mock/unknown source-assessment counts are separate and must both remain visible.

Report generation is synchronous with one active report per task (409 analytics_busy). Reuse request_id
after ambiguous transport failure; an existing result replays without another AI call. Different
author/rubric/language returns 409 request_conflict. Provider failure/timeout creates no successful report;
refresh saved reports before an explicit retry. Default timeout ANALYTICS_TIMEOUT_SECONDS=90, capped120.
The interactive API supports at most 10000 released students per task (422 analytics_limit). The AI
package may bound prompt grade rows; its warnings are preserved. Computed statistics use all valid rows.
Provider diagnostics are sanitized; schema-invalid output is 502, unavailable provider/timeout is 503.

## 9. Project teams and remaining planned capabilities

### Implemented project-team API (Phase 3)

These routes apply only to projects with require_team=true. All reads require current task access.
Admin has no team permissions. All paginated lists return {items, next_cursor}, newest ID first,
with optional before (positive ID) and limit (1–50, default 20).

| Route | Permission / contract |
| --- | --- |
| POST /tasks/{task_id}/teams | Student; {request_id: UUID, name: 2–150 characters}; 201 TeamInfo |
| GET /tasks/{task_id}/teams | Student sees own/created/pending-invited teams; staff sees all; optional status filter |
| GET /teams/{id} | Staff, creator, active member or pending invitee; unrelated students get 404 |
| GET /teams/{id}/history | Staff, creator or active member; pending invitees cannot read historical rosters |
| POST /teams/{id}/actions | {request_id: UUID, expected_version: positive integer, action, conditional field}; 200 {team_id, version} |
| GET /team-invitations | Student's own pending invitations in currently accessible tasks |
| POST /team-invitations/{id}/respond | Invited student; {request_id, expected_version, decision: accept or decline}; 200 {team_id, version} |

TeamInfo: id, task_id, name, created_by (nullable for legacy), status, version, locked_at,
members, invitations (pending only), actions, unavailable_reason. Member fields match team_snapshot.
Invitation fields: id, team_id, task_id, team_name, student_id, name, status, created_at.
History items: id, action, version, roster (frozen TeamSnapshot), created_at. Actor/request auditing
is persisted internally; neither private work nor grades are exposed through team routes.

Actions and required extra field:

- Owner: invite (student_number, exact match), remove (student_id, not owner),
  cancel_invitation (invitation_id), request_approval, archive.
- Active non-owner member: leave.
- TA/professor: approve or reject, only while awaiting_approval and after all invitees accepted.
- Unrelated fields/unknown actions are rejected by validation. Mutations return receipts, then UI refreshes.

Lifecycle: draft → awaiting_approval → approved/rejected. Roster/invitation changes return to
draft and clear approval. Archive releases active memberships and cancels pending invitations,
retaining history. Creator consent is recorded on creation; invitees explicitly accept. One active
membership per student/task is DB-enforced. Pending invitations do not reserve membership.
Maximum 20 members plus pending invitations; no minimum beyond the creator. Invitees must match
cohort/major, and approval/submission rechecks all members. Exact student numbers avoid exposing
a searchable student directory. Display the consent/privacy preview before accepting.

Every roster action checks expected_version. UUID receipts deduplicate identical retries;
reusing a UUID with different data returns request_conflict. Refresh after uncertain responses,
never retry automatically. Roster mutations and team submissions share a transaction-scoped task
lock. Approval applies to its exact version; the first successful team-linked submission freezes
membership and saves the approved roster on each individual attempt. No shared grading or access
to teammate submissions, files, grades, or original tutoring conversations is granted.

Team errors: 409 team_required, team_not_approved, team_legacy_review, team_locked, team_archived,
team_changed, team_consent_required, team_membership_exists, team_invitation_exists, request_conflict;
403 team_forbidden/permission_denied/task_forbidden; 404 team_student_unavailable/not_found;
422 team_not_required/team_limit/validation. Preserve detail and translate code.

Legacy teams are read-only/review-blocked; old consent, approval and submission snapshots are not
fabricated. Existing membership slots remain reserved. A separate reviewed remediation workflow
is not available in this release. Duplicate historical task/student memberships stop migration
before changes, preserving all records for review.

### Implemented public GitHub evidence (Phase 4)

Only team-required projects are supported. Academic roles can read repository links if staff or an
active team member; a pending invitation alone grants no access. Snapshot reads/downloads are
restricted to the owner or teaching staff with task access, never teammates by membership alone.
All new lists use {items,next_cursor}, before (positive ID) and limit (1–50, default 20).

| Route | Contract |
| --- | --- |
| GET /teams/{id}/repositories | Link history, newest first |
| POST /teams/{id}/repositories | Student member of approved team; {request_id: UUID, repo_url}; 201 RepositoryInfo |
| GET /repositories/{id} | RepositoryInfo, including actions and unavailable_reason |
| POST /repositories/{id}/actions | {request_id, expected_version, action}; 200 {repository_id,version} receipt |
| GET /repositories/{id}/commits | Imported commit metadata and staff-reviewed attribution |
| GET /repositories/{id}/history | Immutable proposal/approval/sync/attribution events |
| POST /repositories/{id}/snapshots | Owning student; {request_id,commit_sha}; 201 SnapshotInfo |
| GET /repository-snapshots/{id} | Owner/staff SnapshotInfo |
| GET /repository-snapshots/{id}/download | Owner/staff saved ZIP, attachment, private/no-store |

RepositoryInfo: id, task_id, team_id, repo_url (null for unverified legacy links), full_name,
status (pending/approved/rejected/superseded/legacy), version, approved_team_version,
last_synced_at, sync_error, partial_history, is_fixture, actions, unavailable_reason.
Proposals accept only canonical owner/repository or https://github.com/owner/repository URLs
(optional .git suffix). Public identity is verified and pinned by GitHub's numeric repository ID;
renamed, private, missing or replaced repositories require a new reviewed proposal. Up to five
pending proposals per team. No credentials, private repositories or arbitrary upstream URLs.

Actions:

- approve/reject: TA/professor only, with current approved team. Approval replaces any previous
  active link without deleting history; approved_team_version pins the roster. Roster changes require
  repository reapproval. A superseded or legacy link cannot be reactivated; propose a new link.
- sync: approved current-roster repository; member or staff. Reads public metadata and at most 100
  recent default-branch commits; never follows user-supplied pagination URLs. Imported SHA uniqueness
  prevents duplicates. partial_history=true when 100 rows were returned (conservative) or not yet synced.
  History is not comprehensive; fewer rows do not prove complete contributions. Old commits are retained.
- attribute: TA/professor only; extra commit_id and student_id (null clears attribution). Choose a
  current consented member. Never infer identity from username matching or use counts as effort scores.
  Corrections record actor, timestamp and old/new student IDs without changing grades.

Every action checks expected_version. Repeated identical request UUIDs replay receipts; reuse with
different data returns request_conflict. Failed sync persists a sanitized sync_error but keeps the last
successful timestamp and commits; it does not record success or consume a successful receipt. Explicit
retry uses refreshed state. No automatic mutation retry. UI preserves URL/SHA/explanation inputs.

CommitInfo: id, commit_hash, author_name, author_github_username (empty when absent), message (bounded),
committed_at (UTC), student_id, attributed_by, attributed_at. Unreviewed legacy student IDs are not
presented as verified. History items: id, actor_id, action, version, details, created_at. All timestamps
are formatted locally by the frontend. User-authored commit text is displayed as text, not executed HTML.

SnapshotInfo: id, repository_id, commit_sha, created_at, provenance. Provenance contains task_id,
team_id, repository_id, repo_url, github_id, commit_sha, archive_sha256, compressed_bytes, captured_at,
team_version, repository_version, is_fixture, files, omitted_files and frozen selected-commit attribution.
Manifest files contain path, size, sha256 and included (eligible initial AI input). Snapshot capture:

1. Check membership, repository approval, rubric/deadline/individual confirmation eligibility.
2. Verify public numeric repository identity and a full lowercase 40-character commit SHA.
3. Download via validated GitHub archive redirects; reject unsafe archive entries and size excesses.
4. Store the original ZIP bytes, digest and provenance transactionally in PostgreSQL after rechecking
   eligibility. This is staged evidence, not an attempt, and does not yet lock the team roster.
5. Submit repository_snapshot_id via POST /submissions/; backend checks owner, task/team, active link
   and approval version again. Same rules and first-submission roster locking as text/file attempts.

Limits: 25 MiB compressed, 100 MiB expanded, 1,000 files, at most 2,000 archive entries. No symlinks,
special files, duplicate/case-colliding paths, traversal, encryption or unsupported compression.
Nothing is extracted to disk or executed; no dependencies/hooks/submodule fetches. UTF-8 supported
code/text files up to 512 KiB each, 4 MiB combined, enter the existing bounded evaluation pipeline.
Other files remain in the saved archive and are marked excluded. Later pipeline limits also produce
assessment warnings. A snapshot without supported readable content is rejected.

Submission detail exposes repository_snapshot to its owner/staff independently of grade release;
assessment findings remain hidden until professor confirmation. Saved bytes are digest-checked and
used for grading without GitHub, even after branch/source/link changes. Show the pinned SHA beside
findings. Attribution corrections never rewrite captured provenance. A staged snapshot may be reused
for a new attempt by its owner while eligibility/link/roster checks hold. No automatic cleanup occurs.

Errors preserve detail/code: 422 repository_url/repository_limit/repository_unsafe_archive/
repository_empty/repository_artifact_conflict; 413 repository_size; 409 repository_identity/
repository_exists/repository_not_approved/repository_changed/repository_integrity/request_conflict;
429 github_rate_limit; 502 github_unsafe_redirect/github_invalid_response; 503 github_unavailable.
Normal 403/404 access failures still apply. GitHub failure never prevents text/file submission.

GITHUB_FIXTURE_MODE is server-only, opt-in and requires MOCK_MODE=true. Only isolated verification
Compose enables it; its two fixed fixture repositories are visibly marked is_fixture=true, separately
from AI is_mock. There is no silent fallback to fixtures. Live public GitHub/AI acceptance is separate.

### Still planned/deferred

No main API routes exist for communication
monitoring, generated practice or email. AI-package capabilities and database
tables are not public APIs. Do not implement navigation that implies these are live.

See [the integration plan/checkpoint](BACKEND_UI_INTEGRATION_PLAN.md) for the agreed expansion.

## 10. Account administration and operations (Phase 5)

Routes below require an active admin; students/TAs/professors receive 403. Admin authority does
not grant access to any academic API. UI: /{locale}/admin, /admin/users/{id}, /admin/audit and
/admin/metrics. /{locale}/profile is available to all active roles.

| Route | Contract |
| --- | --- |
| GET /admin/users | q (optional, max 150 characters): literal case-insensitive name/email/student-number search; before and limit (1–100, default 30); items and next_cursor |
| GET /admin/users/{id} | IdentityResponse plus is_active and created_at; never password hash or JWT |
| PATCH /admin/users/{id} | expected_version required; only explicitly supplied allowed fields change; returns updated AccountInfo |
| GET /admin/audit | before/limit pagination; items contain id, actor_id (null for operator bootstrap), action, target_type, target_id, fields (names only), created_at |
| GET /admin/ai-metrics | days=1–365 (default 30); since plus operation/provider groups |

Admin correction fields: name (2–150), email, is_active; student_number (1–50), cohort_year (1–9999),
major (1–255), github_username (nullable GitHub-shaped 1–39) on student accounts; department (nullable,
1–255 when present) and role=teaching_assistant|professor on existing staff accounts. Unknown keys
or wrong account-class fields return 422. No student↔staff/admin conversions, deletion, passwords or
permission-level edits. Empty department/GitHub are sent as null. Versioned no-op requests do not
increment history. Errors: 409 account_changed, account_identifier_taken or last_active_admin;
422 account_role_restricted. Refresh before retrying conflicts; never silently apply stale corrections.

Corrections affect future task access. Historical submission/approved-roster/attribution snapshots
are not rewritten; GitHub edits never reattribute commits. Admin changes, profile edits, bootstrap,
rubric decisions, grade confirmation, team actions, repository decisions/attribution and chat sharing/
revocation append content-free audit rows in the same transaction. Attribution targets the commit ID.
No pre-Phase-5 event backfill or prior field values. IDs remain even when a task is later deleted.
Detailed repository attribution history remains teaching-staff/team-scoped, not an admin content API.

AI groups include calls, errors, incomplete, average_latency_ms (completed calls only), mock_calls,
unknown_mock_calls, truncated_calls and unknown_truncation_calls. Each application AI invocation
creates a durable started record before provider execution, then success/error plus measured latency.
Writes use separate transactions so academic rollback does not erase failures; interrupted processes
may leave started rows. Cancellation counts as an application error, not proof a provider stopped.
No identities, prompts, responses, exception messages or arbitrary metadata are stored. Provider codes
are allowlisted; missing provenance stays unknown. Actual mock usage comes from the executing engine,
including no-key mock mode. Provider provenance is worker-thread-local so simultaneous calls cannot
overwrite one another's provider/model. Truncation combines backend tutoring budgets and engine-reported budgets.
Counts are not provider-attempt/billing metrics. Records begin at deployment of Phase 5.

Public admin registration now returns 422. Existing admin rows are preserved and active at migration;
operators must review historical accounts created under the old demo policy. Bootstrap new admins
with `docker compose exec backend python -m backend.bootstrap_admin`; it prompts for name/email
and a confirmed password (at least 12 characters), refuses existing emails, and never converts users.
Bootstrap/status/profile edits share a short transaction lock. Two simultaneous suspensions cannot
remove the last active admin. No administrative account is automatically created or password printed.

## 11. Contract regeneration and verification

Run the backend, then in frontend: `npm.cmd run api:types`.
Default schema URL is http://localhost:8001/openapi.json; override API_SCHEMA_URL as needed.
Commit both generated snapshot and transport declarations with contract changes.
See [README](../../README.md) for Docker, isolated PostgreSQL checks, component tests and Playwright.
