# Global AGENTS Instructions

## Scope
- Cross-project defaults for collaboration and execution style.
- Repository or subdirectory AGENTS override this file.
- Keep this file generic; do not assume project-specific build/test/release commands here.
- Keep this file policy-level; put role-specific model, reasoning, and workflow tuning in `~/.codex/config.toml` and `~/.codex/agents/*.toml`.

## Rule Priority
- Apply instructions in this order unless a narrower-scope AGENTS overrides them: safety/privacy/approval rules, explicit user instructions, mode-specific constraints, workflow requirements, then style preferences.
- Treat the rules in this file as applying to both the main agent and every subagent unless a rule explicitly says otherwise.
- When rules seem to conflict, preserve the stricter safety constraint and the clearer user intent first, then follow the preferred workflow around that boundary.

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

## Planning, Clarification, And Persistence

### Feature Delivery Contract (Superpowers Workflow)
- Use this canonical flow for new features and behavior changes:
  1. `superpowers:brainstorming` (clarify intent, constraints, success criteria, design approval)
  2. `superpowers:using-git-worktrees` (isolated workspace)
  3. `superpowers:writing-plans` (implementation plan in `docs/plans/`)
  4. `superpowers:executing-plans` or `superpowers:subagent-driven-development`
  5. `superpowers:requesting-code-review` + local persistent review conversation via `codex-persistent-terminal`
  6. `superpowers:finishing-a-development-branch` (complete branch flow)
- Always include explicit `Final Goal`, `Definition of Success`, and `Evidence Plan` in the plan/design artifacts.
- Never declare completion without verification evidence. If blocked, report blocker, risk, and next action explicitly.

### Plan Mode (Clarification-First)
- When in plan mode, do not implement. Only clarify requirements and produce a decision-complete plan.
- Apply the **User Questioning Policy (Before And During Execution)** below as the canonical questioning rule set.
- A decision-complete plan includes: assumptions, file/module breakdown, explicit verification steps, and definition of done.

### User Questioning Policy (Before And During Execution)
- Scope: this policy applies to both pre-implementation clarification and in-progress implementation.
- In pre-implementation brainstorming/planning, use `request_user_input` to resolve material ambiguities before coding when options are clear.
- During implementation, if new uncertainty appears (requirements, scope boundaries, risk tradeoffs, or missing context), ask immediately; do not defer questions until the end.
- Prefer `request_user_input` for decision points with clear options; keep each round focused (1-3 questions) and continue execution after answers are received.
- Do not hide uncertainty by guessing when a wrong assumption could cause rework or unsafe changes.

### Execution Persistence (Finish The Job)
- After the plan is agreed and execution begins, proceed end-to-end until the task is complete.
- Do not stop mid-execution to provide a partial progress report or to ask "should I continue?" unless blocked or explicit approval is required.
- Asking clarifying questions per the User Questioning Policy is expected when needed to unblock correctness/safety, and is not considered unnecessary pausing.
- Only pause early when: a required decision/input blocks safe progress; a destructive/high-impact action needs explicit approval; a long-running job exceeds a reasonable time window to actively monitor; or verification fails and cannot be resolved with reasonable effort.
- Maintain a checklist derived from the agreed plan and ensure all items (including verification) are completed before the final report.
- Long-running work: if likely short, actively poll/monitor to completion; if likely long, use `longrun-orchestrator`.
- Reporting: Final Report only when the checklist is complete or truly blocked; Interim Update only when paused and must include a resume trigger.
- Plan status blocks apply only when there is an explicit agreed plan/checklist (never for pure Q&A or minor one-off requests).

### Planning Records (Planning-With-Files)
- Canonical persistent planning files are workspace-root:
  - `WORKSPACE/task_plan.md`
  - `WORKSPACE/findings.md`
  - `WORKSPACE/progress.md`
- For complex tasks, use `planning-with-files` and keep these files updated during execution.
- By default, these planning files are part of delivery context and should be committed with related task work unless the user explicitly requests otherwise.
- Treat legacy memory files (`WORKSPACE/.codex/MEMORY.md`, `WORKSPACE/.codex/memory/*`) as historical context only; do not use them as the primary active planning system.
- Never store secrets; redact sensitive command/output before writing planning records.

