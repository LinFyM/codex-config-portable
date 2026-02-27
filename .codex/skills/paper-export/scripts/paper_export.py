#!/usr/bin/env python3
from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable


ALLOWED_EXTS = {
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".svg",
    ".eps",
    ".csv",
    ".tsv",
    ".json",
    ".yaml",
    ".yml",
    ".tex",
}

EXCLUDED_EXTS = {
    ".pt",
    ".pth",
    ".ckpt",
    ".safetensors",
    ".bin",
    ".npy",
    ".npz",
}

SECRET_NAME_RE = re.compile(r"(secret|token|api[_-]?key|password|passwd|credential|private[_-]?key)", re.I)

# Safety caps: paper exports should be small-ish and reproducible.
MAX_FILE_BYTES_DEFAULT = 50 * 1024 * 1024  # 50 MiB
MAX_TEX_BYTES_DEFAULT = 256 * 1024  # 256 KiB


@dataclasses.dataclass(frozen=True)
class ExportStats:
    files: int
    total_bytes: int


def _utc_now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def _is_hidden_path(rel: Path) -> bool:
    return any(part.startswith(".") for part in rel.parts)


def _should_include(rel: Path, size_bytes: int, *, max_file_bytes: int, max_tex_bytes: int) -> tuple[bool, str | None]:
    name = rel.name
    suffix = rel.suffix.lower()

    if _is_hidden_path(rel):
        return False, "hidden_path"

    if suffix in EXCLUDED_EXTS:
        return False, "excluded_ext"

    if suffix not in ALLOWED_EXTS and name != "README.md":
        return False, "not_allowlisted"

    if SECRET_NAME_RE.search(str(rel)):
        return False, "secret_like_name"

    if size_bytes > max_file_bytes:
        return False, "too_large"

    if suffix == ".tex" and size_bytes > max_tex_bytes:
        return False, "tex_too_large"

    # README.md: allow regardless of extension.
    return True, None


def _iter_files(src: Path) -> Iterable[Path]:
    # Do not follow symlinks: keeps exports safe and deterministic.
    for root, dirs, files in os.walk(src, followlinks=False):
        root_p = Path(root)

        # Prune hidden directories early.
        dirs[:] = [d for d in dirs if not d.startswith(".")]

        for fn in files:
            if fn.startswith("."):
                continue
            yield root_p / fn


def _find_git_root(start: Path, *, max_up: int = 6) -> Path | None:
    cur = start.resolve()
    for _ in range(max_up + 1):
        if (cur / ".git").exists():
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent
    return None


def _git_commit_and_dirty(git_root: Path) -> tuple[str | None, bool | None]:
    try:
        commit = (
            subprocess.check_output(["git", "-C", str(git_root), "rev-parse", "HEAD"], text=True)
            .strip()
        )
    except Exception:
        return None, None

    try:
        status = subprocess.check_output(["git", "-C", str(git_root), "status", "--porcelain"], text=True)
        dirty = bool(status.strip())
    except Exception:
        dirty = None

    return commit, dirty


def _best_effort_metric_summary(src: Path) -> dict[str, Any]:
    """
    Best-effort extraction: search for common metric files and try to summarize
    the last-row scalars. This is intentionally heuristic.
    """
    candidates: list[Path] = []
    for pat in ("**/metrics.jsonl", "**/metrics.json", "**/final_metrics.json", "**/results.json"):
        candidates.extend(src.glob(pat))

    if not candidates:
        return {"found": False}

    # Prefer metrics.jsonl if present.
    candidates.sort(key=lambda p: (p.name != "metrics.jsonl", len(str(p))))
    p = candidates[0]

    try:
        if p.suffix == ".jsonl":
            last: dict[str, Any] | None = None
            with p.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    last = json.loads(line)
            row = last or {}
        else:
            row = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(row, list) and row:
                row = row[-1]
            if not isinstance(row, dict):
                row = {"_value": row}
    except Exception as e:
        return {"found": True, "path": str(p), "error": f"failed_to_parse: {e.__class__.__name__}"}

    # Extract scalars only; keep a small top-k to avoid manifest bloat.
    scalars: dict[str, Any] = {}
    for k, v in row.items():
        if isinstance(v, (int, float, str, bool)) or v is None:
            scalars[k] = v
        elif isinstance(v, dict):
            # One-level flatten for common nested metrics.
            for kk, vv in v.items():
                if isinstance(vv, (int, float, str, bool)) or vv is None:
                    scalars[f"{k}.{kk}"] = vv

    keep_keys_pref = [
        "exit_reason",
        "steps",
        "step",
        "loss",
        "eval_loss",
        "ppl",
        "accuracy",
        "f1",
        "em",
    ]
    ordered: list[tuple[str, Any]] = []
    for k in keep_keys_pref:
        if k in scalars:
            ordered.append((k, scalars[k]))

    for k in sorted(scalars.keys()):
        if k in {kk for kk, _ in ordered}:
            continue
        ordered.append((k, scalars[k]))
        if len(ordered) >= 25:
            break

    return {"found": True, "path": str(p), "summary": dict(ordered)}


def _write_text(p: Path, s: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding="utf-8")


