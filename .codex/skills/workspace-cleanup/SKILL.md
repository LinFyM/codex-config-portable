---
name: workspace-cleanup
description: Use when the user requests repository or workspace cleanup, or when there is concrete evidence of obsolete paths, duplicate implementations, stale scripts or docs, artifact accumulation, canonical-output ambiguity, or material disk pressure. Audit tracked source, tests, scripts, configs, docs, entrypoints, and untracked or ignored runtime artifacts; remove or consolidate only items whose lifecycle is verified.
---

# Workspace Cleanup

Reduce the repository and workspace to one coherent active state. This is an
evidence-driven retirement workflow, not merely a temporary-file cleaner and
not a recurring phase ceremony. Git history, frozen configs, durable findings,
and intentional artifacts preserve history; obsolete executable or documentary
paths do not need to remain active for archival comfort.

## Scope

- Tracked source, tests, scripts, commands, entrypoints, adapters, configs, and
  compatibility or versioned paths that may be obsolete, duplicated, or no
  longer reachable from the canonical workflow.
- Tracked documentation, status notes, runbooks, generated reports, and indexes
  that may be stale, contradictory, superseded, or duplicated. Preserve durable
  scientific evidence and current handoff state; consolidate or remove obsolete
  narrative copies.
- Untracked and ignored temporary roots such as `.codex/tmp`, historical
  `.codex/longrun` output, logs, failed runs, caches, exports, and near-duplicate
  generated artifacts.
- Directory shape, naming, and canonical roots when proliferation makes active
  ownership unclear.

`code-architecture-gate` prevents new structural growth during implementation.
For an explicit repository-wide cleanup, this skill owns the workflow and
applies the same canonical-path and retirement principles directly; do not load
both workflows.

## Rules

- Resolve the repository root and inspect branch plus `git status` before
  classifying anything. Preserve unrelated user changes.
- Classify each candidate as `keep`, `consolidate`, `delete`, `temporary`, or
  `review`. A cleanup request authorizes removal of verified obsolete items; it
  does not authorize guessing about ambiguous ownership or evidence.
- Establish retirement evidence from current imports and callers, CLI and
  config entrypoints, CI or launch scripts, docs links, recent project state,
  and Git history. Static non-reference alone is insufficient for dynamically
  discovered plugins, reflection, shell entrypoints, or external consumers.
- Keep one canonical active implementation and one current document for each
  purpose. Update references as part of deletion; do not leave compatibility
  stubs unless a verified consumer still requires them and a removal trigger is
  recorded.
- Retain durable invariant tests. Remove tests, fixtures, scripts, and docs that
  exist only for a retired implementation after its evidence is preserved.
- Never delete ambiguous or unrelated user-authored work. Ask when ownership or
  lifecycle cannot be established from the cleanup request and repository evidence.
- Clearly task-created and superseded temporary outputs may be removed after
  verifying that no deliverable, evidence, or running process still references
  them.
- Prefer one canonical retained output. Move short-lived diagnostics under
  `WORKSPACE/.codex/tmp/<label>_<timestamp>/` only while they remain useful;
  moving files to tmp is not a permanent cleanup.
- Preserve unique experiment evidence, checkpoints, datasets, and formal
  outputs unless their lifecycle and deletion authority are explicit.
- Do not hide obsolete code, scripts, docs, tests, or outputs in an in-tree
  archive. Moving or renaming clutter is not cleanup.
- Keep outputs concise; only print long file lists when asked or when debugging.

## Workflow

1. Inventory tracked and untracked state: repository tree, Git status, active
   entrypoints, large or duplicated surfaces, ignored/runtime roots, and current
   project documentation.
2. Group candidates by purpose and identify the canonical owner. Record concise
   keep/consolidate/delete/review decisions; do not create a new cleanup report
   unless durable handoff value warrants one.
3. Verify references and lifecycle for each deletion cluster. Prefer Git history
   over keeping superseded live code or documents.
4. Remove or consolidate in coherent batches, updating imports, commands,
   configs, docs links, and tests that would otherwise point to retired paths.
5. Run verification proportional to what was removed: import or syntax checks,
   targeted existing tests, CLI smoke checks, config parsing, link/reference
   searches, and the canonical workflow when practical. Do not build a new test
   framework just for cleanup.
6. Reinspect Git status and the repository tree. Report material net source/file
   reduction, bytes freed for artifacts, canonical paths retained, intentional
   evidence preserved, and ambiguous candidates left for review.

A cleanup is incomplete when verified obsolete or duplicate surfaces remain
without a lifecycle. A correct audit may still delete nothing when every
candidate is active, intentional, or ambiguous.

## Artifact Inventory Helper

The bundled helper supplements the repository audit for untracked and ignored
artifacts; it does not inspect the full tracked code and documentation lifecycle.

```bash
python3 ~/.codex/skills/workspace-cleanup/scripts/inventory.py --help
```

Common options:

- `--since-hours 24` to focus on recent changes
- `--label task_name` to name the suggested tmp folder
- `--no-known-temp` to skip ignored known temp roots
- `--max-scan-files N` to bound ignored-temp scanning
- `--json` to output machine-readable results
