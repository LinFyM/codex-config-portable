---
name: gpu-preflight
description: "Use when the user asks for current NVIDIA GPU state, when selecting a shared device, or immediately before a GPU launch whose device eligibility may have changed. Produce a live scheduling snapshot only. Do not invoke as general ML-process paperwork, repeatedly reload it within one launch, use it as historical health evidence, or assume fixed GPU identities or availability."
---

# GPU Preflight

This is a focused live probe, not a planning, training, debugging, or monitoring
workflow. When another launch record already exists, run the helper directly and
attach only the selected device identity or blocker; do not create a second
preflight document or replay this skill for each status poll.

## Quick Start

```bash
python3 ~/.codex/skills/gpu-preflight/scripts/gpu_preflight.py
```

Use JSON when another tool will consume the result:

```bash
python3 ~/.codex/skills/gpu-preflight/scripts/gpu_preflight.py --json
```

Query explicit SSH hosts from a login or peer node:

```bash
python3 ~/.codex/skills/gpu-preflight/scripts/gpu_preflight.py --nodes <host-a>,<host-b>
```

## Evidence

- Node and live GPU index.
- Stable UUID and serial, model, driver, and compute mode.
- Total/used/free memory and utilization.
- Active compute PID, process name, memory, and OS owner when still visible.
- Candidate, busy, and prohibited device states, plus node-level unreachable or process-check failure evidence when applicable.

## Scheduling Rules

- Treat every result as a snapshot, not a reservation.
- Identify a device with node + index + UUID or serial. An old index alone is
  not durable evidence.
- A GPU in `Prohibited` compute mode is unavailable even when idle.
- Automatic candidates are conservative: devices with active compute processes
  are not recommended automatically. A process-bearing device may still be eligible
  under the project's co-residency contract after live ownership, peak-memory
  headroom, utilization, and interference assessment.
- If process ownership cannot be checked, return no recommendation for that
  node rather than assuming it is free.
- Recheck immediately before launch and set the selected devices explicitly.
- Distinguish busy, unavailable, and faulty. Do not kill jobs, reset GPUs,
  change compute mode, reload drivers, or reboot without explicit authority.
- For incident or health conclusions, add the relevant kernel/Xid logs, service
  history, and historical evidence; this scheduling snapshot alone is not enough.

## Options

- `--max-util <percent>`: candidate utilization threshold.
- `--max-mem-used-mib <MiB>`: candidate memory threshold.
- `--top-k <N>`: number of candidates shown.
- `--nodes <host,...>`: optional nodes; defaults to the current host.
- `--timeout-s <seconds>`: per-command timeout.

An empty automatic candidate list does not itself prohibit a launch. Assess any project-authorized
co-residency using the live evidence; unknown ownership remains unresolved evidence.
If no device is eligible, report the actual blocker instead of guessing or relying
on a historical card count.
