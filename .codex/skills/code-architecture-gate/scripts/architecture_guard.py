#!/usr/bin/env python3
"""Git-aware architecture growth and legacy-ratchet checks.

The guard intentionally uses only the Python standard library. It measures
physical lines, Python function size/complexity, direct directory density, Git
diff growth, and likely parallel version families. It does not rewrite files.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Optional

from architecture_metrics import (
    FunctionMetric,
    function_metrics,
    normalized_function_name,
    normalized_version_path,
)


SOURCE_SUFFIXES = {
    ".c",
    ".cc",
    ".cpp",
    ".cs",
    ".go",
    ".h",
    ".hpp",
    ".java",
    ".js",
    ".jsx",
    ".kt",
    ".kts",
    ".php",
    ".py",
    ".rb",
    ".rs",
    ".scala",
    ".sh",
    ".swift",
    ".ts",
    ".tsx",
}

INACTIVE_PARTS = {
    ".codex",
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "archive",
    "archives",
    "build",
    "deprecated",
    "dist",
    "generated",
    "legacy",
    "node_modules",
    "site-packages",
    "target",
    "third_party",
    "vendor",
    "venv",
}

FILE_REVIEW = 600
FILE_HARD = 800
FILE_WIRING_ONLY = 1000
FUNCTION_REVIEW = 60
FUNCTION_HARD = 120
COMPLEXITY_REVIEW = 15
COMPLEXITY_HARD = 25
DIRECTORY_REVIEW = 25
DIRECTORY_HARD = 40
CHANGE_ADDITIONS_REVIEW = 500
CHANGE_NEW_FILES_REVIEW = 3
CHANGE_NET_ESCALATION = 1000
CHANGE_NEW_FILES_ESCALATION = 5


@dataclass(frozen=True)
class FileMetric:
    path: str
    lines: int
    baseline_lines: int
    delta_lines: int
    status: str


def run_git(root: Path, args: list[str], *, check: bool = True) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if check and proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or f"git {' '.join(args)} failed")
    return proc.stdout


def resolve_root(explicit: Optional[str]) -> Path:
    if explicit:
        root = Path(explicit).resolve()
        run_git(root, ["rev-parse", "--show-toplevel"])
        return root
    proc = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if proc.returncode != 0:
        raise SystemExit("Not in a Git repository. Pass --root explicitly.")
    return Path(proc.stdout.strip()).resolve()


def is_source(path: str) -> bool:
    return PurePosixPath(path).suffix.lower() in SOURCE_SUFFIXES


def is_active_source(path: str) -> bool:
    pure = PurePosixPath(path)
    return is_source(path) and not any(part.lower() in INACTIVE_PARTS for part in pure.parts)


def list_current_source(root: Path) -> list[str]:
    raw = run_git(root, ["ls-files", "-co", "--exclude-standard", "-z"])
    paths = sorted({part for part in raw.split("\0") if part and is_active_source(part)})
    return [path for path in paths if (root / path).is_file()]


def read_lines(path: Path) -> int:
    with path.open("rb") as handle:
        return sum(1 for _ in handle)


def baseline_text(root: Path, base: str, path: str) -> Optional[str]:
    proc = subprocess.run(
        ["git", "show", f"{base}:{path}"],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    if proc.returncode != 0:
        return None
    return proc.stdout.decode("utf-8", errors="replace")


def text_line_count(text: Optional[str]) -> int:
    if text is None:
        return 0
    return len(text.splitlines())


def diff_numstat(root: Path, base: str) -> dict[str, tuple[int, int]]:
    raw = run_git(root, ["diff", "--numstat", base, "--"])
    result: dict[str, tuple[int, int]] = {}
    for line in raw.splitlines():
        parts = line.split("\t", 2)
        if len(parts) != 3 or parts[0] == "-" or parts[1] == "-":
            continue
        path = parts[2]
        if is_active_source(path):
            result[path] = (int(parts[0]), int(parts[1]))
    tracked = set(run_git(root, ["ls-files", "-z"]).split("\0"))
    for path in list_current_source(root):
        if path not in tracked and path not in result:
            result[path] = (read_lines(root / path), 0)
    return result


@dataclass
class AnalysisState:
    file_metrics: list[FileMetric] = field(default_factory=list)
    hard: list[str] = field(default_factory=list)
    review: list[str] = field(default_factory=list)
    python_details: list[dict[str, Any]] = field(default_factory=list)
    function_version_groups: dict[str, set[str]] = field(
        default_factory=lambda: defaultdict(set)
    )


def analyze_function(
    path: str,
    func: FunctionMetric,
    before: Optional[FunctionMetric],
    state: AnalysisState,
) -> None:
    grew_lines = before is None or func.lines > before.lines
    grew_complexity = before is None or func.complexity > before.complexity
    if func.lines > FUNCTION_HARD and grew_lines:
        state.hard.append(
            f"{path}:{func.start} {func.qualname}: {func.lines} lines, "
            f"new or growing above {FUNCTION_HARD}"
        )
    elif func.lines > FUNCTION_REVIEW:
        state.review.append(f"{path}:{func.start} {func.qualname}: {func.lines} lines")
    if func.complexity > COMPLEXITY_HARD and grew_complexity:
        state.hard.append(
            f"{path}:{func.start} {func.qualname}: complexity {func.complexity}, "
            f"new or growing above {COMPLEXITY_HARD}"
        )
    elif func.complexity > COMPLEXITY_REVIEW:
        state.review.append(
            f"{path}:{func.start} {func.qualname}: complexity {func.complexity}"
        )
    if func.lines > FUNCTION_REVIEW or func.complexity > COMPLEXITY_REVIEW:
        state.python_details.append({"path": path, **asdict(func)})


def analyze_python_file(
    root: Path,
    path: str,
    baseline: Optional[str],
    state: AnalysisState,
) -> None:
    current_text = (root / path).read_text(encoding="utf-8", errors="replace")
    current_funcs, parse_error = function_metrics(current_text)
    baseline_funcs, _ = function_metrics(baseline) if baseline is not None else ([], None)
    baseline_by_name = {item.qualname: item for item in baseline_funcs}
    if parse_error:
        state.review.append(f"{path}: {parse_error}")
    for func in current_funcs:
        normalized = normalized_function_name(func.qualname)
        state.function_version_groups[f"{path}:{normalized}"].add(func.qualname)
        analyze_function(path, func, baseline_by_name.get(func.qualname), state)


def analyze_changed_files(
    root: Path,
    base: str,
    changed_paths: list[str],
    current_set: set[str],
) -> AnalysisState:
    state = AnalysisState()
    for path in changed_paths:
        if path not in current_set:
            continue
        baseline = baseline_text(root, base, path)
        baseline_lines = text_line_count(baseline)
        current_lines = read_lines(root / path)
        status = "new" if baseline is None else "modified"
        state.file_metrics.append(
            FileMetric(path, current_lines, baseline_lines, current_lines - baseline_lines, status)
        )
        if current_lines > FILE_HARD and (status == "new" or current_lines > baseline_lines):
            state.hard.append(
                f"{path}: {status} file is {current_lines} lines and "
                f"crosses/grows above {FILE_HARD}"
            )
        elif current_lines > FILE_REVIEW:
            state.review.append(f"{path}: changed file is {current_lines} lines")
        if current_lines > FILE_WIRING_ONLY:
            state.review.append(
                f"{path}: {current_lines} lines; verify edits are wiring/declarative or reduce size"
            )
        if path.endswith(".py"):
            analyze_python_file(root, path, baseline, state)
    return state


def paths_by_directory(paths: Iterable[str]) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = defaultdict(list)
    for path in paths:
        grouped[str(PurePosixPath(path).parent)].append(path)
    return grouped


def analyze_directories(
    current_paths: list[str],
    changed_paths: list[str],
    new_paths: list[str],
    state: AnalysisState,
) -> list[dict[str, Any]]:
    directory_members = paths_by_directory(current_paths)
    new_by_dir = paths_by_directory(new_paths)
    changed_by_dir = paths_by_directory(changed_paths)
    dense: list[dict[str, Any]] = []
    for directory, members in sorted(directory_members.items()):
        count = len(members)
        if count > DIRECTORY_REVIEW and changed_by_dir.get(directory):
            dense.append(
                {
                    "directory": directory,
                    "direct_source_files": count,
                    "new_files": new_by_dir.get(directory, []),
                }
            )
            state.review.append(f"{directory}: {count} direct source files")
        if count > DIRECTORY_HARD and new_by_dir.get(directory):
            state.hard.append(
                f"{directory}: added {len(new_by_dir[directory])} peer file(s) "
                f"to a directory with {count} direct source files"
            )
    return dense


def analyze_version_families(
    current_paths: list[str],
    changed_paths: list[str],
    state: AnalysisState,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    version_groups: dict[str, list[str]] = defaultdict(list)
    for path in current_paths:
        normalized = normalized_version_path(path)
        if normalized != path:
            version_groups[normalized].append(path)
    path_families = [
        {"normalized": key, "paths": sorted(paths)}
        for key, paths in sorted(version_groups.items())
        if len(paths) >= 2 and any(path in changed_paths for path in paths)
    ]
    function_families = [
        {"owner": key, "functions": sorted(names)}
        for key, names in sorted(state.function_version_groups.items())
        if len(names) >= 2
    ]
    for group in path_families:
        state.review.append(
            f"parallel version family {group['normalized']}: {', '.join(group['paths'])}"
        )
    for group in function_families:
        state.review.append(
            f"parallel function family {group['owner']}: {', '.join(group['functions'])}"
        )
    return path_families, function_families


def analyze_change_budget(
    diff: dict[str, tuple[int, int]],
    new_paths: list[str],
    state: AnalysisState,
) -> tuple[int, int, int]:
    additions = sum(pair[0] for pair in diff.values())
    deletions = sum(pair[1] for pair in diff.values())
    net = additions - deletions
    if additions > CHANGE_ADDITIONS_REVIEW:
        state.review.append(f"change adds {additions} active source lines")
    if len(new_paths) > CHANGE_NEW_FILES_REVIEW:
        state.review.append(f"change adds {len(new_paths)} active source files")
    if net > CHANGE_NET_ESCALATION:
        state.review.append(
            f"change has net active-source growth of {net} lines; "
            "architecture rationale and retirement decision are required"
        )
    if len(new_paths) > CHANGE_NEW_FILES_ESCALATION:
        state.review.append(
            f"change adds {len(new_paths)} active source files; "
            "ownership map and retirement decision are required"
        )
    return additions, deletions, net


def find_inactive_source_changes(root: Path, base: str, state: AnalysisState) -> list[str]:
    changed = sorted(
        path
        for path in run_git(root, ["diff", "--name-only", base, "--"]).splitlines()
        if is_source(path) and not is_active_source(path)
    )
    if changed:
        state.review.append(
            "source changed under archive/legacy/generated/vendor-like paths; "
            "verify this is not fake retirement"
        )
    return changed


def build_payload(
    root: Path,
    base: str,
    changed_paths: list[str],
    new_paths: list[str],
    deleted_paths: list[str],
    diff_counts: tuple[int, int, int],
    state: AnalysisState,
    dense_directories: list[dict[str, Any]],
    path_families: list[dict[str, Any]],
    function_families: list[dict[str, Any]],
    inactive_changed: list[str],
) -> dict[str, Any]:
    additions, deletions, net = diff_counts
    return {
        "root": str(root),
        "base": base,
        "result": "block" if state.hard else ("review" if state.review else "pass"),
        "diff": {
            "additions": additions,
            "deletions": deletions,
            "net": net,
            "changed_active_source_files": len(changed_paths),
            "new_active_source_files": new_paths,
            "deleted_active_source_files": deleted_paths,
        },
        "hard_violations": state.hard,
        "review_flags": state.review,
        "changed_files": [
            asdict(metric)
            for metric in sorted(state.file_metrics, key=lambda item: (-item.lines, item.path))
        ],
        "large_python_functions": sorted(
            state.python_details,
            key=lambda item: (-item["lines"], -item["complexity"], item["path"]),
        ),
        "dense_directories": dense_directories,
        "parallel_version_families": path_families,
        "parallel_function_families": function_families,
        "inactive_source_changes": inactive_changed,
    }


def print_items(title: str, items: list[str], limit: int) -> None:
    if not items:
        return
    print(f"\n{title}:")
    for item in items[:limit]:
        print(f"  - {item}")
    if len(items) > limit:
        print(f"  ... (+{len(items) - limit} more)")


def print_human(payload: dict[str, Any], max_details: int) -> None:
    diff = payload["diff"]
    print(f"Architecture guard: {payload['result'].upper()}")
    print(
        f"Active-source diff: +{diff['additions']} / -{diff['deletions']} / "
        f"net {diff['net']}; changed {diff['changed_active_source_files']}, "
        f"new {len(diff['new_active_source_files'])}, "
        f"deleted {len(diff['deleted_active_source_files'])}"
    )
    print_items("Hard violations", payload["hard_violations"], max_details)
    print_items("Review flags", payload["review_flags"], max_details)
    if not payload["hard_violations"] and not payload["review_flags"]:
        print("No structural growth flags detected.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=None, help="Git repository root")
    parser.add_argument("--base", default="HEAD", help="Git ref used as the baseline")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="return non-zero for review flags as well as hard violations",
    )
    parser.add_argument("--max-details", type=int, default=20)
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    root = resolve_root(args.root)
    try:
        run_git(root, ["rev-parse", "--verify", args.base])
        current_paths = list_current_source(root)
        diff = diff_numstat(root, args.base)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    changed_paths = sorted(diff)
    current_set = set(current_paths)
    new_paths = [
        path
        for path in changed_paths
        if baseline_text(root, args.base, path) is None and path in current_set
    ]
    deleted_paths = [path for path in changed_paths if path not in current_set]
    state = analyze_changed_files(root, args.base, changed_paths, current_set)
    dense = analyze_directories(current_paths, changed_paths, new_paths, state)
    path_families, function_families = analyze_version_families(
        current_paths, changed_paths, state
    )
    diff_counts = analyze_change_budget(diff, new_paths, state)
    inactive_changed = find_inactive_source_changes(root, args.base, state)
    payload = build_payload(
        root,
        args.base,
        changed_paths,
        new_paths,
        deleted_paths,
        diff_counts,
        state,
        dense,
        path_families,
        function_families,
        inactive_changed,
    )

    if args.json:
        json.dump(payload, sys.stdout, indent=2, ensure_ascii=True)
        sys.stdout.write("\n")
    else:
        print_human(payload, args.max_details)

    if state.hard or (args.strict and state.review):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
