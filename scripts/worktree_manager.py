#!/usr/bin/env python3
"""
worktree_manager.py - Manages isolated Git worktrees for Superagent worker sessions.
Ensures every agent operates in an isolated workspace without polluting the main branch.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Optional


def run_git(cmd: List[str], cwd: Optional[Path] = None, check: bool = True) -> subprocess.CompletedProcess:
    """Helper to run a git command and return CompletedProcess."""
    try:
        return subprocess.run(
            ["git"] + cmd,
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            check=check,
        )
    except subprocess.CalledProcessError as e:
        print(f"Git command failed: git {' '.join(cmd)}", file=sys.stderr)
        print(f"Stdout: {e.stdout}", file=sys.stderr)
        print(f"Stderr: {e.stderr}", file=sys.stderr)
        raise


class WorktreeManager:
    def __init__(self, repo_dir: Path):
        self.repo_dir = repo_dir
        self.worktrees_dir = repo_dir / ".worktrees"

    def ensure_gitignore(self) -> None:
        """Ensure .worktrees/ is ignored in git."""
        gitignore = self.repo_dir / ".gitignore"
        entry = ".worktrees/\n"
        if gitignore.exists():
            content = gitignore.read_text(encoding="utf-8")
            if ".worktrees" not in content:
                gitignore.write_text(content + ("\n" if not content.endswith("\n") else "") + entry, encoding="utf-8")
                print("Added .worktrees/ to .gitignore")
        else:
            gitignore.write_text(entry, encoding="utf-8")
            print("Created .gitignore with .worktrees/")

    def create(self, ticket_id: int, base_branch: str = "main") -> Path:
        """Create an isolated worktree for a ticket on branch feature/ticket-<id>."""
        self.ensure_gitignore()
        self.worktrees_dir.mkdir(parents=True, exist_ok=True)
        branch_name = f"feature/ticket-{ticket_id:02d}"
        wt_path = self.worktrees_dir / f"ticket-{ticket_id:02d}"

        if wt_path.exists():
            print(f"Worktree already exists at {wt_path}")
            return wt_path

        # Check if branch exists
        branch_check = run_git(["rev-parse", "--verify", branch_name], cwd=self.repo_dir, check=False)
        if branch_check.returncode == 0:
            print(f"Branch '{branch_name}' already exists. Checking out into worktree.")
            run_git(["worktree", "add", str(wt_path), branch_name], cwd=self.repo_dir)
        else:
            print(f"Creating new branch '{branch_name}' from '{base_branch}' in worktree...")
            run_git(["worktree", "add", "-b", branch_name, str(wt_path), base_branch], cwd=self.repo_dir)

        print(f"Worktree successfully created at:\n  {wt_path}")
        print(f"Branch: {branch_name}")
        return wt_path

    def list_worktrees(self) -> None:
        """List active git worktrees."""
        res = run_git(["worktree", "list"], cwd=self.repo_dir)
        print(res.stdout)

    def merge_worktree(self, ticket_id: int, target_branch: str = "main", no_ff: bool = True) -> bool:
        """Merge the ticket branch into target branch."""
        branch_name = f"feature/ticket-{ticket_id:02d}"
        print(f"Checking out target branch '{target_branch}'...")
        run_git(["checkout", target_branch], cwd=self.repo_dir)

        cmd = ["merge", branch_name]
        if no_ff:
            cmd.append("--no-ff")
            cmd.extend(["-m", f"Merge feature/ticket-{ticket_id:02d} into {target_branch}"])

        print(f"Merging {branch_name} into {target_branch}...")
        merge_res = run_git(cmd, cwd=self.repo_dir, check=False)
        if merge_res.returncode == 0:
            print(f"Successfully merged {branch_name} into {target_branch}.")
            return True
        else:
            print(f"Merge conflict or error while merging {branch_name}:", file=sys.stderr)
            print(merge_res.stderr, file=sys.stderr)
            return False

    def remove(self, ticket_id: int, delete_branch: bool = False, force: bool = False) -> None:
        """Remove a worktree directory and prune git metadata."""
        wt_path = self.worktrees_dir / f"ticket-{ticket_id:02d}"
        cmd = ["worktree", "remove"]
        if force:
            cmd.append("--force")
        cmd.append(str(wt_path))

        if wt_path.exists():
            res = run_git(cmd, cwd=self.repo_dir, check=False)
            if res.returncode != 0:
                print(f"Worktree contains build artifacts, removing with --force...")
                run_git(["worktree", "remove", "--force", str(wt_path)], cwd=self.repo_dir)
            print(f"Removed worktree {wt_path}")
        else:
            print(f"Worktree path {wt_path} does not exist.")

        run_git(["worktree", "prune"], cwd=self.repo_dir)

        if delete_branch:
            branch_name = f"feature/ticket-{ticket_id:02d}"
            run_git(["branch", "-d" if not force else "-D", branch_name], cwd=self.repo_dir)
            print(f"Deleted branch {branch_name}")


def main():
    parser = argparse.ArgumentParser(description="Manage Git worktrees for Superagent workers")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # create
    create_p = subparsers.add_parser("create", help="Create a worktree for a ticket")
    create_p.add_argument("ticket_id", type=int, help="Numeric ticket ID")
    create_p.add_argument("--base", default="main", help="Base branch (default: main)")
    create_p.add_argument("--root", default=".", help="Root repo directory")

    # list
    list_p = subparsers.add_parser("list", help="List active worktrees")
    list_p.add_argument("--root", default=".", help="Root repo directory")

    # merge
    merge_p = subparsers.add_parser("merge", help="Merge ticket branch into base branch")
    merge_p.add_argument("ticket_id", type=int, help="Numeric ticket ID")
    merge_p.add_argument("--target", default="main", help="Target branch (default: main)")
    merge_p.add_argument("--root", default=".", help="Root repo directory")

    # remove
    remove_p = subparsers.add_parser("remove", help="Remove worktree")
    remove_p.add_argument("ticket_id", type=int, help="Numeric ticket ID")
    remove_p.add_argument("--delete-branch", action="store_true", help="Also delete the branch")
    remove_p.add_argument("--force", action="store_true", help="Force removal")
    remove_p.add_argument("--root", default=".", help="Root repo directory")

    args = parser.parse_args()
    mgr = WorktreeManager(Path(args.root).resolve())

    if args.command == "create":
        mgr.create(args.ticket_id, args.base)
    elif args.command == "list":
        mgr.list_worktrees()
    elif args.command == "merge":
        mgr.merge_worktree(args.ticket_id, args.target)
    elif args.command == "remove":
        mgr.remove(args.ticket_id, args.delete_branch, args.force)


if __name__ == "__main__":
    main()
