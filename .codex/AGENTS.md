# Global AGENTS Instructions

## Scope
- Cross-project defaults for collaboration and execution style.
- Repository or subdirectory AGENTS override this file.
- Keep this file generic; do not assume project-specific build/test/release commands here.

## Server Environment (GPU Nodes)
- Two nodes: `gpu01`, `gpu02`; each has 8 GPUs: `NVIDIA A40 (46068 MiB)`.
- Any GPU scheduling decision must check both nodes; report availability for both plus a recommendation.
- Prefer the `gpu-preflight` skill.

## Communication
- Default to concise, practical responses in Chinese unless the user requests another language; lead with the outcome.
- State assumptions clearly when context is incomplete; if uncertain, say so explicitly.

## Working Style
- Read relevant context before making edits; prefer minimal, targeted changes; preserve conventions.
- For decisions with non-obvious tradeoffs, pause and present clear options before proceeding.

## Macro Goal Alignment (North-Star First)
- Treat macro project intent as a first-class constraint: details must serve the north-star objective.
- If macro intent is ambiguous (especially after resuming / context loss), invoke the `project-alignment` skill before implementation.
- Before coding, confirm a short alignment contract: north-star goal, task role, scope boundaries, non-negotiables, and success signals.

## Feature Delivery Contract (Goal -> Test -> Fix)
- For any new feature/functionality, define an explicit success contract before coding:
  - `Final Goal`: one sentence for the user-visible outcome.
  - `Definition of Success`: acceptance criteria that can be checked.
  - `Evidence Plan`: tests/checks that prove completion.
- Use this mandatory loop for new features and behavior changes:
  1. implement the minimal change that satisfies the success contract;
  2. add or update automated tests (happy path + key edge case + regression when fixing a bug);
  3. run the relevant quality gates;
  4. if failures occur, read traceback/error logs, identify root cause, fix, and re-run;
  5. repeat until tests pass or a real blocker is identified.
- Never declare completion without verification evidence. If blocked, report blocker, risk, and next action explicitly.
- Prefer the `feature-delivery-loop` skill for this workflow.

## Legacy Cleanup & Deconfliction
- New feature delivery must include legacy impact analysis: list which old paths/configs/flags become obsolete.
- Avoid long-lived dual-path behavior unless explicitly required for staged migration.
- If dual-path is temporarily required, define a removal plan with:
  - owner;
  - removal trigger/date;
  - regression checks to run before deletion.
- Remove or deprecate unused code/config/docs in the same delivery cycle when safe.
- Definition of Done must include:
  - no conflicting logic paths for the same behavior;
  - obsolete switches/flags are removed or clearly marked with sunset plan;
  - tests cover the retained canonical path.

## Plan Mode (Clarification-First)
- When in plan mode, do not implement. Only clarify requirements and produce a decision-complete plan.
- Apply the **User Questioning Policy (Before And During Execution)** below as the canonical questioning rule set.
- A decision-complete plan includes: assumptions, file/module breakdown, explicit verification steps, and definition of done.

## User Questioning Policy (Before And During Execution)
- Scope: this policy applies to both pre-implementation clarification and in-progress implementation.
- In pre-implementation discussion/planning, use `request_user_input` to resolve material ambiguities before coding.
- During implementation, if new uncertainty appears (requirements, scope boundaries, risk tradeoffs, or missing context), ask immediately; do not defer questions until the end.
- Prefer `request_user_input` for decision points with clear options; keep each round focused (1-3 questions) and continue execution after answers are received.
- Do not hide uncertainty by guessing when a wrong assumption could cause rework or unsafe changes.

## Execution Persistence (Finish The Job)
- After the plan is agreed and execution begins, proceed end-to-end until the task is complete.
- Do not stop mid-execution to provide a partial progress report or to ask "should I continue?" unless blocked or explicit approval is required.
- Asking clarifying questions per the User Questioning Policy is expected when needed to unblock correctness/safety, and is not considered unnecessary pausing.
- Only pause early when: a required decision/input blocks safe progress; a destructive/high-impact action needs explicit approval; a long-running job exceeds a reasonable time window to actively monitor; or verification fails and cannot be resolved with reasonable effort.
- Maintain a checklist derived from the agreed plan and ensure all items (including verification) are completed before the final report.
- Long-running work: if likely short, actively poll/monitor to completion; if likely long, use `longrun-orchestrator`.
- Reporting: Final Report only when the checklist is complete or truly blocked; Interim Update only when paused and must include a resume trigger.
- Plan status blocks apply only when there is an explicit agreed plan/checklist (never for pure Q&A or minor one-off requests).

## Memory System (Workspace-Scoped)
- Workspace-scoped only: store and read memory only inside the active workspace (repo/working dir).
- Never create or update memory files under `$HOME`, the filesystem root, or an unrelated directory.
- Canonical memory paths: `WORKSPACE/.codex/MEMORY.md` and `WORKSPACE/.codex/memory/YYYY-MM-DD.md`.
- Prefer skills: `memory-recall` (resume) and `memory-flush` (event-based checkpoints; for example milestones, before `/compact`, task switches, end-of-day wrap-up).
- Default reporting: update memory silently; disclose memory/housekeeping only when asked or when handoff/resume/debug requires it.
- When project architecture / method direction / key contracts change, proactively write a memory checkpoint immediately (don’t wait for end-of-day).
- Never store secrets; redact sensitive command/output before writing.

