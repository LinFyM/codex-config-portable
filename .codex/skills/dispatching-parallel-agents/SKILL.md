---
name: dispatching-parallel-agents
description: Use subagents only for clearly separable work that can actually run in parallel and is expected to save substantial elapsed time after coordination and integration. Conserve tokens; skip routine review, speculative quality improvements, competing solutions, and simple reads better handled with parallel tools unless the user explicitly requests additional agent work.
---

# Dispatching Parallel Agents

## Decide And Reassess

- Default to completing the task in the main agent. Delegate only when work is clearly independent, can run alongside useful main-agent work, and will save substantial elapsed time after coordination and integration. A possible quality benefit alone is insufficient.
- When that condition holds, use the smallest useful delegation without asking again. Respect user limits and explicit requests for additional agent work.
- Do not turn task phases into dispatch checkpoints. Another delegation wave must independently justify substantial time savings; it is not a default continuation of the first.
- Conserve tokens by giving each agent only the relevant context, a bounded deliverable, and a stopping condition. Avoid full-history forks when a focused handoff is sufficient.
- Do not hard-code a subagent model or require profile files. Let the active runtime assign capacity unless the user explicitly asks for a model.
- Prefer direct parallel tool calls for simple reads and checks. Keep tightly coupled diagnosis, unresolved architecture decisions, and destructive operations with the main agent.

## Good Delegation Targets

- Independent exploration across different subsystems or evidence sources.
- Bounded investigation or implementation that can inform the critical path while the main agent advances non-overlapping work.
- Disjoint implementation slices with clear file ownership.
- Distinct implementation workstreams that satisfy the time-saving condition above. Competing solutions require an explicit request; do not generate them merely for a second opinion.
- Independent verification, documentation, or compatibility work only when it
  meets the same substantial time-saving condition. Do not routinely add a
  reviewer or tester for size, reassurance, or a possible quality improvement.

## Dispatch Contract

1. Give each agent one bounded objective, the necessary inputs, explicit constraints, expected evidence or output, and a stopping condition.
2. Assign disjoint write ownership. State which files are off limits, note that other agents may be working, and forbid reverting unrelated changes.
3. Use the runtime-provided isolated workspace for write-capable agents when available; otherwise use `using-git-worktrees`. Read-only agents may share the source tree.
4. Continue useful non-overlapping work in the main agent. Wait only when a result becomes necessary for the next decision.
5. Review evidence centrally, resolve conflicts, integrate one coherent result, run final verification, and close agents when their bounded work is complete.

## Boundaries

- Do not delegate force-pushes, history rewrites, hard resets, deletion of ambiguous work, privilege changes, production interruption, or other destructive actions.
- Do not send multiple agents the same vague question. Parallel candidates need distinct hypotheses or approaches and shared evaluation criteria.
- Do not use subagents to manufacture process, duplicate the main agent's
  analysis, or expand testing beyond what the underlying task warrants.
- Stop delegating when results are weak, scopes overlap, or coordination costs exceed the likely gain. Continue directly instead of spawning replacements reflexively.
