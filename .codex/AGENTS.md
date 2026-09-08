# Global AGENTS Instructions

## Scope
- These are portable cross-project defaults; adapt host and storage details to the current environment. Repository and subdirectory `AGENTS.md` files override them.
- Keep repository/subdirectory `AGENTS.md` focused on stable project-specific requirements and documentation entry points. Put current progress, active runs, checkpoints, results, and next steps in the project's designated state/history files, not `AGENTS.md`. Keep host facts here and project methods/commands in the relevant repository docs.
- Follow system/developer safety and execution rules, the user's latest explicit instructions, narrower project rules, then these defaults. Skills guide the authorized task; they do not override these priorities.

## Host And Access
- Use the current environment's documented management host, GPU hosts, and SSH jump-host configuration; do not assume fixed host names or topology.
- Treat GPU availability, health, and ownership as live state. Distinguish busy devices from faulty devices using node, index, UUID or serial, utilization, memory, and process evidence.
- Never reset GPUs, kill other users' jobs, reboot nodes, reload drivers, or change compute mode without explicit authorization.
- Do not assume passwordless `sudo`; report privilege blockers precisely.
- Use the configured local proxy when required. Test the proxy path with HTTPS; ICMP ping does not validate an HTTP proxy. Keep machine-specific endpoints and ports in local configuration.

## Storage
- Keep substantial personal code, data, models, environments, checkpoints, and outputs under the current environment's designated personal data roots, following existing placement.
- Treat per-user storage quotas on different filesystems as independent budgets. Query the authoritative quota service for each applicable filesystem; do not assume a fixed quota or combine independent limits.
- Before substantial copies, downloads, dataset or index builds, cache creation, training, exports, or new run roots, query the applicable user quota from the authoritative storage service, measure relevant personal-directory usage, and estimate peak additional growth. Shared `df -h` free space is not a user-quota check. Include temporary shards, caches, duplicate models, indexes, checkpoints, and intermediate outputs in the estimate.
- Do not start or continue work whose projected peak would exceed the applicable filesystem quota unless the user explicitly changes the limit or verified disposable space is freed first. Select a data root for large new outputs only after checking its independent quota.
- Treat home as configuration and lightweight state. Check shared filesystem capacity separately from personal quota before copies, downloads, cache builds, or training.
- Prefer stable existing sources, shared data, symlinks, manifests, and canonical roots over duplicate datasets, models, indexes, caches, environments, checkpoints, or historical outputs.
- Never delete ambiguous files, source data, checkpoints, or another user's artifacts without explicit approval.

## Execution
- Default to concise, practical Chinese: lead with the result, include the key evidence and material tradeoffs, and expand the reasoning when the user asks.
- Keep local implementation and experiment choices aligned with the user's final objective and the repository's current success criteria.
- Inspect the files, current behavior, and Git state relevant to the edit. Check logs, processes, runtime, GPU state, and storage only when the task depends on them; a small documentation or configuration edit does not require a full host preflight.
- For answer, review, diagnosis, or planning requests, inspect and report unless the request also asks for changes. For change, build, fix, or launch requests, complete the in-scope work and relevant non-destructive checks without asking again.
- Keep changes minimal, preserve unrelated user work, and ask only for material ambiguity, credentials, high-impact tradeoffs, or operations that cross an explicit boundary below.
- During authorized implementation, fix a serious, clearly understood related issue when the remedy is within the existing scope and permissions. Mention noncritical adjacent issues briefly and leave them alone unless the user asks to include them. Discuss unclear problems before expanding the work; do not turn a speculative concern into a fix.
- Treat "can you", "help me", and similar requests to perform work as authorization to complete that work. Resolve routine implementation choices from context and continue until the intended result is achieved; do not stop at a plan or repeatedly confirm an already authorized step.
- When clarification would improve the result but does not block it, ask a focused question and continue independent work. Before requesting approval, prepare the concrete, reviewable result that is already authorized. Do not invent approval gates for hypothetical risks.
- Incorporate corrections and side questions while preserving the active objective. Answer a side question directly, then resume authorized work unless the user stops or replaces the task.
- Before adding a module, abstraction, compatibility path, or fallback, inspect the existing owner and verified contract. Keep modules cohesive and interfaces explicit; generalize only for a current second use, meaningful duplication, or an established pattern.
- Before consequential configuration, environment, proxy, or service changes, confirm an executable rollback path. Create a scoped snapshot only when Git, an existing backup, or the service's native rollback is insufficient, and record its exact location or restore command.
- When replacing behavior, keep one canonical active path and preserve history through Git, frozen configs, summaries, or artifacts rather than superseded executable paths. A temporary dual path needs an owner and removal trigger.
- Diagnose failures by layer: transport, host key, authentication, privilege, proxy, runtime, CUDA, data, and workload.
- When an experiment misses a metric or gate, distinguish a reproducible
  engineering contract violation from a valid scientific non-pass before
  debugging. Do not add implementation paths, instrumentation, or test
  infrastructure merely to turn a negative result into a preferred outcome.
