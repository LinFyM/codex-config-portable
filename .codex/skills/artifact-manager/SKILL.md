---
name: artifact-manager
description: Use when repeated revisions of a generated artifact need one canonical latest file plus temporary rollback history. Do not use for live source, tests, scripts, or documentation structure, and do not treat its workspace-temp history as durable evidence.
---

# Artifact Manager

## Quick Start

```bash
python3 ~/.codex/skills/artifact-manager/scripts/revise.py \
  --latest docs/figures/foo.png \
  --new /tmp/foo.png \
  --note "Apply feedback: tighten spacing"
```

List history with:

```bash
python3 ~/.codex/skills/artifact-manager/scripts/list.py --latest docs/figures/foo.png
```

## Rules

- Keep one canonical latest path for an iterated generated artifact.
- The helper snapshots the previous latest file on each scripted revision for short-lived rollback.
- Store rollback history under `WORKSPACE/.codex/tmp/artifacts/`, never under `$HOME`; keep durable milestones or evidence in an intentional project-owned location instead.
- Scope includes generated figures, reports, exported tables, diagrams, rendered documents, and config snapshots.
- Do not use this skill for source files, scripts, tests, training entrypoints, or documentation structure.
- Never delete automatically. Prefer copy; use move only when ownership and rollback are clear.
