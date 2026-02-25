#!/usr/bin/env bash
set -euo pipefail

# Convert one or more .drawio files to .drawio.png previews.
# - Does NOT run `git add` (staging is a user decision).
# - Uses draw.io Desktop CLI (export mode).
#
# Notes for this server environment:
# - Some shells/IDEs set `ELECTRON_RUN_AS_NODE=1`, which makes draw.io behave like Node
#   and reject export flags (e.g. "-x", "-f"). We explicitly unset it for invocations.
# - Headless export requires an X display. If `$DISPLAY` is missing, we try:
#   1) `xvfb-run` if available
#   2) `Xvnc` (present on many clusters) as a temporary local-only X server

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <file.drawio> [file2.drawio ...]" >&2
  exit 2
fi

if ! command -v drawio >/dev/null 2>&1; then
  echo "drawio CLI not found in PATH. Expected 'drawio' executable." >&2
  exit 127
fi

have_display() {
  [[ -n "${DISPLAY-}" ]] && command -v xdpyinfo >/dev/null 2>&1 && xdpyinfo >/dev/null 2>&1
}

start_xvnc() {
  # Echo "PID DISPLAY LOG" on success.
  if ! command -v Xvnc >/dev/null 2>&1; then
    return 1
  fi

  for n in {99..110}; do
    local disp=":${n}"
    local log
    log="$(mktemp -t drawio-xvnc-${n}-XXXX.log)"

    # Local-only, no TCP X11 listener, no authentication (ok because local-only).
    Xvnc "$disp" -geometry 1280x800 -depth 24 -SecurityTypes None -localhost -nolisten tcp >"$log" 2>&1 &
    local pid=$!

    # Wait for readiness
    for _ in {1..40}; do
      if DISPLAY="$disp" xdpyinfo >/dev/null 2>&1; then
        echo "$pid $disp $log"
        return 0
      fi
      sleep 0.2
    done

    kill "$pid" >/dev/null 2>&1 || true
  done

  return 1
}

# Ensure we have an X display for the whole run.
DISPLAY_CTX="${DISPLAY-}"
XVNC_PID=""
XVNC_LOG=""

if ! have_display; then
  if command -v xvfb-run >/dev/null 2>&1; then
    DISPLAY_CTX="" # special-cased below
  else
    if xvnc_info="$(start_xvnc)"; then
      XVNC_PID="$(awk '{print $1}' <<<"$xvnc_info")"
      DISPLAY_CTX="$(awk '{print $2}' <<<"$xvnc_info")"
      XVNC_LOG="$(awk '{print $3}' <<<"$xvnc_info")"
      trap 'kill "$XVNC_PID" >/dev/null 2>&1 || true' EXIT
    else
      echo "No X display available (DISPLAY unset) and neither xvfb-run nor Xvnc could be started." >&2
      echo "Tip: install Xvfb (xvfb-run) or ensure Xvnc is runnable for headless export." >&2
      exit 1
    fi
  fi
fi

fail=0
for drawio_file in "$@"; do
  if [[ -d "$drawio_file" ]]; then
    echo "Skipping directory: $drawio_file" >&2
    fail=1
    continue
  fi
  if [[ ! -f "$drawio_file" ]]; then
    echo "Missing file: $drawio_file" >&2
    fail=1
    continue
  fi
  if [[ "$drawio_file" != *.drawio ]]; then
    echo "Skipping non-.drawio file: $drawio_file" >&2
    continue
  fi

  png="${drawio_file%.drawio}.drawio.png"
  echo "Converting $drawio_file -> $png"

  # Important: keep unknown Electron/Chromium flags AFTER the input path, otherwise
  # draw.io's CLI parser may treat them as positional args and fail input detection.
  if [[ -n "${DISPLAY_CTX}" ]]; then
    env -u ELECTRON_RUN_AS_NODE DISPLAY="$DISPLAY_CTX" \
      drawio -x -f png -s 2 -t -o "$png" "$drawio_file" --no-sandbox \
      >/dev/null 2>&1 || true
  else
    # xvfb-run path
    env -u ELECTRON_RUN_AS_NODE \
      xvfb-run -a drawio -x -f png -s 2 -t -o "$png" "$drawio_file" --no-sandbox \
      >/dev/null 2>&1 || true
  fi

  if [[ -s "$png" ]]; then
    echo "OK: $png"
    continue
  fi

  echo "FAIL: drawio PNG export failed for $drawio_file" >&2
  if [[ -n "$XVNC_LOG" && -f "$XVNC_LOG" ]]; then
    echo "Hint: Xvnc log at $XVNC_LOG" >&2
  fi
  fail=1
done

exit "$fail"