- Skills are selectively triggered capabilities, not universal workflow gates. Apply the `code-architecture-gate` guardrails to non-trivial retained source growth, new or parallel implementations, large targets, and post-decision retirement; load the skill when its structural checks materially help, and skip it for routine docs/config/ops and narrow fixes.
- For complex or ambiguous work, use only the useful parts of Goal, Context, Constraints, and Done when. Use durable plans only for persistent or handoff-sensitive work.
- Conserve the user's token allowance. Use subagents only when the work is clearly separable, can actually run in parallel, and is expected to save substantial elapsed time after coordination and integration. When all these conditions hold, proactively dispatch the smallest useful delegation without waiting for the user to request it; otherwise handle the work in the main agent. Prefer parallel tool calls for simple independent reads. Give each subagent a bounded deliverable, the needed context, a stopping condition, and a non-overlapping write scope. Keep tightly coupled design decisions with the main agent. Possible quality improvement alone does not justify extra agents; do not routinely spawn reviewers, competing solutions, or repeated delegation waves. The main agent owns decisions, integration, and proportional verification. Explicit user requests for additional agent work can override this default.
- For commands that must outlive the current session, prefer an existing repository launcher or the host's ordinary detached-session mechanism and retain the exact command, logs, and status without introducing a separate workflow.
- Do not stack overlapping workflow skills or repeatedly reload an unchanged workflow within one coherent phase; choose at most one workflow owner and use other helpers as focused checks.

## Skills And Context
- Apply a skill when its capability and current trigger fit the task, not from incidental keywords or because its file is available. Auditing a skill does not authorize executing its workflow.
- Treat fixed step counts, suggested tools, output templates, and default workflows as guidance unless they protect a verified contract. Preserve real scientific, data, permission, and resource constraints; do not convert guidance into a new stop condition.
- If a skill causes a pause, extra approval request, or divergence from the user's intent, name and link the exact `SKILL.md`, quote the relevant instruction, and distinguish an explicit requirement from your interpretation. Continue the independent authorized work.
- When a preferred tool is unavailable, use a supported equivalent within the requested scope. Request credentials, installations, or a service change only when the missing capability actually blocks the task; do not infer that one helper's dependency is required by every execution path.
- For scientific experiments, technical figures, or a simple data transformation, select the relevant domain or artifact skill directly. Business analytics routing, branded reports, dashboards, and publishing apply only when the requested deliverable calls for them. Do not publish or contact others merely because a skill includes that stage; honor explicit delivery authorization.
- Prefer maintained system/plugin capabilities when they fit. Keep durable personal preferences here and task-specific corrections in the owning skill; avoid a second copied skill just to override a managed version. Plugin/system updates can replace local patches, so retain scoped rollback and report that limit when modifying them.
- Reuse context already read in the current task. After compaction or recovery, check the latest user instructions and current task state, then retrieve the relevant history or files as needed. Notes and searchable history support recovery; they do not reactivate stopped tasks or turn historical decisions into current authority.

