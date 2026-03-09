#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

usage() {
  cat <<'EOF'
Usage: start_session.sh WORKSPACE SESSION_NAME [--poll-retries N] [--poll-interval SECONDS]

Start a new long-lived tmux-backed Codex session and write workspace-scoped metadata.
EOF
}

poll_retries=15
poll_interval=1
positionals=()

while [[ $# -gt 0 ]]; do
  case "$1" in
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

pt_require_cmd tmux
pt_require_cmd codex
pt_require_cmd python3

WORKSPACE="$(pt_realpath "${positionals[0]}")"
NAME="${positionals[1]}"
pt_validate_session_name "$NAME"
[[ -d "$WORKSPACE" ]] || pt_fail "Workspace does not exist: $WORKSPACE"

META_FILE="$(pt_meta_path "$WORKSPACE" "$NAME")"
pt_ensure_meta_dir "$WORKSPACE"

pt_tmux_has_session "$NAME" && pt_fail "tmux session already exists: $NAME. Use attach_session.sh instead."
[[ ! -e "$META_FILE" ]] || pt_fail "Metadata already exists: $META_FILE. Use a new name or resume_session.sh."

created_at="$(pt_now_iso)"
pt_write_meta "$META_FILE" \
  "tmux_session_name=$NAME" \
  "workspace=$WORKSPACE" \
  "created_at=$created_at" \
  "recovered_from_session_id=__NULL__" \
  "current_session_id=__NULL__" \
  "last_known_state=starting"

workspace_quoted="$(pt_shell_quote "$WORKSPACE")"
tmux new-session -d -s "$NAME" "cd $workspace_quoted && exec codex"
sleep 1
pt_tmux_has_session "$NAME" || pt_fail "tmux session exited immediately after launch: $NAME"

session_id=""
for ((i = 0; i < poll_retries; i++)); do
  if session_id="$(python3 "$SCRIPT_DIR/find_session_id.py" --workspace "$WORKSPACE" --created-after "$created_at" --format id 2>/dev/null)"; then
    break
  fi
  sleep "$poll_interval"
done

if [[ -n "$session_id" ]]; then
  pt_write_meta "$META_FILE" \
    "current_session_id=$session_id" \
    "last_known_state=waiting_for_input"
else
  pt_write_meta "$META_FILE" "last_known_state=waiting_for_input"
fi

pt_print_meta "$META_FILE"
