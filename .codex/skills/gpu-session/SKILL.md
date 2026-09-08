---
name: gpu-session
description: Maintain an explicitly requested tmux-backed GPU memory footprint on selected NVIDIA devices, locally or on a named SSH host. Use only when the user intentionally asks to hold, release, restore, or verify specific GPUs between jobs. Never infer a reserved device set or start from stale availability.
---

# GPU Session

This skill intentionally consumes GPU memory. Select devices from fresh
`gpu-preflight` evidence and never start on another user's GPUs.

## Start

```bash
python3 ~/.codex/skills/gpu-session/scripts/gpu_session.py start \
  --session <name> \
  --devices <gpu-indexes> \
  --python <verified-cuda-python> \
  --gib-per-device <GiB> \
  --min-mib <MiB>
```

The default Python is the interpreter running the manager, or
`GPU_SESSION_PYTHON` when set. Pass `--python` explicitly when the current
interpreter does not provide CUDA PyTorch. Add `--host <ssh-host>` only for a
deliberate remote session.

## Status And Stop

```bash
python3 ~/.codex/skills/gpu-session/scripts/gpu_session.py status \
  --session <name> --devices <gpu-indexes>

python3 ~/.codex/skills/gpu-session/scripts/gpu_session.py stop \
  --session <name>
```

## Rules

- Device indices, memory target, and session name must be explicit; there is no canonical reserved GPU set.
- Run `gpu-preflight` immediately before start and verify process ownership.
- Start refuses devices with active compute processes or memory above
  `--max-existing-mib`. Use `--allow-busy` only with explicit user authorization
  and after verifying that every existing process belongs to this user and the
  intended workload; it never overrides another user's process ownership.
- Start refuses to replace an existing tmux session. Use `--replace` only after
  verifying that the named session belongs to this workload.
- Record the owner/purpose, tmux session, selected devices, expected release
  time or condition, and exact stop command in the active run notes.
- Stop only the named session. Do not kill unrelated processes to make room.
- Recheck actual memory occupancy after start; a tmux session existing is not sufficient evidence.
- The script supports `--host` for deliberate remote use; local operation is
  the default.
