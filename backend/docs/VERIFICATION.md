# Frontend release verification

Verified on 18 September 2026 against the local implementation. This is a local/demo
release, not a certification for public university deployment.

## Environment and isolation

- Docker Compose project: `uniassist-verify`, using `docker-compose.test.yml`.
- Production standalone Next.js frontend: `http://localhost:13000`.
- Real FastAPI backend: `http://localhost:18001`; real PostgreSQL: port `15432`.
- AI evaluations use `MOCK_MODE=true`; the UI identifies mock assessment output.
- Browser journeys run in installed Microsoft Edge (Chromium) through Playwright.
- Verification uses separate database/upload volumes and uniquely named test accounts.
  The normal application database and its volumes were not reset or deleted.

## Original release results

| Check | Result |
| --- | --- |
| Strict TypeScript checking | Passed |
| ESLint | Passed |
| Production Next.js build in Docker | Passed |
| Development Docker target build | Passed |
| Vitest / Testing Library | 10 tests passed |
| Backend HTTP/PostgreSQL and migration tests | 6 tests passed |
| AI service/file-parser regression tests | 16 tests passed |
| Playwright against production Docker frontend and real backend | 4 journeys passed |
| Production and development Compose configuration | Validated |
| Fresh database migration/startup | Passed |
| Historical-schema upgrade with seeded records | Passed |
| Database/backend/frontend restart persistence | Passed |

The historical-schema test upgrades revision `e49cd157b008` to `f2a20260918`, then
repeats the upgrade. Existing grades, feedback and file records are retained. Missing
historical submission text stays empty; unknown filenames and AI provenance remain unknown.

For restart verification, all three isolated services were restarted and became healthy.
Before and after restart, the submissions query returned 35 rows and the same checksum
of ordered IDs, final grades and feedback: `07185159b6fb4321ffcb63bea32e735c`.
This demonstrates persistence for those records, not a backup/restore or disaster-recovery test.
Later test runs create additional records, so this count is a point-in-time observation.

## Coverage demonstrated

The browser journeys exercise:

- Student, TA and professor registration/login; session reload, logout, missing-session
  redirection, forbidden-role navigation and same-origin mutation protection.
- Lab PDF upload and task creation, assignment creation and individual project creation.
- AI rubric suggestion/refinement, manual rubric criteria, version approval and Arabic dialogs.
- Approved rubric display on student task/submission-form pages before submission, and the
  associated rubric on an unreleased attempt. Backend checks verify draft/rejected rubric privacy,
  cohort/major restrictions and preservation of the original attempt rubric after replacement.
- Student submission, staff discovery, TA AI evaluation, professor override/release,
  and hidden assessment content before release.
- Upload-first submission recovery: a deliberately failed second step retains the text
  and uploaded file ID; retry does not upload again. Authenticated artifact download is checked.
- Arabic validation and RTL mobile results, route/query-preserving language switching,
  keyboard navigation and dialog dismissal.

Backend tests additionally exercise text-only, file-only and combined attempts; associated
rubric history and score bounds; cohort/major and artifact ownership; deadlines, late
assignments and confirmed-grade cutoffs; team-required project rejection; repeated/concurrent
evaluation protection; AI failure rollback and safe error responses; and persisted mock
provenance/code findings. Concurrency tests use actual PostgreSQL transactions and locks.

Focused frontend tests cover translation-key parity, role-specific status labels,
accessible field labeling, English/Arabic approved rubric rendering and bounded request-body handling.

The rubric-visibility update was rechecked with TypeScript, lint, the production Docker build,
all 10 frontend tests, all 6 backend tests and all 4 browser journeys. No database migration is
needed for this update. AI regression and restart-persistence results above are from the initial
release verification. Apply the update to the normal stack with
`docker compose up --build -d backend frontend`; the verification run only rebuilt the isolated stack.

## Tutoring expansion verification

