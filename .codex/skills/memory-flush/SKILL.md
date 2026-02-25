---
name: memory-flush
description: Write a small, workspace-scoped memory checkpoint to WORKSPACE/.codex/memory/YYYY-MM-DD.md and optionally promote stable decisions/gotchas to WORKSPACE/.codex/MEMORY.md. Use after milestones, before /compact, before starting a new chat to continue the same work, when switching tasks/subprojects, or at end-of-day wrap-up.
---

# Memory Flush

## Workflow

1. Resolve the workspace root (project-scoped only).
   - Try `git rev-parse --show-toplevel`.
   - If not in git, walk up for a `.git/` directory.
   - If still ambiguous (scratch dirs / multiple workspaces / no VCS), ask the user to confirm the workspace root path before writing anything.

2. Ensure the canonical memory paths exist under the workspace root.
   - Create: `WORKSPACE/.codex/memory/`
   - Ensure: `WORKSPACE/.codex/MEMORY.md` exists (create if missing; keep it short).

3. Append a compact checkpoint to today's daily log (event-based, not per message).
   - File: `WORKSPACE/.codex/memory/YYYY-MM-DD.md`
   - Add a timestamped entry.
   - Keep the entire entry small (target: <= 10 lines).
   - Prefer concrete pointers over prose: key file paths, commands, experiments, and outcomes.

4. Optionally promote stable facts to curated memory.
   - File: `WORKSPACE/.codex/MEMORY.md`
   - Only promote durable, reusable items (architecture facts, conventions, decisions, gotchas).
   - Promote 1-3 bullets at a time. Avoid rewriting large sections.

5. Report what changed.
   - Default: keep the response minimal (target <= 5 lines) and do not spam file paths.
   - Only list exact files/paths when the user asks, when debugging requires it, or when preparing a handoff/new chat.
   - If helpful, output a short status panel: goal, current status, blockers, next 3 steps, key files/commands.

## Daily Log Entry Template

```text
## HH:MM
Goal: ...
Progress: ... (files/commands)
Decisions: ...
Blockers: ...
Next: ...
Refs: ... (paths/commands/issues)
```

## Safety

- Never store secrets, tokens, credentials, private keys, or sensitive local configuration values in memory files.
- If any command/output contains secrets, redact before writing.
