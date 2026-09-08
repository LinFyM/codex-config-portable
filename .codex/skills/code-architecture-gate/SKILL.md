---
name: code-architecture-gate
description: Use for retained source changes with structural risk, including large or complex targets, substantial growth, new modules or entrypoints, parallel or versioned paths, or retirement after a design decision. Apply size, ownership, reuse, and lifecycle guardrails. Skip docs/config/operations, generated or throwaway code, and narrow changes without structural effect.
---

# Code Architecture Gate

Keep the active codebase small enough to understand and change. Git history,
configs, results, and artifacts preserve evidence; superseded executable paths
do not stay active merely to preserve history.

This skill is a structural guardrail, not an implementation methodology, TDD
requirement, test-framework requirement, or recurring review ceremony. Load it
once for a coherent structural change or phase and reuse the same baseline;
reload or rescan only when scope or retained-code shape changes materially.

## Trigger

Use this skill when any of these applies:

- adding or materially expanding a retained module, runner, entrypoint, mode,
  strategy, or test surface;
- changing ownership boundaries or deciding whether to reuse, split, or create;
- materially changing the structure or responsibilities of a file above 600 lines or a function above 60 lines; size alone does not trigger a scan for a narrow fix;
- adding a parallel, numbered, legacy, recovery, fallback, or replacement path;
- a task adds more than 500 active source lines or more than three active source files;
- a product, architecture, or experiment decision makes an old path obsolete.

Do not invoke it for routine config/docs/ops changes or narrow fixes with no
structural effect. Provisional throwaway probes under a temporary root are not
retained source, but promoting them into active entrypoints or accumulating
multiple experiment versions is structural work. Use `workspace-cleanup` for
an explicit whole-repository retirement pass; let that skill own the workflow
and apply this skill's lifecycle principles without loading both.

## Default Scale Guardrails

Repository rules may override these numbers. Treat them as design signals, not
an excuse to split cohesive code into fragments.

| Surface | Target | Review signal | Escalation boundary |
| --- | ---: | ---: | ---: |
| Retained source file | <=400 lines | >600 | >800 |
| Function or method | <=40 lines | >60 | >120 |
| Cyclomatic complexity | <=10 | >15 | New/growing >25 needs simplification or a cohesive exception |
| Direct peer source files in one directory | 5-20 | >25 | Adding another peer above 40 needs reorganization or a cohesive exception |

Escalation boundaries are strong default upper bounds, not mechanical split
commands or automatic rejection. A cohesive generated/declarative surface,
protocol table, parser, state machine, or other well-owned unit may exceed one
when a narrower repository rule or task scope supports it, splitting would
reduce clarity, and the rationale is recorded in normal delivery notes. Files
above 1000 lines are wiring, generated, or declarative by default; substantive
growth needs a cohesive exception and a credible ownership or retirement plan.

Agent-owned architecture self-review is required at more than 500 added active
lines or more than three new active source files; it is not a human approval
gate. Net growth above 1000 active lines or more than five new active source
files needs an explicit architecture rationale, ownership map, and retirement
decision before completion, but is not rejected when the task genuinely
requires that surface.
Generated/vendor code is excluded.

## Legacy Ratchet

- Existing violations do not force an unrelated cleanup.
- A file above 800 lines should not grow in normal work. Material work should
  extract a cohesive responsibility and leave the file smaller or no larger.
  If a narrow change must grow it, keep the increment minimal and explain why
  extraction would currently be less safe or less coherent.
- A function above 120 lines or complexity above 25 follows the same ratchet:
  simplify when practical; otherwise keep necessary growth narrow and record
  the cohesive exception. Crossing the review signals still needs scrutiny.
- Narrow fixes may touch a legacy violation; keep the patch local and report
  the pre-existing structure only when it materially limits the change or validation.
- Moving code into many tiny files, an in-tree `archive/`, or differently named
  duplicate helpers does not count as improvement.

## Active-Code Lifecycle

1. Keep one canonical active implementation for one behavior.
2. Put legitimate variability in data, configuration, or a bounded strategy
   interface before copying an orchestrator or runner.
3. Preserve historical evidence with commits/tags, frozen configs, summaries,
   and immutable artifacts. Do not require every historical runner to execute
   on the latest tree.
4. A temporary dual path needs an owner, reason, removal trigger, and the
   regression checks required before deletion.
5. When replacing a selected or rejected path, retire its obsolete active
   entrypoints, flags, branches, adapters, and experiment-only tests as part
   of that change. Keep the decision coherent without making unrelated cleanup
   block an authorized experiment; a temporarily retained path needs a reason,
   owner, and removal trigger and must not remain an accidental default.
6. Keep durable invariant tests. Retire tests that only exercise a retired
   implementation after its evidence is preserved.

## Workflow

1. Inspect `git status`, the target files, neighboring modules, callers, tests,
   and existing implementations.
2. When the change hits a size, complexity, ownership, directory, or parallel-
   path risk, run one baseline scan:

   ```bash
   python3 ~/.codex/skills/code-architecture-gate/scripts/architecture_guard.py
   ```

   Use `--base <ref>` when reviewing a branch or multi-commit change. For a
   smaller structural change below those signals, an ordinary diff and local
   size check is enough. The script may label escalation signals as `hard`;
   that means resolve them or record a permitted exception, not seek human
   approval.
3. Make the ownership decision in the work or normal notes: what existing path
   owns the behavior, what is reused, what becomes obsolete, and why any new
   retained file is necessary. Do not create a separate artifact just for this.
4. Use a proportional change budget. Prefer replacement and deletion over a
   new parallel path, and do not create a future-general framework without a
   current second use case.
5. Implement by cohesive responsibility. Keep entrypoints thin and interfaces
   explicit; avoid mechanical file splitting.
6. Run the guard again only when the final retained change materially differs
   from the baseline or crosses a review signal. Use the smallest faithful
   verification for the changed behavior: an existing test, syntax or smoke
   check, direct experiment, or repository gate as appropriate. Do not create
   tests or a testing framework merely to satisfy this architecture guard.
7. Report detailed source growth, new files, retired paths, and unresolved
   signals when they are material; otherwise a normal scoped diff summary is
   sufficient.

## Completion Gate

Do not claim completion when:

- the guard reports a newly introduced or growing escalation violation without
  either resolving it or recording a cohesive exception allowed by the narrower
  repository contract or task scope;
- a superseded active path remains without a documented removal trigger;
- numbered or parallel implementations were added without either a bounded
  migration contract under the lifecycle rules above or a rationale that
  configuration or a strategy boundary cannot express the difference;
- a claimed cleanup only moved code or split files and did not reduce active
  duplication, responsibility, or net source size;
- the next replacement path was added while a superseded path still acts as
  an accidental default or lacks the required transition/removal contract.

The guard is evidence, not a substitute for judgment. Resolve escalation
violations or record a cohesive exception; for review signals, either improve
the design or record the relevant rationale and retirement action in normal
delivery notes.
