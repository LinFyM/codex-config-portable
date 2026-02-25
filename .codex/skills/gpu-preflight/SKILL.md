---
name: gpu-preflight
description: Check idle GPU availability across both nodes (gpu01 and gpu02) and recommend candidate devices before launching jobs. Use when you need to choose a node/GPU for training or inference, or to report GPU availability with a concrete recommendation.
---

# GPU Preflight

## Quick start

```bash
python3 ~/.codex/skills/gpu-preflight/scripts/gpu_preflight.py
```

## What this skill does

- Queries GPU status on `gpu01` and `gpu02` (8 GPUs each).
- Summarizes per-GPU utilization and memory usage.
- Produces a short list of candidate GPUs and a single recommended `node:gpu_index`.

## Rules

- Always check both nodes (`gpu01`, `gpu02`) before making any GPU scheduling recommendation.
- Prefer `ssh` in batch mode and fail fast if a node is unreachable (do not hang waiting for a password prompt).

## CLI usage

```bash
python3 ~/.codex/skills/gpu-preflight/scripts/gpu_preflight.py --help
```

Common options:

- `--nodes gpu01,gpu02` (override node list)
- `--max-util 5` (candidate threshold, percent)
- `--max-mem-used-mib 1000` (candidate threshold)
- `--top-k 5` (how many candidates to print)
- `--json` (machine-readable output)

## Output contract (for agent reporting)

- When reporting availability, include both nodes and the recommended GPU candidates.
- If any node cannot be queried, state that explicitly and do not assume it is idle.
