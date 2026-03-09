#!/usr/bin/env bash
set -euo pipefail

pt_fail() {
  echo "[ERROR] $*" >&2
  exit 1
}

pt_require_cmd() {
  command -v "$1" >/dev/null 2>&1 || pt_fail "Required command not found: $1"
}

pt_now_iso() {
  date -u +"%Y-%m-%dT%H:%M:%SZ"
}

pt_realpath() {
  python3 - "$1" <<'PY'
from pathlib import Path
import sys

print(str(Path(sys.argv[1]).expanduser().resolve()))
PY
}

pt_shell_quote() {
  python3 - "$1" <<'PY'
import shlex
import sys

print(shlex.quote(sys.argv[1]))
PY
}

pt_meta_dir() {
  printf '%s/.codex/tmp/persistent-terminal' "$1"
}

pt_meta_path() {
  printf '%s/%s.json' "$(pt_meta_dir "$1")" "$2"
}

pt_ensure_meta_dir() {
  mkdir -p "$(pt_meta_dir "$1")"
}

pt_validate_session_name() {
  case "${1:-}" in
    ""|*[!A-Za-z0-9._:-]*)
      pt_fail "Session name must use only letters, digits, dot, underscore, colon, or hyphen: '$1'"
      ;;
  esac
}

pt_tmux_has_session() {
  tmux has-session -t "$1" 2>/dev/null
}

pt_write_meta() {
  local meta_file="$1"
  shift
  python3 - "$meta_file" "$@" <<'PY'
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

meta_path = Path(sys.argv[1])
meta = {}
if meta_path.exists():
    try:
        meta = json.loads(meta_path.read_text())
    except json.JSONDecodeError:
        meta = {}

for item in sys.argv[2:]:
    key, value = item.split("=", 1)
    meta[key] = None if value == "__NULL__" else value

meta["updated_at"] = (
    datetime.now(timezone.utc)
    .replace(microsecond=0)
    .isoformat()
    .replace("+00:00", "Z")
)
meta_path.parent.mkdir(parents=True, exist_ok=True)
meta_path.write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n")
PY
}

pt_read_meta_field() {
  local meta_file="$1"
  local key="$2"
  python3 - "$meta_file" "$key" <<'PY'
import json
import sys
from pathlib import Path

meta_path = Path(sys.argv[1])
key = sys.argv[2]
if not meta_path.exists():
    sys.exit(1)

data = json.loads(meta_path.read_text())
value = data.get(key)
if value is None:
    sys.exit(1)

if isinstance(value, (dict, list)):
    print(json.dumps(value))
else:
    print(value)
PY
}

pt_print_meta() {
  python3 - "$1" <<'PY'
from pathlib import Path
import sys

print(Path(sys.argv[1]).read_text(), end="")
PY
}
