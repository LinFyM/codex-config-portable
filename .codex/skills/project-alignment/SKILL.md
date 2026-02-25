---
name: project-alignment
description: >-
  Clarify and align project-level goals before implementation. Use when starting
  complex work, resuming after context degradation, switching components, or
  whenever macro intent is ambiguous and detailed implementation may drift from
  the project's north-star objective.
---

# Project Alignment

## Quick Start

1. Read macro context first:
   - `WORKSPACE/.codex/MEMORY.md` (north-star facts and durable constraints)
   - `WORKSPACE/.codex/STATE.md` if present
   - latest `WORKSPACE/.codex/memory/YYYY-MM-DD.md` logs
   - relevant architecture/design docs for the current task
2. Write a short alignment hypothesis:
   - one-sentence north-star goal
   - how the current task should serve that goal
   - likely risks of drifting from the goal
3. Ask clarification questions in rounds until the macro intent is unambiguous.
4. Output an alignment contract before implementation starts.

## Clarification Protocol (No Total Question Cap)

- Keep asking questions until all material macro ambiguities are resolved.
- Do not impose a hard cap on total rounds.
- Keep each round focused and concise (prefer 1-3 high-leverage questions per round).
- Prioritize questions that can change architecture, roadmap direction, or success criteria.
- If answers introduce new ambiguity, ask another round immediately.
- If the user explicitly asks to proceed with assumptions, restate assumptions clearly and continue.

## Required Question Dimensions

Cover these dimensions before coding:

1. North-star objective:
   - what final system capability matters most
2. Scope boundaries:
   - in-scope vs out-of-scope for this task
3. Non-negotiables:
   - constraints that must not be broken (architecture, API, training/eval invariants, safety rules)
4. Success criteria:
   - what evidence/metrics indicate correct macro alignment
5. Priority tradeoffs:
   - speed vs quality vs complexity vs backward compatibility
6. Failure boundaries:
   - what outcomes are unacceptable even if local metrics improve

## Alignment Contract Output (Before Implementation)

Produce a concise contract with:

- `North Star`: one sentence
- `Task Role`: how this task contributes to the north star
- `In Scope` / `Out of Scope`
- `Non-Negotiables`
- `Success Signals`
- `Assumptions` (if any)
- `Abort/Redo Triggers`: conditions that require rollback or redesign

Start implementation only after this contract is confirmed (explicitly by user, or implicitly when user says continue).

## During Execution

- Re-check alignment when the task pivots (new requirements, failing approach, major refactor).
- If macro alignment drifts, pause implementation and run another clarification round.
- Keep updates brief: report only meaningful alignment changes, not every micro-adjustment.

## Memory Update Rule

- Promote stable macro decisions to `WORKSPACE/.codex/MEMORY.md`.
- Put session-level progress and temporary context in daily logs.
- Avoid duplicating long progress notes in `AGENTS.md`.
