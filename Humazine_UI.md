# UniAssist UI review and proposed visual direction

Reviewed: 21 September 2026. Scope: review and proposal only; no application code changed.

Implementation follow-up: the agreed direction was applied on 22 September 2026. See section 9 for the delivered changes and verification; the original review below remains the baseline.

Subsequent user-requested copy change (22 September 2026): removed the local/demo staff self-selection notice from sign-in, registration and workspace screens in both languages. Earlier recommendations to retain that banner are superseded. Assessment-specific mock notices remain in place.

**AI Slop Score: 5/10 — several recognizable template patterns.** Lower is better.

**Distinctiveness Score: 5/10 — appropriate for an MVP, with limited visual identity.** Higher is better.

These are qualitative design judgments using the requested skill's five-category rubrics, not measurements of whether AI authored the interface. The scores apply to the current UI, not the unimplemented proposal.

## 1. Direct diagnosis and evidence

UniAssist already feels like a serious academic tool. Restrained teal, explicit rubric versions, local timestamps, Arabic support, and clearly labeled mock assessments give it a credible foundation. Its weakness is that too many different activities receive the same visual treatment: a white rounded panel, a bold heading, muted explanation, and another bordered container inside it.

That repetition obscures the product's strongest idea: students submit individual work, staff review evidence against a specific rubric, and professors explicitly release results. The improvement should make those relationships visible through layout and hierarchy.

### Review coverage

- Inspected the running isolated verification frontend at `http://localhost:13000`: English desktop sign-in, student task list, student task detail, and professor task detail; English mobile sign-in and Arabic mobile task list.
- Captured desktop screens at 1440 × 1000 and mobile screens at 390 × 844. Inspected the existing Arabic released-result screenshot at [released-ar-mobile.png](frontend/test-results/workflow-three-roles-compl-c93d5-ssment-and-switch-to-Arabic-chromium/released-ar-mobile.png), dated the same day. This local test artifact may be replaced by later test runs.
- Examined shared CSS, workspace navigation, buttons, status labels, auth, task, review, rubric, tutor, team, repository, insights, and account UI source. Secondary workflows were source-reviewed rather than exhaustively browser-tested.
- Read [AGENTS.md](AGENTS.md), the [integration checkpoint](backend/docs/BACKEND_UI_INTEGRATION_PLAN.md), and the relevant [API guide](backend/docs/FRONTEND_API_GUIDE.md) boundaries.
- Used existing verification accounts for inspection. No academic records were created or changed. Generated inspection screenshots were kept in the system temporary directory.

The sample data contains long automated-test titles and mixed-language prose. Those strings are not treated as branding defects. Findings concern how the interface handles them. This is a visual review with limited accessibility observations, not a complete accessibility or functional certification.

## 2. Specific generic patterns found

