---
name: paper-export
description: Export paper-ready artifacts (figures/tables/metrics/config/README and small tex snippets) from an experiment output directory into ~/project/exp/paper_exports/{project}/{run_id}/ for local incremental pulling via paper-sync. Use when you need a stable, repeatable export layout with a manifest.json (timestamp, run_id, git commit if available, and a best-effort metric summary). Safe by default (no destructive deletes; skips large training artifacts, checkpoints, and common binary blobs).
---

# Paper Export

## Quick Start

Run:

```bash
python /data0/user/ymdai/.codex/skills/paper-export/scripts/paper_export.py \
  --project <project> \
  --run-id <run_id> \
  --src <experiment_output_dir>
```

This writes to the default export directory:

`~/project/exp/paper_exports/<project>/<run_id>/`

It will also generate:
- `manifest.json`: export timestamp, run_id, git commit (best-effort), and a best-effort metric summary
- `README.md`: how to pull locally via `paper-sync`

## What Gets Exported

Included (recursive under `--src`):
- Figures: `*.pdf/*.png/*.jpg/*.jpeg/*.svg/*.eps`
- Tables/metrics/config: `*.csv/*.tsv/*.json/*.yaml/*.yml`
- `README.md` (anywhere under `--src`)
- Small TeX snippets: `*.tex` (size-capped)

Excluded:
- Checkpoint/binary blobs: `*.pt/*.pth/*.ckpt/*.safetensors/*.bin`
- Array dumps: `*.npy/*.npz`
- Hidden files (for example `.env`) and files with suspicious secret-like names (best-effort)
- Anything not matching the allowlist above

Safety defaults:
- No destructive deletes (export is overwrite/update-only).
- Uses `rsync` for incremental updates when available; otherwise falls back to Python copy.

## Notes For Agents

- Prefer exporting from a single run output directory (one `--src`) so the exported tree stays stable.
- If the export looks incomplete, inspect `manifest.json` warnings and re-run; the tool is designed to be repeatable.

## Resources

### scripts/paper_export.py

Single entrypoint for exporting paper-ready artifacts with filtering and `manifest.json` generation.
