---
name: memory-recall
description: "Recall workspace-scoped memory to resume work quickly: read WORKSPACE/.codex/MEMORY.md and recent WORKSPACE/.codex/memory/YYYY-MM-DD.md logs, scan for Next/Blocker/Decision/Assumption, and output a concise status panel with pointers. Use at the start of a new chat, when context is degraded, or when re-entering a complex project after time away."
---

# Memory Recall

## Workflow

1. Resolve the workspace root (read-only; do not create memory files here).
   - Try `git rev-parse --show-toplevel`.
   - If not in git, walk up for a `.git/` directory.
   - If ambiguous (scratch dirs / multiple workspaces / no VCS), ask the user to confirm the workspace root path before reading anything.

2. Load the curated memory first.
   - Read: `WORKSPACE/.codex/MEMORY.md` (and `WORKSPACE/.codex/STATE.md` if present).
   - Extract only the most relevant bullets for the current request; do not paste the whole file unless asked.

3. Load recent daily logs.
   - Read the last 1-3 files under `WORKSPACE/.codex/memory/` (most recent dates).
   - Focus on Goal/Progress/Blockers/Next and any concrete pointers (paths/commands).

4. Run a quick keyword scan within `WORKSPACE/.codex/`.
   - Search for: `Next|Blocker|Decision|Assumption|TODO`
   - Prefer returning matches with file paths and line numbers.

5. Output a concise "resume panel".
   - Goal (current / last known)
   - Current status (what is done / in progress)
   - Blockers / open questions
   - Next 3 steps
   - Key files / commands / references to inspect next

## Safety

- Never reveal secrets found in memory files; redact sensitive values if encountered.