| Pattern | Specific evidence | Why it matters | Proposed change |
|---|---|---|---|
| One panel treatment for almost everything | [globals.css](frontend/src/app/globals.css), `.panel`: white background, 1px border, 16px radius, 24px padding. Used for filters, task instructions, rubric summaries, guidance, history, loading and empty states. | Actions, documents, and temporary states appear equally important. | Define separate document, toolbar, list-row, notice, and decision treatments. Use section rules where a container adds no meaning. |
| Equal-weight task-card grid | [tasks.tsx](frontend/src/features/tasks.tsx), `TaskList`, line 103: two/three-column grid; every task repeats title, excerpt, deadline and full-width “Open task.” | Deadline/status comparison requires scanning across large cards. Student and staff work inherit nearly the same composition. | Student task rows organized around next action; staff rows with existing review counts aligned into columns. Retain shared navigation and components. |
| Excessive framing around filters | `TaskList` places two labeled controls inside a full padded panel above the card grid. | At 390px in Arabic, the first task begins around 620px down the page; its action is below the initial viewport. | A compact filter toolbar with persistent labels. Reduce surrounding padding, not input text size or touch targets. |
| Stacked feature modules bury the main staff task | [tasks.tsx](frontend/src/features/tasks.tsx), lines 334–336: rubric versions, then private guidance, then the review queue. | On the inspected task, the queue heading begins around 1835px down the document at desktop size, even with only one rubric criterion. | Put a queue summary or section link beside task context. Separate preparation and review with local navigation, preserving all existing controls. |
| Nested rounded containers | [teaching.tsx](frontend/src/features/teaching.tsx): rubric section → bordered version → bordered Markdown preview. Similar nesting appears in review and guidance. | Repeated outlines create a component-demo appearance and consume reading space. | Use a version header and ruled criterion rows. Keep authoring previews within a purposeful editor area. |
| Marketing-sized sign-in introduction | [auth.tsx](frontend/src/features/auth.tsx), lines 141–153: large slogan, generous vertical spacing, then three teal bars. | On the inspected mobile screen the sign-in panel starts around 470px. Decoration delays a routine action. | Make the form the first substantial mobile content; keep a short product explanation and visible demo disclosure. |
| Decorative bars resemble a progress control | `Auth` maps `[1, 2, 3]` to identical rounded bars with `aria-hidden`. | They communicate neither progress nor an academic state and have no interaction. | Remove them. Any process illustration should have meaningful labels and clearly distinguish rubric approval, submission, evaluation, and release. |
| Typography has hierarchy but limited identity | [globals.css](frontend/src/app/globals.css), lines 27–30 and 60–70: Arial for English, Noto Sans Arabic for Arabic, bold headings, global negative heading tracking. | Readable, but mostly a generic type scale. Academic prose has no shared reading-width limit; Arabic inherits Latin-oriented tracking rules. | Define bilingual type roles, comfortable prose measures, tabular numeric data, and zero Arabic letter spacing. |
| A wrapping utility header substitutes for navigation structure | [workspace.tsx](frontend/src/components/workspace.tsx), lines 78–129: brand, identity, language, profile, inbox and logout, followed by the demo banner. | Arabic mobile uses several rows before reaching task content; current location has little persistent visual emphasis. | Compact primary navigation with an explicit active destination; group account utilities while keeping language switching discoverable. |
| Result hierarchy emphasizes the grade before learning | [review.tsx](frontend/src/features/review.tsx), lines 104–168: rubric precedes artifact/result; grade block precedes feedback. Confirmed in the Arabic result screenshot. | The mobile student reads reference material and a score before reaching improvement guidance, weakening the product's feedback-first promise. | Keep release status and mock provenance visible, then show released feedback, grade, criterion evidence, and supporting artifact/history. |
| Academic list excerpts are treated as generic plain text | `TaskList`, line 126, renders `task.description` as a clamped paragraph. The inspected math fixtures show raw LaTeX delimiters and command text. | The overview feels less considered than the Markdown/math task detail. | Use a bounded, safe academic excerpt or deliberately omit the excerpt for dense rows. Preserve the stored string and prevent equations from widening the list. |

The application does **not** show the common purple/indigo gradient, neon/glass, emoji-feature-icon, animated-card, or scroll-reveal patterns in the inspected surfaces. It is also not a centered hero/three-feature-card marketing site. A three-column task list is a real product list; its problem here is scanability and equal weighting.

### What should be preserved

- The restrained teal direction and light academic surfaces.
- Role-aware status wording, exact timestamps, rubric totals and immutable version references.
- Prominent mock-assessment notices and the local/demo disclosure.
- The useful artifact/evidence split already present on desktop review.
- Arabic RTL, mixed-direction isolation, local font delivery, and contained math overflow.
- Labeled form fields, explicit errors/retries, the workspace skip link, and visible focus styles present in source.

## 3. Why the interface converges on these patterns

The observable cause is a small presentation vocabulary: `.panel`, `.stack`, shared buttons, badges, and scattered color utilities. New features are composed by stacking those same elements. Only background and foreground are defined as root color variables; most color and spacing decisions live directly in CSS or JSX.

This makes consistency easy but gives preparation, evidence, and decisions insufficient visual distinction. The code also reveals module order taking precedence over role-specific priorities. This is an inference from the implementation, not a claim about its authors or their process. Replacing the component library would not by itself solve it.

## 4. Priority fixes

| Priority | Change | Observable success criterion |
|---|---|---|
| 1 | Reorganize staff task detail around preparation and review. | A visible queue entry/count is available near task context; reviewing work does not require passing the guidance editor. |
| 1 | Make student released results feedback-first. | Released feedback precedes the grade block and artifact on mobile; mock provenance remains visible before assessment content. |
| 1 | Replace equal task cards with aligned task rows. | Title, exact deadline, current state and next action can be scanned together; staff review counts are easy to compare. |
| 2 | Introduce an attempt receipt and a criterion evidence layout. | Attempt number, associated rubric version, status and actual timestamps stay visibly connected to the work. |
| 2 | Define surface and density roles; simplify the mobile header/filter area. | Borders identify meaningful regions; primary task content appears sooner without reducing control sizes. |
| 2 | Apply bilingual typography and semantic tokens. | Prose, metadata, decisions and numeric evidence have consistent, distinct roles in both locales. |
| 3 | Simplify sign-in and remove the decorative bars. | At 390 × 844, the initial screen contains the email, password and sign-in controls with the demo disclosure still available. |

## 5. Proposed direction: Academic Review Desk

**A precise workspace organized like an academic review file:** a task brief, a record of the student's attempt, criterion-level evidence, and an explicit human decision. White document surfaces sit on a cool neutral canvas. Teal identifies actions and selection; rules, alignment, and readable typography carry the hierarchy.