Phase 1 of [the preserved integration plan](BACKEND_UI_INTEGRATION_PLAN.md) is implemented and
verified with mock AI. This section supersedes original-release counts for the current source.

| Check | Current result |
| --- | --- |
| TypeScript, ESLint, production Docker frontend build | Passed |
| Frontend tests including safe Markdown and translation parity | 11 passed |
| Backend HTTP/PostgreSQL, concurrency, privacy and migrations | 11 passed |
| Entire AI-package suite | 44 passed |
| Real-backend Playwright journeys in Edge | 6 passed |
| Historical schema upgrade through f4a20260918 | Passed, including preserved legacy chat |
| Isolated db/backend/frontend restart | Healthy; tutoring-record counts/checksums unchanged |

New coverage includes tutoring without an accepted rubric, after deadline/release, owned-submission
context, no unreleased feedback/draft rubric in prompts, failed/interrupted turn retries, duplicate
and concurrent requests, rate limits, paginated legacy history excluding system messages, and actual
mock provenance. Sharing tests verify preview IDs, wrong-recipient denial, no access to original chats,
immutable cutoff snapshots, later-message privacy, idempotent revocation, and task deletion cascades.
Lab-mode changes are staff-only and affect future turns. Browser tests cover recovery after a failed
send, reloaded history, English/Arabic conversation creation, mobile layout, preview/confirmation,
recipient-only read-only snapshots, revocation and persisted lab settings.

The full browser rerun passed all six journeys. An earlier run caught a test selector matching Next's
hidden route-announcement alert; the test now targets the visible error message. Earlier tutor testing
also identified and fixed composer isolation while switching to a newly created conversation.

Restart evidence (before and after, no test writes between reads):

| Table | Rows | MD5 of ordered JSON records |
| --- | ---: | --- |
| chat_messages | 53 | 63136b38304a9f11b2eb22375f8fb00b |
| chat_turns | 25 | 5cf8658b3e2eaa2505c4cbca57a05d08 |
| chat_shares | 2 | 7fe7b0445def8412c7fc7392197c2671 |
| task_tutor_settings | 2 | 5c266629d9cad3247a2b42bd162a15ee |

Only counts and checksums were printed, not transcript contents. This is persistence evidence,
not backup/restore certification. Normal application services and volumes were not changed.
Live-provider language, hint-only behavior and solution-leakage acceptance remain unverified.
Phases 2–5 (teaching insights, teams, GitHub and administration) remain to be implemented.

## Phase 2 teaching-tools verification

Private guidance and released-only teaching insights are implemented with migration f5a20260918.
Current checks: 14 backend/PostgreSQL tests, 13 frontend tests and 45 AI-package tests pass; two
explicitly opt-in live-provider checks are skipped. TypeScript/lint and the production Docker build
pass. All seven real-backend browser journeys pass, and db/backend/frontend return healthy after
restart with unchanged Phase 2 record checksums:

| Evidence | Count | Before/after checksum |
| --- | ---: | --- |
| grading_guidance ordered JSON | 6 | c9e675d6013eec2624ec322764c1caeb |
| teaching_reports ordered JSON | 7 | eb9ecb311c49c3d9a636966dc9e7cb50 |
| submission ID / guidance ID links | 20 | d0ef71d26f2f4e57c4627d7f897a0262 |

Only counts/hashes were printed, not private guidance or report contents. Normal application services
and volumes were not reconfigured. Root Compose syntax validates with the new runtime threshold/timeout
variables; root .env was not edited.

New backend checks cover immutable/version-pinned guidance, student denial before/after release,
empty guidance disabling future key content, historical null pointers, task deletion, captured grading
versus tutor/rubric/analytics payloads, numeric-only analysis, minimum group/criterion samples,
AI-only result exclusion, rubric grouping, final-grade normalization, retained original criterion
scores, report request deduplication, provider failure rollback, concurrency and stale-at-completion.
Browser coverage includes failed guidance save with retained input, explicit save confirmation,
threshold empty state, failed report request without false success, saved/reloaded reports, changed
release warnings, English/Arabic generation, mobile width and exact evaluation guidance display.

