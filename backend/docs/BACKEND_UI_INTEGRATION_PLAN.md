# UniAssist — complete backend-to-UI integration plan

This is the canonical expansion plan and resumption checkpoint. Preserve it across sessions.
The original root `plan.md` describes the first frontend release, not this expansion.

## Resume here

- Current phase: **Phase 5 implemented and isolated mock/fixture-verified; all five expansion phases complete**.
- UI copy follow-up (2026-09-22): removed the local/demo staff self-selection notice from auth and
  workspace screens in both languages at the user's request. Mock-assessment provenance remains.
- Latest UI follow-up (2026-09-22): **Academic Review Desk direction implemented** from
  `Humazine_UI.md` using humanize-ui. Semantic tokens/local bilingual fonts, task rows, staff review
  navigation, attempt records and feedback-first student results. 54 frontend tests, TypeScript,
  lint, production build and all 16 real-backend browser journeys pass. Only the isolated verification
  frontend was rebuilt/restarted. See the UI follow-up checkpoint at the end of this file.
- Latest follow-up (2026-09-21): **Academic Markdown/math and live staff previews implemented**.
  52 frontend tests, TypeScript/lint, production Docker build and nine affected browser journeys pass.
  English/Arabic mobile equation screenshots inspected; long equations scroll inside their panels.
  Only the isolated verification frontend was rebuilt/restarted. See the follow-up checkpoint below.
- Phase 5 baseline checks: 48 backend/PostgreSQL tests, 21 frontend tests, 47 AI-package tests passed (two opt-in
  live tests skipped); TypeScript/lint and production Docker build passed. Ten browser journeys pass,
  including profile failure recovery, account correction/suspension/reactivation and Arabic operations.
  Final regression passes after identity refresh/attribution audit refinements. Additional AI tests
  cover thread-local provider provenance and truncation. Account/audit/AI-operation restart checksums
  match exactly; all isolated services are healthy.
  No normal application volumes were changed. Live GitHub/AI remain unverified.
- Database head: f8a20260919 (account status/version and audit/AI operations). Only isolated verification databases have been upgraded.
- Read this file, root `AGENTS.md`, and `FRONTEND_API_GUIDE.md` before continuing.
- Workspace has substantial existing uncommitted implementation and user edits. Preserve them.
- Do not inspect/print secrets from `.env`, overwrite environment files, reset databases, or delete volumes.
- Test only the isolated `uniassist-verify` Compose project unless explicitly changing the normal stack.
- Root `AGENTS.md` is ignored by the user's existing `.gitignore`; this tracked-path document is the
  durable handoff. Do not change that ignore rule without instruction.

### Progress and evidence

Phase 5 implementation: profile/admin screens, strict API contracts, operator-only bootstrap,
per-request suspension/current-role checks, concurrent last-admin protection, content-free audit
and separately committed AI-call records. File metadata omits storage paths. Audit/AI records begin
now, without fabricated backfills. Existing admins remain active pending operator review. Account
corrections never rewrite historical rosters/submissions/attribution. See the final checkpoint below.

Phase 4 completion summary: additive repository/event/snapshot migration and typed APIs
are implemented; safe public-only GitHub client (23 targeted tests passing), proposal/approval,
bounded sync, attribution corrections, private archive capture and stored-only grading are wired.
Repository HTTP and concurrency/provider-failure tests pass. UI/routes/BFF/catalogs and generated
contracts are implemented; TypeScript/lint, frontend and migration tests pass. All nine browser
journeys pass; Arabic mobile screenshot inspected. Phase 4 restart checksums match.
Keep tests separate from persistence comparisons.
New code: services/github_client.py, repository_service.py; schemas/routers/repository.py;
frontend/features/repositories.tsx. Isolated Compose explicitly sets GITHUB_FIXTURE_MODE=true
with MOCK_MODE=true; all fixture evidence is labeled. Normal Compose remains real public GitHub.

Phase 3 checkpoint: migration, typed team/invitation/history APIs, consent/version checks,
approval invalidation, individual submission snapshots and roster locking are implemented.
English/Arabic screens and BFF routes pass production build and browser verification. Dedicated
team lifecycle, concurrent acceptance/submission, migration preservation/conflict and privacy tests pass.
Only team-required projects use this workflow. Owners can archive unlocked teams; members can
leave before locking. Maximum 20 members plus pending invitations; no invented minimum size.
Legacy teams retain members without fabricated consent, remain review-blocked/read-only, and
reserve membership slots. A reviewed legacy remediation workflow is not implemented.

| Phase | State | Evidence / remaining work |
| --- | --- | --- |
| 0. Reconcile contracts | Complete | Plan/checkpoint saved; current academic rules and model-only foundations reconciled |
| 1. Tutor and sharing | Implemented, mock-verified | Tutor/shares/settings/legacy provenance; 11 backend, 11 frontend, 44 AI, six browser tests; restart persistence passed, live AI unverified |
| 2. Teaching tools/insights | Implemented, mock-verified | Private guidance, released-only rubric groups and bilingual reports; 14 backend, 13 frontend, 45 AI tests, seven browser journeys and restart persistence passed; live checks skipped |
| 3. Teams | Implemented, mock-verified | 20 backend, 15 frontend, 45 AI tests, eight browser journeys; restart persistence passed; legacy records remain review-blocked |
| 4. Public GitHub | Implemented, fixture/mock-verified | 47 backend, 17 frontend, 45 AI tests, nine browser journeys and restart persistence pass; live GitHub unverified |
| 5. Admin/profiles/operations | Implemented, mock-verified | 48 backend, 21 frontend, 47 AI, ten browser tests; build and account/audit/operations restart persistence pass |

