---
name: artifact-manager
description: Manage iterative artifacts by keeping a canonical "latest" file in the repo while archiving snapshots to WORKSPACE/.codex/tmp/artifacts/ARTIFACT_ID/history with a small manifest. Use when repeated revisions would otherwise create many versioned files (png/pdf/svg/yaml/logs/scripts) and you need clear latest vs history without clutter. Never delete without explicit user approval.
---

# Artifact Manager

## Quick start

Replace/update a canonical latest file, archiving the previous version:

```bash
python3 ~/.codex/skills/artifact-manager/scripts/revise.py \\
  --latest docs/figures/foo.png \\
  --new /tmp/foo.png \\
  --note "Apply feedback: tighten spacing"
```

List the history:

```bash
python3 ~/.codex/skills/artifact-manager/scripts/list.py --latest docs/figures/foo.png
```

## Core conventions

- Keep only one canonical `latest` path in the repo for an iterated artifact.
- Archive snapshots only when needed (milestones, reviews, user explicitly asks to keep versions).
- Store history under `WORKSPACE/.codex/tmp/artifacts/` (workspace-scoped; do not write under `$HOME`).

## Safety

- Do not delete anything automatically. Only propose commands.
- Prefer `copy` for new files by default; use `--move` only when safe.
