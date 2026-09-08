---
name: formal-training-launch
description: Use before an expensive canonical ML run whose outputs will be retained as scientific, comparison, or production evidence, or before resuming such a run under a materially changed contract. Skip exploratory experiments, smoke checks, disposable profiling, and ordinary evaluation, indexing, or cache work unless the project explicitly designates their outputs as canonical.
---

# Formal Training Launch

Create one concise, auditable launch record before consuming significant GPU
time or storage for a canonical run. This is a launch-contract guardrail, not a
planning, debugging, long-run persistence, or approval workflow. Do not turn
exploratory work into formal-run paperwork or load overlapping workflow skills
merely because the run uses GPUs.

Reuse the existing record for the same run identity or unchanged resume. Update
only fields whose command, inputs, outputs, devices, scale, or scientific
contract changed materially; do not recreate the contract on every poll,
checkpoint, retry, or resume.

## Preflight

Record in the active task plan or run summary:

- canonical workspace, branch, commit, and relevant local changes;
- exact command, environment, model and data provenance;
- run scale in meaningful units such as rows, tokens, epochs, or questions;
- output and temporary roots plus a storage estimate;
- GPU allocation and execution mode: DDP, sharded, CPU-parallel, or intentionally single-process;
- upstream artifact dependencies and required validation;
- metric, evaluation split, and comparison contract;
- resume policy and handling of invalid or superseded outputs.

Use existing project documentation rather than creating another dashboard or
wrapper. Do not ask again merely because the run is formal or expensive. Ask
only when an unresolved choice or a change from the authorized contract
materially alters cost, scientific validity, shared-resource use, or destructive
overwrite behavior.

## Launch And Resume

- Run the host's focused live GPU and storage checks immediately before launch.
  These are data checks, not additional workflow ceremonies.
- Confirm the recorded command and paths match what is actually executed.
- On an unchanged resume, validate only drift-prone live state plus checkpoint
  integrity, required provenance or alignment, and output destination. Do not
  repeat the full launch record.
- Reuse only artifacts compatible with the current contract; label reused results separately from newly run results.
- Parallelize only when it preserves the method and evaluation contract. State the reason for an expensive single-process phase when relevant.

## Monitoring

Monitor both liveness and contract drift: wrong workspace or commit, unintended device use, stale or mismatched checkpoints, data/eval mismatch, non-advancing logs, non-finite metrics, storage exhaustion, and outputs written outside the recorded root.

The handoff should reference the existing run record and add only current
status, validation evidence, changed fields, and remaining risk.