## Subagents And Parallel Work

### Subagent Routing
- Prefer using subagents for non-trivial work when the task can be cleanly decomposed into independent research, review, implementation, verification, or monitoring tracks.
- Unless the user explicitly requests that subagents not be used, proactively use them in appropriate situations; do not wait for the user to mention or request subagents first.
- The main agent should actively consider delegation or parallelization instead of defaulting to single-threaded execution when subagents would improve speed, isolation, or code quality.
- This is a strong preference, not permission to violate higher-priority approval, safety, or environment constraints.
- Preferred role routing:
  - `reviewer`: correctness, security, regressions, and missing tests.
  - `explorer`: read-only codebase mapping, evidence gathering, triage, and log analysis.
  - `worker`: bounded implementation or fix work with explicit file ownership.
  - `docs_researcher`: official docs and source-backed API or framework research.
  - `helper_fast`: simple chores, inventories, grep-heavy scans, and quick summaries.
- Prefer read-only subagents for exploration and research. Use write-capable subagents only when the change scope is already clear.
- Do not run multiple write-capable subagents on overlapping files or responsibilities in the same worktree.
- If subagent deployment fails because the active subagent count has reached its limit, close no-longer-needed subagents and retry, or reuse an existing suitable subagent instead of silently giving up on delegation.

### Parallel Candidate Implementations
- For difficult, high-uncertainty implementations, the main agent may run a controlled parallel-candidate workflow instead of committing early to one approach.
- Use this workflow only when:
  - the task is complex enough that 2-3 materially different implementations are plausible;
  - the tradeoff is hard to resolve from inspection alone;
  - the expected value of parallel exploration is higher than the added coordination cost.
- Before spawning candidate implementations, the main agent must:
  - write a short comparison plan with the candidate approaches, evaluation criteria, and stopping rule;
  - define what “better” means for this task (for example correctness, simplicity, performance, maintainability, or test results);
  - cap the candidate count to a small number, usually 2 and at most 3.
- Each candidate implementation must run in its own isolated git worktree and branch.
- Candidate subagents may work on overlapping files only when they are isolated in separate worktrees. Do not run overlapping write-capable subagents in the same worktree.
- Assign each candidate a clearly different implementation direction. Do not spawn multiple agents that are effectively doing the same thing.
- After candidate work completes, the main agent must:
  - review all candidates itself;
  - run comparable verification for each viable candidate;
  - select one winner explicitly and explain why it wins;
  - keep only the winning implementation as the retained path.
- Losing candidates must not be merged back by default.
- Cleanup of losing branches, worktrees, and temporary artifacts should happen after the winner is validated. Follow the existing safety rules for destructive actions and ask for confirmation before deleting branches or other high-impact artifacts.
- Prefer this workflow for architecture-heavy features, risky refactors, or unclear implementation choices. Do not use it for routine edits, small bugfixes, or tasks where a single well-scoped implementation path is already clear.

## Engineering Quality
- For non-trivial work (new feature/refactor/multi-file), produce a written plan (usually via `superpowers:writing-plans`) before coding.
- For new features/functions, include test updates by default; if automation is truly impossible, provide a reproducible manual check and state residual risk.
- Avoid degradation handling, fallback, hacks, heuristics, local stabilizations, or post-processing bandages that are not faithful general algorithms.
- When replacing behavior, prefer "replace then remove" over "add and keep both"; explicitly clean dead code and stale configs.
- When adding a new module or feature, identify the code path being replaced first and clean or retire it in the same delivery cycle when safe.
- Before placing new logic, decide explicitly whether it belongs in an existing module/file or in a new one.
- Prevent "god files": keep entrypoints thin; add new functionality in new modules/files when reasonable.
- Size/complexity limits (defaults unless repo overrides):
  - Files: soft 400-600 lines; hard 800 lines.
  - Functions: soft 40-60 lines; hard 120 lines.
  - Complexity: target <= 10, avoid > 15.