The distinctive feature should be the connection between work and its academic record. Decorative school imagery, oversized serif headlines, achievement badges and AI sparkle motifs do not help that connection.

### Reference basis and design decisions

No live Refero tools were available. Research used the existing rendered product and the installed skills' bundled references; no live Refero screens or flows are claimed.

| Decision | Reference | What is adopted |
|---|---|---|
| Dominant direction: document and evidence workspace | Anti-ai-slop [Research Archive](C:/Users/HP/.agents/skills/anti-ai-slop-ui/references/visual_directions.md) | Clear source metadata, readable documents, evidence tables, restrained motion. Keep UniAssist's cool neutrals and required teal. |
| Main structural pattern | Anti-ai-slop [Evidence Ledger and Workflow Timeline](C:/Users/HP/.agents/skills/anti-ai-slop-ui/references/layout_patterns.md) | Connect entity context, evidence and actual state. Use timeline steps only where supported by the API. |
| Operational density for staff | Anti-ai-slop [dashboard contrast example](C:/Users/HP/.agents/skills/anti-ai-slop-ui/examples/bad_to_good_dashboard.md) | Filters, aligned rows, review priority and useful details; do not introduce decorative KPI cards. |
| Surface and color discipline | Refero [anti-slop](C:/Users/HP/.codex/plugins/cache/refero/refero/1.0.2/skills/refero-design/references/anti-ai-slop.md) and [color](C:/Users/HP/.codex/plugins/cache/refero/refero/1.0.2/skills/refero-design/references/color.md) | Use fewer containers and strict semantic color roles. Avoid replacing one template with a cream/serif/earth-tone template. |
| Bilingual reading and scanning | Refero [typography](C:/Users/HP/.codex/plugins/cache/refero/refero/1.0.2/skills/refero-design/references/typography.md), existing Arabic UI, AGENTS.md | Work-tool typography, controlled line length, local font assets, Arabic-specific spacing. |
| Human authority remains explicit | AGENTS.md and API guide | Professor release is distinct from AI evaluation; tutoring, private guidance, and student feedback retain their access boundaries. |

These decisions form a proposed reference lock for a future implementation, not an implemented or visually validated redesign.

### Screen composition

**Student task list:** compact page title and filters, then task rows showing type/title, deadline, latest-attempt state, and “Open task.” Urgency uses the existing 48-hour definition. Do not label a task “ready to submit” from its deadline alone; eligibility comes from the server. Avoid introducing “unread feedback” or “started work” states without supporting data.

**Student task detail:** task title and exact deadline, a visible eligibility/action area, instructions/reference, approved criteria, and attempt history. On wide screens, use a reading column with a 320px context column. On mobile, place action/eligibility near the title; keep criteria accessible before submitting.

**Staff task detail:** task context followed by local destinations for review, rubric versions, and private guidance. Existing counts inform emphasis. Preparation controls remain accessible, but an empty private-guidance editor should not dominate every visit. TA and professor use the same workspace; professor-only approval/release controls retain their authority boundaries.

**Staff submission review:** a compact attempt receipt above the existing artifact/evidence split. Present criterion name, available reasoning/findings, and AI score in aligned rows. Put explicit release controls after the evidence, with a visible route to that section. Do not imply every AI finding has a verified artifact citation.

**Student result:** status and provenance → released feedback → confirmed grade out of the associated total → criterion evidence → artifact and reference details. Before release, preserve the current withholding of all provisional assessment content.

**Tutor, teams, repositories and admin:** carry over typography and surface roles, preserving each workflow's structure. Tutor conversations remain task-linked and private. Repository snapshots retain SHA/provenance and omitted-file notices. Admin remains a separate operations workspace with no added academic visibility.

### Two signature components

1. **Attempt receipt.** A compact ruled record: attempt number, submitted timestamp, associated rubric version/total, current state, and release timestamp when supplied. For repository evidence, include the saved commit identity with access to its full SHA. Never invent missing event times or imply a saved snapshot is already submitted.
2. **Criterion evidence rows.** Expectations, available assessment reasoning, and AI points occupy consistent positions. Professor-confirmed overall grade is visually distinct from unchanged AI criterion scores. Mobile stacks the same fields in reading order.

## 6. Proposed design tokens

These values are a concrete starting specification. They require rendered English/Arabic validation before adoption.

### Palette