Update this table and the checkpoint at the end of each implementation milestone. Distinguish
source implementation, automated verification, and live-provider acceptance.

## 1. Goal and confirmed decisions

Connect every existing backend foundation to an appropriate user experience, adding missing
APIs and workflows. Preserve the working grading lifecycle and English/Arabic Dockerized app.

- Students receive task-specific AI guidance whenever the task is accessible, including after
  submission, deadlines and grade release. Submission eligibility is independent.
- Tutoring provides hints, explanations and debugging guidance, not completed assessed work.
- Conversations are private unless their student owner explicitly shares one with staff.
- Students create teams and invite classmates. All invitees accept before a TA/professor approves
  the complete roster. Changes require reapproval and stop after the first team-linked submission.
- GitHub integration initially supports public repositories only.
- Cohort AI insights use released grades only.
- Student, TA and professor self-registration remain available for this local/demo application.
- Professor-only rubric approval and grade confirmation remain unchanged.

### Coverage inventory

| Foundation | Starting state | Destination |
| --- | --- | --- |
| Authentication/tasks/rubrics/submissions/files | Working APIs and core UI | Preserve; close metadata/usability gaps |
| Socratic tutor | AI function, no main API/UI | Task-linked tutoring |
| Lab assistant | AI function, no main API/UI | Lab guidance in the tutor workspace |
| Chat sessions/messages/sources | Models/helpers | Persistent conversations and explicit sharing |
| Cohort analytics | AI function, no main API/UI | Staff task insights |
| Teams/membership | Models only | Invitations, approval, individual team-context submissions |
| Repositories/commits | Models only | Public linking, synchronization and evidence |
| Code review | Submission evaluation integrated | Frozen repository evidence |
| Admin accounts | Model only | Limited account administration |
| AI metrics/provenance | Partial, mostly in-memory | Sanitized operational overview |
| Reference chunks/embeddings | Text chunks, not vectors | Tutor materials, not a vector dashboard |

Complete integration does not mean exposing every table as a screen. Infrastructure supports
useful workflows. Email, push notifications, communication monitoring, generated practice,
private repositories, automatic contribution scoring, courses/enrollment and extra task types remain deferred.

## 2. Implementation phases

### Phase 0 — contracts and coverage

- Inventory each main endpoint and AI facade operation: role, UI consumer, tests, and state
  (existing/planned/implemented/verified).
- Reconcile AGENTS, API guide and database design. Remove one-day lab visibility, TA rubric
  approval claims, and obsolete submission/reference-file descriptions.
- Preserve public approved rubric expectations and immutable historical attempt rubrics.
- Separate proposed from implemented endpoints. Model/AI-function existence is not availability.
- Keep browser → authenticated Next.js API → FastAPI → PostgreSQL/in-process AI architecture.
- Preserve session security, allowlists, server authorization, no shared caching, upload recovery
  and explicit mutation retries.

### Phase 1 — persistent tutoring and lab assistance

Student UI:

- Add “Ask AI tutor” on task and submission pages, a task conversation list, new conversation,
  history, composer and continue-later support.
- Optional owned-submission association. Task conversations work without a submission or approved rubric.
- Labs use lab assistance; assignments/projects use the Socratic tutor. Staff select experiment
  guidance or coding hints; existing labs default to experiment guidance.
- Deadline/confirmation never disables tutoring while task access remains allowed.
- English/Arabic conversation language is explicit. Interface switching does not rewrite history.
- Show pending, failed, retry, mock and context-limit states. Preserve unsent input.
- Render Markdown/code/math safely with react-markdown, raw HTML disabled, safe links and no external images.

Backend/AI boundary:

- Reuse chat tables; add durable request IDs, turn state, language and safe provenance.
- Construct context server-side from accessible task, designated public reference, approved criteria,
  and optionally selected owned submission. Include assessment only after professor confirmation.
- Never include another student's work, private grading keys, draft rubrics or unreleased evaluations.
- Lab `model_answers` stays empty. Never rely on prompt instructions to hide secrets supplied to the tutor.
- Do not reuse the existing generic task-context function requiring an accepted rubric for tutoring.
- Load bounded history from PostgreSQL; ignore browser-supplied roles/history/identity/context.
- Initial transport: synchronous non-streaming replies, bounded provider timeout, no new queue service.
- Client request IDs deduplicate turns; one active turn per conversation. Completed duplicates replay
  the result. Failed/interrupted turns support explicit recovery without duplicate visible messages.
- Map chat/analytics provider errors; no successful-looking fallback after provider failure.
- Configurable per-user rate/message limits and context budgets.
- Persist actual materials used. Do not invent citations or relevance scores.

Sharing:

- Owner selects staff recipient, previews conversation and shares a read-only snapshot through a
  selected last message. Future messages are not automatically shared.
- Owner can revoke future access (cannot retract what was already seen).
- Staff see only snapshots explicitly addressed to them; no student impersonation/chat continuation.
- Sharing has no grading side effects. Admin operations never imply private-transcript access.

### Phase 2 — staff teaching tools and released-result insights

- Separate staff-only immutable grading-guidance versions from public instructions/PDFs/rubrics.
- Record the guidance version used by an evaluation; pass only to grading via `grading_key`, not
  tutoring or rubric generation. Preserve history; do not invent backfills.
