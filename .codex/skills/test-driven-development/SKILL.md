---
name: test-driven-development
description: Use when the user explicitly asks in natural language for TDD, test-driven development, red-green-refactor, or a failing test before implementation, and the task concerns stable production behavior or a reproducible bug with a meaningful automated oracle. Do not infer TDD from general requests to implement, test, validate, improve coverage, fix, or complete a feature. Skip exploratory research, experiment iteration, scripts, configuration, operations, data work, and environment repair.
---

# Test-Driven Development

This is an opt-in implementation style, not a universal quality gate. An
explicit natural-language request is sufficient; the user does not need special
skill syntax. Do not infer TDD merely because production code changes, tests are
requested, coverage should improve, or an automated test could be written.

## Core Loop

1. **Red:** Write the smallest test that expresses the required behavior or reproduces the bug. Run it and confirm it fails for the expected reason.
2. **Green:** Make the smallest production change that passes the test.
3. **Refactor:** Improve clarity without changing behavior, then rerun relevant tests.

## When It Adds Value

- The user explicitly asks for TDD or test-first work, or a narrower repository
  contract explicitly requires it.
- Shared production logic, APIs, parsers, state transitions, algorithms, and regressions.
- Bugs with a stable reproduction that could return later.
- Behavior changes where examples and edge cases are part of the contract.

## When To Use Another Verification Style

- Shell or SSH configuration: validate parsed config and test the real connection.
- Service or environment repair: use health checks and an end-to-end smoke test.
- Data migration: use relevant counts, manifests, and dry runs; add checksums only when the integrity contract requires them.
- Documentation-only changes: inspect rendered or referenced output.
- Exploratory research code: validate the mechanism or experiment directly.
  Add durable invariant or regression tests later only if the behavior becomes
  retained and stable; do not reconstruct test-first history after the fact.

## Test Quality

- Prefer observable behavior over implementation details.
- Use the repository's existing framework and conventions.
- Keep fixtures small and deterministic.
- Avoid mocks when a cheap real boundary is available; mock only the external dependency that makes the test unstable or expensive.
- For bug fixes, make sure the new test fails on the old behavior and passes after the fix.

## Completion

Run the focused test first. Run a broader suite only when shared behavior, blast
radius, or a repository integration gate warrants it. Report tests not run and
residual risk. Do not add contrived tests simply to claim TDD compliance.
