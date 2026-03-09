#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

usage() {
  cat <<'EOF'
Usage: attach_session.sh WORKSPACE SESSION_NAME

Attach to an existing tmux-backed Codex session. This script exports TERM=xterm-256color first.
EOF
}

[[ $# -eq 2 ]] || {
  usage >&2
  exit 1
}

pt_require_cmd tmux
pt_require_cmd python3

WORKSPACE="$(pt_realpath "$1")"
NAME="$2"
pt_validate_session_name "$NAME"
META_FILE="$(pt_meta_path "$WORKSPACE" "$NAME")"
[[ -f "$META_FILE" ]] || pt_fail "Metadata not found: $META_FILE"

tmux_session_name="$(pt_read_meta_field "$META_FILE" tmux_session_name 2>/dev/null || true)"
[[ -n "$tmux_session_name" ]] || tmux_session_name="$NAME"

if ! pt_tmux_has_session "$tmux_session_name"; then
  current_session_id="$(pt_read_meta_field "$META_FILE" current_session_id 2>/dev/null || true)"
  if [[ -n "$current_session_id" ]]; then
    pt_fail "tmux session '$tmux_session_name' is not running. Recover with: $SCRIPT_DIR/resume_session.sh '$WORKSPACE' '$NAME' --session-id $current_session_id"
  fi
  pt_fail "tmux session '$tmux_session_name' is not running and metadata has no current_session_id."
fi

export TERM=xterm-256color
if ! tmux attach-session -t "$tmux_session_name"; then
  pt_fail "tmux attach failed for '$tmux_session_name'. Ensure TERM=xterm-256color and retry."
fi