- Warn that released assessment must not reproduce private solutions; add live leakage acceptance checks.
- Staff task Insights tab: deterministic released-result statistics separate from generated suggestions.
- Use latest professor-confirmed attempt per student; exclude pending/AI-only results.
- Normalize grades by actual total; group criterion stats by rubric version. Overrides never rewrite AI
  criterion scores; labels retain that distinction.
- AI receives numeric grade snapshots and aggregate criterion/severity stats, not identities, chats,
  raw work, filenames or free-text student feedback.
- Minimum three qualifying students per analyzed group (existing configurable threshold); otherwise
  show insufficient results. No rankings, individual-risk labels or automated decisions.
- Persist reports with input fingerprint, rubric versions, time, language and mock provenance.
  Mark stale after new releases; generation is an explicit staff action.

### Phase 3 — teams with accepted invitations and staff approval

- Student project team creation, exact-student-number invitations and in-app invitation inbox.
  No university-wide searchable student directory.
- Enforce project cohort/major and one active membership per student/task.
- Draft → awaiting approval → approved/rejected. Approval requires all invited members accepted
  and an unchanged complete roster; either TA or professor can decide.
- Before first submission, roster changes invalidate approval. After first team-linked submission,
  roster is locked. Preserve membership snapshots.
- Team-required submissions need approved membership; return precise eligibility reasons.
- Each member submits their own attempt/explanation and receives an individual grade. No automatic
  teammate submission creation or grade release.
- Existing rubric/deadline/resubmission rules remain. Teammates do not gain access to private artifacts,
  grades or chats by membership alone.
- Legacy teams require review; do not fabricate historical consent or approvals.

### Phase 4 — public GitHub and reproducible evidence

Implementation decisions: repository approval is tied to the currently approved team version;
roster changes require repository reapproval too. Staff approval replaces the previous active link
without deleting it. Commit-to-student attribution is explicit, staff-confirmed and audited; never
inferred as effort. Capture a private snapshot before submission (repository + full SHA), then use
repository_snapshot_id instead of file_id. Compressed bytes, digest and manifest live in PostgreSQL
for transactional, restart-safe evidence; no checkout/extraction to disk, code execution or dependencies.
Provider access is unauthenticated/public-only. Isolated verification may enable clearly labeled
deterministic GitHub fixtures; no private token, arbitrary upstream host or silent fixture fallback.

- Approved project-team workspace: member proposes repository, staff approves before use as evidence.
- Team-project scoped initially, matching existing model. Individual projects retain text/file submissions.
- One active repository per team; preserve historical links/snapshots after replacement.
- Canonical public GitHub identifiers only. Server requests and archive redirects restricted to approved
  GitHub hosts, never arbitrary URLs.
- Explicit sync of metadata and bounded recent commits. Show sync time, unavailable/private repo,
  rate limits and partial history. Unique repository+commit hash prevents duplicate imports.
- GitHub username attribution is unverified until staff confirm/correct. Commit counts never grade effort.
- Student selects commit SHA for repository-based submission. Preserve snapshot and provenance so
  branch changes/removal cannot change previously submitted evidence.
- Reuse parsing/evaluation; never execute code, install repository dependencies or run hooks.
- Limits: 25 MiB compressed, 100 MiB expanded, 1,000 files, traversal/symlink protections.
- Normal file/text submission remains available on GitHub failures. Sync does not trigger grading.
- Show SHA provenance beside findings; staff explicitly evaluate each latest pending attempt.

### Phase 5 — profile, admin and operations

- Profile permits name/GitHub username changes only; students cannot edit academic identity or role.
- Admin account search, profile correction, suspension/reactivation and TA↔professor changes.
- No hard account deletion or student↔staff conversion in this release.
- Operator-only admin bootstrap; close public admin registration while keeping demo academic roles.
- Suspension checked on login and every authenticated request, including existing JWTs.
- Protect last active admin. Audit admin changes, approvals, attribution corrections and chat shares/revocations.
- Admin aggregate AI metrics: calls/errors/latency/provider/operation/truncation/actual mock usage.
- Persist sanitized operational records across restarts; never log prompts, replies, keys or transcripts.
- Complete file metadata display, never display storage paths; authorized downloads only.

## 3. Public interfaces and persistence

Preserve existing routes/shapes unless explicitly changed. New endpoints need typed schemas and
regenerated frontend transport types. These are proposed until verified in the checkpoint.

| Capability | Main-backend interface |
| --- | --- |
| Profile | PATCH /auth/me for permitted fields |
| Tutor sessions | GET/POST /tasks/{id}/chat-sessions; GET /chat-sessions/{id} |
| Turns | GET/POST /chat-sessions/{id}/messages; explicit failed-turn retry |
| Sharing | POST /chat-sessions/{id}/shares; owner revoke; recipient staff list/detail |
| Teaching configuration | Staff task tutoring settings; versioned grading-guidance read/create |
| Insights | GET /tasks/{id}/analytics; explicit report generation |
| Teams | Task list/create, team detail, invite/respond, approval request/staff decision |
| Repositories | Team proposal, staff approval, details/commits/sync |
| Repository submission | Extend submission create with approved repository + SHA |
| Admin | Users list/detail/update, audit log, aggregate AI metrics |

