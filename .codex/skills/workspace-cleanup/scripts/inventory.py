#!/usr/bin/env python3
"""
Workspace cleanup inventory:
- git-aware: list untracked/modified files
- classify artifacts into keep/temporary/review
- suggest safe move/delete commands (do not execute)
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class FileInfo:
    relpath: str
    abspath: str
    size_bytes: int
    mtime_iso: str


@dataclass(frozen=True)
class Classified:
    kind: str  # keep|temporary|review
    reason: str
    info: FileInfo


def run(cmd: List[str], cwd: Optional[Path] = None) -> Tuple[int, str, str]:
    p = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd is not None else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return p.returncode, p.stdout, p.stderr


def git_root() -> Path:
    rc, out, _ = run(["git", "rev-parse", "--show-toplevel"])
    if rc != 0:
        raise SystemExit("Not in a git repo. Run inside a workspace git repo.")
    return Path(out.strip()).resolve()


def list_untracked(root: Path) -> List[str]:
    # Avoid `git -C` for compatibility with older git builds.
    rc, out, err = run(["git", "ls-files", "-o", "--exclude-standard", "-z"], cwd=root)
    if rc != 0:
        raise SystemExit(err.strip() or "git ls-files failed")
    parts = [p for p in out.split("\0") if p]
    return parts


def list_status_porcelain(root: Path) -> List[str]:
    # Avoid `git -C` for compatibility with older git builds.
    rc, out, err = run(["git", "status", "--porcelain", "-z"], cwd=root)
    if rc != 0:
        raise SystemExit(err.strip() or "git status failed")
    return [p for p in out.split("\0") if p]


def file_info(root: Path, relpath: str) -> Optional[FileInfo]:
    p = (root / relpath).resolve()
    try:
        st = p.stat()
    except FileNotFoundError:
        return None
    mtime = dt.datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds")
    return FileInfo(relpath=relpath, abspath=str(p), size_bytes=st.st_size, mtime_iso=mtime)


_TEMP_DIR_MARKERS = [
    ".pytest_cache/",
    "__pycache__/",
    ".mypy_cache/",
    ".ruff_cache/",
    ".cache/",
    ".ipynb_checkpoints/",
    ".codex/tmp/",
    ".codex/longrun/",
]

_TEMP_EXTS = {".log", ".tmp", ".bak", ".swp", ".pyc"}


def classify(relpath: str) -> Tuple[str, str]:
    rp = relpath.replace("\\", "/")
    for m in _TEMP_DIR_MARKERS:
        if rp.startswith(m) or f"/{m}" in f"/{rp}":
            return "temporary", f"under temp/cache dir marker {m}"

    ext = Path(rp).suffix.lower()
    if ext in _TEMP_EXTS:
        return "temporary", f"temporary extension {ext}"

    base = Path(rp).name
    if base.startswith("core.") or base.endswith(".core"):
        return "temporary", "core dump"

    # Conservative defaults:
    # - scripts/config copies often need review
    if ext in {".yml", ".yaml", ".sh"}:
        return "review", f"{ext} needs keep-vs-temp decision"

    if rp.startswith("results/") or rp.startswith("output/") or rp.startswith("logs/") or rp.startswith("wandb/"):
        return "review", f"runtime outputs under {rp.split('/')[0]}/"

    return "review", "unknown; needs decision"


def iso_now_tag() -> str:
    return dt.datetime.now().strftime("%Y%m%d_%H%M%S")


def normalize_name_for_dup(path: str) -> str:
    # Heuristic normalization to cluster near-duplicates.
    name = Path(path).name
    name = re.sub(r"(20\\d{6}_\\d{6})", "<ts>", name)
    name = re.sub(r"(_run\\d+|_v\\d+|_seed\\d+)", "<var>", name)
    name = re.sub(r"(\\d{6,})", "<n>", name)
    return name


def sha256_small_file(path: Path, limit_bytes: int = 2_000_000) -> Optional[str]:
    try:
        st = path.stat()
    except FileNotFoundError:
        return None
    if st.st_size > limit_bytes:
        return None
    h = sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(1024 * 1024)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--since-hours", type=float, default=None, help="only consider files modified in last N hours")
    ap.add_argument("--label", default="cleanup", help="label used for suggested tmp folder name")
    ap.add_argument("--json", action="store_true", help="output JSON")
    ap.add_argument("--max-list", type=int, default=60, help="max files to print per section in human output")
    args = ap.parse_args()

    root = git_root()
    untracked = list_untracked(root)
    status = list_status_porcelain(root)

    cutoff_ts: Optional[float] = None
    if args.since_hours is not None:
        cutoff_ts = (dt.datetime.now() - dt.timedelta(hours=args.since_hours)).timestamp()

    classified: List[Classified] = []
    for rel in untracked:
        info = file_info(root, rel)
        if info is None:
            continue
        if cutoff_ts is not None:
            try:
                if (root / rel).stat().st_mtime < cutoff_ts:
                    continue
            except FileNotFoundError:
                continue
        kind, reason = classify(rel)
        classified.append(Classified(kind=kind, reason=reason, info=info))

    keep = [c for c in classified if c.kind == "keep"]
    temporary = [c for c in classified if c.kind == "temporary"]
    review = [c for c in classified if c.kind == "review"]

    # Duplicate hints (by normalized filename, and identical content hash for small files)
    dup_groups: Dict[str, List[str]] = {}
    hash_groups: Dict[str, List[str]] = {}
    for c in review:
        key = normalize_name_for_dup(c.info.relpath)
        dup_groups.setdefault(key, []).append(c.info.relpath)
        digest = sha256_small_file(Path(c.info.abspath))
        if digest:
            hash_groups.setdefault(digest, []).append(c.info.relpath)

    dup_groups = {k: v for k, v in dup_groups.items() if len(v) >= 2}
    hash_groups = {k: v for k, v in hash_groups.items() if len(v) >= 2}

    suggested_tmp = str(root / ".codex" / "tmp" / f"{args.label}_{iso_now_tag()}")

    payload = {
        "workspace_root": str(root),
        "untracked_count": len(untracked),
        "status_porcelain": status,
        "classified": [dataclasses.asdict(c) for c in classified],
        "keep": [dataclasses.asdict(c) for c in keep],
        "temporary": [dataclasses.asdict(c) for c in temporary],
        "review": [dataclasses.asdict(c) for c in review],
        "duplicate_name_groups": dup_groups,
        "duplicate_content_groups": hash_groups,
        "suggested_tmp_dir": suggested_tmp,
        "suggested_commands": {
            "mkdir_tmp": f"mkdir -p {shlex_quote(suggested_tmp)}",
            "move_review_to_tmp": (
                "# review first; then:\n"
                f"# mv <file1> <file2> ... {shlex_quote(suggested_tmp)}/"
            ),
            "delete_temporary": "# rm -rf <temporary_paths>    # ONLY after explicit approval",
        },
    }

    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=True))
        return 0

    def fmt_size(n: int) -> str:
        if n >= 1024 * 1024:
            return f"{n/1024/1024:.1f}MiB"
        if n >= 1024:
            return f"{n/1024:.1f}KiB"
        return f"{n}B"

    print(f"Workspace: {root}")
    print(f"Untracked: {len(untracked)}")
    print(f"Suggested tmp dir: {suggested_tmp}")

    def print_section(title: str, items: List[Classified]) -> None:
        print(f"\n{title} ({len(items)}):")
        if not items:
            print("  (none)")
            return
        for c in sorted(items, key=lambda x: (-x.info.size_bytes, x.info.relpath))[: args.max_list]:
            print(f"  {c.info.relpath}  [{fmt_size(c.info.size_bytes)}]  ({c.reason})")
        if len(items) > args.max_list:
            print(f"  ... (+{len(items) - args.max_list} more)")

    print_section("Temporary candidates", temporary)
    print_section("Review candidates", review)

    if dup_groups:
        print("\nPotential near-duplicates (by name):")
        shown = 0
        for k, v in sorted(dup_groups.items(), key=lambda kv: -len(kv[1])):
            print(f"  {k}: {len(v)}")
            for p in v[:10]:
                print(f"    {p}")
            if len(v) > 10:
                print(f"    ... (+{len(v)-10} more)")
            shown += 1
            if shown >= 8:
                break

    if hash_groups:
        print("\nIdentical files (by content hash, small files only):")
        shown = 0
        for _, v in sorted(hash_groups.items(), key=lambda kv: -len(kv[1])):
            print(f"  {len(v)} files:")
            for p in v[:10]:
                print(f"    {p}")
            if len(v) > 10:
                print(f"    ... (+{len(v)-10} more)")
            shown += 1
            if shown >= 6:
                break

    print("\nNext actions (safe):")
    print(f"  mkdir -p {suggested_tmp}")
    print("  Move review candidates you don't want to keep into that tmp dir.")
    print("  Only delete temporary candidates after explicit approval.")
    return 0


def shlex_quote(s: str) -> str:
    import shlex

    return shlex.quote(s)


if __name__ == "__main__":
    raise SystemExit(main())
