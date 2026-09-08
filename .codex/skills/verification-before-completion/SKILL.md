---
name: verification-before-completion
description: Use before claiming work is complete, fixed, passing, or ready. Run fresh checks proportional to the claim and report any unverified scope.
---

# Verification Before Completion

Match evidence to the claim instead of applying one universal test ritual.

Fresh evidence does not imply a new automated test. For research, data,
operations, and infrastructure work, the faithful check may be a direct
experiment, contract check, parsed configuration, live probe, counts,
or output inspection. Use checksums only when an actual integrity or provenance
contract requires them. Do not build test infrastructure solely to satisfy this
skill.

For prose-only documentation or skill changes, inspecting the scoped diff is
sufficient. Parse config or metadata only when their syntax or semantics changed;
inspect links or rendering only when affected. Do not add hashes, integrity
manifests, full-tree scans, or runtime tests for a text edit.

## Check

1. Identify the observable result that would support the claim.
2. Run the smallest faithful fresh check and inspect its exit status and relevant output.
3. Reproduce the original symptom for bug fixes when practical.
4. Add broader tests only when shared behavior or blast radius warrants them.
5. State checks that could not run, partial coverage, and remaining risk.

Once the relevant checks pass, deliver the result. Repeat or broaden them only
for new changes, failures, unresolved concerns, or required repository gates.

## Examples

- Config or environment repair: parse or load the config, then exercise the affected path.
- Narrow code change: targeted test plus relevant lint or type check when available.
- Shared behavior: focused regression test followed by the repository's broader gate.
- Long-running work: verify durable process state, logs, outputs, and completion status rather than process existence alone.

Do not infer success from a code diff, an agent report, an old test run, or confidence. Scope the final statement to the evidence actually observed.