- Derive identity, membership, access and context from backend state.
- Submission accepts upload OR repository snapshot, plus optional text, never competing artifact sources.
- Paginate new lists, chat history and commit reads. Read models expose available actions/reason codes.
- Distinguish auth, permission, conflict, unavailable context, rate limit and provider failures.
- Add only explicit BFF route/method entries. Never expose AI demo routes directly to the browser.
- Additive Alembic migrations for turns/shares, invitations/approvals, snapshots, guidance/reports,
  account status and audits. Preserve existing records. Preflight conflicts rather than deleting rows.
- Text chunks remain text chunks. Semantic vector search is not required for this integration.

## 4. Verification and acceptance

Each phase needs real FastAPI/PostgreSQL tests and browser coverage before it is marked verified.

- Regress existing grading, rubric visibility, role, auth, artifact and Arabic flows.
- Tutor before submission/rubric, resume after reload/restart, continue past deadline/release.
- Context excludes private keys, other students and unreleased evaluations.
- Duplicate/concurrent sends, failures, timeouts/restarts preserve input and do not duplicate messages.
- Private/unshared access denied to staff/admin; snapshots/revocation enforce consent.
- Safe mixed-language Markdown/code/math and hostile-content rendering.
- Insights enforce released-only, rubric grouping, threshold and stale-report rules.
- Invitations/approval enforce eligibility, uniqueness, accepted roster and concurrency.
- Historical team membership fixed; grading remains individual.
- GitHub URL/redirect/archives safe, sync idempotent, evidence survives branch changes/unavailability.
- Suspended tokens rejected; last-admin protection; no admin transcript access.
- Fresh/upgrade migrations and Docker persistence without deleting volumes.
- Keyboard, responsive/RTL, empty/loading/error/permission states and input recovery per new flow.

Mock AI is the deterministic baseline. Live-provider smoke checks (both languages, hint-only behavior,
answer leakage) are required before claiming real tutoring readiness; report skipped checks honestly.

## 5. Preservation and rollout

- Maintain this plan's checkpoint with changed files, schema head, commands/results, blockers and exact
  next actions. A future session must not have to reconstruct progress from conversation history.
- Update AGENTS, API guide and database design for each implemented rule. Preserve original plan history.
- Implement ordered vertical slices; no placeholder successful screens for nonexistent APIs.
- Additive migration-gated Docker startup, server-only secrets, pinned new frontend dependencies.
- Deterministic GitHub fixtures rather than required external accounts in test suites.
- Demo self-registration and broad existing staff access are not institutional production authorization.
- Completion: task-aware tutoring/selective sharing; approved teams; individual reproducible submissions;
  professor-released feedback; staff insights; safe account administration and operational health.

### Implementation references

- GitHub archive/contents: https://docs.github.com/en/rest/repos/contents
- Safe Markdown renderer: https://github.com/remarkjs/react-markdown

## Session checkpoint log

### Start of expansion

Saved the agreed scope before source changes. Next: reconcile stale database documentation, implement
task-linked persistent tutoring with authorization and idempotency, then add bilingual UI and tests.
Sharing, staff lab-mode settings and Markdown/math may be separate Phase 1 increments; do not mark
the whole phase complete until every item is implemented and verified.

### Core tutoring source and verification checkpoint

- Added migration f3a20260918: session language/request ID and chat_turns durable request/lease state.
- New main API: backend/backend/routers/chat.py, schemas/chat.py, services/chat_service.py.
- New UI: frontend/src/features/tutor.tsx and components/tutor-markdown.tsx; route and task/result links,
  BFF allowlist, English/Arabic messages, generated transport/OpenAPI updated.
- AI facade/request/engine accept response_language=en/ar with backward-compatible English default.
  Mock Arabic responses are deterministic; no live providers called.
- Context is public task/reference/approved criteria plus optional owned submission text and released
  feedback. No auto-reading submission files; the composer tells students to paste focused excerpts.
- Short transaction locks reserve turns; provider execution occurs outside the DB transaction. A timed
  out provider thread may continue, but generation/lease fencing prevents publishing stale replies.
- Phase 1 remaining: consent-based snapshot sharing/revocation and recipient UI; staff lab-mode setting;
  safe legacy unpaired-message read path; fuller per-turn AI metadata/source persistence; live-provider
  language/guardrail acceptance. Current labs use experiment guidance; code-related questions still use hints.
- Next exact work: finish browser tests and restart-persistence check; then implement sharing using the
  saved policy (read-only selected-message snapshot, explicit recipient, revoke; never all-staff access).
- Test commands: root .\\.venv\\Scripts\\python.exe -m pytest backend/tests -q; AI tests with
  PYTHONPATH=AI-Service and MOCK_MODE=true; frontend npm.cmd run typecheck / lint / test;
  E2E_CHANNEL=msedge E2E_URL=http://localhost:13000 npm.cmd run test:e2e.
- Do not claim the complete integration plan or Phase 1 is finished. Phases 2–5 have no implementation yet.

### Tutoring/sharing implementation checkpoint (supersedes the preceding checkpoint)

- Added f4a20260918 after f3: chat_shares immutable consent snapshots, task_tutor_settings and
  ChatTurn.ai_metadata. Normal application stack untouched; only uniassist-verify upgraded.
- Completed owner preview/share/list/revoke, exact staff-recipient inbox/detail, staff experiment/coding
  mode, owner-only legacy user/assistant history and sanitized provider/version/latency provenance.
