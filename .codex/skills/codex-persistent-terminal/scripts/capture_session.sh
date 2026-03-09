#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

usage() {
  cat <<'EOF'
Usage: capture_session.sh WORKSPACE SESSION_NAME [--lines N] [--scrollback N]

Capture recent tmux pane output, infer a coarse session state, and update workspace metadata.
EOF
}

lines=80
scrollback=2000
positionals=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --lines)
      [[ $# -ge 2 ]] || pt_fail "--lines requires a value"
      lines="$2"
      shift 2
      ;;
    --scrollback)
      [[ $# -ge 2 ]] || pt_fail "--scrollback requires a value"
      scrollback="$2"
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
pt_require_cmd python3

WORKSPACE="$(pt_realpath "${positionals[0]}")"
NAME="${positionals[1]}"
pt_validate_session_name "$NAME"
META_FILE="$(pt_meta_path "$WORKSPACE" "$NAME")"
[[ -f "$META_FILE" ]] || pt_fail "Metadata not found: $META_FILE"

tmux_session_name="$(pt_read_meta_field "$META_FILE" tmux_session_name 2>/dev/null || true)"
[[ -n "$tmux_session_name" ]] || tmux_session_name="$NAME"
current_session_id="$(pt_read_meta_field "$META_FILE" current_session_id 2>/dev/null || true)"
created_at="$(pt_read_meta_field "$META_FILE" created_at 2>/dev/null || true)"

if ! pt_tmux_has_session "$tmux_session_name"; then
  pt_write_meta "$META_FILE" "last_known_state=tmux_missing"
  python3 - "$META_FILE" "$tmux_session_name" "$current_session_id" <<'PY'
import json
import sys
from pathlib import Path

meta = json.loads(Path(sys.argv[1]).read_text())
payload = {
    "ok": False,
    "error": "tmux session not found",
    "state": "tmux_missing",
    "tmux_session_name": sys.argv[2],
    "current_session_id": sys.argv[3] or meta.get("current_session_id"),
    "metadata": meta,
}
print(json.dumps(payload, indent=2, ensure_ascii=False))
PY
  exit 3
fi

captured="$(tmux capture-pane -p -S "-$scrollback" -t "$tmux_session_name")"

if [[ -z "$current_session_id" && -n "$created_at" ]]; then
  if current_session_id="$(python3 "$SCRIPT_DIR/find_session_id.py" --workspace "$WORKSPACE" --created-after "$created_at" --format id 2>/dev/null)"; then
    pt_write_meta "$META_FILE" "current_session_id=$current_session_id"
  else
    current_session_id=""
  fi
fi

state="$(
  python3 - "$captured" <<'PY'
import re
import sys

text = sys.argv[1]
lines = [line.rstrip() for line in text.splitlines()]

def is_status_line(line: str) -> bool:
    stripped = line.strip()
    return "·" in stripped and "left" in stripped and stripped.startswith("gpt-")

def is_splash(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return True
    prefixes = (
        "╭", "│", "╰", "model:", "directory:", "Tip:", "⚠", "voice_transcription.",
        "unpredictably.", "› Use /skills to list available skills",
    )
    return stripped.startswith(prefixes)

status_index = None
for index in range(len(lines) - 1, -1, -1):
    if is_status_line(lines[index]):
        status_index = index
        break

content_lines = lines if status_index is None else lines[:status_index]
content_text = "\n".join(content_lines)
lower = content_text.lower()

if "working" in lower or "esc to interrupt" in lower or "ctrl+c to interrupt" in lower:
    print("working")
    raise SystemExit

meaningful = [line for line in content_lines if not is_splash(line)]

prompt_indices = [i for i, line in enumerate(content_lines) if line.strip().startswith("› ")]
if prompt_indices:
    last_prompt_index = prompt_indices[-1]
    trailing = [line for line in content_lines[last_prompt_index + 1 :] if line.strip()]
    trailing_meaningful = [line for line in trailing if not is_splash(line)]
    if trailing_meaningful:
        print("final_answer")
        raise SystemExit
    if len(prompt_indices) >= 2:
        previous_prompt_index = prompt_indices[-2]
        between_prompts = [
            line for line in content_lines[previous_prompt_index + 1 : last_prompt_index] if line.strip()
        ]
        between_meaningful = [line for line in between_prompts if not is_splash(line)]
        if between_meaningful:
            print("final_answer")
            raise SystemExit
    print("waiting_for_input")
    raise SystemExit

if meaningful:
    print("final_answer")
else:
    print("unknown")
PY
)"

pt_write_meta "$META_FILE" "last_known_state=$state"
trimmed="$(printf '%s\n' "$captured" | tail -n "$lines")"

python3 - "$META_FILE" "$state" "$tmux_session_name" "$current_session_id" "$lines" "$trimmed" <<'PY'
import json
import sys
from pathlib import Path

meta = json.loads(Path(sys.argv[1]).read_text())
payload = {
    "ok": True,
    "state": sys.argv[2],
    "tmux_session_name": sys.argv[3],
    "current_session_id": sys.argv[4] or meta.get("current_session_id"),
    "lines": int(sys.argv[5]),
    "excerpt": sys.argv[6],
    "metadata": meta,
}
print(json.dumps(payload, indent=2, ensure_ascii=False))
PY