| Token | Value | Role |
|---|---|---|
| `color.canvas` | `#F4F7F6` | Cool neutral page background |
| `color.surface` | `#FFFFFF` | Documents, forms, dialogs |
| `color.surfaceSubtle` | `#EDF2F1` | Secondary context and table headers |
| `color.text` | `#203431` | Headings and body |
| `color.textMuted` | `#526663` | Metadata and supporting copy |
| `color.divider` | `#D7E1DF` | Decorative separators, not the sole control boundary |
| `color.controlBorder` | `#78908B` | Input boundaries |
| `color.action` | `#12645E` | Primary actions and active navigation |
| `color.actionHover` | `#0D4C48` | Hover/pressed action emphasis |
| `color.onAction` | `#FFFFFF` | Text on filled action buttons |
| `color.selection` | `#E4F1EE` | Selected row/destination background |
| `color.focus` | `#0F766E` | Focus outline, 2px with 3px offset |
| `color.successText` / `successBg` | `#1D6344` / `#EAF4ED` | Confirmed/released status |
| `color.warningText` / `warningBg` | `#85550B` / `#FFF5DE` | Due soon, attention, provisional or mock notices with explicit labels |
| `color.dangerText` / `dangerBg` | `#A02C32` / `#FCEFF0` | Errors and destructive decisions |
| `color.infoText` / `infoBg` | `#315E80` / `#EDF3F8` | Informational context |

Teal is not a decoration for every card. Distinguish “Submitted,” “Instructor review in progress,” and “Grade released” with text; color supplements the label. Different warning meanings must retain explicit wording. Keep the local/demo disclosure separate from assessment mock provenance.

Calculated contrast ratios: primary text/white **13.15:1**, muted text/white **6.11:1**, white/action **6.98:1**, and the four status text/background pairs **5.87–6.46:1**. Control border/white is **3.41:1**. These are sRGB calculations for the specified pairs, not a full rendered accessibility pass.

### Typography

| Token | Proposed value |
|---|---|
| `font.latin` | `"Source Sans 3", Arial, sans-serif` |
| `font.arabic` | `"Noto Sans Arabic", sans-serif` — retain existing bundled family |
| `font.mono` | `ui-monospace, "Cascadia Code", Consolas, monospace` |
| `type.pageTitle` | 30px / 38px, weight 700; mobile 26px / 34px |
| `type.sectionTitle` | 20px / 28px, weight 600 |
| `type.itemTitle` | 17px / 26px, weight 600 |
| `type.body` | 16px / 26px; Arabic 16px / 30px |
| `type.label` | 14px / 22px, weight 600; Arabic line-height 26px |
| `type.metadata` | 13px / 20px; Arabic 13px / 24px |
| `type.score` | 24px / 32px, weight 600, tabular figures |
| `type.code` | 13px / 21px, monospace, isolated LTR where appropriate |
| `measure.prose` | Maximum 68ch English; initial 60ch Arabic, tune against rendered text |