- Share POST includes preview_turn_ids. If an older failed turn completes after preview, mismatched
  snapshot IDs are rejected rather than silently sharing unpreviewed content. Later turns stay private.
- UI: features/tutor-sharing.tsx; student tutor preview/dialog/revoke; staff/shared-tutoring routes;
  lab task mode selector. Updated exact BFF allowlist, both catalogs and generated OpenAPI/types.
- Fixed tutor conversation navigation isolation (keyed workspace and disabled composer while routing).
  Browser assertions now distinguish visible error notices from Next's hidden route announcement.
- Verified 11 backend tests, 11 frontend tests, strict TS/lint, production Docker frontend build,
  all six real-backend Edge browser journeys. All 44 AI-package tests passed earlier this expansion.
- Migration test now also seeds historical chat messages and checks preservation without inventing
  turn records or provenance; its focused rerun passed. Test databases/volumes remain intact.
- Backend tests: tests/test_chat.py, test_chat_transactions.py and test_chat_sharing.py.
  Browser tests: frontend/tests/e2e/workflow.spec.ts. No real provider called.
- Restart checksum check passed for isolated chat_messages (53), chat_turns (25), chat_shares (2)
  and task_tutor_settings (2); all three services healthy after restart. Checksums in VERIFICATION.md.
- Next implementation: Phase 2, immutable staff-only grading guidance and released-result insights.
  Read the exact Phase 2 privacy, threshold, grouping, provenance and stale-report rules above first.
  Existing analytics facade is in AI-Service/ai_tutor; it is not yet exposed by the main backend.
- Remaining acceptance limitation: live-provider language, hint-only behavior and leakage smoke checks.
  This does not establish production readiness. Phases 2–5 remain unimplemented, not silently deferred.

### Phase 2 source checkpoint (supersedes prior next-action notes)

- Added migration f5a20260918: grading_guidance, submissions.grading_guidance_id and teaching_reports.
  Existing evaluation pointers remain null; no invented historical private guidance.
- New backend models/schemas/router/services: teaching.py and services/teaching_service.py. Main app
  registers staff-only guidance and analytics endpoints. Grading chooses latest immutable guidance at
  evaluation start; submission staff detail points to the version used. No key content in student APIs.
- Guidance POST uses task/request UUID deduplication, serial version assignment, 12000-character limit.
  Empty versions intentionally disable future key content. Tutor/rubric-generation paths never read it.
- Analytics chooses latest confirmed attempt per student, not blindly is_latest. Normalizes by actual
  rubric total, groups by rubric, minimum max(3, configured threshold), no scores for undersized groups.
  Criterion aggregates exclude ambiguous/missing evidence and also require enough samples. All original
  AI scores retain their meaning after professor overrides. Mock/unknown source counts remain visible.
- AI input contains numeric final grades, generated Criterion N labels and aggregate severity counts:
  no task prose, private keys, authored rubric text, identities, raw work, feedback, filenames or chat.
- Persisted reports store rubric/version, aggregate snapshot, fingerprint, language, timestamp, result
  and sanitized actual AI provenance. Explicit synchronous generation is locked per task; bounded timeout,
  failed calls roll back, repeated request UUID replays. New releases mark historical reports stale.
- Concurrency test caught SQLAlchemy identity-map reuse hiding a release during generation; fixed with
  populate_existing reads before comparing current evidence. Stale-at-completion test now passes.
- UI: features/guidance.tsx and insights.tsx, staff task insights route, task/review integration, exact
  BFF entries, both catalogs, generated OpenAPI/transport. Inputs survive failures; old reports preserved.
- AI analytics request/facade/engine gained default-English response_language; Arabic mock output is
  explicit demo content. Grading prompt warns not to reproduce private solutions in released fields.
- Tests: backend/tests/test_teaching.py + test_teaching_transactions.py (three new tests), frontend
  contract tests (+two localized warning checks), one new full browser journey. Existing suites pass:
  14 backend, 13 frontend, 45 AI; two live tests deliberately skipped. New browser journey passed.
- Optional AI-Service/tests/test_teaching_acceptance.py uses synthetic data only. It requires
  RUN_LIVE_TEACHING_ACCEPTANCE=1 and configured providers; it fails on mock fallback. Canary checks
  are not proof of semantic solution non-leakage; human review of real output remains mandatory.
- Final regression: all seven Edge browser journeys passed against the isolated production frontend
  and real FastAPI/PostgreSQL. Final backend authorization rebuild applied. All services healthy after
  restart; six guidance rows, seven reports and 20 evaluation-guidance links retain identical checksums.
  Detailed hashes and opt-in live-test commands are in VERIFICATION.md.
- Next exact action: implement Phase 3 teams using the accepted-invitation/staff-approval/locked-roster
  rules above. Inspect current Team/TeamMember models and submission eligibility before proposing the
  additive migration. Preserve individual grading and private artifacts/chats. No team/repository/admin
  changes were started in Phase 2. Do not claim live-provider acceptance or full-plan completion.

### Phase 3 final checkpoint — 2026-09-19

- Completed this phase only. New projects with require_team=true support creator consent, exact-number
  invitations, in-app inbox, accepted rosters, TA/professor approval/rejection and immutable history.
  Each member still submits and receives a grade independently; no teammate private-content access.
- Migration f6a20260918 follows f5. Adds team state/version/approval/lock, active task membership,
  invitations, actor/request-deduplicated events and nullable submission.team_snapshot. Partial unique
  active membership and pending invitation indexes enforce uniqueness. Historical duplicate memberships
  abort without deleting records. Legacy rows retain unknown consent/approval and are review-blocked.
