---
name: planning-with-files
description: Use when task state genuinely needs to survive compaction, another session, or a human/agent handoff, or when the user explicitly requests persistent planning files. Complexity or research work alone is not sufficient when an inline plan can remain reliable. Do not trigger from tool-call count.
---

# Planning With Files

## Purpose

Keep long work recoverable without turning every task into project administration.

Load this workflow once when establishing or recovering durable state. Reuse the
existing ledger thereafter; do not reread the skill or rewrite planning files on
every turn, tool call, experiment checkpoint, or routine status poll.

## Files

Reuse an established repository ledger when one exists. For a large,
multi-session, or handoff-heavy task, a visible root-level trio of
`task_plan.md`, `findings.md`, and `progress.md` is appropriate when it improves
recovery and coordination. Use the repository's existing equivalents when they
already serve those roles.

For work that needs durable state but not a repository-wide ledger, keep it
task-scoped, preferably under `.codex/plans/<task-id>/` when that location fits
the repository's ignore and retention policy. Start with one `state.md`
containing the goal, success criteria, boundaries, current phase, evidence, and
handoff state; split out findings or progress only when separate ledgers improve
recovery.

For smaller work, use an inline checklist instead. Do not create empty planning
files merely to satisfy a template. Honor project-specific planning paths when
the repository already treats them as durable documentation.

Concise optional templates live under `templates/`. Use only the files and
sections the task needs; do not expand them into a mandatory phase model.

## Workflow

1. Inspect existing planning files and current workspace state.
2. Record the final goal, definition of success, boundaries, and evidence plan.
3. Keep one current phase in progress and update phase status only when it actually changes.
4. Save durable findings after meaningful decisions or discoveries, not after an arbitrary number of reads, commands, or heartbeats.
5. Record repeated failures with the attempted action, evidence, and changed next approach.
6. Before handoff or completion, reconcile the files with current reality.

## Storage And Git

- Never store secrets, tokens, private keys, or sensitive raw logs.
- Keep temporary command output under `.codex/tmp/` and link or summarize only durable evidence.
- Do not commit planning files by default. Commit them only when requested or when they are genuine project documentation.

## Recovery

After a resumed or compacted session, read the repository's established ledger
or the task-scoped `state.md` first. When the root trio is present, start with
`task_plan.md`, then read the relevant parts of `findings.md` and `progress.md`.
Verify drift-prone external state before acting.
