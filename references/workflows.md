# Operational Workflows: Superagent Multi-Agent Execution

This guide provides the complete end-to-end execution workflow for running the Superagent architecture.

---

## Stage 1: Requirements Breakdown into Tickets

Before initiating development, decompose the project brief or PRD into modular tickets:

1. **Scaffold Board & Tickets:**
   ```bash
   python3 scripts/ticket_manager.py init
   python3 scripts/ticket_manager.py create "User Authentication" --mode team --runs alongside
   python3 scripts/ticket_manager.py create "Dashboard Layout" --mode solo --runs alongside
   python3 scripts/ticket_manager.py create "Billing Portal" --mode solo --runs "waiting on 1"
   ```

2. **Complete the Ticket Specs:**
   * Edit `specs/tickets/01-user-authentication/rd.md` with explicit scope and files.
   * Edit `specs/tickets/01-user-authentication/eval.md` with deterministic test commands.

3. **Promote to Ready:**
   * Once validated, mark the tickets as ready for the Router:
   ```bash
   python3 scripts/ticket_manager.py set-status 1 ready
   python3 scripts/ticket_manager.py set-status 2 ready
   ```

---

## Stage 2: Launching the Orchestrator (Router)

1. **Start the Router Session:**
   * The Router is launched with automatic permission mode enabled so it can execute checks and dispatch subagents autonomously.
   * Command:
     ```bash
     claude --agent Router --dangerously-skip-permissions
     ```
   * Prompt the Router:
     > *"Inspect `specs/tickets/board.md` and begin dispatching all tickets marked 'ready' that are unblocked."*

2. **Router Background Tasks:**
   * Immediately schedule the Sentinel Watchdog to run periodically in the background:
     ```bash
     python3 scripts/sentinel_watchdog.py --threshold 15
     ```

---

## Stage 3: Executor Dispatch & Worktree Isolation

For each unblocked `ready` ticket:

1. **Provision Git Worktree:**
   ```bash
   python3 scripts/worktree_manager.py create <TICKET_ID> --base main
   python3 scripts/ticket_manager.py set-status <TICKET_ID> in_progress --assignee Executor-<ID>
   ```

2. **Spawn Executor Agent:**
   * Launch a dedicated subagent pointing to `.worktrees/ticket-<TICKET_ID>/`.
   * Pass the contents of `rd.md` and `eval.md` in the prompt.
   * In **Solo Mode**, one subagent works in the worktree.
   * In **Team Mode**, multiple collaborative subagents communicate using the Agent Teams mechanism against a shared contract.

3. **Executor Development Loop:**
   * Implement code exclusively inside `.worktrees/ticket-<TICKET_ID>/`.
   * Run local lint, tests, and build.
   * Capture verification proof in `.worktrees/ticket-<TICKET_ID>/proof/`.
   * Commit changes to `feature/ticket-<TICKET_ID>`.

---

## Stage 4: Evaluation Gate & Integration

1. **Router Evaluation:**
   * When Executor reports done, the Router reads the Executor's proof and checks every assertion in `eval.md`.
   * **If criteria fail:** Router keeps the ticket `in_progress` and instructs the Executor to resolve the specific failing checks.
   * **If criteria pass:** Router marks ticket `review` → `merged`.

2. **Merge Worktree to Main:**
   * Launch the Combiner agent to execute:
     ```bash
     python3 scripts/worktree_manager.py merge <TICKET_ID> --target main
     ```

3. **Verifier E2E Test:**
   * Verifier agent launches the application in a headless browser (Playwright / Agent Browser).
   * Runs functional UI walk-throughs.
   * **On Success:** Prune the worktree:
     ```bash
     python3 scripts/worktree_manager.py remove <TICKET_ID> --delete-branch
     ```
     Unlock any dependent tickets on `board.md` (e.g. changing status from `draft` to `ready`).
   * **On Failure:** Spawn **Reproduction Agent** to diagnose, patch, and re-verify before finalizing merge.
