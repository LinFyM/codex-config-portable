#!/usr/bin/env python3
"""
revise.py: Maintain a canonical 'latest' artifact while archiving snapshots.

Workflow:
- Resolve WORKSPACE root (git toplevel) and require workspace-scoped writes.
- Compute artifact_id from --artifact-id or from --latest path.
- Archive current latest (if exists) into:
    WORKSPACE/.codex/tmp/artifacts/<artifact_id>/history/<timestamp>__<basename>
- Copy/move --new into --latest.
- Append a JSONL entry to manifest.jsonl with note + hashes + paths.

Never deletes anything.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, asdict
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
    root = p.stdout.strip()
    if not root:
        raise SystemExit("Failed to resolve git root.")
    return Path(root).resolve()


def sha256_file(path: Path, max_bytes: int = 200_000_000) -> str:
    # Hash for traceability; cap read size to avoid pathological files.
    h = hashlib.sha256()
    total = 0
    with path.open("rb") as f:
        while True:
            b = f.read(1024 * 1024)
            if not b:
                break
            total += len(b)
            if total > max_bytes:
                raise SystemExit(f"Refusing to hash huge file (> {max_bytes} bytes): {path}")
            h.update(b)
    return h.hexdigest()


def safe_id(s: str) -> str:
    s = s.strip().replace(os.sep, "_")
    s = re.sub(r"[^a-zA-Z0-9._-]+", "-", s)
    s = re.sub(r"-{2,}", "-", s).strip("-")
    return s or "artifact"


def derive_artifact_id(latest: str) -> str:
    p = Path(latest)
    # Use parent + stem to reduce collisions.
    parent = safe_id(str(p.parent).replace("\\", "/"))
    stem = safe_id(p.stem)
    return safe_id(f"{parent}__{stem}")


@dataclass(frozen=True)
class ManifestEntry:
    ts: str
    artifact_id: str
    latest_rel: str
    new_src: str
    action: str  # revise
    note: str
    archived_path: Optional[str]
    latest_sha256_before: Optional[str]
    latest_sha256_after: str
    new_sha256: str


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--latest", required=True, help="canonical latest file path (relative to workspace)")
    ap.add_argument("--new", required=True, help="new file to apply as latest")
    ap.add_argument("--note", default="", help="short note for manifest")
    ap.add_argument("--artifact-id", default=None, help="override artifact id")
    ap.add_argument("--move", action="store_true", help="move --new instead of copying it")
    args = ap.parse_args()

    ws = git_root()
    latest_rel = args.latest
    latest_path = (ws / latest_rel).resolve()
    try:
        latest_path.relative_to(ws)
    except ValueError:
        raise SystemExit("--latest must be inside the workspace root.")

    new_path = Path(args.new).expanduser().resolve()
    if not new_path.exists() or not new_path.is_file():
        raise SystemExit(f"--new does not exist or is not a file: {new_path}")

    artifact_id = safe_id(args.artifact_id) if args.artifact_id else derive_artifact_id(latest_rel)
    base_dir = ws / ".codex" / "tmp" / "artifacts" / artifact_id
    hist_dir = base_dir / "history"
    base_dir.mkdir(parents=True, exist_ok=True)
    hist_dir.mkdir(parents=True, exist_ok=True)

    ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    archived_path: Optional[Path] = None
    before_hash: Optional[str] = None

    if latest_path.exists():
        before_hash = sha256_file(latest_path)
        archived_name = f"{ts}__{latest_path.name}"
        archived_path = hist_dir / archived_name
        shutil.copy2(latest_path, archived_path)

    # Ensure latest parent dir exists.
    latest_path.parent.mkdir(parents=True, exist_ok=True)

    # Apply new -> latest
    new_hash = sha256_file(new_path)
    if args.move:
        shutil.move(str(new_path), str(latest_path))
    else:
        shutil.copy2(new_path, latest_path)
    after_hash = sha256_file(latest_path)

    entry = ManifestEntry(
        ts=ts,
        artifact_id=artifact_id,
        latest_rel=latest_rel,
        new_src=str(new_path),
        action="revise",
        note=args.note,
        archived_path=str(archived_path) if archived_path else None,
        latest_sha256_before=before_hash,
        latest_sha256_after=after_hash,
        new_sha256=new_hash,
    )

    manifest = base_dir / "manifest.jsonl"
    with manifest.open("a", encoding="utf-8") as f:
        f.write(json.dumps(asdict(entry), ensure_ascii=True) + "\n")

    # Minimal stdout for scripting.
    print(f"artifact_id={artifact_id}")
    print(f"latest={latest_rel}")
    if archived_path:
        print(f"archived={archived_path.relative_to(ws)}")
    print(f"manifest={manifest.relative_to(ws)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

