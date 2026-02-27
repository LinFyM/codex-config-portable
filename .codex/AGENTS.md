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

## Plan Mode (Clarification-First)
- When in plan mode, do not implement. Only clarify requirements and produce a decision-complete plan.
- If the user request is ambiguous, ask clarifying questions until there is no material ambiguity that could change the implementation.
- Prefer the structured user question tool (`request_user_input`) when available and decisions can be expressed as 2-3 options.
- Ask 1-3 questions per round; repeat rounds as needed (avoid long questionnaires).
- A decision-complete plan includes: assumptions, file/module breakdown, explicit verification steps, and definition of done.

## Execution Persistence (Finish The Job)
- After the plan is agreed and execution begins, proceed end-to-end until the task is complete.
- Do not stop mid-execution to provide a partial progress report or to ask "should I continue?" unless blocked or explicit approval is required.
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
- Never store secrets; redact sensitive command/output before writing.

## Engineering Quality
- For non-trivial work (new feature/refactor/multi-file), write a short plan before coding: goal/non-goals/modules/verification.
- Prevent "god files": keep entrypoints thin; add new functionality in new modules/files when reasonable.
- Size/complexity limits (defaults unless repo overrides):
  - Files: soft 400-600 lines; hard 800 lines.
  - Functions: soft 40-60 lines; hard 120 lines.
  - Complexity: target <= 10, avoid > 15.
- After implementation, run the repo's existing quality gates (format/lint/typecheck/tests). If none, run minimal checks and propose lightweight tooling.

### Repo Hygiene (Configs, Scripts & Artifacts)
- Reuse/edit existing YAML/config/scripts; avoid near-duplicates (parameterize/override instead).
- Keep one canonical `latest`; archive iteration history under `WORKSPACE/.codex/tmp/artifacts/` (prefer `artifact-manager`).
- Put temporary outputs under `WORKSPACE/.codex/tmp/...` or system `/tmp` (do not scatter across the repo).
- For non-trivial tasks, run `workspace-cleanup` to inventory keep vs temporary; never delete without explicit user approval.

## Git Workflow (Autopilot With Guardrails)
- Do not work directly on protected branches (`main`/`master`/release) unless the user explicitly requests it; use a feature branch.
- For non-trivial work, checkpoint with small, reviewable commits; push the feature branch as a backup once local gates pass.
- Allowed without extra confirmation (low-risk): `git status`, `git diff`, `git add`, `git commit`, `git push` (feature branch).
- Must ask for explicit confirmation (high-impact): opening PRs, merging/rebasing onto protected branches, remote URL changes, deleting branches, history rewrites, destructive operations (`push --force*`, `git reset --hard`, broad cleanups).
- Prefer `git-autopilot` for review -> fix -> verify -> commit/push; use `yeet` only when the user explicitly wants PR creation via `gh`.
- For GitHub automation, first verify `gh auth status -h github.com`; if unauthenticated, ask the user to run `gh auth login`.

## Git Worktrees (Parallel Work)
- Use worktrees when it materially reduces risk or time (parallel feature+fix tracks, long runs, keeping a clean baseline).
- Conventions: `WORKSPACE/.codex/tmp/worktrees/<slug>_<timestamp>/`, branch `wt/<slug>-YYYYMMDD-HHMM`, outputs worktree-scoped.
- If large tracked artifacts may duplicate, propose a worktree plan and ask before creating.
- Merging/rebasing onto protected branches remains explicit-confirmation (see Git Workflow).

## Code Review (Automated Loop)
- Use the latest available code model and high reasoning by default for reviews (keep `model`, `review_model`, `model_reasoning_effort` aligned in `config.toml`).
- Treat review as a gate; if P0/P1 issues are found, fix and re-review (cap iterations, then escalate).
- On older kernels where `codex review` is unavailable, prefer `git-autopilot` to run review via `codex exec -s danger-full-access ...`.

## Safety & Delivery
- Ask before destructive/high-impact actions; never expose secrets/tokens/credentials.
- Run the smallest relevant verification steps; clearly separate "verified" vs "not verified".
- Keep delivery concise: what changed (why), key files touched, remaining risks/todos, and only useful next-step options.

## Skills & Continuous Improvement
- Keep this file policy-level; put step-by-step playbooks in skills so they load only when relevant.
- Prefer refining existing skills over growing this file. If the same correction repeats, propose updating AGENTS instructions.

## Paper Assets Sync (Server -> Local)
- Server: use `paper-export` to export to `~/project/exp/paper_exports/<project>/<run_id>/`; client: use `paper-sync` to pull incrementally.
- Export only paper-ready assets; do not export checkpoints/datasets/secrets; do not delete extraneous by default.
- Client pull: edit `/Users/daiyuming/Documents/自动化/.codex/paper_sync.json`, then run `python3 /Users/daiyuming/Documents/自动化/scripts/paper_sync.py` (rsync preferred).