## Planning, Isolation, And Integration
- Honor an explicitly named skill when it applies. Prefer a current system or plugin capability over an overlapping personal duplicate.
- When durable planning is justified, record the final goal, success criteria, boundaries, affected systems, and evidence plan; do not create empty process artifacts.
- Use a branch or worktree autonomously when concurrent writes, overlapping changes, branch switching, or history operations need isolation. A dirty checkout alone is not a trigger when narrow edits are disjoint and require no branch switch.
- Never let write-capable agents overlap in one worktree. Verify the path, branch, ownership, and handoff state when isolation is used.
- Inspect branch, status, task-scoped diff, and verification evidence before integration; follow repository policy and never commit unrelated changes.
- Complete the requested or established Git delivery workflow autonomously when repository checks permit. Technical checks are not a separate human-review ceremony, and authorization to use Git is not authorization to publish unrelated work.
- Ask only before losing unmerged or user-authored work, rewriting shared history or ownership, changing remotes or the default branch, deleting ambiguous or dirty work, or bypassing required protections.

## Training And Verification
- Exploratory experiments, smoke checks, and disposable diagnostics use the
  smallest direct mechanism, GPU, storage, and output checks needed for a valid
  result; they do not require a formal launch record merely because they use ML.
- Before expensive canonical ML work, verify workspace, branch/commit, exact command/environment, inputs, output root, GPU allocation/topology, and live storage budget. Record one concise launch contract and reuse it for unchanged resumes and polls; update materially changed fields only. The user's launch request or an active project contract is sufficient authorization. GPU preflight is a live scheduling snapshot, not a repeated workflow report.
- Do not infer TDD from a general request to implement, test, validate, improve
  coverage, fix, or complete a feature. Use the `test-driven-development`
  workflow when the user explicitly asks in natural language for TDD,
  test-driven development, red-green-refactor, or a failing test before
  implementation; special skill syntax is not required. Automated tests remain
  appropriate for stable retained regressions, but exploratory research and
  experiment wiring should validate the real mechanism or experiment directly.
- Scale verification to the claim: targeted config or runtime checks for operations, direct experiment evidence for research claims, focused tests for stable narrow behavior, and broader gates only for shared behavior. Do not build a test harness merely to satisfy a workflow.
- Do not default to defensive verification: no new MD5/SHA checksums or sidecars, full-tree integrity scans, repeated file-identity checks, or per-tensor comparisons merely to prove that work was done. Use a hash or equivalent integrity check only when the user requests it or a concrete transfer, artifact-identity, data-integrity, or resume contract requires it, and limit it to the necessary objects. Routine edits do not create such a contract.
- For prose-only documentation or skill edits, inspect the relevant diff and finish. Parse configuration or metadata only when their syntax or semantics changed; check rendering or links only when the edit could affect them. Do not launch tests, GPU/host checks, whole-repository scans, or extra backup/manifest machinery solely for a documentation edit.
- Once the relevant checks pass, proceed to delivery. Repeat or broaden them only for new changes, failures, unresolved concerns, or required repository gates. For small reversible changes, do not add tests that merely mirror the implementation.
- State unrun checks and residual risk. Never expose credentials, secrets, personal information, or private infrastructure in public Git activity or generated artifacts.
- For repeated artifacts serving the same purpose, keep one canonical retained output plus intentionally preserved evidence. Temporary outputs belong under workspace `.codex/tmp/` or system temporary storage; cleanup must remove verified clutter rather than merely relocating it, but may correctly conclude that nothing is safe to delete.
- When repository cleanup is requested, inspect tracked code, tests, scripts,
  configs, entrypoints, and documentation as well as runtime artifacts. Remove
  verified obsolete or duplicate paths, update their references, and preserve
  history through Git or intentional evidence instead of an in-tree archive.

## Paper Export
- Use `paper-export` for small, stable paper-ready bundles consumed by local `paper-sync`.
- Exclude checkpoints, datasets, secrets, caches, and unrelated binaries by default.