The concurrency test discovered an identity-map caching issue that masked grade changes during
generation; analytics now refreshes ORM values when calculating report staleness.

### Optional live-provider smoke checks

These are not run automatically and may incur provider charges. Configure a provider through the
existing AI package environment first, then opt in using synthetic data only:

```powershell
$env:PYTHONPATH="$PWD\AI-Service"
$env:RUN_LIVE_TEACHING_ACCEPTANCE='1'
.\.venv\Scripts\python.exe -m pytest AI-Service/tests/test_teaching_acceptance.py -q
Remove-Item Env:RUN_LIVE_TEACHING_ACCEPTANCE
```

Tests reject silent mock fallback, check that a synthetic private canary is not copied into releasable
grading fields, and check Arabic report output. Canary/string checks do not prove absence of semantic
solution leakage; human review of feedback, reasoning and findings remains necessary before real release.
No real provider has been acceptance-tested in this phase.

## Reproduce

From the repository root, with the local Python environment installed as described in README:

```powershell
docker compose -p uniassist-verify -f docker-compose.test.yml up --build -d
.\.venv\Scripts\python.exe -m pytest backend/tests -q
$env:PYTHONPATH="$PWD\AI-Service"
$env:MOCK_MODE='true'
.\.venv\Scripts\python.exe -m pytest AI-Service/tests -q
cd frontend
npm.cmd run typecheck
npm.cmd run lint
npm.cmd test
$env:E2E_URL='http://localhost:13000'
$env:E2E_CHANNEL='msedge'
npm.cmd run test:e2e
```

For Playwright-managed Chromium instead of installed Edge, run
`npx.cmd playwright install chromium` and unset `E2E_CHANNEL`. The managed Chromium
download was interrupted by network resets in this environment; Edge was used successfully.

Verification databases and volumes remain available for inspection. Tests are deliberately
non-destructive and do not clean up previous runs automatically.

## Remaining limits

- Live external AI providers were not acceptance-tested; mock AI was used for reproducibility.
- Browser coverage is Edge/Chromium, not Firefox or Safari. Keyboard/mobile checks are
  targeted checks, not a full accessibility audit or exhaustive device matrix.
- Production Compose configuration was validated, but the user's normal stack was not
  started or reconfigured. The isolated production-image stack was built and exercised.
- Historical forward migrations were tested; the complete historical downgrade chain was not.
- Self-registration into staff roles is intentional for the demo. Institutional role assignment,
  rate limiting, backups, retention policy and deployment hardening remain production work.
- Admin management remains planned expansion work. Legacy-team consent
  remediation is not implemented. Communication monitoring, practice generation, email and notifications are deferred.

See [FRONTEND_API_GUIDE.md](FRONTEND_API_GUIDE.md) for resulting contracts and
[README.md](../../README.md) for setup and operational notes.

## Phase 3 verification — 2026-09-19

Implemented migration f6a20260918, team/invitation/history APIs, version-checked staff approval,
individual roster snapshots, English/Arabic team workspaces, inbox and submission/review integration.
Verification uses only the isolated uniassist-verify stack, real FastAPI/PostgreSQL and mock AI.

- Backend: lifecycle, consent, reapproval, archive/leave/remove/cancel/reject, receipt replay,
  concurrent membership acceptance, concurrent first submission versus member removal, task access,
  teammate artifact/assessment privacy, independent grade release and deadline cutoffs.
- Migration: historical team/member/submission records survive; no invented accepted_at/approval/
  roster snapshots. Historical duplicate memberships stop upgrade and preserve all rows/revision.
- Frontend: 15 focused tests including bilingual locked-roster controls and translation-key parity;
  TypeScript and lint pass. Production multi-stage Docker build passes.
