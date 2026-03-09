---
name: codex-persistent-terminal
description: Run and recover long-lived Codex CLI conversations in Linux tmux sessions with workspace-scoped metadata and SESSION_ID tracking. Use when Codex needs to keep watching one interactive session, continue the same conversation after detach/reattach, recover after terminal loss with exact `SESSION_ID` resume, or monitor tmux-backed Codex output without relying on VS Code integrated terminals.
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

- Default to creating a new tmux session. Do not take over the user's current VS Code integrated terminal session unless they explicitly point to it.
- Start new conversations with `start_session.sh`. It launches `codex` inside tmux with the old-tmux-safe form `tmux new-session -d -s "$NAME" 'cd "$WORKSPACE" && codex'`.
- Monitor with `capture_session.sh` when you only need output or state. Prefer `capture-pane` for read-only monitoring.
- Continue the conversation by attaching with `attach_session.sh`. This script exports `TERM=xterm-256color` before attaching.
- Recover a lost terminal with `resume_session.sh`. Prefer exact `SESSION_ID`; use `--last` only when the exact id is unavailable.

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
- If tmux is gone but metadata still contains `current_session_id`, resume with that exact id.
- If metadata is present but `SESSION_ID` is still missing, use `find_session_id.py` against `~/.codex/history.jsonl` and `~/.codex/sessions/...`.
- When `capture_session.sh` reports `tmux_missing`, treat that as a recovery decision point:
  - If `current_session_id` is known, use `resume_session.sh --session-id`.
  - If only the most recent session is known, use `resume_session.sh --last`.

## When To Use

- The user asks to keep watching one Codex session for a long time.
- The user asks to continue the same Codex conversation after detach or terminal close.
- The user asks to recover the same conversation in a fresh terminal.
- The user asks to monitor or inspect a Codex task that is running inside tmux.
