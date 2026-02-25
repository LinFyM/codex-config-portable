---
name: workspace-cleanup
description: Inventory untracked/temporary artifacts in the active workspace and produce a safe cleanup plan (keep/temporary/review) with suggested move/delete commands. Use when a task created many intermediate files (tmp scripts, duplicate YAMLs, logs, outputs) and you want to avoid workspace clutter. Do not delete anything without explicit user approval.
---

# Workspace Cleanup

## Quick start

```bash
python3 ~/.codex/skills/workspace-cleanup/scripts/inventory.py
```

## What this skill does

- Detects untracked files (git) and common temporary artifacts.
- Classifies candidates into `keep`, `temporary`, or `review` (needs a human decision).
- Produces a small cleanup plan and safe command suggestions.

## Rules

- Workspace-scoped only: resolve workspace root via `git rev-parse --show-toplevel`.
- Do not delete anything without explicit user approval.
- Prefer consolidation over scattering: move temporary artifacts under `WORKSPACE/.codex/tmp/<label>_<timestamp>/` when appropriate.
- Keep outputs concise; only print long file lists when asked or when debugging.

## CLI usage

```bash
python3 ~/.codex/skills/workspace-cleanup/scripts/inventory.py --help
```

Common options:

- `--since-hours 24` to focus on recent changes
- `--label task_name` to name the suggested tmp folder
- `--json` to output machine-readable results

