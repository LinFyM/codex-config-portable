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
- For creative work, feature work, or behavior changes, start with `superpowers:brainstorming` before implementation.
- Do not implement before design approval; the approved design is the macro alignment contract.

## Feature Delivery Contract (Superpowers Workflow)
- Use this canonical flow for new features and behavior changes:
  1. `superpowers:brainstorming` (clarify intent, constraints, success criteria, design approval)
  2. `superpowers:using-git-worktrees` (isolated workspace)
  3. `superpowers:writing-plans` (implementation plan in `docs/plans/`)
  4. `superpowers:executing-plans` or `superpowers:subagent-driven-development`
  5. `superpowers:requesting-code-review` + local `codex review --uncommitted`
  6. `superpowers:finishing-a-development-branch` (complete branch flow)
- Always include explicit `Final Goal`, `Definition of Success`, and `Evidence Plan` in the plan/design artifacts.
- Never declare completion without verification evidence. If blocked, report blocker, risk, and next action explicitly.

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
- In pre-implementation brainstorming/planning, use `request_user_input` to resolve material ambiguities before coding when options are clear.
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

## Planning Records (Planning-With-Files)
- Canonical persistent planning files are workspace-root:
  - `WORKSPACE/task_plan.md`
  - `WORKSPACE/findings.md`
  - `WORKSPACE/progress.md`
- For complex tasks, use `planning-with-files` and keep these files updated during execution.
- By default, these planning files are part of delivery context and should be committed with related task work unless the user explicitly requests otherwise.
- Treat legacy memory files (`WORKSPACE/.codex/MEMORY.md`, `WORKSPACE/.codex/memory/*`) as historical context only; do not use them as the primary active planning system.
- Never store secrets; redact sensitive command/output before writing planning records.

## Engineering Quality
- For non-trivial work (new feature/refactor/multi-file), produce a written plan (usually via `superpowers:writing-plans`) before coding.
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

## Git Workflow (Guardrails)
- Do not work directly on protected branches (`main`/`master`/release) unless the user explicitly requests it; use a feature branch.
- For non-trivial work, checkpoint with small, reviewable commits; push the feature branch as a backup once local gates pass.
- Before opening any PR, you must run local review and resolve findings:
  - preferred: `codex review --uncommitted`
  - older kernel fallback: `codex exec -s danger-full-access review --uncommitted`
  - if P0/P1 issues are found, fix and re-run review until cleared or explicitly escalated.
- Allowed without extra confirmation (low-risk): `git status`, `git diff`, `git add`, `git commit`, `git push` (feature branch).
- Must ask for explicit confirmation (high-impact): opening PRs, merging/rebasing onto protected branches, remote URL changes, deleting branches, history rewrites, destructive operations (`push --force*`, `git reset --hard`, broad cleanups).
- For GitHub automation, first verify `gh auth status -h github.com`; if unauthenticated, ask the user to run `gh auth login`.
- PR privacy rule: never include personal information in PR title/body/comments/attachments/commit messages (for example real name, personal email, phone number, home/company address, ID numbers, private account handles, local absolute paths containing identity). Redact before publishing.

## Git Worktrees (Parallel Work)
- Use worktrees when it materially reduces risk or time (parallel feature+fix tracks, long runs, keeping a clean baseline).
- Default directory strategy (superpowers-compatible):
  - if `.worktrees/` exists, use it;
  - else if `worktrees/` exists, use it;
  - else ask user between project-local `.worktrees/` and global `~/.config/superpowers/worktrees/<project>/`.
- For project-local worktree dirs (`.worktrees/` / `worktrees/`), verify ignored status before creation with `git check-ignore`; if not ignored, fix `.gitignore` first.
- Worktree drift guard (mandatory when a target worktree/branch/path is specified): before any file edit and before final handoff, run `pwd` and `git rev-parse --abbrev-ref HEAD`, and verify both match the target.
- If the path/branch check fails, stop immediately; do not write files until switched back to the correct worktree and re-verified.
- Re-run the same check after any command likely to change execution context (for example `cd`, `git worktree ...`, or wrapper scripts that may change cwd).
- Merging/rebasing onto protected branches remains explicit-confirmation (see Git Workflow).
- Branch/worktree bookkeeping: whenever you create/delete/merge a git branch or worktree, update the workspace `AGENTS.md` “Git branch registry” section to reflect the current state (branch name, purpose, and worktree path if any).

## Code Review (Automated Loop)
- Use the latest available code model and high reasoning by default for reviews (keep `model`, `review_model`, `model_reasoning_effort` aligned in `config.toml`).
- Treat review as a gate; if P0/P1 issues are found, fix and re-review (cap iterations, then escalate).
- PR gate requirement: no PR creation before a successful local Codex review run (or explicit user-approved exception).
- Use `superpowers:requesting-code-review` during implementation, then enforce local `codex review` before PR.

## GitHub Codex Cloud Review (Visibility Rule)
- In some repos/orgs, Codex “cloud review” may signal **pass** by only adding a 👍 reaction on the PR, with no comment/review.
- `gh pr view` default output does not show reactions, so it can look like “no feedback”.
- When a PR is expected to have Codex cloud review but you can’t see any feedback, use the `gh-codex-cloud-review` skill.
  - Quick check (counts only): `gh pr view <PR> --json reactionGroups`
  - Authoritative check (who reacted): `gh api repos/<OWNER>/<REPO>/issues/<PR>/reactions`
  - Script helper: `python3 ~/.codex/skills/gh-codex-cloud-review/scripts/check_pr_codex_cloud_review.py <PR|URL> --repo <OWNER>/<REPO>`

## Safety & Delivery
- Ask before destructive/high-impact actions; never expose secrets/tokens/credentials.
- Never expose personal information (PII) in any shared artifact (PRs, issues, logs, screenshots, docs, comments).
- Run the smallest relevant verification steps; clearly separate "verified" vs "not verified".
- Keep delivery concise: what changed (why), key files touched, remaining risks/todos, and only useful next-step options.

## Skills & Continuous Improvement
- Keep this file policy-level; put step-by-step playbooks in skills so they load only when relevant.
- Prefer refining existing skills over growing this file. If the same correction repeats, update the relevant skill first.
- Preferred delivery stack for implementation: `superpowers` workflow + `planning-with-files` records.

## Paper Assets Sync (Server -> Local)
- Server: use `paper-export` to export to `~/project/exp/paper_exports/<project>/<run_id>/`; client: use `paper-sync` to pull incrementally.
- Export only paper-ready assets; do not export checkpoints/datasets/secrets; do not delete extraneous by default.
- Client pull: edit `/Users/daiyuming/Documents/自动化/.codex/paper_sync.json`, then run `python3 /Users/daiyuming/Documents/自动化/scripts/paper_sync.py` (rsync preferred).
