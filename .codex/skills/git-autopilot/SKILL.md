---
name: git-autopilot
description: >-
  End-to-end delivery pipeline for non-trivial work. Create/switch to a safe feature branch, run a local review gate using the latest model + high reasoning, automatically fix P0/P1 findings, re-review, run minimal verification, then commit and push under Option B guardrails (PR/merge still require explicit user confirmation).
---

# Git Autopilot (Option B + Review->Fix Loop)

## When to use

- The user wants the work to be managed proactively with git and (optionally) a remote.
- The task is non-trivial and should follow an automated loop: review -> fix -> re-review -> verify -> commit/push.
- You need safe rollback/redo ability while iterating.

## Non-goals

- Do not open PRs, merge, rebase onto protected branches, or force-push without explicit user confirmation.
- Do not delete branches, files, or artifacts without explicit user confirmation.

## Preflight (always)

1. Resolve `WORKSPACE` via `git rev-parse --show-toplevel`. If not in a git repo, stop and ask the user whether to initialize git for this workspace.
2. Record:
   - current branch
   - `git status --porcelain`
   - remote(s) (`git remote -v`)
3. If on a protected branch (`main`/`master`/release), create/switch to a feature branch before making edits.
   - Use a predictable name: `codex/<slug>-YYYYMMDD`.

## Checkpointing & rollback strategy

- Prefer small, reviewable commits as checkpoints.
- For rollback:
  - If the bad change is already committed: prefer `git revert <sha>` (non-destructive).
  - If the bad change is uncommitted and you need to restart: create a safety net first:
    - either a WIP commit (preferred), or
    - save a patch under `WORKSPACE/.codex/tmp/patches/<label>_<timestamp>.patch`
  - Only propose destructive rollback (e.g. `git reset --hard`) after explicit user confirmation.

## Review gate (latest model + high reasoning)

Goal: always run a local review gate and fix issues before commit/push.

### Recommended command (CentOS7/older kernels)

On older Linux kernels, the default sandbox can fail due to missing Landlock support. Use `codex exec` with full access sandbox for review:

```bash
codex exec -s danger-full-access review --uncommitted
```

Notes:
- The review uses the current session model by default; set `review_model` in `~/.codex/config.toml` to force the latest model for reviews.
- Ensure `model_reasoning_effort = "high"` in `~/.codex/config.toml`.
- If you need custom review instructions: `review --uncommitted` does not accept a custom prompt in this CLI version.
  - Use a freeform `codex exec` review instead (have it run `git diff` and review with your desired rubric).

### Review->fix loop

1. Run the review gate.
2. If the review reports P0/P1 issues:
   - implement fixes immediately
   - re-run the review gate
3. Repeat until:
   - no P0/P1 issues remain, or
   - you are blocked by missing requirements/decisions, or
   - repeated attempts fail (cap at 3 iterations, then escalate to the user with options).

## Verification (minimal, repo-aware)

- After P0/P1 issues are cleared, run the smallest relevant verification steps available in the repo:
  - use existing repo tooling if present (formatter/lint/typecheck/tests)
  - otherwise run minimal language-appropriate checks (e.g. for Python: `python -m compileall`, then `pytest -q` if a tests directory exists)
- If verification cannot be run, state exactly why and what risk remains.

## Commit & push (Option B)

1. Stage only the intended changes (avoid sweeping adds).
2. Write a Conventional Commit style message if the repo uses it.
3. Push the feature branch to the remote as a backup after gates pass:
   - allowed by default for the current feature branch
4. PR creation / merge / rebase / force push:
   - stop and ask for explicit user confirmation.

## Artifact hygiene (end of task)

- If the task produced iterative artifacts (figures/exports/reports/generated configs):
  - keep a single canonical `latest` path
  - store history under `WORKSPACE/.codex/tmp/artifacts/`
  - prefer the `artifact-manager` skill when needed
- Run the cleanup gate:
  - prefer the `workspace-cleanup` skill to inventory new artifacts as `keep` vs `temporary`.