- Backend implementation: models/teams.py, schemas/team.py, routers/team.py, services/team_service.py,
  access/submission services and response schemas. Roster operations use actor-then-task locks;
  team submissions take the same task lock before attempt locks. Version checks reject stale approvals.
  Approved snapshots are attached transactionally; first successful submission locks all roster changes.
- Frontend: features/teams.tsx (project list, team detail/history, invitation inbox), task/review/workspace
  links, BFF allowlist, English/Arabic catalogs, generated OpenAPI and transport types. UUID retries,
  explicit consent/approval dialogs, refreshed state on failure and preserved invitation input.
- Synchronized AGENTS, FRONTEND_API_GUIDE, DATABASE_DESIGN, README and original-plan supersession note.
  Root AGENTS remains ignored by the existing user rule; this checkpoint is the durable tracked-path reference.
- Verification: 20 backend HTTP/PostgreSQL/migration tests pass, including concurrent invitation acceptance,
  submission versus removal serialization, legacy restrictions, individual release/privacy and old-data
  preservation/duplicate preflight. 15 frontend tests pass; typecheck/lint and production Docker build pass.
  45 AI tests pass, two live tests skipped. Eight full Edge/Chromium journeys pass against real backend/DB.
  Team browser coverage includes input recovery after 503, inbox consent, TA approval, snapshot review,
  Arabic mobile layout and locked controls. Full accessibility/cross-browser and live AI remain unverified.
- Restart persistence: 19 team rows, 94 history rows and 53 non-null submission snapshots retained
  identical checksums after isolated DB/backend/frontend restart. All services healthy. Exact hashes and
  known limits are in VERIFICATION.md. Verification databases/volumes and runtime artifacts are retained.
- Commands: root `.\\.venv\\Scripts\\python.exe -m pytest backend/tests -q`; frontend `npm.cmd run
  typecheck`, `npm.cmd run lint`, `npm.cmd test`; set E2E_CHANNEL=msedge and E2E_URL=http://localhost:13000
  then `npm.cmd run test:e2e`. Build with `docker compose -p uniassist-verify -f docker-compose.test.yml
  up --build -d frontend`. No normal-stack deployment, secret edits or volume deletion occurred.
- Next exact action, when requested: Phase 4 public GitHub. Read the approved-team snapshot/locking
  contracts first, inspect Repository/Commit foundations, then design additive immutable repository
  evidence and bounded safe sync. Do not start Phase 5 or invent contribution-based grades. Individual
  projects remain text/file-only. Legacy-team remediation remains separate reviewed work, not implicit
  permission to delete/reassign memberships or fabricate consent.

### Phase 4 final checkpoint — 2026-09-19

- Implemented only Phase 4. New backend files: services/github_client.py and repository_service.py,
  schemas/repository.py, routers/repository.py, migration f7a20260919. Extended Repository/Commit,
  added RepositoryEvent/RepositorySnapshot, linked Submission.repository_snapshot_id. Registered
  routes/models and pinned the directly used httpx dependency. No GitHub token/plugin required.
- Public links are canonical and pinned to GitHub numeric identity. Current members propose; either
  TA/professor approves for the exact approved team version. One active link per team; replacement
  supersedes prior links without deleting records. Legacy links stay unverified/read-only.
- Sync is explicit, up to 100 recent default-branch commits, idempotent by repository/SHA. Preserve
  last success and commits on provider failure; expose sanitized error and partial-history wording.
  Staff attribution assign/correct/clear is audited; original author metadata remains unchanged.
  Student identities are never inferred from username or commit count; no contribution grading.
- Snapshot capture verifies access, approval, deadline/rubric/cutoff, public identity and full SHA.
  Download requests/redirects are bounded to API/codeload hosts and exact safe paths. ZIPs are inspected
  in memory, never extracted/executed. Limits: 25 MiB compressed, 100 MiB expanded, 1000 files/2000
  entries; supported UTF-8 input up to 512 KiB/file, 4 MiB combined, then existing AI parser limits.
  Reject traversal, links, special/duplicate paths, encryption and unsupported compression. Manifest
  marks initial omissions; further grading warnings remain visible after release.
- Staged snapshots are owner-only (plus teaching staff), persisted as original BYTEA plus SHA-256,
  manifest, capture/approval/roster/source/fixture provenance and frozen selected-commit attribution.
  Capture is not submission; subsequent POST /submissions/ accepts snapshot OR upload plus text.
  Eligibility and roster locking remain individual; duplicate capture UUIDs replay without new bytes.
  Saved evidence can be reused by its owner for a new attempt while current checks hold. No deletion
  API or retention cleanup exists; PostgreSQL backups/capacity must include staged archives.
- Evaluation verifies stored archive digest and uses saved contents, not GitHub. Replacement/branch
  changes/unavailability and attribution corrections cannot rewrite submitted evidence. Tests prove
  grading works after link replacement with all GitHub methods forced to fail. Task deletion still works.
- Frontend: features/repositories.tsx, team links, locale routes, exact BFF allowlist, snapshot-aware
  submission form and review, catalogs and regenerated OpenAPI/types. URL/SHA/text survive errors;
  snapshot link supports direct navigation/reload. SHA provenance, safe download, omissions and explicit
  fixture labels are visible; assessment still releases only on professor confirmation.
