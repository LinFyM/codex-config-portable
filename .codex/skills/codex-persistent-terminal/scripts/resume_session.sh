#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

usage() {
  cat <<'EOF'
Usage: resume_session.sh WORKSPACE SESSION_NAME [--session-id UUID | --last] [--poll-retries N] [--poll-interval SECONDS]

Recover a Codex conversation into a fresh tmux session. Prefer --session-id when available.
EOF
}

session_id=""
use_last=0
poll_retries=10
poll_interval=1
positionals=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --session-id)
      [[ $# -ge 2 ]] || pt_fail "--session-id requires a value"
      session_id="$2"
      shift 2
      ;;
    --last)
      use_last=1
      shift
      ;;
    --poll-retries)
      [[ $# -ge 2 ]] || pt_fail "--poll-retries requires a value"
      poll_retries="$2"
      shift 2
      ;;
    --poll-interval)
      [[ $# -ge 2 ]] || pt_fail "--poll-interval requires a value"
      poll_interval="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      positionals+=("$1")
      shift
      ;;
  esac
done

[[ ${#positionals[@]} -eq 2 ]] || {
  usage >&2
  exit 1
}

if [[ -n "$session_id" && "$use_last" -eq 1 ]]; then
  pt_fail "Use either --session-id or --last, not both"
fi

pt_require_cmd tmux
pt_require_cmd codex
pt_require_cmd python3

WORKSPACE="$(pt_realpath "${positionals[0]}")"
NAME="${positionals[1]}"
pt_validate_session_name "$NAME"
[[ -d "$WORKSPACE" ]] || pt_fail "Workspace does not exist: $WORKSPACE"

META_FILE="$(pt_meta_path "$WORKSPACE" "$NAME")"
pt_ensure_meta_dir "$WORKSPACE"

if pt_tmux_has_session "$NAME"; then
  pt_fail "tmux session already exists: $NAME. Use attach_session.sh instead of resume_session.sh."
fi

created_at="$(pt_read_meta_field "$META_FILE" created_at 2>/dev/null || true)"
[[ -n "$created_at" ]] || created_at="$(pt_now_iso)"

if [[ -z "$session_id" && "$use_last" -eq 0 ]]; then
  session_id="$(pt_read_meta_field "$META_FILE" current_session_id 2>/dev/null || true)"
fi

resume_display=""
if [[ -n "$session_id" ]]; then
  resume_display="$session_id"
elif [[ "$use_last" -eq 1 ]]; then
  resume_display="$(python3 "$SCRIPT_DIR/find_session_id.py" --workspace "$WORKSPACE" --latest --format id 2>/dev/null || true)"
else
  pt_fail "No SESSION_ID available. Provide --session-id <ID> or use --last."
fi

recovered_from="${resume_display:-__NULL__}"
current_id="${resume_display:-__NULL__}"
pt_write_meta "$META_FILE" \
  "tmux_session_name=$NAME" \
  "workspace=$WORKSPACE" \
  "created_at=$created_at" \
  "recovered_from_session_id=$recovered_from" \
  "current_session_id=$current_id" \
  "last_known_state=resuming"

workspace_quoted="$(pt_shell_quote "$WORKSPACE")"
if [[ -n "$session_id" ]]; then
  session_id_quoted="$(pt_shell_quote "$session_id")"
  tmux new-session -d -s "$NAME" "cd $workspace_quoted && exec codex resume $session_id_quoted"
else
  tmux new-session -d -s "$NAME" "cd $workspace_quoted && exec codex resume --last"
fi

sleep 1
pt_tmux_has_session "$NAME" || pt_fail "tmux session exited immediately during resume: $NAME"

if [[ "$current_id" == "__NULL__" ]]; then
  current_id=""
  for ((i = 0; i < poll_retries; i++)); do
    if current_id="$(python3 "$SCRIPT_DIR/find_session_id.py" --workspace "$WORKSPACE" --latest --format id 2>/dev/null)"; then
      break
    fi
    sleep "$poll_interval"
  done
  if [[ -n "$current_id" ]]; then
    pt_write_meta "$META_FILE" \
      "recovered_from_session_id=$current_id" \
      "current_session_id=$current_id"
  fi
fi

pt_write_meta "$META_FILE" "last_known_state=waiting_for_input"
pt_print_meta "$META_FILE"
