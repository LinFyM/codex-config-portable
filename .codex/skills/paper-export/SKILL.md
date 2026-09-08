---
name: paper-export
description: Export paper-ready artifacts (figures, tables, metrics, configs, README files, and small TeX snippets) from an experiment output directory into a stable export tree for incremental pulling with paper-sync. Uses a manifest with provenance and safe size/type filters; never exports checkpoints or secret-like files by default.
---

# Paper Export

## Quick Start

Run:

```bash
python3 ~/.codex/skills/paper-export/scripts/paper_export.py \
  --project <project> \
  --run-id <run_id> \
  --src <experiment_output_dir>
```

The helper's built-in fallback export directory is:

`~/project/exp/paper_exports/<project>/<run_id>/`

Use `--out` with the established paper-sync destination. Use the built-in fallback only when it matches the active storage convention.

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
- Resolve this skill from the current session's advertised installation path; do not infer that a data-directory installation is stale.
- Use `--out <path>` when the active `paper-sync` configuration expects a
  different export root from the default.
- If the export looks incomplete, inspect `manifest.json` warnings and re-run; the tool is designed to be repeatable.

## Resources

### scripts/paper_export.py

Single entrypoint for exporting paper-ready artifacts with filtering and `manifest.json` generation.