- Tests added: test_github_safety.py (23 checks), test_repositories.py, test_repository_transactions.py;
  migration preservation/duplicate-commit coverage; two localized snapshot component checks and
  repositories.spec.ts browser journey. Full totals: 47 backend, 17 frontend, 45 AI passed; two live AI
  checks skipped. TypeScript/lint/production Docker build pass. All nine Edge browser journeys pass.
  Initial mobile test found SHA warning overflow; fixed review wrapping and reran the whole suite.
- Isolated Compose sets GITHUB_FIXTURE_MODE=true alongside MOCK_MODE=true. It supports fixed
  uniassist-fixtures/demo and replacement repos, each explicitly flagged is_fixture. Normal Compose
  uses actual unauthenticated public GitHub even with mock AI. There is no failure-to-fixture fallback.
  Docs consulted: official GitHub REST contents/archive and commits docs (API version 2026-03-10).
  No real repository-provider acceptance was performed; fixture results are not live GitHub evidence.
- Restart checks pass for 9 repositories, 4 commits, 26 audit events and 8 archive/provenance snapshots;
  4 submitted snapshot links remain. Exact counts/digests are in VERIFICATION.md. No application volumes,
  environment secrets, ignore rules or user changes were reset. Test artifacts/DBs remain for inspection.
- AGENTS, FRONTEND_API_GUIDE, DATABASE_DESIGN, README and VERIFICATION are synchronized. AGENTS remains
  ignored by the user's existing rule. The original plan's release scope is historical, not current API.
- Next exact action, when requested: Phase 5 profile/admin/operations. Inspect auth identity/JWT checks,
  user/staff/admin models, bootstrap and existing sanitized AI metadata first. Implement narrowly allowed
  profile edits, suspension checks on every request, operator-only bootstrap, last-admin protection,
  account corrections/audit and durable aggregate operational metrics. Preserve private tutor/assessment
  boundaries; do not broaden admin into transcript access or fabricate repository contribution scores.

### Phase 5 final checkpoint — 2026-09-19

- Completed Phase 5. New files: models/operations.py, schemas/accounts.py, services/account_service.py,
  routers/admin.py, backend/bootstrap_admin.py, migration f8a20260919; frontend/features/accounts.tsx,
  components/file-metadata.tsx, account component/browser tests and backend/tests/test_accounts.py.
  Auth/identity, BFF allowlist, workspace routing, catalogs and generated OpenAPI/types are synchronized.
- Self-service name/student GitHub only. Admin account search/detail/corrections/status and TA↔professor
  changes are version-checked. No deletion, student↔staff/admin conversion or password-reset API.
  Current DB identity controls existing JWT authorization. Suspension blocks login/every new request;
  reactivation permits still-valid JWTs. In-flight work is not cancelled. Student academic corrections
  change future task access, never historical rosters/submissions/attribution. GitHub changes never
  infer commit ownership. Identity/role/cohort/major changes reset client academic caches.
- Public admin registration is closed. Operator-only interactive bootstrap never overwrites/converts
  accounts and records a content-free event. Bootstrap/profile/admin edits share a short advisory lock;
  concurrent suspensions cannot remove the last active admin. Existing admins are preserved as active
  by migration, requiring operator review before deployment under the new policy.
- Admin has only account/audit/aggregate operations views. All academic routers explicitly reject admin
  identities, including original/shared chats, assessments, files and repository archives. Frontend
  role gating is usability only. No private-content dashboard or impersonation was introduced.
- Transactional audit records capture actor/target IDs, action, changed field names and timestamp.
  Account/profile/bootstrap, rubric decisions, grade confirmation, team actions, repository approval/
  attribution and shares/revocations are instrumented. Attribution events target commit IDs; detailed
  prior/new attribution stays in the existing academic-scoped history. Audit target IDs do not cascade
  on task deletion. No private values/transcripts or fabricated historical event backfill.
- Durable AI application-call records use separate transactions, surviving academic rollback. Started
  rows remain visible as incomplete after interruption. Metrics expose calls/errors/completed latency,
  provider/operation, actual engine mock usage and known/unknown truncation. No prompts/replies/keys/
  arbitrary metadata/error messages stored. Provider exception text is no longer logged; provider/model
  provenance is thread-local, preventing concurrent calls from crossing metadata. Rubric/tutor/lab budget
  truncation now reaches metadata. No claim that application calls equal provider billing/retries.
- File upload/info schemas no longer expose storage_path; metadata UI shows safe filename/type/purpose/
  bytes/time with authorized downloads. Missing stored files have unknown size, not invented metadata.
- Full verification: 48 backend/PostgreSQL tests pass; fresh/old-schema migration checks retain data and
  duplicate preflights; dedicated fresh account DB tests cover last-admin concurrency, public-admin
  rejection, narrow edits, stale conflicts, role corrections, suspended existing JWTs, reactivation,
  admin content denial and sanitized durable success/error metrics. 21 frontend tests pass, including
  both locales' profile/file boundaries and translation parity. TypeScript/lint/production Docker build
  pass. Ten complete Edge/Chromium journeys pass (2.0m final run). Arabic mobile metrics inspected.
  47 AI tests pass; two opt-in live tests skipped. Added concurrency/truncation provenance tests pass.
  Latest backend rebuild also passed the full-release/artifact metadata smoke test.
- Restart persistence: 1,110 account/profile rows, 397 audit rows and 120 AI-operation rows retained
  identical counts/ordered digests after isolated db/backend/frontend restart; all services healthy.
  Exact hashes are in VERIFICATION.md. Audited action categories were checked without private contents.
