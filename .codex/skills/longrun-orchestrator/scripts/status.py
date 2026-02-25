#!/usr/bin/env python3
"""
Inspect status of longrun-orchestrator runs under WORKSPACE/.codex/longrun/.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Optional


def resolve_workspace_root(explicit: Optional[str]) -> Path:
    if explicit:
        return Path(explicit).resolve()
    try:
        p = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            check=True,
        )
        root = p.stdout.strip()
        if root:
            return Path(root).resolve()
    except Exception:
        pass
    raise SystemExit("Not in a git repo. Pass --workspace to choose the workspace root explicitly.")


def latest_run_dir(ws: Path) -> Optional[Path]:
    base = ws / ".codex" / "longrun"
    if not base.is_dir():
        return None
    dirs = [p for p in base.iterdir() if p.is_dir()]
    if not dirs:
        return None
    # Names include timestamp suffix; lexical sort works.
    return sorted(dirs, key=lambda p: p.name)[-1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", default=None, help="workspace root; default: git root or CWD")
    ap.add_argument("--run-id", default=None, help="specific run directory name under .codex/longrun/")
    ap.add_argument("--latest", action="store_true", help="show latest run")
    ap.add_argument("--json", action="store_true", help="print raw JSON state")
    args = ap.parse_args()

    ws = resolve_workspace_root(args.workspace)
    base = ws / ".codex" / "longrun"
    if args.latest:
        run_dir = latest_run_dir(ws)
    elif args.run_id:
        run_dir = base / args.run_id
    else:
        ap.error("Provide --latest or --run-id")
        return 2

    if run_dir is None or not run_dir.is_dir():
        print("(no runs found)")
        return 1

    state_path = run_dir / "state.json"
    if not state_path.is_file():
        print(f"(missing state.json in {run_dir})")
        return 1

    state = json.loads(state_path.read_text(encoding="utf-8"))
    if args.json:
        print(json.dumps(state, indent=2, ensure_ascii=True))
        return 0

    status = state.get("status")
    label = state.get("label")
    main_rc = state.get("main_rc")
    err = state.get("error")

    print(f"run_id: {run_dir.name}")
    print(f"label: {label}")
    print(f"status: {status}")
    if main_rc is not None:
        print(f"main_rc: {main_rc}")
    if err:
        print(f"error: {err}")
    print(f"logs: main.log / then.log / orchestrator.log")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
