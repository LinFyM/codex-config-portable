# Global AGENTS Instructions

## Scope
- This file defines cross-project defaults for collaboration and execution style.
- When repository or subdirectory AGENTS files provide more specific guidance, follow those local instructions.
- Keep this file generic; do not assume project-specific build, test, or release commands here.

## Server Environment (GPU Nodes)
- This server environment has two compute nodes: `gpu01` and `gpu02`.
- Each node has 8 GPUs: `NVIDIA A40 (46068 MiB)`.
- When a task requires idle GPUs, always check both `gpu01` and `gpu02` before deciding where to run.
- Do not make scheduling decisions based only on the current node.
- When reporting availability, include both nodes and the recommended GPU candidates.
- Prefer the `gpu-preflight` skill for consistent, fast, non-interactive checks across both nodes.

## Communication
- Default to concise, practical responses in Chinese unless the user requests another language.
- Lead with the outcome first, then include only the key rationale.
- State assumptions clearly when context is incomplete.
- If uncertain, say so explicitly instead of guessing.

## Working Style
- Read relevant context before making edits.
- Prefer minimal, targeted changes; avoid unrelated refactors.
- Preserve existing project conventions (naming, structure, formatting, tooling).
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
- Do not stop mid-execution to provide a partial progress report or to ask "should I continue?" unless you are blocked or explicit approval is required.
- Only pause early when: a required decision/input blocks safe progress; a destructive/high-impact action needs explicit approval; a long-running job exceeds a reasonable time window to actively monitor; or verification fails and cannot be resolved with reasonable effort.
- Maintain a checklist derived from the agreed plan and ensure all items (including verification) are completed before the final report.

- Long-running work (polling vs automation):
  - If likely short: actively poll/monitor to completion, then continue follow-ups in the same run.
  - If likely long: use the `longrun-orchestrator` skill (resumable logs/state + optional follow-ups).
- Reporting contract:
  - Final Report only when the agreed plan/checklist is complete, or execution is truly blocked and needs user input/approval.
  - Interim Update only when paused; keep it minimal and include a clear resume trigger (see `longrun-orchestrator` guidance).
  - Plan status blocks apply only when there is an explicit agreed plan/checklist. Do not include plan status for pure Q&A or minor one-off requests.

## Memory System (Workspace-Scoped)
- Purpose: make complex projects resumable across new chats and context compaction by keeping a small, durable, human-readable memory in the active workspace.
- Workspace-scoped only: store and read memory only inside the active workspace (the repo / working directory the user is actively working on).
- Never create or update memory files under `$HOME`, the filesystem root, or an unrelated directory.
- Canonical memory paths:
  - `WORKSPACE/.codex/MEMORY.md` (curated, stable facts: architecture, conventions, decisions, gotchas; low churn)
  - `WORKSPACE/.codex/memory/YYYY-MM-DD.md` (daily log; append-only; small entries)
- Prefer skills for memory workflows: `memory-recall` (bootstrap/resume) and `memory-flush` (checkpoints).
- Memory flush is event-based (not per message): milestones; decision/assumption/gotcha changes; before `/compact`; before starting a new chat on the same work; task/subproject switches; end-of-day wrap-up.
- Default reporting: update memory files silently. Do not include "memory updated", audit-file paths, or housekeeping logs in every response.
- Disclose memory/housekeeping details only when:
  - the user asks explicitly, or
  - a handoff/resume requires it (for example, starting a new chat, end-of-day wrap-up), or
  - debugging requires proving what was written where.
- Workspace `AGENTS.md` guidance (avoid duplication with memory):
  - Workspace `AGENTS.md` is stable "how to work in this repo" policy (commands, module boundaries, conventions, safety/ops guardrails, repo overrides).
  - Memory files hold durable decisions/gotchas (`MEMORY.md`) and the chronological log (`memory/YYYY-MM-DD.md`).
- Safety and privacy:
  - Never store secrets, tokens, credentials, private keys, or sensitive local configuration values in memory files.
  - If a command/output contains secrets, redact before writing.

## Engineering Quality
- For any non-trivial task (new feature, refactor, multi-file change), start with a short plan before writing code:
  goal, non-goals, proposed file/module breakdown, and verification steps.
- Prevent "god files": new functionality should usually go into new modules/files; keep entrypoints thin (wiring/config only).
- Prefer feature/domain-oriented structure over dumping helpers into a single utils file.
- File size limits (defaults unless the repo specifies otherwise):
  soft limit: 400-600 lines; hard limit: 800 lines.
  If a file would exceed the hard limit, split it before adding more features.
  (Generated code or vendored third-party code can be exempt, but avoid editing it directly.)
- Function limits:
  soft limit: 40-60 lines; hard limit: 120 lines.
  cyclomatic complexity: target <= 10, avoid > 15.
  If a change increases complexity, extract helpers and reduce nesting (early returns are preferred).
- When adding a new feature to an already-large file, refactor first to create clear module boundaries,
  then implement the feature in the new module(s) (avoid repeatedly growing the same file).
- After implementation, run the repo's existing quality gates (formatter/lint/typecheck/tests).
  If the repo has no established tooling, run minimal language-appropriate safety checks and propose a lightweight toolchain before adding it.
  For Python projects, default to `python -m compileall` and propose `ruff` + `black` + `pytest` (optionally `mypy`).

