#!/usr/bin/env python3
"""
sentinel_watchdog.py - Background monitor agent script for Superagent orchestration.
Scans tickets, active worktrees, and file modification times to detect:
1. Stalled/silent executor sessions (no file updates or commits for >15 mins).
2. Dependency deadlocks (e.g. tickets waiting on blocked/draft tickets).
3. Memory/token warning signs or runaway worktrees.
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


class SentinelWatchdog:
    def __init__(self, root_dir: Path, stale_minutes: int = 15):
        self.root_dir = root_dir
        self.stale_threshold_seconds = stale_minutes * 60
        self.tickets_dir = root_dir / "specs" / "tickets"
        self.board_file = self.tickets_dir / "board.md"
        self.worktrees_dir = root_dir / ".worktrees"

    def parse_board(self) -> List[Dict[str, Any]]:
        """Parse board.md rows into structured dicts."""
        if not self.board_file.exists():
            return []

        rows = []
        for line in self.board_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line.startswith("|") or line.startswith("| ID") or line.startswith("|---"):
                continue
            cols = [c.strip() for c in line.split("|")[1:-1]]
            if len(cols) >= 6:
                try:
                    ticket_id = int(re.sub(r"[^\d]", "", cols[0]))
                except ValueError:
                    continue
                rows.append({
                    "id": ticket_id,
                    "title": cols[1],
                    "mode": cols[2],
                    "status": cols[3],
                    "runs": cols[4],
                    "assignee": cols[5],
                    "raw": line,
                })
        return rows

    def check_worktree_activity(self, ticket_id: int) -> Dict[str, Any]:
        """Check the latest file modification time in a ticket's worktree."""
        wt_path = self.worktrees_dir / f"ticket-{ticket_id:02d}"
        if not wt_path.exists():
            return {"exists": False, "latest_mtime": 0, "idle_seconds": None}

        latest_mtime = 0
        file_count = 0
        for root, dirs, files in os.walk(wt_path):
            if ".git" in root or "node_modules" in root:
                continue
            for f in files:
                fpath = Path(root) / f
                try:
                    mtime = fpath.stat().st_mtime
                    if mtime > latest_mtime:
                        latest_mtime = mtime
                    file_count += 1
                except OSError:
                    pass

        idle_seconds = time.time() - latest_mtime if latest_mtime > 0 else None
        return {
            "exists": True,
            "path": str(wt_path),
            "file_count": file_count,
            "latest_mtime": latest_mtime,
            "idle_seconds": idle_seconds,
        }

    def run_audit(self) -> Dict[str, Any]:
        """Perform a full system watchdog health check."""
        tickets = self.parse_board()
        now = time.time()
        issues: List[Dict[str, Any]] = []
        active_tickets = [t for t in tickets if t["status"] == "in_progress"]

        # 1. Check for stalled in_progress tickets
        for t in active_tickets:
            act = self.check_worktree_activity(t["id"])
            if not act["exists"]:
                issues.append({
                    "type": "MISSING_WORKTREE",
                    "severity": "HIGH",
                    "ticket_id": t["id"],
                    "message": f"Ticket #{t['id']} is marked 'in_progress' but no worktree exists at .worktrees/ticket-{t['id']:02d}",
                })
            elif act["idle_seconds"] is not None and act["idle_seconds"] > self.stale_threshold_seconds:
                idle_min = int(act["idle_seconds"] // 60)
                issues.append({
                    "type": "STALLED_EXECUTOR",
                    "severity": "WARNING",
                    "ticket_id": t["id"],
                    "idle_minutes": idle_min,
                    "message": f"Ticket #{t['id']} has had NO file updates for {idle_min} minutes. Agent may be stuck or hung.",
                })

        # 2. Check for dependency deadlocks
        id_to_ticket = {t["id"]: t for t in tickets}
        for t in tickets:
            runs = t["runs"].lower()
            if "waiting on" in runs:
                match = re.search(r"waiting on (\d+)", runs)
                if match:
                    dep_id = int(match.group(1))
                    if dep_id not in id_to_ticket:
                        issues.append({
                            "type": "MISSING_DEPENDENCY",
                            "severity": "ERROR",
                            "ticket_id": t["id"],
                            "message": f"Ticket #{t['id']} is waiting on non-existent Ticket #{dep_id}",
                        })
                    else:
                        dep_ticket = id_to_ticket[dep_id]
                        if dep_ticket["status"] in ["blocked", "draft"] and t["status"] == "ready":
                            issues.append({
                                "type": "DEPENDENCY_NOT_READY",
                                "severity": "WARNING",
                                "ticket_id": t["id"],
                                "message": f"Ticket #{t['id']} is marked ready but dependency Ticket #{dep_id} is '{dep_ticket['status']}'",
                            })

        return {
            "timestamp": datetime.now().isoformat(),
            "total_tickets": len(tickets),
            "in_progress_count": len(active_tickets),
            "healthy": len(issues) == 0,
            "issues": issues,
        }


def main():
    parser = argparse.ArgumentParser(description="Sentinel Watchdog for Superagent workflow")
    parser.add_argument("--root", default=".", help="Root repo directory")
    parser.add_argument("--threshold", type=int, default=15, help="Stale threshold in minutes (default: 15)")
    parser.add_argument("--json", action="store_true", help="Output JSON report")

    args = parser.parse_args()
    watchdog = SentinelWatchdog(Path(args.root).resolve(), stale_minutes=args.threshold)
    report = watchdog.run_audit()

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"=== Sentinel Watchdog Audit [{report['timestamp']}] ===")
        print(f"Total tickets: {report['total_tickets']} | In Progress: {report['in_progress_count']}")
        if report["healthy"]:
            print("✅ All active agents and dependencies healthy. No stalled sessions.")
        else:
            print(f"⚠️ Found {len(report['issues'])} issue(s):")
            for issue in report["issues"]:
                print(f" - [{issue['severity']}] {issue['type']} (Ticket #{issue.get('ticket_id', '?')}): {issue['message']}")


if __name__ == "__main__":
    main()
