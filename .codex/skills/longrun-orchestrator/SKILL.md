---
name: longrun-orchestrator
description: Launch and monitor long-running commands with resumable status + logs under WORKSPACE/.codex/longrun, and optionally chain follow-up steps after completion. Use when a job will likely exceed a reasonable single-session window, or when you want the agent to keep progressing without manual reminders.
---

# Long-Run Orchestrator

## Quick start (detach + monitor)

```bash
python3 ~/.codex/skills/longrun-orchestrator/scripts/orchestrate.py \\
  --label my_run \\
  --detach \\
  --cmd 'sleep 10' \\
  --then 'echo done'
```

If you are not inside a git repo, pass `--workspace /path/to/workspace` to avoid writing under `$HOME`.

Check status:

```bash
python3 ~/.codex/skills/longrun-orchestrator/scripts/status.py --latest
```

## Contract (how to use in execution persistence)

- If the job is likely short, prefer foreground polling (`--detach` not used).
- If the job is likely long, use `--detach` so work continues after the agent sends an Interim Update.
- Store everything in the active workspace only:
  - `WORKSPACE/.codex/longrun/<label>_<timestamp>/`

## Reporting guidance (Interim Update)

When using this skill and pausing execution, report minimally:

- `Pause reason`: waiting
- What is running (label + command)
- `Resume trigger`: the orchestrator status becomes `completed` (auto-continues if follow-ups are configured)

Only include exact paths when asked or when debugging requires it.