### Repo Hygiene (Configs, Scripts & Artifacts)
- Default: reuse and edit existing YAML/config/scripts; do not create new ones unless necessary.
- Before creating a new `*.yml/*.yaml/*.sh/*.py`, search for an existing baseline; avoid near-duplicates (parameterize/override instead).
- Iteration artifacts: keep one canonical `latest` in-repo; archive only when needed under `WORKSPACE/.codex/tmp/artifacts/` (prefer `artifact-manager`).
- Temporary artifacts: prefer `WORKSPACE/.codex/tmp/<label>_<timestamp>/` or system `/tmp/` (do not scatter across the repo).
- Cleanup gate for non-trivial tasks: run `workspace-cleanup` to inventory keep vs temporary; do not delete without explicit user approval.

## Git Workflow (Option B: Autopilot With Guardrails)
- Default branch hygiene:
  - Do not work directly on protected branches (`main`/`master`/release) unless the user explicitly requests it.
  - If currently on a protected branch, create/switch to a feature branch before making edits.
- Proactive version control:
  - For non-trivial work, checkpoint progress with small, reviewable commits.
  - Default to pushing the current feature branch to the remote as a backup once the local gates pass.
- Allowed without extra confirmation (low-risk):
  - `git status`, `git diff`, `git add`, `git commit`, `git push` (to the current feature branch).
- Must ask for explicit confirmation (high-impact):
  - Opening a PR, merging, rebasing onto protected branches, changing remote URLs, deleting branches.
  - Any history-rewriting or destructive operations: `push --force*`, `git reset --hard`, broad cleanups.
- Rollback & redo (self-serve):
  - Prefer non-destructive rollback (`git revert`) for committed mistakes.
  - For uncommitted changes that need a redo, create a safety net first (WIP commit or a patch under `WORKSPACE/.codex/tmp/patches/`), then ask before discarding work.
- When the user asks for a fully automated deliverable flow (review -> fix -> verify -> commit/push), prefer the `git-autopilot` skill.
- Cloud/PR workflows:
  - Keeping the feature branch pushed is encouraged for resiliency and handoff.
  - Use `yeet` when the user explicitly wants an end-to-end GitHub flow (commit/push + open a PR) via `gh`.
  - Use `gh-fix-ci` to diagnose failing GitHub checks, and `gh-address-comments` to address PR review comments (both are approval-gated by their own skills).
  - Opening PRs / merging remains an explicit user decision.
- GitHub CLI note: for any GitHub automation (`gh-*` skills, branch cleanup, CI inspection), first verify `gh auth status -h github.com`; if unauthenticated, ask the user to run `gh auth login`.

## Git Worktrees (Parallel Work)
- Use worktrees to avoid stash/switch churn and to enable true parallelism (e.g., long-running jobs, independent feature+fix tracks, keeping a clean baseline checkout).
- Agent initiative:
  - If parallelization materially reduces risk or time, proactively create a worktree by default.
  - If the benefit is unclear or disk impact may be high, propose a worktree plan first and ask.
- Prefer the `git-autopilot` skill for the detailed, end-to-end worktree workflow (create worktree -> review/fix loop -> verify -> commit/push).
- Conventions:
  - Put extra worktrees under `WORKSPACE/.codex/tmp/worktrees/<slug>_<timestamp>/` (do not scatter under repo root).
  - Branch naming: `wt/<slug>-YYYYMMDD-HHMM` (push as a backup once local gates pass).
  - Keep outputs worktree-scoped (avoid clobbering shared `results/`); follow `Repo Hygiene` + `artifact-manager`.
- Large tracked artifacts warning:
  - If the repo tracks large binaries (e.g., via Git LFS or committed datasets), worktrees may duplicate large files; ask before creating.
- Merge & cleanup:
  - Merging/rebasing onto protected branches is always explicit-confirmation (see Git Workflow).
  - After a worktree branch is merged or abandoned, remove the worktree and run `git worktree prune` (do not delete user data/artifacts without approval).

## Code Review (Automated Loop: Review -> Fix -> Re-review)
- Use the latest available code model and high reasoning by default for reviews (keep `model`, `review_model`, and `model_reasoning_effort` aligned in `config.toml`).
- Before finalizing non-trivial changes, run a local code review and treat it as a quality gate.
- If review reports P0/P1 issues, automatically fix them, then re-run review; repeat until clean or blocked (cap the loop to a small number of iterations, then escalate).
- Linux sandbox note (CentOS7/older kernels): prefer the `git-autopilot` skill to run review via `codex exec -s danger-full-access ...` when `codex review` is unavailable.
- Keep reporting lightweight: summarize key findings and what changed; do not dump full review transcripts unless asked.

## Safety
- Ask before destructive or high-impact actions (for example: deleting data, force pushes, broad file rewrites, production-impacting commands).
- Never expose secrets, tokens, credentials, or sensitive local configuration values.
- Keep network access and privilege escalation aligned with task necessity.

## Delivery & Verification
- After changes, run the smallest relevant verification steps available (tests/lint/type checks) and clearly separate "verified" vs "not verified".
- If verification cannot be run, explain exactly why and what risk remains.
- Keep delivery concise: what changed (why), key files touched, and only useful next-step options.

## Skills (Progressive Loading)
- Keep this file policy-level; put step-by-step playbooks in skills so they load only when relevant.
- Prefer refining existing skills over growing this file.

## Continuous Improvement
- If the same correction or preference appears repeatedly, propose updating AGENTS instructions so future sessions improve.

## Paper Assets Sync (Server -> Local)
- Convention: on the server use `paper-export` to export; on the client use `paper-sync` to pull incrementally.
