#!/usr/bin/env python3
"""
list.py: Show history for an artifact managed by revise.py.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Optional


def git_root() -> Path:
    p = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    if p.returncode != 0:
        raise SystemExit("Not in a git repo. Run inside the workspace git repo.")
    return Path(p.stdout.strip()).resolve()


def safe_id(s: str) -> str:
    s = s.strip().replace(os.sep, "_")
    s = re.sub(r"[^a-zA-Z0-9._-]+", "-", s)
    s = re.sub(r"-{2,}", "-", s).strip("-")
    return s or "artifact"


def derive_artifact_id(latest: str) -> str:
    p = Path(latest)
    parent = safe_id(str(p.parent).replace("\\", "/"))
    stem = safe_id(p.stem)
    return safe_id(f"{parent}__{stem}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--latest", required=True, help="canonical latest file path (relative to workspace)")
    ap.add_argument("--artifact-id", default=None, help="override artifact id")
    ap.add_argument("--limit", type=int, default=30, help="max history entries to print")
    ap.add_argument("--json", action="store_true", help="print JSON lines")
    args = ap.parse_args()

    ws = git_root()
    artifact_id = safe_id(args.artifact_id) if args.artifact_id else derive_artifact_id(args.latest)
    base_dir = ws / ".codex" / "tmp" / "artifacts" / artifact_id
    manifest = base_dir / "manifest.jsonl"
    if not manifest.exists():
        print("(no manifest found)")
        return 1

    lines = manifest.read_text(encoding="utf-8").splitlines()
    if not lines:
        print("(empty manifest)")
        return 1

    rows = [json.loads(l) for l in lines if l.strip()]
    rows = rows[-args.limit :]

    if args.json:
        for r in rows:
            print(json.dumps(r, ensure_ascii=True))
        return 0

    print(f"artifact_id: {artifact_id}")
    print(f"latest: {args.latest}")
    print(f"entries: {len(rows)} (showing last {min(args.limit, len(lines))})")
    for r in rows:
        ts = r.get("ts")
        note = r.get("note", "")
        archived = r.get("archived_path")
        print(f"- {ts}  archived={bool(archived)}  note={note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

