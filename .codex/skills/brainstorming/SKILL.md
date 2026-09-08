---
name: brainstorming
description: Use before implementation only when a feature, product behavior, interface, or architecture has a material unresolved choice whose answer would change the result. Skip clear requirements, settled scientific or implementation contracts, routine fixes, configuration, migrations, and operational actions.
---

# Brainstorming Into A Decision

## Goal

Resolve decisions that would otherwise cause meaningful rework. The output should be a concise direction supported by the user's goal, existing constraints, and any material preferences they provide. A separate approval is not required when context already settles the choice.

## Trigger Test

Use this skill when at least one of these is true:

- Different reasonable interpretations would produce materially different results.
- The user is choosing product behavior, user experience, architecture, or an irreversible tradeoff.
- Success criteria, scope boundaries, or ownership are genuinely unclear.

Skip it when the user has already specified the desired behavior, the existing code or config determines the implementation, or the task is a narrow repair with an observable correct result.

## Workflow

1. Inspect relevant context first: repository structure, current behavior, constraints, and prior decisions.
2. State the decision that is actually unresolved.
3. Ask focused questions only when the answer cannot be discovered and guessing would be costly.
4. Present alternatives only when they are materially different. Usually one recommendation plus one credible alternative is enough.
5. Recommend a direction and explain the decisive tradeoff.
6. If a material unresolved choice remains, settle it with the user before implementation; otherwise proceed.

## Design Output

For substantial work, capture:

- Final goal and non-goals.
- Definition of success.
- Chosen approach and important tradeoffs.
- Affected components or systems.
- Evidence plan and meaningful risks.

For small decisions, a short paragraph is sufficient.

## Boundaries

- Do not force approval for routine commands, narrow configuration, clear bug fixes, or reversible operational work.
- Do not invent two or three options when one established repository pattern is plainly correct.
- Do not reopen a frozen experiment contract or rejected scientific path merely
  because alternative implementations can be imagined. New evidence or a
  genuinely changed objective is required.
- Do not automatically chain into planning, worktrees, or implementation skills; choose the next step based on scope and risk.