- If adding logic to an existing file, check the expected post-change file size against the limits below before implementing; if the file would become cramped or cross a limit, split the work into a new helper/module instead of forcing it into the existing file.
- Enforcement for size/complexity limits:
  - If a change crosses a soft limit, include a short split/refactor plan in delivery notes.
  - If a change crosses a hard limit, split/refactor before completion by default.
  - Hard-limit exceptions require explicit user approval and must document rationale + follow-up cleanup plan.
- Pre-existing oversized files are legacy exceptions, not permission to keep growing them.
- If a file is already above `1000` lines, default to adding new logic in new helper/modules and keep edits in that file to minimal wiring only.
- After implementation, run the repo's existing quality gates (format/lint/typecheck/tests). If none, run minimal checks and propose lightweight tooling.

### Code Design Discipline
- Keep code modular, cohesive, and loosely coupled. Each module/function should have one clear responsibility and a small, explicit interface.
- Prefer the simplest readable implementation that satisfies the approved requirement. Do not add abstractions, frameworks, layers, factories, registries, or generic extension points unless there is a concrete current need or an established local pattern.
- Write code for known requirements and verified interfaces only. Do not add speculative compatibility paths, guessed schema variants, guessed field names, or "try every possible key" logic.
- When an API, response schema, config contract, or caller expectation is unclear, inspect the source/docs/tests/sample payloads first; if still unclear, ask the user instead of guessing.
- Do not add fallback code merely to make code appear more robust. Fallbacks must be required by the product contract, based on an observed failure mode, and covered by tests or a documented manual check.
- Avoid redundant code and duplicate logic. Reuse existing helpers when they fit; otherwise keep new helpers narrow and easy to delete.
- Optimize for readability and maintainability first, then performance where the workload or measurements justify it. Avoid clever code when straightforward code is sufficient.

### Repo Hygiene (Configs, Scripts & Artifacts)
- Reuse/edit existing YAML/config/scripts; avoid near-duplicates (parameterize/override instead).
- Keep one canonical `latest`; archive iteration history under `WORKSPACE/.codex/tmp/artifacts/` (prefer `artifact-manager`).
- Put temporary outputs under `WORKSPACE/.codex/tmp/...` or system `/tmp` (do not scatter across the repo).
- Before long-running jobs or multi-stage training, estimate the expected disk footprint on the target filesystem and compare it against current free space.
- Classify outputs as `final` vs `temporary` during the task, not after the filesystem is already under pressure.
- For non-trivial tasks, run `workspace-cleanup` to inventory keep vs temporary. Temporary artifacts created by the current task that are clearly superseded, failed, or non-deliverable should be cleaned promptly once they are verified unnecessary; ask before deleting ambiguous or user-authored artifacts.
- Failed longrun directories, retired worktree outputs, duplicate smoke outputs, and `.codex/tmp` artifacts are default cleanup candidates once they are no longer needed.
- Do not treat "put it in tmp" as sufficient cleanup. Temporary files must be actively removed once verified unnecessary.
- Before and after substantial runs, check disk usage explicitly and record meaningful storage risk when relevant.

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

## Git Workflow (Guardrails)
- Do not work directly on protected branches (`main`/`master`/release) unless the user explicitly requests it; use a feature branch.
- For non-trivial work, checkpoint with small, reviewable commits; push the feature branch as a backup once local gates pass.
- Before opening any PR, you must run local review and resolve findings:
  - preferred: start a new tmux-backed persistent review conversation via `codex-persistent-terminal`, ask it to perform the local review, and keep all follow-up fixes + re-review inside that same conversation.
  - if the review terminal is lost, recover the same review conversation with `codex-persistent-terminal` and `codex resume`; do not fall back to spawning a fresh one-shot `codex exec` review by default.
  - if P0/P1 issues are found, fix and continue the same persistent review conversation until cleared or explicitly escalated.
  - timing note: local review can take a long time, including 10+ minutes for deeper runs or re-review loops; wait patiently before assuming the session is stalled unless there is a clear error signal.
