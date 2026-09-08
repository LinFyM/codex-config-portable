---
name: systematic-debugging
description: Use for a reproducible engineering failure that violates a known contract, spans plausible layers, recurs unexpectedly, or survived a reasonable first fix. Do not treat weak metrics, an expected scientific non-pass, a rejected hypothesis, model variance, or an ordinary negative experiment as a software bug unless evidence points to an implementation, data, or runtime defect.
---

# Systematic Debugging

Use evidence to locate the failing layer before making consequential changes. This is a flexible debugging aid, not a mandatory ceremony.

## Classify Before Debugging

First distinguish:

- **Engineering failure:** observed behavior violates a specified interface,
  invariant, data contract, runtime expectation, or reproducibility claim.
- **Scientific non-pass:** the implementation ran under its declared contract,
  but the hypothesis, metric, gate, or comparison did not succeed.
- **Uncertain:** available evidence cannot yet distinguish the two.

Use the workflow below for engineering failures and focused probes for uncertain
cases. For a scientific non-pass, preserve the result and follow the project's
decision rule; do not debug the experiment into a preferred conclusion, add a
new implementation path reflexively, or construct a test framework merely to
keep the hypothesis alive.

## Workflow

1. State the observed behavior, expected behavior, and the smallest reliable reproduction.
2. Read the complete error and inspect recent relevant changes.
3. Split multi-component systems into layers such as transport, authentication, runtime, application, data, and workload.
4. Gather the smallest evidence that distinguishes those layers. Prefer read-only checks first.
5. Form one concrete hypothesis and test it with the smallest reversible change or probe.
6. Fix the identified cause at the narrowest appropriate boundary.
7. Re-run the original reproduction and a proportional regression check.

## Judgment

- A failing automated test is useful when it faithfully captures production behavior, but it is not mandatory for config, operations, environment repair, or one-off diagnostics.
- Existing experiment gates, direct reproductions, data checks, and runtime
  probes may be the right evidence. Do not introduce automated testing as a
  separate deliverable unless it will protect a stable retained contract.
- Do not add broad instrumentation when an existing log, status command, or focused probe answers the question.
- Do not bundle unrelated fixes. Preserve user changes and shared-system safety boundaries.
- If evidence is inconclusive, say what is known, what remains uncertain, and which next observation would separate the remaining hypotheses.
- After repeated failed fixes, revisit assumptions and evidence before expanding scope; ask only when expansion introduces a material choice or external risk.

## Completion

Report the cause as verified only when evidence supports it. Otherwise label it as the leading inference and state the residual uncertainty.
