---
name: requesting-code-review
description: Use when completing tasks, implementing major features, or before merging to verify work meets requirements
---

# Requesting Code Review

Use a reliable, locally-available review gate to catch issues before they cascade.

**Core principle:** Review early, review often; never rely on undefined integrations.

## When to Request Review

**Mandatory:**
- After each task in subagent-driven development
- After completing major feature
- Before merge to main

**Optional but valuable:**
- When stuck (fresh perspective)
- Before refactoring (baseline check)
- After fixing complex bug

## How to Request

**1. Run local Codex review (preferred):**
```bash
# Review current patch before committing
codex review --uncommitted
```

If your work is already committed (no uncommitted diff), create a small follow-up patch (or temporarily stage a diff) so `codex review --uncommitted` has content to review.

**2. Act on findings:**
- Fix P0/P1 immediately.
- Fix P2 before merge when feasible.
- Record intentional deviations in the plan/progress log.

**3. Before merge (PR path):**
- Ensure required CI checks are green.
- If your org uses Codex cloud review, confirm its signal (sometimes it is a 👍 reaction only).

## Example

```
[Just completed a task]

You: Let me run local review before proceeding.

codex review --uncommitted

[Fix findings]
[Re-run codex review]
[Continue]
```

## Integration with Workflows

**Subagent-Driven Development:**
- Review after EACH task
- Catch issues before they compound
- Fix before moving to next task

**Executing Plans:**
- Review after each batch (3 tasks)
- Get feedback, apply, continue

**Ad-Hoc Development:**
- Review before merge
- Review when stuck

## Red Flags

**Never:**
- Skip review because "it's simple"
- Ignore Critical issues
- Proceed with unfixed Important issues
- Argue with valid technical feedback

**If reviewer wrong:**
- Push back with technical reasoning
- Show code/tests that prove it works
- Request clarification

If you need a human review template, use your repo's PR template or include:
- Summary
- Evidence plan / verification commands
- Risks / follow-ups