- Eight Edge/Chromium browser journeys pass. The new journey creates a team, preserves invite input
  after a simulated 503, accepts via inbox, approves as TA, submits individual work, displays the
  snapshot and verifies Arabic mobile roster locking. Screenshot inspected at 390px width; no overflow.
- AI regression: 45 pass, two opt-in live-provider checks skipped. No live-provider claims.

An early build caught a test-only missing TypeScript annotation, now fixed. An integration run
interrupted by concurrent container recreation was rerun against the stable stack and passed.
The browser test's ambiguous alert selector was narrowed to the actual error notice, then all
eight journeys passed. These initial runs are not counted as successful acceptance.

Final backend regression: **20 passed** (106.62 seconds). The added legacy API test confirms read-only
unknown consent, blocked approval/submission and preserved membership reservations. Local typecheck
and lint were rerun after the final test edits and passed.

Restarted isolated DB/backend/frontend after all test mutations finished. Counts and checksums before
and after match exactly; all three services report healthy:

| Persisted records | Count | MD5 of ordered serialized rows/snapshots |
| --- | ---: | --- |
| Teams | 19 | a9ca5a8e9f97a99c46ab16fb944c89d6 |
| Team events | 94 | fbde4dd0d69fbfb84179e76677ffc6f6 |
| Submission team snapshots (non-null) | 53 | 888ded4a86b2753ff043d02811926047 |

These are regression checksums, not security digests. No private contents or secrets were printed.
Normal application containers/volumes were not modified. Phase 4 was unimplemented at this checkpoint;
the following section supersedes that status.

## Phase 4 verification — 2026-09-19

Public-GitHub source implementation is complete with f7a20260919, bounded public-only HTTP,
approved links, audited attribution, private frozen archives and English/Arabic UI.

- Full backend suite: **47 passed**, using real PostgreSQL and HTTP/ASGI. Includes 23 targeted URL,
  redirect, response-bound, archive traversal/link/duplicate/size/manifest and fixture checks; proposal,
  staff approval, sync deduplication, roster reapproval, snapshot ownership, separate grading/release,
  upload/snapshot exclusion, and task deletion; concurrent replacement approvals, identical request
  replay, rate-limit recovery, snapshot deduplication and offline grading after link replacement.
- Migration tests pass for historical preservation and both legacy membership/commit conflict
  preflights. Existing commit attribution remains unverified; no archive/approval is fabricated.
- Frontend: **17 tests pass**, including both locales' fixture/provenance/download rendering and
  translation-key parity. TypeScript and lint pass; production multi-stage Docker build passes.
- AI regression: **45 pass**, two live-provider checks skipped. No live GitHub or paid AI provider
  calls were made. GitHub tests use explicit fixtures, never a silent production fallback.
- Initial nine-journey browser run: eight existing journeys passed; the new journey completed proposal,
  approval, sync, attribution, failed-capture recovery, private snapshot download, submission, grading
  and release, then caught Arabic mobile horizontal overflow from a long SHA in assessment warnings.
  The review container now wraps long identifiers; rebuilt browser acceptance passes all nine journeys.

Final browser regression: **9 passed** (1.3 minutes). Arabic 390px result screenshot was visually
inspected; repository URL, SHA, warnings, feedback and provenance fit without horizontal overflow.
This is targeted mobile/keyboard/shared-dialog coverage, not a full accessibility or browser-matrix audit.
Local TypeScript/lint were rerun after the wrapping fix and passed.

After all mutation tests completed, restarted isolated database/backend/frontend. All services report
healthy. Counts and ordered-row digests before/after match exactly; snapshot digest includes original
compressed archive bytes as well as stored provenance:

| Records | Count | MD5 regression digest |
| --- | ---: | --- |
| Repositories | 9 | 06dcbc478910e4bcd97ad863a3619e75 |
| Commits | 4 | c8c6edefc86d419d4378c72dfd9c3116 |
| Repository audit events | 26 | 1f5bfcf38685103f993b6cce197286f5 |
| Repository snapshots | 8 | 005ed545206a88af3e4b974af5f6c6c5 |