- Allowed without extra confirmation (low-risk): `git status`, `git diff`, `git add`, `git commit`, `git push` (feature branch).
- Must ask for explicit confirmation (high-impact): opening PRs, merging/rebasing onto protected branches, remote URL changes, deleting branches, history rewrites, destructive operations (`push --force*`, `git reset --hard`, broad cleanups).
- For GitHub automation, first verify `gh auth status -h github.com`; if unauthenticated, ask the user to run `gh auth login`.
- PR privacy rule: never include personal information in PR title/body/comments/attachments/commit messages (for example real name, personal email, phone number, home/company address, ID numbers, private account handles, local absolute paths containing identity). Redact before publishing.

## Git Worktrees (Parallel Work)
- Use worktrees when it materially reduces risk or time (parallel feature+fix tracks, long runs, keeping a clean baseline).
- Formal training rule: official/full/prolonged training runs that are intended to produce deliverable checkpoints must be launched from the repository's main workspace on branch `main`, not from a worktree.
- Worktrees may be used for smoke tests, debugging, profiling, sweeps, dry runs, and other temporary validation only; do not treat worktree outputs as the canonical formal-training artifact location.
- Before launching any formal training run, verify both `pwd` and `git rev-parse --abbrev-ref HEAD`; the expected state is the repository main workspace path and branch `main`.
- Default directory strategy (superpowers-compatible):
  - if `.worktrees/` exists, use it;
  - else if `worktrees/` exists, use it;
  - else ask user between project-local `.worktrees/` and global `~/.config/superpowers/worktrees/<project>/`.
- For project-local worktree dirs (`.worktrees/` / `worktrees/`), verify ignored status before creation with `git check-ignore`; if not ignored, fix `.gitignore` first.
- Worktree drift guard (mandatory when a target worktree/branch/path is specified): before any file edit and before final handoff, run `pwd` and `git rev-parse --abbrev-ref HEAD`, and verify both match the target.
- If the path/branch check fails, stop immediately; do not write files until switched back to the correct worktree and re-verified.
- Re-run the same check after any command likely to change execution context (for example `cd`, `git worktree ...`, or wrapper scripts that may change cwd).
- Merging/rebasing onto protected branches remains explicit-confirmation (see Git Workflow).
- Codex discovery note: Codex discovers project `AGENTS.md` files from the current session's project root (typically that checkout's Git root) down to the current working directory. A worktree should carry the repository root's tracked `AGENTS.md` as part of its own checkout. Do not rely on physical parent-directory placement alone to inherit instructions across worktrees.
- Canonical registry convention: if a repository keeps a branch/worktree registry inside the root `AGENTS.md`, every worktree may read that file, but the main workspace checkout's copy is the canonical place for registry maintenance.
- Branch/worktree bookkeeping: whenever you create/delete/merge a git branch or worktree, keep the repo root `AGENTS.md` present in worktree checkouts, and update the canonical “Git branch registry” from the main workspace only. Do not maintain divergent registry edits separately inside worktrees.

## Code Review (Automated Loop)
- Use the latest available code model and high reasoning by default for reviews (keep `model`, `review_model`, `model_reasoning_effort` aligned in `config.toml`).
- Treat review as a gate; if P0/P1 issues are found, fix and re-review (cap iterations, then escalate).
- PR gate requirement: no PR creation before a successful local Codex review run (or explicit user-approved exception).
- Use `superpowers:requesting-code-review` during implementation, then enforce a local tmux-backed persistent Codex review conversation before PR.
- Local review persistence rule: do not treat local review as a series of independent one-shot `exec` sessions. Open one persistent review conversation, keep feeding diffs/findings/fixes back into that same conversation, and only finish when that conversation reports no remaining blocking issues or the user explicitly accepts an escalation.

## GitHub Codex Cloud Review (Visibility Rule)
- In some repos/orgs, Codex “cloud review” may signal **pass** by only adding a 👍 reaction on the PR, with no comment/review.
- In some repos/orgs, a 👀 reaction from `chatgpt-codex-connector[bot]` means the cloud review has already started.
- `gh pr view` default output does not show reactions, so it can look like “no feedback”.
- timing note: cloud review can also take a long time to show up, including 10+ minutes before reactions/comments/check signals appear; wait patiently before concluding that no review happened.
- If the bot's 👀 reaction is already present, do **not** post another `@chatgpt-codex-connector please review` comment. Treat 👀 as the in-progress signal and wait for the final 👍 / comment / review result.
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