Source Sans 3 is a proposed new local asset, selected for its UI purpose; Adobe describes the family as designed for user-interface environments. [Official Source Sans repository](https://github.com/adobe-fonts/source-sans). Bundle required weights locally; do not introduce build-time font fetching. The Arabic pairing and exact line metrics still need visual validation.

Use weights 400/600/700, matching the existing Arabic assets. Arabic headings use natural line-height around 1.5 and `letter-spacing: 0`; do not apply Latin uppercase/tracking treatments. Use tabular numbers for comparable scores/counts, while retaining localized timestamp formatting. Monospace is for identifiers/code, not body prose. Keep KaTeX's math fonts.

### Spacing, surfaces, and layout

| Token | Proposed value/rule |
|---|---|
| `space.scale` | 4, 8, 12, 16, 24, 32, 48px |
| `layout.maxWidth` | 1280px for workspace; prose constrained independently |
| `layout.pageGutter` | 16px mobile, 24px tablet, 32px desktop |
| `layout.sectionGap` | 32px desktop; 24px mobile |
| `layout.columnGap` | 24px |
| `layout.contextWidth` | 320px when a second column fits comfortably |
| `layout.breakpoints` | Below 640px: stacked; 640–1023px: flexible rows; 1024px+: optional context/review columns |
| `density.taskRow` | Minimum 72px; 12–16px block padding; grow for Arabic/long titles |
| `density.tableRow` | Minimum 48px; grow naturally for wrapping |
| `density.control` | Minimum 44px interactive target; input text 16px |
| `surface.documentPadding` | 24px desktop, 16px mobile |
| `surface.toolbarPadding` | 0–12px; no automatic outer card |
| `radius.control` | 6px |
| `radius.document` | 8px where an outer container is justified |
| `radius.dialog` | 12px |
| `radius.row` | 0px; rows separated with rules |
| `radius.status` | 4px; pills reserved for genuinely compact tags if needed |
| `shadow.surface` | None |
| `shadow.popover` | `0 4px 16px rgb(32 52 49 / 12%)` |
| `shadow.dialog` | `0 12px 40px rgb(32 52 49 / 16%)` |

Use logical properties so layouts mirror in Arabic. Avoid fixed row heights. On mobile, preserve labels when tables become stacked records; contain horizontal scrolling for code, equations and tables that need it. A sticky context area must release at narrow widths and never cover focused controls.

### Icons and motion

| Token | Proposed value/rule |
|---|---|
| `icon.family` | Existing Lucide dependency; restrained outline icons |
| `icon.size` | 16px inline, 20px toolbar; hit area remains at least 44px |
| `icon.stroke` | 1.75–2px, consistent within each component |
| `motion.fast` | 120ms for color/opacity state changes |
| `motion.normal` | 180ms for opening/closing a disclosure or dialog |
| `motion.easing` | `cubic-bezier(0.2, 0, 0, 1)` |
| `motion.reduced` | Remove transforms and nonessential transitions; preserve textual progress feedback |

Use icons for actions and meaning, not to fill every heading. Mirror directional navigation icons, not identifiers or math. No card lifting, animated gradients, decorative reveals, or invented percentage progress for synchronous evaluation.

## 7. Score breakdown

### AI Slop Score — 5/10

Each category is scored 0–2 using the [skill rubric](C:/Users/HP/.agents/skills/anti-ai-slop-ui/rubrics/ai_slop_score.md).

| Category | Score | Rationale |
|---|---:|---|
| Palette defaultness | 0 | Restrained teal is explicitly appropriate to the product; no generic AI-purple treatment. |
| Layout defaultness | 1 | Repetitive task grid and stacked sections, offset by a meaningful artifact/review split and review tables. |
| Component defaultness | 2 | Rounded white panels, nested borders, badges and button treatments dominate the reviewed UI with a starter-kit appearance. |
| Typography genericness | 1 | Clear basic hierarchy and intentional Arabic coverage, but little distinction between academic reading and generic application text. |
| Decorative noise | 1 | Sign-in bars and oversized promotional spacing add a small amount of purposeless decoration; no pervasive effects. |
| **Total** | **5** | **Revise the highest-impact areas. A wholesale visual reset is unnecessary.** |

### Distinctiveness Score — 5/10

Each category is scored 0–2 using the [skill rubric](C:/Users/HP/.agents/skills/anti-ai-slop-ui/rubrics/distinctiveness_score.md).

| Category | Score | Rationale |
|---|---:|---|
| Product fit | 2 | Real rubric, attempt, evidence, staff authority and bilingual workflows are clearly present. |
| Visual system clarity | 1 | Consistent palette and reusable primitives, but weak semantic token coverage and surface differentiation. |
| Layout character | 1 | Some workflow-specific arrangements; too many screens still inherit the same panel stack. |
| Typographic identity | 1 | Readable but not especially recognizable; bilingual roles need refinement. |
| Signature moments | 0 | Strong domain information has not yet become a recognizable visual pattern. |
| **Total** | **5** | **MVP-appropriate; the task rows, attempt receipt and evidence rows are three concrete ways to improve it.** |

Implementation Readiness Score is not assigned: this deliverable is a review and token proposal, with no redesigned screen built or tested. Suggested future goals are AI Slop ≤3 and Distinctiveness ≥7, to be rescored from actual renders.

## 8. Future implementation sequence and acceptance gate

1. Define semantic tokens and surface roles in `globals.css` and shared components. Add local Latin font assets only during an authorized implementation.
2. Prototype one populated student task list and one staff task/review screen using real API-shaped data. Establish the visual direction before applying it across every feature.
3. Update `tasks.tsx` and `teaching.tsx` for task rows and staff navigation. Preserve query filters, latest-attempt defaults, server eligibility and existing mutations.
4. Update `review.tsx` and rubric presentation for the receipt/evidence pattern and student feedback-first ordering. Preserve associated rubric totals, provisional-data gates and explicit professor confirmation.
5. Apply the confirmed typography, navigation and surface vocabulary to auth and secondary screens, retaining their distinct permissions and privacy boundaries.
6. Inspect English/Arabic at 390px, 768px and 1440px, plus 200% zoom. Check long task titles, long equations, filenames/SHAs, empty states, failures, pending evaluation, released mock results and real-result presentation when available.

Before shipping a later implementation, verify keyboard order, focus visibility, dialog focus/escape behavior, contrast, touch targets, reduced motion and mobile overflow. Preserve input/upload references on failure and explicit retry behavior. Test applicable role/release journeys after the visual changes.

The visual acceptance question is concrete: can a student locate the next permitted action and useful feedback quickly, and can staff connect an attempt to its exact rubric and evidence without scrolling through unrelated editors? Keep every privacy, consent and academic authority boundary intact while improving that experience.

## 9. Implementation and verification — 22 September 2026

Applied the agreed Academic Review Desk direction using the [humanize-ui skill](C:/Users/HP/.codex/plugins/cache/humanize-ui/humanize-ui/0.1.0/skills/humanize-ui/SKILL.md). The teal brand, existing React/Radix components, localized routes and academic behavior are retained.

### Delivered

- Semantic palette, surfaces, radius, focus, motion, typography and density tokens in `frontend/src/app/globals.css`. CSS layers allow local utility overrides without the previous global panel styles unexpectedly winning.
- Locally bundled Source Sans 3 at weights 400/600/700, alongside the existing Noto Sans Arabic. The only added package is `@fontsource/source-sans-3@5.3.0`; no UI or animation library was added. Arabic selects its own font, and the wordmark stays isolated LTR.
- Compact task rows with exact deadlines, truthful latest-attempt states and existing staff review counts. Raw Markdown/math excerpts were deliberately omitted from the dense list; full instructions retain the academic renderer.
- Workspace navigation with visible active destinations, compact account utilities and discoverable language switching. Demo disclosure remains visible.
- Task actions and eligibility near the title. Instructions and context form a reading/context layout on desktop and stack on mobile. Accepted criteria remain visible on task and submission pages.
- Staff task navigation links directly to review, rubrics, guidance and insights. The submission queue now comes before preparation editors. Native section links preserve browser and keyboard behavior without introducing a tabs dependency.
- Attempt records connect submission time, actual rubric version/total, status, release time when available and repository SHA when present. Student results put released feedback before grades and supporting artifacts. Staff retain the artifact/evidence split and explicit professor decision controls.
- Ruled criterion evidence rows and consistent preview/notice styling. Semantic colors carry through tutoring, teams, repository evidence, profiles and operations without changing their permission boundaries.
- Mobile sign-in begins with the form and disclosure. The decorative bars were replaced by a concise, accurate description of the human-supervised academic process on desktop.

### Additional research applied

The [shadcn Item pattern](https://ui.shadcn.com/docs/components/base/item) informed task-row composition: separate content, metadata and action areas. The [shadcn Table pattern](https://ui.shadcn.com/docs/components/base/table) supported aligned operational data. These ideas were implemented with the project's existing elements and APIs; no registry code or alternative component foundation was installed. The inherited Research Archive/Evidence Ledger references remain the dominant direction. Beautiful UI was also attempted but unavailable, so it supplied no implementation evidence.

### Verification completed

| Check | Result |
|---|---|
| TypeScript | Passed |
| ESLint | Passed |
| Frontend component/contract tests | **54 passed**; includes English/Arabic release gating and feedback-before-grade/artifact order |
| Production Docker build | Passed with local font assets |
| Real-backend Playwright journeys | **16 passed**, rerun successfully after the Arabic-font correction |
| Responsive layout | English/Arabic checks at 390, 768 and 1440px; no page overflow in tested views |
| Magnification | Task-row reflow at 200% CSS zoom; this is browser-rendered CSS magnification, not a cross-browser native zoom certification |
| Keyboard and motion | Visible focus, dialog cancel focus, Escape dismissal and focus restoration, reduced-motion transitions verified |
| Locale behavior | Actual Arabic font family checked; route/query filters survive language switching |
| Visual inspection | Desktop sign-in/task rows/task detail; Arabic mobile sign-in, task list, staff task, released result and long equations inspected |

The browser suite covers account correction/suspension, teams, public repository fixtures, lab/rubric workflows, three-role assessment/release, tutoring/retry, sharing/revocation, private guidance/insights, upload recovery and session/origin behavior. Generated screenshots are under `frontend/test-results/`; they are verification artifacts and can be replaced by later runs.

Two issues found during verification were fixed before handoff: a stylesheet byte-order mark broke production CSS parsing, and an unlayered root font token overrode the Arabic locale font. The final build and browser run include both fixes.

Only the isolated `uniassist-verify` frontend was rebuilt/restarted, available at `http://localhost:13000`. Backend contracts and migrations were unchanged. The tests use mock AI/public-repository fixtures; live-provider acceptance and Safari/Firefox or complete assistive-technology audits were not performed.

### Post-implementation visual gate

Qualitative rescore of the inspected implementation: **AI Slop 2/10** (palette 0, layout 0, components 1, typography 1, decoration 0); **Distinctiveness 8/10** (product fit 2, system clarity 2, layout character 2, typography 1, signature moments 1). Remaining room for improvement is concentrated in secondary screens that still use conventional document panels. The main task and review journeys now express the product through their structure.

## 10. Independent rerun of the rubric and lint — 22 September 2026

Reran the anti-ai-slop-ui review after removal of the local/demo notice. The installed script is named `ui_lint.py` (the request called it `ul_lint.py`). No application code was changed during this review.

```powershell
python C:\Users\HP\.agents\skills\anti-ai-slop-ui\scripts\ui_lint.py frontend/src
```

**Actual script result: `AI Slop Risk: 0.0/10`.** Scanned **28** eligible UI source files, with **zero findings**. The scan covers authored HTML/JSX/TSX/CSS and related UI formats under `frontend/src`, rather than dependencies or generated build output. It does not scan translation JSON or assess rendered usability.

The script prints five generic recommendations even when there are no findings. Its suggestions about purple gradients, emoji, radius, feature cards and adding tokens are unconditional boilerplate, not newly detected problems in UniAssist. It does not calculate a Distinctiveness Score.

Fresh screenshots were captured and inspected from the running verification frontend: English desktop sign-in, populated staff task list, populated staff task detail, and Arabic mobile staff task detail. The review also uses the previously inspected student attempt/result patterns and current source. This is a focused visual recheck, not a fresh exhaustive accessibility audit.

| Measurement | Original review | Current rerun |
|---|---:|---:|
| Script risk (lower is better) | Not run in the original review | **0.0/10** |
| Visual AI Slop Score (lower is better) | 5/10 | **2/10** |
| Visual Distinctiveness Score (higher is better) | 5/10 | **8/10** |

The visual scores remain consistent with the implementation review; removing the notice does not justify an artificial score increase. Slop categories remain palette **0**, layout **0**, components **1**, typography **1**, decoration **0**. Distinctiveness categories remain product fit **2**, system clarity **2**, layout character **2**, typography **1**, signature moments **1**.

### Remaining visual weaknesses and next priorities

1. **Repeated document panels:** rubric, guidance and other supporting sections still repeat a white bordered container. The tokens are coherent, but the rhythm remains conventional. Where grouping stays clear, replace additional outer containers with simple section rules.
2. **Long preparation sections:** the empty guidance editor and Markdown preview occupy considerable vertical space, especially in Arabic. A deliberate edit/disclosure interaction could shorten routine review visits while preserving drafts and discoverability. Keep the queue first.
3. **Mobile review tables:** the Arabic queue uses contained horizontal scrolling, leaving some columns offscreen. Labeled stacked records or a stronger scroll affordance would improve scanability. This is a usability refinement, not a lint failure.
4. **Restrained rather than memorable typography:** the bilingual fonts and roles fit the product, but the identity comes primarily from task/evidence structure. Strengthen consistent metadata and evidence alignment before considering another font change.

These patterns persist because generic document containers still carry several secondary workflows; they are not evidence of excessive decoration or a need for a new library. Keep the existing Academic Review Desk direction and tokens. Decision: **retain the current design and address these as focused refinements**. A zero heuristic score should not be interpreted as a perfect interface.

## 11. Ten-phase full-humanization roadmap — 22 September 2026

This roadmap continues the Academic Review Desk direction from the current measured baseline: **AI Slop 2/10**, **Distinctiveness 8/10**, and heuristic risk **0.0/10**. The completion target is AI Slop at or below **1/10**, Distinctiveness at or above **9/10**, and heuristic risk remaining **0.0/10**.

### Reference lock

The existing task rows, attempt receipt, criterion evidence rows and explicit professor decision area are the internal build target. Preserve the cool neutral canvas, white document surfaces, restrained teal action role, Source Sans 3 and Noto Sans Arabic, thin rules, compact metadata, tabular figures, minimal shadow and functional motion.

The implementation adapts narrow interaction patterns from several sources without importing their component libraries:

- [Primer ActionList](https://primer.style/product/components/action-list/) informs single-column records with descriptions and trailing status.
- [GOV.UK task lists](https://design-system.service.gov.uk/components/task-list/) inform concise whole-row actions and readable sentence-case states.
- [GOV.UK summary lists](https://design-system.service.gov.uk/components/summary-list/) inform key/value provenance and account records.
- [Carbon accordion](https://carbondesignsystem.com/components/accordion/usage/) informs progressive disclosure of optional history and preparation content.
- [Carbon data tables](https://carbondesignsystem.com/components/data-table/usage/) inform full-width operational data with consistent density.

The palette, fonts, radii, spacing, semantic colors and motion values in section 6 remain locked. New presentation roles use the existing tokens: ruled record lists, summary lists, chronological history, native disclosures and action wells. No frontend dependency, backend contract, route, permission or academic rule is added.

### Phase tracker

| Phase | State | Deliverable | Acceptance |
|---|---|---|---|
| 1. Shared desk patterns | **Complete** | Reusable record, summary, history, disclosure, document-section and action-area CSS patterns | Logical properties, 44px disclosure targets, mobile stacking and existing tokens verified |
| 2. Responsive review data | **Complete** | Submission queue and insight tables are full-width datasets with labeled mobile records | Native table headers remain; translated labels replace routine horizontal scrolling below 640px |
| 3. Private grading guidance | **Complete** | Intentional new-version disclosure and compact version history | Draft survives disclosure changes; disabling guidance remains explicit |
| 4. Rubric preparation | **Complete** | Rubric evidence ledger with disclosed creation/refinement tools | Version, source, status, total and professor authority remain clear |
| 5. Teams and invitations | **Complete** | Whole-row team records, roster decisions and chronological lifecycle history | Consent, approval, locking and conflict behavior remain unchanged |
| 6. Repository evidence | **Complete** | Repository, commit, snapshot and attribution evidence ledger | Full SHA, fixture, omitted-file and authorization context stay prominent |
| 7. Tutoring and sharing | **Complete** | Academic transcript, session records and frozen-share preview | Privacy, retries, language, revocation and draft behavior remain intact |
| 8. Profile and operations | **Complete** | Summary-list identity, account records, audit history and aligned metrics | Operations reveal no academic content and retain version checks |
| 9. Task and submission forms | **Complete** | Ruled form sections, deliberate preview hierarchy and evidence receipts | Eligibility, input/upload recovery and ambiguous-mutation handling remain intact |
| 10. Bilingual visual QA | Planned | Full English/Arabic responsive audit, final score and evidence | Typecheck, lint, unit, build, E2E and anti-slop gates pass |

Each completed phase records its behavior and verification here before its commit is published. The current task list and assessment review hierarchy are regression references throughout all ten phases.

### Phase 2 evidence

The submission review queue and criterion analytics now use the Carbon-informed full-width data treatment. Column headers carry explicit `scope="col"`; at narrow widths the same table rows become vertically ruled records with visible translated field labels. The queue retains its URL-backed latest/status filters, status wording, exact timestamp and review link. Focused English/Arabic component coverage verifies both datasets and all mobile labels.

### Phase 3 evidence

Private guidance now keeps its purpose and release-safety warning visible while the empty editor and preview remain closed until staff choose “Add a guidance version.” The native disclosure retains its mounted editor, so typed content survives closing and reopening. Saving empty content still uses the existing explicit confirmation to disable guidance for future evaluations. Immutable versions use transparent ruled disclosures, with the newest version identified in the history.

### Phase 4 evidence

Rubric preparation now reads as a version ledger before it reads as an editor. AI suggestion remains a direct task action; manual version creation and per-version refinement use native ruled disclosures whose mounted inputs retain local drafts. Version, source, status, criteria, point totals and professor approval controls stay visible outside those disclosures. The approval area uses the same explicit action rule as final academic decisions.

### Phase 5 evidence

Team and invitation collections now use Primer/GOV.UK-inspired whole-row destinations: the name and concise roster context lead, while sentence-case lifecycle state or invitation time trails. Team detail uses a summary list for status, version and lock time; roster members and pending invitations share one ruled record list. Consent, invitation, approval and archive actions remain explicit action areas, and preserved roster events read as a chronological history inside an optional native disclosure.

### Phase 6 evidence

Repository proposals now scan as whole-row records with repository identity, fixture provenance and lifecycle state. Repository detail uses key/value rows for approval version, last sync and bounded-history status; commits form a ruled evidence ledger with attribution and snapshot actions kept beside the exact commit. Captured evidence uses a summary list for URL, full SHA, capture time and omitted-file count, while the archive hash and file manifest remain available through a native disclosure. Immutable repository events use the shared chronological history treatment.

### Phase 7 evidence

Tutoring now reads as an academic transcript: each persisted question and tutor response has a stable speaker column, exact question timestamp and ruled reading area, with pending, failed and mock states attached to the response they qualify. Conversation sessions and received shares use whole-row records with trailing language, time or state. Earlier unverified messages and frozen-share preparation use native progressive disclosure; shared previews and recipient snapshots reuse the transcript treatment. Request deduplication, draft retention, polling, explicit retries, fixed conversation language, recipient-only sharing and revocation behavior are unchanged.

### Phase 8 evidence

Profile and account detail screens now separate immutable identity facts from the fields that can be changed, using aligned summary rows and an explicit correction action area. Account search results are whole-row destinations with trailing account state. Content-free audit events use a chronological history, while AI operation groups present technical provider/operation identity above aligned, tabular numeric rows. Existing optimistic version checks, supported role boundaries, suspension safeguards and the prohibition on academic content in operations remain unchanged.

### Phase 9 evidence

Task creation now separates task instructions, audience and timing, and type-specific submission requirements into ruled fieldsets, with the existing Markdown/math preview kept beside the authored instructions. Upload progress, ambiguous-create reconciliation and the final create action share one action area. Student submission separates the preserved attempt text from file or repository evidence, then reports upload receipt and attempt creation state in a dedicated action area. Eligibility still comes from the server, successful uploads are retained after failure, ambiguous mutations require a server refresh, and no mutation is automatically retried.
