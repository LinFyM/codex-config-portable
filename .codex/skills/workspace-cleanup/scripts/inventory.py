#!/usr/bin/env python3
"""
Workspace cleanup inventory:
- git-aware: list untracked/modified files
- include bounded scans of known ignored temporary roots
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
from typing import Any, Dict, List, Optional, Tuple


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

_KNOWN_TEMP_ROOTS = [
    ".codex/tmp",
    ".codex/longrun",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
]


def list_known_temp_files(root: Path, limit: int) -> Tuple[List[str], bool]:
    found: List[str] = []
    truncated = False
    for rel_root in _KNOWN_TEMP_ROOTS:
        base = root / rel_root
        if not base.is_dir():
            continue
        for path in base.rglob("*"):
            if not path.is_file() or path.is_symlink():
                continue
            found.append(path.relative_to(root).as_posix())
            if len(found) >= limit:
                truncated = True
                return found, truncated
    return found, truncated


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


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser()
    ap.add_argument("--since-hours", type=float, default=None, help="only consider files modified in last N hours")
    ap.add_argument("--label", default="cleanup", help="label used for suggested tmp folder name")
    ap.add_argument("--json", action="store_true", help="output JSON")
    ap.add_argument("--max-list", type=int, default=60, help="max files to print per section in human output")
    ap.add_argument(
        "--no-known-temp",
        action="store_true",
        help="skip ignored files under known workspace temp/cache roots",
    )
    ap.add_argument(
        "--max-scan-files",
        type=int,
        default=5000,
        help="maximum ignored temp/cache files to inventory",
    )
    return ap.parse_args()


def cutoff_timestamp(since_hours: Optional[float]) -> Optional[float]:
    if since_hours is None:
        return None
    return (dt.datetime.now() - dt.timedelta(hours=since_hours)).timestamp()


def classify_candidates(
    root: Path,
    candidates: List[str],
    cutoff_ts: Optional[float],
) -> List[Classified]:
    classified: List[Classified] = []
    for relpath in candidates:
        info = file_info(root, relpath)
        if info is None:
            continue
        if cutoff_ts is not None:
            try:
                if (root / relpath).stat().st_mtime < cutoff_ts:
                    continue
            except FileNotFoundError:
                continue
        kind, reason = classify(relpath)
        classified.append(Classified(kind=kind, reason=reason, info=info))
    return classified


def collect_inventory(
    args: argparse.Namespace,
) -> Tuple[Path, List[str], List[str], List[str], bool, List[Classified]]:
    root = git_root()
    untracked = list_untracked(root)
    status = list_status_porcelain(root)
    known_temp: List[str] = []
    known_temp_truncated = False
    if not args.no_known_temp:
        known_temp, known_temp_truncated = list_known_temp_files(
            root, args.max_scan_files
        )
    candidates = sorted(set(untracked) | set(known_temp))
    classified = classify_candidates(
        root, candidates, cutoff_timestamp(args.since_hours)
    )
    return root, untracked, status, known_temp, known_temp_truncated, classified


def duplicate_groups(
    review: List[Classified],
) -> Tuple[Dict[str, List[str]], Dict[str, List[str]]]:
    name_groups: Dict[str, List[str]] = {}
    hash_groups: Dict[str, List[str]] = {}
    for item in review:
        relpath = item.info.relpath
        name_groups.setdefault(normalize_name_for_dup(relpath), []).append(relpath)
        digest = sha256_small_file(Path(item.info.abspath))
        if digest:
            hash_groups.setdefault(digest, []).append(relpath)
    return (
        {key: paths for key, paths in name_groups.items() if len(paths) >= 2},
        {key: paths for key, paths in hash_groups.items() if len(paths) >= 2},
    )


def build_payload(
    root: Path,
    untracked: List[str],
    status: List[str],
    known_temp: List[str],
    known_temp_truncated: bool,
    classified: List[Classified],
    suggested_tmp: str,
) -> Dict[str, Any]:
    keep = [item for item in classified if item.kind == "keep"]
    temporary = [item for item in classified if item.kind == "temporary"]
    review = [item for item in classified if item.kind == "review"]
    name_groups, content_groups = duplicate_groups(review)
    return {
        "workspace_root": str(root),
        "untracked_count": len(untracked),
        "known_temp_count": len(known_temp),
        "known_temp_scan_truncated": known_temp_truncated,
        "status_porcelain": status,
        "classified": [dataclasses.asdict(item) for item in classified],
        "keep": [dataclasses.asdict(item) for item in keep],
        "temporary": [dataclasses.asdict(item) for item in temporary],
        "review": [dataclasses.asdict(item) for item in review],
        "duplicate_name_groups": name_groups,
        "duplicate_content_groups": content_groups,
        "size_bytes": {
            "all_candidates": sum(item.info.size_bytes for item in classified),
            "temporary": sum(item.info.size_bytes for item in temporary),
            "review": sum(item.info.size_bytes for item in review),
        },
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


def fmt_size(size_bytes: int) -> str:
    if size_bytes >= 1024 * 1024:
        return f"{size_bytes / 1024 / 1024:.1f}MiB"
    if size_bytes >= 1024:
        return f"{size_bytes / 1024:.1f}KiB"
    return f"{size_bytes}B"


def print_section(title: str, items: List[Classified], max_list: int) -> None:
    print(f"\n{title} ({len(items)}):")
    if not items:
        print("  (none)")
        return
    ordered = sorted(items, key=lambda item: (-item.info.size_bytes, item.info.relpath))
    for item in ordered[:max_list]:
        print(
            f"  {item.info.relpath}  [{fmt_size(item.info.size_bytes)}]  "
            f"({item.reason})"
        )
    if len(items) > max_list:
        print(f"  ... (+{len(items) - max_list} more)")


def print_duplicate_groups(
    title: str,
    groups: Dict[str, List[str]],
    max_groups: int,
    show_group_key: bool,
) -> None:
    if not groups:
        return
    print(f"\n{title}:")
    ordered = sorted(groups.items(), key=lambda item: -len(item[1]))[:max_groups]
    for key, paths in ordered:
        label = f"{key}: {len(paths)}" if show_group_key else f"{len(paths)} files:"
        print(f"  {label}")
        for path in paths[:10]:
            print(f"    {path}")
        if len(paths) > 10:
            print(f"    ... (+{len(paths) - 10} more)")


def print_human(args: argparse.Namespace, payload: Dict[str, Any]) -> None:
    root = payload["workspace_root"]
    print(f"Workspace: {root}")
    print(f"Untracked: {payload['untracked_count']}")
    print(f"Known temp/cache files: {payload['known_temp_count']}")
    if payload["known_temp_scan_truncated"]:
        print(f"Known temp/cache scan truncated at {args.max_scan_files} files")
    print(f"Suggested tmp dir: {payload['suggested_tmp_dir']}")


def print_inventory_details(
    args: argparse.Namespace,
    payload: Dict[str, Any],
    temporary: List[Classified],
    review: List[Classified],
) -> None:
    print_human(args, payload)
    print_section("Temporary candidates", temporary, args.max_list)
    print_section("Review candidates", review, args.max_list)
    print_duplicate_groups(
        "Potential near-duplicates (by name)",
        payload["duplicate_name_groups"],
        max_groups=8,
        show_group_key=True,
    )
    print_duplicate_groups(
        "Identical files (by content hash, small files only)",
        payload["duplicate_content_groups"],
        max_groups=6,
        show_group_key=False,
    )
    print("\nNext actions (safe):")
    print(f"  mkdir -p {payload['suggested_tmp_dir']}")
    print("  Assign a canonical owner or explicit lifecycle to every retained review candidate.")
    print("  Delete only verified task-created temporary files; ask before ambiguous/user-authored data.")


def main() -> int:
    args = parse_args()
    root, untracked, status, known_temp, truncated, classified = collect_inventory(args)
    suggested_tmp = str(root / ".codex" / "tmp" / f"{args.label}_{iso_now_tag()}")
    payload = build_payload(
        root, untracked, status, known_temp, truncated, classified, suggested_tmp
    )
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=True))
        return 0
    temporary = [item for item in classified if item.kind == "temporary"]
    review = [item for item in classified if item.kind == "review"]
    print_inventory_details(args, payload, temporary, review)
    return 0


def shlex_quote(s: str) -> str:
    import shlex

    return shlex.quote(s)


if __name__ == "__main__":
    raise SystemExit(main())
