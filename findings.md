# Findings: Superagent Orchestration Repository Setup

- **GitHub Auth:** User `memurcie` is authenticated via `gh` CLI with full `repo` and `workflow` scopes.
- **Repository Name:** `superagent-orchestration`
- **Visibility:** Public (as explicitly requested by user)
- **Included Components:**
  1. `SKILL.md`: Standard specification for Claude Code & Antigravity / Gemini CLI skills.
  2. `scripts/`:
     - `ticket_manager.py`: Ticket & board management CLI
     - `worktree_manager.py`: Git worktree lifecycle management
     - `sentinel_watchdog.py`: Stalled session & deadlock surveillance
  3. `references/`:
     - `agent_configs.md`: System prompts and model parameters
     - `ticket_templates.md`: Structured markdown contracts (`board.md`, `rd.md`, `eval.md`)
     - `workflows.md`: End-to-end operational guide
  4. `assets/architecture.png`: Visual infographic of the multi-agent hierarchy.
