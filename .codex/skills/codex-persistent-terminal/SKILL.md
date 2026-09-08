---
name: codex-persistent-terminal
description: "Manage a long-lived Codex CLI conversation in Linux tmux when the user explicitly asks to create, attach, recover, or inspect a persistent session. Inspection is one-time and read-only; continued polling belongs to a monitoring mechanism. Recovery prefers an exact SESSION_ID."
---

# Codex Persistent Terminal

## Quick Start

Start a new tmux-backed Codex session:

```bash
~/.codex/skills/codex-persistent-terminal/scripts/start_session.sh /path/to/workspace my-codex
```

Read recent output and inferred state:

```bash
~/.codex/skills/codex-persistent-terminal/scripts/capture_session.sh /path/to/workspace my-codex --lines 80
```

Attach for stable continued conversation:

```bash
~/.codex/skills/codex-persistent-terminal/scripts/attach_session.sh /path/to/workspace my-codex
```

Recover after the old terminal or tmux session is gone:

```bash
~/.codex/skills/codex-persistent-terminal/scripts/resume_session.sh /path/to/workspace my-codex --session-id <SESSION_ID>
```

Or fall back to the most recent matching session:

```bash
~/.codex/skills/codex-persistent-terminal/scripts/resume_session.sh /path/to/workspace my-codex --last
```

## Workflow

- Match the operation the user requested. Create a new tmux session only for an
  explicit start request; do not turn monitoring, inspection, or attachment into
  a new Codex process. Do not take over the user's current VS Code integrated
  terminal unless they explicitly point to it.
- Start new conversations with `start_session.sh`. It launches `codex` inside tmux with the old-tmux-safe form `tmux new-session -d -s "$NAME" 'cd "$WORKSPACE" && codex'`.
- Inspect with `capture_session.sh` when you only need current output or state. This is
  read-only; if the named session is missing, report that state instead of
  creating or resuming one implicitly.
- Continue the conversation by attaching with `attach_session.sh`. This script exports `TERM=xterm-256color` before attaching.
- Recover a lost terminal with `resume_session.sh`. Prefer exact `SESSION_ID`.
  Use `--last` only after checking that the candidate workspace and conversation
  are unambiguous; otherwise list candidates and stop.

## Rules

- Keep runtime metadata in `WORKSPACE/.codex/tmp/persistent-terminal/`.
- Each session record must keep at least:
  - `tmux_session_name`
  - `workspace`
  - `created_at`
  - `recovered_from_session_id`
  - `current_session_id`
  - `last_known_state`
- Prefer exact `SESSION_ID` recovery over `codex resume --last`.
- Do not recommend `codex resume --last "PROMPT"` as the default path. Resume first, wait until the session is actually back, then send the next message.
- Treat `tmux send-keys ... Enter` as an auxiliary path only. It is useful for injecting text or automation experiments, but not the most reliable way to keep a conversation going.
- For stable continued chatting, attach to tmux and send the message from the attached terminal.

## Failure Handling

- If attach fails with `open terminal failed: terminal does not support clear`, set `TERM=xterm-256color` and retry. `attach_session.sh` already does this automatically.
- If the tmux session is still alive, do not start a recovery tmux session. Attach to the existing one instead.
- For an authorized recovery, if tmux is gone but metadata contains `current_session_id`, resume with that exact id.
- For recovery, if metadata is present but `SESSION_ID` is missing, use `find_session_id.py` against `~/.codex/history.jsonl` and `~/.codex/sessions/...`.
- When `capture_session.sh` reports `tmux_missing`, report that state for an inspection request. For an authorized recovery or continuation request, resume the known exact session ID; use `--last` only after establishing an unambiguous matching session.

## When To Use

- The user asks to continue the same Codex conversation after detach or terminal close.
- The user asks to recover the same conversation in a fresh terminal.
- The user asks to inspect a Codex task that is running inside tmux. Use a watchdog or automation for continued polling.