Four submissions retain snapshot references. Regression MD5s are not security proofs; each archive
separately uses persisted SHA-256 for integrity. No private contents or secrets were printed. Tests
retain isolated databases/volumes for inspection; the normal application stack and secrets are untouched.
Live GitHub repository access and live AI remain unverified. Phase 5 has not started.

## Phase 5 — profiles, account administration and operations (2026-09-19)

This entry supersedes the previous Phase 5 status above. Implemented migration f8a20260919,
narrow self-profile/admin APIs, operator bootstrap, active-status enforcement, content-free audits,
durable aggregate AI operations and safe file metadata UI. Only isolated verification data was used.

- **48 backend tests pass** in the final full run (155.19s). Account tests create their own fresh
  PostgreSQL database and apply the full migration chain. They verify public admin registration
  rejection, bootstrap overwrite refusal, last-active-admin protection including concurrent suspension,
  immutable role classes, narrow self-service, unique identifiers, version conflicts, TA/professor role
  updates taking effect on existing JWTs, suspension/reactivation, search, admin academic-content denial,
  and content-free durable success/failure metrics. Migration tests preserve historical records and
  confirm existing accounts become active with empty new history tables (no fabricated activity).
- **21 frontend tests pass**; TypeScript and lint pass. New tests cover EN/AR self-service fields and
  file metadata/authorized URLs without storage paths. Existing translation parity and academic/privacy
  checks remain. Production standalone Docker builds pass with the new routes and generated types.
- **10 Edge/Chromium browser journeys pass**, final full run 2.0 minutes against real FastAPI/PostgreSQL.
  New account journey uses operator code to provision a synthetic admin in the isolated DB, edits a
  student profile, preserves input after injected 503, reloads persisted changes, searches/corrects a
  student, suspends/rejects their existing session, reactivates, views content-free audit/metrics, switches
  to Arabic and checks a 390px mobile layout. Arabic metrics screenshot was inspected. Existing nine
  academic/tutor/team/repository journeys still pass. This is not a full browser/accessibility audit.
- **47 AI-package tests pass**, two live-provider acceptance checks skipped. New tests prove concurrent
  worker calls do not cross provider metadata and rubric truncation is reported. Provider exception
  bodies were removed from application log statements. Live-provider behavior remains unverified.
- After the final backend provenance rebuild, the complete submission/evaluation/release smoke test
  passes, including safe artifact metadata. Latest source passes git diff --check. Existing CRLF and
  dependency deprecation/config-loader warnings do not fail tests; no dependency upgrades were made.

After all mutating tests finished, restarted only the isolated db/backend/frontend services. Each is
healthy and migration head is f8a20260919. Ordered-row counts/digests match exactly before/after:

| Records | Count | MD5 regression digest |
| --- | ---: | --- |
| Account identity/status/version + student/staff profiles (excluding password hashes) | 1110 | bc60726598003445b87c16355279738b |
| Content-free audit events | 397 | 93c0f562e57b6adc8ee03262d3c95fb0 |
| Durable AI operations | 120 | 77ebae26ea46482e2fc18c536e5a2cfe |

Audit action counts confirm account/profile/bootstrap, rubric acceptance/rejection, grade confirmation,
team approval/changes, repository approval/attribution and chat sharing/revocation are actually recorded.
Only action codes/counts and aggregate digests were printed, never personal fields or private contents.
These MD5s are regression comparisons, not cryptographic security claims. Old development records with
unknown operation/provenance remain unknown; no metrics or audits were fabricated/reclassified.

The normal app stack, `.env`, credentials and volumes were not changed. Test databases/accounts and
artifacts remain available for inspection. Operators must review pre-existing demo admins and bootstrap
their own real admin interactively when deploying. No production admin or default password was created.
Live GitHub/AI remain unverified; no new external provider calls were made. See the final integration
checkpoint for deferred production governance, retention, accessibility and institutional provisioning.