- Guides synchronized: AGENTS, FRONTEND_API_GUIDE, DATABASE_DESIGN, README, original plan supersession
  note, this checkpoint and VERIFICATION. Root AGENTS remains ignored by the user's existing rule.
  No normal application containers/volumes, environment secrets or ignore rules were changed in Phase 5.
  Test-created accounts/databases/archives/artifacts are retained; do not delete volumes to clean tests.
- Resume: no remaining Phase 5 implementation. Before any follow-up, read this checkpoint and API guide.
  Normal-stack deployment was not performed: user may run `docker compose up --build -d`, then
  `docker compose exec backend python -m backend.bootstrap_admin` to create their own admin securely.
  Do not automatically provision a real admin or change credentials. Live GitHub/AI, institutional
  provisioning, full accessibility/cross-browser audit, retention/backups and deployment hardening
  remain separate work. Communication monitoring, generated practice, notifications/email, private
  repositories, contribution grading, legacy-team remediation and account-class conversions remain
  deferred, not unfinished features to start without a new request.


### Follow-up checkpoint - academic Markdown and math (2026-09-21)

- Shared `AcademicMarkdown` replaces the tutor-specific viewer. Existing dollar math and math
  fences remain supported; a local micromark/mdast extension adds LaTeX parentheses/brackets,
  including multiline matrices. Code, links and escaped delimiters keep Markdown semantics;
  unmatched delimiters and invalid equations remain readable. Criterion names use inline rendering.
- Coverage: task-detail instructions, rubric names/descriptions, assessment feedback/reasoning/
  findings/warnings, private guidance history/used versions, both sides of tutoring and shared
  transcripts, and teaching insights. Existing academic authorization and release gates remain.
- Staff fields have local live previews for instructions, manual rubrics, refinement feedback and
  private guidance, with English/Arabic syntax hints and empty states. Original request strings
  and saved content are unchanged. Submitted artifacts and identifiers retain literal display.
- Raw HTML, images and trusted KaTeX commands stay disabled. Local fonts, MathML, equation LTR
  isolation and horizontal scrolling are retained. Inline-size containment prevents long equations
  from widening the surrounding grid panels; English/Arabic mobile screenshots were inspected.
- Verification: 52 frontend tests pass, including parser boundaries, hostile input, localized
  previews, unchanged save payloads/failure recovery, guidance and student grade-release filtering.
  TypeScript and ESLint pass. The production Docker build passes, including a clean npm ci with
  the updated lockfile (only explicit type dependencies were added).
- Nine Playwright journeys pass in Edge/Chromium against the real isolated backend: two new
  English/Arabic math authoring/save/approval/student/mobile checks plus all seven existing
  workflow journeys (lab/rubrics, assessment/release, tutoring/retry, sharing/revocation, private
  guidance/insights, upload recovery, and session/origin/locale behavior).
  Screenshots: `frontend/test-results/markdown-*/math-*-mobile.png` (generated, untracked).
- Only `uniassist-verify` frontend was rebuilt/restarted. Test accounts/tasks remain in its database.
  No migrations or backend/AI behavior changed; their unit suites and the separate account/team/
  repository browser suites were not rerun for this frontend-only follow-up. Normal-stack deployment,
  live providers and broader cross-browser accessibility verification remain separate work.

### UI follow-up checkpoint — 2026-09-22

- Applied the agreed `Humazine_UI.md` Academic Review Desk direction using the humanize-ui skill.
  Existing React/Radix/Next/Tailwind stack retained. Only new dependency: locally bundled
  `@fontsource/source-sans-3@5.3.0`; existing Noto Sans Arabic remains the Arabic font.
- Semantic CSS tokens and layers, consistent controls/notices, compact active navigation, task rows,
  server-eligibility actions near task context, and a staff review queue before preparation editors.
  Task-list excerpts are omitted to avoid displaying raw Markdown/math; task detail retains full prose.
- Attempt receipt shows actual timestamps, associated rubric version/total and saved repository SHA.
  Released student feedback precedes grade/artifact; staff evidence and explicit professor release
  controls retain the same authorization, persistence and mutation behavior. No API or migration changes.
- English/Arabic component release/order regressions: 54 frontend tests pass. TypeScript, ESLint and
  production Docker build pass. All 16 Edge/Chromium Playwright journeys pass against the real isolated
  backend, including accounts, teams, repository fixtures and the seven original academic workflows.
- Four new design browser checks cover bilingual sign-in, actual locale font, focus/reduced motion,
  task rows at 390/768/1440px, 200% CSS zoom reflow, route/query retention during language switching,
  queue navigation, dialog Escape/cancel focus and focus restoration. Existing mobile math checks pass.
- Inspected desktop task/sign-in views and Arabic mobile sign-in, task rows, staff task, released result
  and long equations. Generated evidence lives in `frontend/test-results/`. Production stylesheet BOM
  and Arabic font cascade problems found during verification were fixed and final checks rerun.
- Only `uniassist-verify` frontend was rebuilt/restarted, at http://localhost:13000. Test data remains
  in its isolated database. The pre-existing `.gitignore` edit was preserved. Normal stack, migrations,
  live GitHub/AI and backend/AI unit suites were outside this presentation-only change. Browser coverage
  is Edge/Chromium; full assistive-technology and other browser verification is not claimed.
