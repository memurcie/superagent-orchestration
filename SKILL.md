---
name: superagent-orchestration
description: Multi-agent software engineering orchestration based on DeepSeek's Superagent architecture. Decomposes tasks into file-driven ticket contracts (rd.md, eval.md, board.md), enforces a strictly non-coding Router orchestrator, isolates worker sessions in dedicated Git worktrees, monitors cluster health with a background Sentinel Watchdog, and integrates via Combiner, Verifier, and Reproduction agents. Use when user wants to run multi-agent coding workflows, coordinate multiple Claude Code or Antigravity sessions, prevent context thrashing, build complex software autonomously, or implement the DeepSeek superagent pattern.
---

# Superagent Multi-Agent Orchestration

Implements the **DeepSeek "Superagent" multi-agent architecture** in Claude Code and Antigravity. Eliminates context thrashing and human cognitive overload by dividing responsibilities between a strictly non-coding Router, isolated Git worktree Executors, a background Sentinel Watchdog, and automated integration agents.

```
[User] ◄──► [Router Agent (Frontier Tier)] ◄───► [specs/tickets/board.md]
                     │
         ┌───────────┴───────────┬──────────────────────┐
         ▼                       ▼                      ▼
[Sentinel Watchdog]       [Solo Executor]        [Team Executors]
(Background Monitor)    (.worktrees/ticket-01)  (.worktrees/ticket-02)
                                 │                      │
                                 ▼                      ▼
                            [eval.md Gate] ◄────────────┘
                                 │
                                 ▼
                         [Combiner Agent] ──► Merges Worktree to Main
                                 │
                                 ▼
                         [Verifier Agent] ──► E2E Browser Testing
                                 │ (On Failure)
                                 ▼
                       [Reproduction Agent] ──► Auto-Diagnose & Patch
```

---

## Core Rules

1. **Router Does NOT Code:** The Router coordinates, dispatches, and validates. It must never edit application source code, preventing context contamination.
2. **Strict Workspace Isolation:** Every Executor works exclusively inside its allocated Git worktree (`.worktrees/ticket-<ID>/`) on branch `feature/ticket-<ID>`.
3. **No Unspecified Work:** Tasks must exist as structured ticket directories in `specs/tickets/` with both `rd.md` (requirements) and `eval.md` (acceptance criteria).
4. **Autonomous Gates:** Code merges only after passing `eval.md` automated checks and Verifier browser testing.

---

## Quick Start: 4-Step Orchestration Loop

### Step 1: Initialize Board & Tickets

Decompose features into tickets using `scripts/ticket_manager.py`:

```bash
# Initialize specs/tickets/board.md
python3 scripts/ticket_manager.py init

# Create tickets (solo or team mode)
python3 scripts/ticket_manager.py create "OAuth Google Login" --mode team --runs alongside
python3 scripts/ticket_manager.py create "User Profile Card" --mode solo --runs alongside
python3 scripts/ticket_manager.py create "Subscription Billing" --mode solo --runs "waiting on 1"

# Promote tickets to ready when specifications in rd.md and eval.md are filled
python3 scripts/ticket_manager.py set-status 1 ready
python3 scripts/ticket_manager.py set-status 2 ready
```

* For template definitions and field semantics, see [references/ticket_templates.md](references/ticket_templates.md).

---

### Step 2: Launch the Router & Sentinel

1. Launch Claude Code / Antigravity with the Router role and automated permissions enabled:
   ```bash
   claude --agent Router --dangerously-skip-permissions
   ```
2. Spawn the **Sentinel Watchdog** in the background to monitor executor activity every 10 minutes:
   ```bash
   python3 scripts/sentinel_watchdog.py --root . --threshold 15
   ```
   * If any executor is silent or locked for >15 minutes, Sentinel alerts the Router.

---

### Step 3: Dispatch Executors in Isolated Worktrees

For each ticket marked `ready` and unblocked on `board.md`:

1. **Create the isolated Git worktree:**
   ```bash
   python3 scripts/worktree_manager.py create 1 --base main
   python3 scripts/ticket_manager.py set-status 1 in_progress --assignee Executor-01
   ```
2. **Launch the Executor Subagent:**
   * Direct the Executor to `.worktrees/ticket-01/`.
   * Pass the ticket's `rd.md` requirements and `eval.md` tests.
   * **Solo Mode:** Single subagent completes implementation.
   * **Team Mode:** Subagents collaborate using Claude Code agent teams.
   * Executor saves logs, test outputs, or UI snapshots in `.worktrees/ticket-01/proof/`.

* See [references/agent_configs.md](references/agent_configs.md) for detailed system prompts and role boundaries.

---

### Step 4: Verification, Merge & Bug Triage

1. **Router Evaluation:** When the Executor finishes, Router verifies all criteria in `eval.md`.
2. **Merge via Combiner:**
   ```bash
   python3 scripts/worktree_manager.py merge 1 --target main
   ```
3. **Browser E2E Verification:** Verifier tests the merged app in a headless browser (Playwright / Agent Browser).
   * **If tests pass:** Clean up worktree and unlock dependent tickets:
     ```bash
     python3 scripts/worktree_manager.py remove 1 --delete-branch
     python3 scripts/ticket_manager.py set-status 1 merged
     ```
   * **If tests fail:** The **Reproduction Agent** inspects browser traces, reproduces the issue, and applies an isolated hotfix.

* For complete end-to-end operational guides, see [references/workflows.md](references/workflows.md).

---

## Bundled CLI Tools

| Script | Purpose | Key Commands |
|---|---|---|
| `scripts/ticket_manager.py` | Scaffold, list, and update tickets and `board.md` | `init`, `create <title>`, `list`, `set-status <id> <status>` |
| `scripts/worktree_manager.py` | Create, list, merge, and prune isolated Git worktrees | `create <id>`, `list`, `merge <id>`, `remove <id>` |
| `scripts/sentinel_watchdog.py` | Detect stalled sessions, circular deadlocks, and stale worktrees | `sentinel_watchdog.py --root . [--json]` |

---

## Reference Guides

* [references/agent_configs.md](references/agent_configs.md): System prompts, tool access restrictions, and model tiers for Router, Sentinel, Executor, Combiner, Verifier, and Reproduction agents.
* [references/ticket_templates.md](references/ticket_templates.md): Standard schemas for `board.md`, `rd.md`, and `eval.md`.
* [references/workflows.md](references/workflows.md): Comprehensive step-by-step lifecycle from PRD intake to production merge.
