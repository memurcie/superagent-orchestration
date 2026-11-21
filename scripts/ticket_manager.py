#!/usr/bin/env python3
"""
ticket_manager.py - CLI tool for managing the Superagent specs/tickets workflow.
Supports creating, listing, updating, and formatting tickets and board.md.
"""

import argparse
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

BOARD_TEMPLATE = """# Tickets Board

| ID | Title | Mode | Status | Runs | Assignee | Last Updated |
|---|---|---|---|---|---|---|
"""

RD_TEMPLATE = """# Feature: {title} (Ticket #{ticket_id})

## 1. Objective & Scope
- **Summary:** {description}
- **In Scope:**
  - 
- **Out of Scope (Do NOT touch):**
  - 

## 2. Technical Requirements
- Target Files:
  - 
- Dependencies:
  - 

## 3. Explicit Decisions & Constraints
- Decision 1: 

## 4. Worktree Directory
- Path: `.worktrees/ticket-{ticket_id}`
- Branch: `feature/ticket-{ticket_id}`
"""

EVAL_TEMPLATE = """# Evaluation Criteria: {title} (Ticket #{ticket_id})

## 1. Automated Checks
- [ ] Lint check passes: `npm run lint` / `flake8`
- [ ] Unit tests pass: `npm test` / `pytest`
- [ ] Build succeeds: `npm run build`

## 2. Behavioral / Browser Criteria
- [ ] Criterion 1: 
- [ ] Criterion 2: 

## 3. Edge Cases & Boundary Conditions
- [ ] Handled error state / network failure
- [ ] Validated empty/null inputs

## 4. Verification Evidence
- [ ] Screenshot or terminal log recorded in `.worktrees/ticket-{ticket_id}/proof/`
"""


class TicketManager:
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.tickets_dir = root_dir / "specs" / "tickets"
        self.board_file = self.tickets_dir / "board.md"

    def init_workspace(self) -> None:
        """Initialize specs/tickets directory and board.md if not present."""
        self.tickets_dir.mkdir(parents=True, exist_ok=True)
        if not self.board_file.exists():
            self.board_file.write_text(BOARD_TEMPLATE, encoding="utf-8")
            print(f"Created board at: {self.board_file}")
        else:
            print(f"Board already exists at: {self.board_file}")

    def get_next_id(self) -> int:
        """Find the next numerical ticket ID."""
        if not self.tickets_dir.exists():
            return 1
        existing_ids = []
        for item in self.tickets_dir.iterdir():
            if item.is_dir():
                match = re.match(r"^(\d+)-", item.name)
                if match:
                    existing_ids.append(int(match.group(1)))
        return max(existing_ids, default=0) + 1

    def create_ticket(
        self,
        title: str,
        description: str = "",
        mode: str = "solo",
        runs: str = "alongside",
    ) -> Path:
        """Create a new ticket folder with rd.md and eval.md, and register in board.md."""
        self.init_workspace()
        ticket_id = self.get_next_id()
        slug = re.sub(r"[^\w\s-]", "", title.lower()).strip()
        slug = re.sub(r"[-\s]+", "-", slug)[:40]
        ticket_folder_name = f"{ticket_id:02d}-{slug}"
        ticket_folder = self.tickets_dir / ticket_folder_name
        ticket_folder.mkdir(parents=True, exist_ok=True)

        # Write rd.md
        rd_path = ticket_folder / "rd.md"
        rd_content = RD_TEMPLATE.format(
            title=title,
            ticket_id=ticket_id,
            description=description or "Detailed feature specification.",
        )
        rd_path.write_text(rd_content, encoding="utf-8")

        # Write eval.md
        eval_path = ticket_folder / "eval.md"
        eval_content = EVAL_TEMPLATE.format(title=title, ticket_id=ticket_id)
        eval_path.write_text(eval_content, encoding="utf-8")

        # Update board.md
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        row = f"| {ticket_id:02d} | [{title}]({ticket_folder_name}/rd.md) | {mode} | draft | {runs} | - | {now} |\n"
        with self.board_file.open("a", encoding="utf-8") as f:
            f.write(row)

        print(f"Ticket #{ticket_id} created at: {ticket_folder}")
        print(f"Board updated: {self.board_file}")
        return ticket_folder

    def list_tickets(self) -> None:
        """Print the contents of board.md or ticket listing."""
        if not self.board_file.exists():
            print("No board.md found. Run 'init' or 'create' first.")
            return
        print(self.board_file.read_text(encoding="utf-8"))

    def update_status(self, ticket_id: int, new_status: str, assignee: Optional[str] = None) -> bool:
        """Update the status and optional assignee of a ticket in board.md."""
        if not self.board_file.exists():
            print("No board.md found.")
            return False

        lines = self.board_file.read_text(encoding="utf-8").splitlines()
        updated = False
        target_prefix = f"| {ticket_id:02d} |"
        target_prefix_alt = f"| {ticket_id} |"

        new_lines = []
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        for line in lines:
            if line.startswith(target_prefix) or line.startswith(target_prefix_alt):
                cols = [c.strip() for c in line.split("|")[1:-1]]
                if len(cols) >= 7:
                    cols[3] = new_status
                    if assignee:
                        cols[5] = assignee
                    cols[6] = now
                    line = f"| {' | '.join(cols)} |"
                    updated = True
            new_lines.append(line)

        if updated:
            self.board_file.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
            print(f"Updated ticket #{ticket_id} status to '{new_status}'")
            return True
        else:
            print(f"Ticket #{ticket_id} not found on board.")
            return False


def main():
    parser = argparse.ArgumentParser(description="Manage Superagent tickets and board")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # init
    init_p = subparsers.add_parser("init", help="Initialize specs/tickets/ and board.md")
    init_p.add_argument("--root", default=".", help="Root project directory")

    # create
    create_p = subparsers.add_parser("create", help="Create a new ticket")
    create_p.add_argument("title", help="Ticket title / short name")
    create_p.add_argument("--desc", default="", help="Description")
    create_p.add_argument("--mode", choices=["solo", "team"], default="solo", help="Execution mode")
    create_p.add_argument("--runs", default="alongside", help="Dependency: 'alongside' or 'waiting on ID'")
    create_p.add_argument("--root", default=".", help="Root project directory")

    # list
    list_p = subparsers.add_parser("list", help="Display tickets board")
    list_p.add_argument("--root", default=".", help="Root project directory")

    # set-status
    status_p = subparsers.add_parser("set-status", help="Update ticket status")
    status_p.add_argument("ticket_id", type=int, help="Numeric ticket ID")
    status_p.add_argument("status", choices=["draft", "ready", "in_progress", "review", "merged", "blocked"], help="New status")
    status_p.add_argument("--assignee", default=None, help="Assigned agent or session name")
    status_p.add_argument("--root", default=".", help="Root project directory")

    args = parser.parse_args()
    mgr = TicketManager(Path(args.root).resolve())

    if args.command == "init":
        mgr.init_workspace()
    elif args.command == "create":
        mgr.create_ticket(args.title, args.desc, args.mode, args.runs)
    elif args.command == "list":
        mgr.list_tickets()
    elif args.command == "set-status":
        mgr.update_status(args.ticket_id, args.status, args.assignee)


if __name__ == "__main__":
    main()