## Engineering Quality
- For non-trivial work (new feature/refactor/multi-file), write a short plan before coding: goal/non-goals/modules/verification.
- For new features/functions, include test updates by default; if automation is truly impossible, provide a reproducible manual check and state residual risk.
- When replacing behavior, prefer "replace then remove" over "add and keep both"; explicitly clean dead code and stale configs.
- Prevent "god files": keep entrypoints thin; add new functionality in new modules/files when reasonable.
- Size/complexity limits (defaults unless repo overrides):
  - Files: soft 400-600 lines; hard 800 lines.
  - Functions: soft 40-60 lines; hard 120 lines.
  - Complexity: target <= 10, avoid > 15.
- Enforcement for size/complexity limits:
  - If a change crosses a soft limit, include a short split/refactor plan in delivery notes.
  - If a change crosses a hard limit, split/refactor before completion by default.
  - Hard-limit exceptions require explicit user approval and must document rationale + follow-up cleanup plan.
- After implementation, run the repo's existing quality gates (format/lint/typecheck/tests). If none, run minimal checks and propose lightweight tooling.

### Repo Hygiene (Configs, Scripts & Artifacts)
- Reuse/edit existing YAML/config/scripts; avoid near-duplicates (parameterize/override instead).
- Keep one canonical `latest`; archive iteration history under `WORKSPACE/.codex/tmp/artifacts/` (prefer `artifact-manager`).
- Put temporary outputs under `WORKSPACE/.codex/tmp/...` or system `/tmp` (do not scatter across the repo).
- For non-trivial tasks, run `workspace-cleanup` to inventory keep vs temporary; never delete without explicit user approval.

## Git Workflow (Autopilot With Guardrails)
- Do not work directly on protected branches (`main`/`master`/release) unless the user explicitly requests it; use a feature branch.
- For non-trivial work, checkpoint with small, reviewable commits; push the feature branch as a backup once local gates pass.
- Before opening any PR, you must run Codex's dedicated review mode locally and resolve review findings:
  - preferred: `codex review --uncommitted`
  - older kernel fallback: `codex exec -s danger-full-access review --uncommitted`
  - if P0/P1 issues are found, fix and re-run review until cleared or explicitly escalated.
- Allowed without extra confirmation (low-risk): `git status`, `git diff`, `git add`, `git commit`, `git push` (feature branch).
- Must ask for explicit confirmation (high-impact): opening PRs, merging/rebasing onto protected branches, remote URL changes, deleting branches, history rewrites, destructive operations (`push --force*`, `git reset --hard`, broad cleanups).
- Prefer `git-autopilot` for review -> fix -> verify -> commit/push; use `yeet` only when the user explicitly wants PR creation via `gh`.
- For GitHub automation, first verify `gh auth status -h github.com`; if unauthenticated, ask the user to run `gh auth login`.
- PR privacy rule: never include personal information in PR title/body/comments/attachments/commit messages (for example real name, personal email, phone number, home/company address, ID numbers, private account handles, local absolute paths containing identity). Redact before publishing.

## Git Worktrees (Parallel Work)
- Use worktrees when it materially reduces risk or time (parallel feature+fix tracks, long runs, keeping a clean baseline).
- Conventions: `WORKSPACE/.codex/tmp/worktrees/<slug>_<timestamp>/`, branch `wt/<slug>-YYYYMMDD-HHMM`, outputs worktree-scoped.
- If large tracked artifacts may duplicate, propose a worktree plan and ask before creating.
- Worktree drift guard (mandatory when a target worktree/branch/path is specified): before any file edit and before final handoff, run `pwd` and `git rev-parse --abbrev-ref HEAD`, and verify both match the target.
- If the path/branch check fails, stop immediately; do not write files until switched back to the correct worktree and re-verified.
- Re-run the same check after any command likely to change execution context (for example `cd`, `git worktree ...`, or wrapper scripts that may change cwd).
- Merging/rebasing onto protected branches remains explicit-confirmation (see Git Workflow).
- Branch/worktree bookkeeping: whenever you create/delete/merge a git branch or worktree, update the workspace `AGENTS.md` “Git branch registry” section to reflect the current state (branch name, purpose, and worktree path if any).

## Code Review (Automated Loop)
- Use the latest available code model and high reasoning by default for reviews (keep `model`, `review_model`, `model_reasoning_effort` aligned in `config.toml`).
- Treat review as a gate; if P0/P1 issues are found, fix and re-review (cap iterations, then escalate).
- PR gate requirement: no PR creation before a successful local Codex review run (or explicit user-approved exception).
- On older kernels where `codex review` is unavailable, prefer `git-autopilot` to run review via `codex exec -s danger-full-access ...`.

## Safety & Delivery
- Ask before destructive/high-impact actions; never expose secrets/tokens/credentials.
- Never expose personal information (PII) in any shared artifact (PRs, issues, logs, screenshots, docs, comments).
- Run the smallest relevant verification steps; clearly separate "verified" vs "not verified".
- Keep delivery concise: what changed (why), key files touched, remaining risks/todos, and only useful next-step options.

## Skills & Continuous Improvement
- Keep this file policy-level; put step-by-step playbooks in skills so they load only when relevant.
- Prefer refining existing skills over growing this file. If the same correction repeats, propose updating AGENTS instructions.
- Prefer `feature-delivery-loop` when implementing new features or behavior changes that require a clear success bar plus test/fix iterations.

## Paper Assets Sync (Server -> Local)
- Server: use `paper-export` to export to `~/project/exp/paper_exports/<project>/<run_id>/`; client: use `paper-sync` to pull incrementally.
- Export only paper-ready assets; do not export checkpoints/datasets/secrets; do not delete extraneous by default.
- Client pull: edit `/Users/daiyuming/Documents/自动化/.codex/paper_sync.json`, then run `python3 /Users/daiyuming/Documents/自动化/scripts/paper_sync.py` (rsync preferred).