def _export_with_rsync(src: Path, out: Path, rel_files: list[Path]) -> None:
    # rsync expects the file list to be relative to the source root.
    tmp = out / ".paper_export_files.txt"
    tmp.parent.mkdir(parents=True, exist_ok=True)

    with tmp.open("wb") as f:
        for rel in rel_files:
            f.write(str(rel).encode("utf-8", errors="surrogateescape"))
            f.write(b"\0")

    cmd = [
        "rsync",
        "-a",
        "--from0",
        f"--files-from={tmp}",
        f"{src}/",
        f"{out}/",
    ]
    subprocess.check_call(cmd)

    try:
        tmp.unlink()
    except Exception:
        pass


def _export_with_python_copy(src: Path, out: Path, rel_files: list[Path]) -> None:
    for rel in rel_files:
        s = src / rel
        d = out / rel
        d.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(s, d)


def export_paper_artifacts(
    *,
    project: str,
    run_id: str,
    src: Path,
    out: Path,
    max_file_bytes: int,
    max_tex_bytes: int,
) -> dict[str, Any]:
    src = src.expanduser().resolve()
    out = out.expanduser().resolve()

    if not src.exists() or not src.is_dir():
        raise SystemExit(f"--src must be an existing directory: {src}")

    out.mkdir(parents=True, exist_ok=True)

    included: list[Path] = []
    skipped: dict[str, int] = {}
    total_bytes = 0

    for p in _iter_files(src):
        try:
            st = p.stat()
        except FileNotFoundError:
            continue
        rel = p.relative_to(src)
        ok, reason = _should_include(rel, st.st_size, max_file_bytes=max_file_bytes, max_tex_bytes=max_tex_bytes)
        if not ok:
            skipped[reason or "skipped"] = skipped.get(reason or "skipped", 0) + 1
            continue
        included.append(rel)
        total_bytes += int(st.st_size)

    included.sort()

    rsync_path = shutil.which("rsync")
    copy_mode = "rsync" if rsync_path else "python_copy"
    if copy_mode == "rsync":
        _export_with_rsync(src, out, included)
    else:
        _export_with_python_copy(src, out, included)

    git_root = _find_git_root(src)
    git_commit = None
    git_dirty = None
    if git_root is not None:
        git_commit, git_dirty = _git_commit_and_dirty(git_root)

    metric_summary = _best_effort_metric_summary(src)

    manifest: dict[str, Any] = {
        "exported_at_utc": _utc_now_iso(),
        "project": project,
        "run_id": run_id,
        "src": str(src),
        "out": str(out),
        "copy_mode": copy_mode,
        "stats": {"files": len(included), "total_bytes": total_bytes},
        "git": {
            "root": str(git_root) if git_root is not None else None,
            "commit": git_commit,
            "dirty": git_dirty,
        },
        "metrics": metric_summary,
        "skipped_counts": skipped,
        "filters": {
            "allowed_exts": sorted(ALLOWED_EXTS),
            "excluded_exts": sorted(EXCLUDED_EXTS),
            "max_file_bytes": max_file_bytes,
            "max_tex_bytes": max_tex_bytes,
        },
    }

    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    readme = f"""# Paper Export ({project}/{run_id})

This directory is generated by the server-side `paper-export` skill.

Purpose: export only paper-ready artifacts (figures/tables/metrics/config/README and small TeX snippets)
from an experiment output directory, in a stable layout for incremental pulling on your local machine.

Generated files:
- `manifest.json`: export metadata (timestamp, git commit best-effort, metric summary best-effort)

Recommended workflow:
1) On the server: re-run the export whenever the run produces new paper-relevant outputs.
2) On the client (local): use your `paper-sync` workflow to pull incrementally from this directory.

Notes:
- Export is safe by default: it does not delete files in the export directory.
- Only a small allowlist of file types is copied; training artifacts and large binaries are skipped.
"""
    _write_text(out / "README.md", readme)

    return manifest


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Export paper-ready artifacts from experiment outputs.")
    p.add_argument("--project", required=True, help="Project name for export path: <project>.")
    p.add_argument("--run-id", required=True, help="Run identifier for export path: <run_id>.")
    p.add_argument("--src", required=True, help="Source experiment output directory to scan and export.")
    p.add_argument(
        "--out",
        default=None,
        help="Optional override output directory. Default: ~/project/exp/paper_exports/<project>/<run_id>/",
    )
    p.add_argument(
        "--max-file-mb",
        type=int,
        default=MAX_FILE_BYTES_DEFAULT // (1024 * 1024),
        help="Skip individual files larger than this size (MiB). Default: %(default)s",
    )
    p.add_argument(
        "--max-tex-kb",
        type=int,
        default=MAX_TEX_BYTES_DEFAULT // 1024,
        help="Skip .tex files larger than this size (KiB). Default: %(default)s",
    )
    return p.parse_args(argv)


def main(argv: list[str]) -> int:
    args = _parse_args(argv)
    project = str(args.project).strip()
    run_id = str(args.run_id).strip()
    src = Path(args.src)
    if args.out:
        out = Path(args.out)
    else:
        out = Path("~/project/exp/paper_exports") / project / run_id

    manifest = export_paper_artifacts(
        project=project,
        run_id=run_id,
        src=src,
        out=out,
        max_file_bytes=int(args.max_file_mb) * 1024 * 1024,
        max_tex_bytes=int(args.max_tex_kb) * 1024,
    )

    # Keep stdout minimal and machine-readable-ish for chaining.
    print(json.dumps({"out": manifest["out"], "files": manifest["stats"]["files"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

