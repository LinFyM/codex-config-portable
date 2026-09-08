---
name: using-git-worktrees
description: Use autonomously when overlapping edits, branch or history operations, concurrent writers, or independent implementations require isolation. A dirty checkout alone is not a trigger when narrow edits are disjoint and need no branch switch. Skip read-only, routine, non-repository, and tightly coupled small work.
---

# Using Git Worktrees

A worktree is an isolation mechanism, not a reason to create another
implementation, branch, or review stream. Use one only for work that already
needs isolation, and remove task-owned worktrees after verified integration.

## Decide And Isolate

- Create a worktree without asking when a trigger in the description clearly applies.
- Treat a dirty checkout as evidence to inspect, not an automatic worktree. If
  task-scoped edits are disjoint from existing changes, require no branch
  switch, and have no concurrent writer, preserve the checkout and work in place.
- Use the runtime-provided isolated worker workspace when subagent tooling already supplies one. Do not nest an extra Git worktree unless repository state or integration requires it.
- Do not create parallel implementations merely to justify isolation. Candidate
  branches require materially different hypotheses or explicit task value.
- Otherwise give each write-capable delegated task its own branch and worktree. Read-only agents do not need a worktree.
- Keep tightly coupled edits in one owned checkout instead of fragmenting them across branches.

## Preflight

1. Confirm the repository root, current branch, and `git status`.
2. Identify the base ref, intended integration target, and whether the task branch/worktree is agent-created and task-owned.
3. Check repository instructions for branch naming, worktree placement, and canonical execution paths.
4. Reuse an existing `.worktrees/` or `worktrees/` convention. For project-local placement, verify the directory is ignored with `git check-ignore`.
5. If no convention exists, choose a stable global root or an ignored project-local `.worktrees/` directory based on the existing environment. Ask only when placement has meaningful storage, retention, or ownership consequences.

## Create

Use a descriptive branch, normally with the `codex/` prefix:

```bash
git worktree add <path> -b codex/<topic> <base-ref>
```

Verify the location and branch before edits:

```bash
cd <path>
git rev-parse --show-toplevel
git rev-parse --abbrev-ref HEAD
git status --short --branch
```

Run only the setup and baseline checks needed for the task. Record pre-existing failures instead of silently fixing unrelated issues.

## Coordinate Active Worktrees

- Recheck path and branch before edits when multiple worktrees are active, and keep write ownership disjoint.
- Follow repository rules that require formal jobs or canonical artifacts to run from a specific workspace or branch.

## Integrate And Clean Up

- Inspect task-scoped diffs and verification evidence, then integrate autonomously when repository checks and policy permit. Rebase or use pull-rebase only on a clean, agent-created, task-owned branch; for user-owned or ambiguous branches, fetch and merge without rewriting history, or ask if rewriting is genuinely required.
- Before cleanup, verify that the integration target contains the task changes by ancestry or explicit diff/patch equivalence and that no unintegrated changes, unpreserved user artifacts, or required deliverables remain.
- Remove fully integrated, clean, task-owned worktrees and branches autonomously when ownership and retention are clear. Delete a remote task branch only when the repository workflow expects it and merged state is verified.
- Never remove a worktree with uncommitted user work or delete an ambiguous or unmerged branch. Ask only when that destructive ambiguity remains.
