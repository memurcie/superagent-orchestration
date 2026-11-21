# Ticket Templates & Specification Standards

In the Superagent workflow, tickets are not vague prompts. They are structured contracts between the human/Router and the autonomous Executors.

Each ticket resides in: `specs/tickets/<ID>-<slug>/`

```
specs/tickets/
├── board.md                      # Central task register
├── 01-user-auth/
│   ├── rd.md                     # Requirements & Technical Boundaries
│   └── eval.md                   # Automated & Functional Verification Rules
└── 02-billing-portal/
    ├── rd.md
    └── eval.md
```

---

## 1. `board.md` (Central Registry)

Tracks live progress, execution modality, and dependency graphs.

```markdown
# Tickets Board

| ID | Title | Mode | Status | Runs | Assignee | Last Updated |
|---|---|---|---|---|---|---|
| 01 | [User Auth](01-user-auth/rd.md) | team | merged | alongside | Router | 2026-11-21 14:00 |
| 02 | [Profile Settings](02-profile-settings/rd.md) | solo | ready | waiting on 01 | - | 2026-11-21 14:30 |
| 03 | [Stripe Billing](03-stripe-billing/rd.md) | solo | in_progress | alongside | Executor-2 | 2026-11-21 15:15 |
```

### Column Definitions
* **ID:** Numerical identifier (two digits: `01`, `02`, etc.).
* **Title:** Markdown link pointing directly to the ticket's `rd.md`.
* **Mode:**
  * `solo`: Executed by a single isolated subagent.
  * `team`: Executed by collaborative subagents using agent teams.
* **Status:**
  * `draft`: Being authored or awaiting review.
  * `ready`: Fully specified; ready for Router to dispatch.
  * `in_progress`: Actively worked on by assigned Executor.
  * `review`: Work finished, awaiting Router verification against `eval.md`.
  * `merged`: Integrated into `main` and verified.
  * `blocked`: Waiting on external fix or decision.
* **Runs:**
  * `alongside`: Can execute in parallel immediately.
  * `waiting on <ID>`: Blocked until ticket `<ID>` is marked `merged`.
* **Assignee:** Subagent identifier or session name.

---

## 2. `rd.md` (Requirements & Boundaries)

```markdown
# Feature: [Feature Name] (Ticket #[ID])

## 1. Objective & Scope
- **Summary:** Concise 1-2 sentence description of the goal.
- **In Scope:**
  - Concrete deliverable 1
  - Concrete deliverable 2
- **Out of Scope (Do NOT touch):**
  - Existing legacy components that must remain unmodified
  - Untouched database tables or unrelated API endpoints

## 2. Technical Architecture
- **Target Files to Create/Modify:**
  - `src/components/auth/LoginModal.tsx`
  - `src/server/api/auth.ts`
- **Dependencies & Libraries:**
  - Explicit package versions to use

## 3. Explicit Decisions & Constraints
- Decision 1: Use JWT stored in secure httpOnly cookies.
- Decision 2: Follow existing Tailwind dark theme tokens.

## 4. Worktree Directory
- **Path:** `.worktrees/ticket-[ID]`
- **Branch:** `feature/ticket-[ID]`
```

---

## 3. `eval.md` (Acceptance & Verification)

```markdown
# Evaluation Criteria: [Feature Name] (Ticket #[ID])

## 1. Automated Quality Gates
- [ ] TypeScript / Linter compiles without errors: `npm run lint`
- [ ] Unit tests pass: `npm test -- tests/auth.spec.ts`
- [ ] Build succeeds without warnings: `npm run build`

## 2. Behavioral Verification
- [ ] User can click 'Login' and see the modal appear within 200ms.
- [ ] Submitting valid credentials redirects to `/dashboard`.
- [ ] Submitting invalid password triggers error toast with code 401.

## 3. Edge Cases & Boundary Handling
- [ ] Network timeout handled gracefully with retry prompt.
- [ ] Empty form submission prevented by client-side validation.

## 4. Verification Evidence
- [ ] Test run terminal output saved in `.worktrees/ticket-[ID]/proof/test.log`
- [ ] Screenshot of verified UI state saved in `.worktrees/ticket-[ID]/proof/screenshot.png`
```
