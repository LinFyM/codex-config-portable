#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parent.parent
TENSOR_SESSION_SCRIPT = SKILL_DIR / "scripts" / "tensor_session.py"
DEFAULT_PYTHON = os.environ.get("GPU_SESSION_PYTHON", sys.executable)


def parse_args() -> argparse.Namespace:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--host", help="Optional remote host, for example gpu01.")
    common.add_argument("--session", help="Explicit tmux session name.")
    common.add_argument("--devices", help="Comma separated GPU indices.")
    common.add_argument("--gib-per-device", type=float, default=30.0)
    common.add_argument("--dtype", choices=("float16", "bfloat16", "float32"), default="float16")
    common.add_argument("--poll-seconds", type=float, default=30.0)
    common.add_argument("--min-mib", type=int, default=28000)
    common.add_argument("--timeout-secs", type=int, default=90)
    common.add_argument("--workdir", default=str(Path.cwd()))
    common.add_argument("--python", default=DEFAULT_PYTHON)
    common.add_argument("--no-wait", action="store_true")
    common.add_argument("--replace", action="store_true", help="Replace the named existing tmux session.")
    common.add_argument(
        "--max-existing-mib",
        type=int,
        default=1000,
        help="Refuse start above this existing memory use per selected GPU.",
    )
    common.add_argument(
        "--allow-busy",
        action="store_true",
        help="Allow existing memory/process use; requires explicit user authorization.",
    )

    parser = argparse.ArgumentParser(
        description="Manage tmux-backed GPU sessions locally or over ssh.",
        parents=[common],
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("start", parents=[common])
    subparsers.add_parser("stop", parents=[common])
    subparsers.add_parser("status", parents=[common])
    subparsers.add_parser("wait", parents=[common])
    return parser.parse_args()


def _require_devices(args: argparse.Namespace) -> None:
    if not args.devices:
        raise SystemExit("--devices is required for this command")


def _require_session(args: argparse.Namespace) -> None:
    if not args.session:
        raise SystemExit("--session is required")


def _run_shell(command: str, host: str | None, check: bool = True) -> subprocess.CompletedProcess[str]:
    if host:
        cmd = ["ssh", "-o", "BatchMode=yes", host, command]
    else:
        cmd = ["bash", "-lc", command]
    return subprocess.run(cmd, text=True, capture_output=True, check=check)


def _session_exists(host: str | None, session: str) -> bool:
    result = _run_shell(f"tmux has-session -t {shlex.quote(session)}", host, check=False)
    return result.returncode == 0


def _stop_session(host: str | None, session: str) -> None:
    if _session_exists(host, session):
        _run_shell(f"tmux kill-session -t {shlex.quote(session)}", host, check=False)


def _query_gpu_memory(host: str | None) -> dict[int, int]:
    result = _run_shell(
        "nvidia-smi --query-gpu=index,memory.used --format=csv,noheader,nounits",
        host,
        check=True,
    )
    usage: dict[int, int] = {}
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        raw_idx, raw_mem = [part.strip() for part in line.split(",", 1)]
        usage[int(raw_idx)] = int(raw_mem)
    return usage


def _query_compute_process_gpus(host: str | None) -> set[int]:
    result = _run_shell(
        "nvidia-smi --query-compute-apps=gpu_uuid --format=csv,noheader,nounits",
        host,
        check=False,
    )
    if result.returncode != 0:
        raise SystemExit((result.stderr or result.stdout).strip() or "failed to query GPU processes")
    active_uuids = {line.strip() for line in result.stdout.splitlines() if line.strip()}
    if not active_uuids:
        return set()
    mapping = _run_shell(
        "nvidia-smi --query-gpu=index,uuid --format=csv,noheader,nounits",
        host,
        check=True,
    )
    active_indices: set[int] = set()
    for line in mapping.stdout.splitlines():
        raw_index, raw_uuid = [part.strip() for part in line.split(",", 1)]
        if raw_uuid in active_uuids:
            active_indices.add(int(raw_index))
    return active_indices


def _parse_devices(raw: str) -> list[int]:
    try:
        devices = [int(part.strip()) for part in raw.split(",") if part.strip()]
    except ValueError as exc:
        raise SystemExit(f"invalid --devices value: {raw!r}") from exc
    if not devices or any(device < 0 for device in devices) or len(set(devices)) != len(devices):
        raise SystemExit("--devices must contain unique non-negative GPU indices")
    return devices


def _preflight_start(args: argparse.Namespace, devices: list[int]) -> None:
    usage = _query_gpu_memory(args.host)
    missing = [device for device in devices if device not in usage]
    if missing:
        raise SystemExit(f"GPU indices do not exist on {args.host or 'local'}: {missing}")
    active = _query_compute_process_gpus(args.host)
    busy = [
        device
        for device in devices
        if usage[device] > args.max_existing_mib or device in active
    ]
    if busy and not args.allow_busy:
        raise SystemExit(
            f"refusing busy GPUs on {args.host or 'local'}: {busy}; "
            "rerun gpu-preflight and obtain explicit authorization before --allow-busy"
        )


def _wait_for_session(host: str | None, devices: list[int], min_mib: int, timeout_secs: int) -> None:
    deadline = time.time() + timeout_secs
    while time.time() < deadline:
        usage = _query_gpu_memory(host)
        if all(usage.get(device, 0) >= min_mib for device in devices):
            return
        time.sleep(2)
    device_csv = ",".join(str(device) for device in devices)
    raise SystemExit(f"session failed to reach target occupancy on {host or 'local'}:{device_csv}")


def _build_session_payload(args: argparse.Namespace) -> str:
    inner_cmd = shlex.join(
        [
            args.python,
            str(TENSOR_SESSION_SCRIPT),
            "--devices",
            args.devices,
            "--gib-per-device",
            str(args.gib_per_device),
            "--dtype",
            args.dtype,
            "--poll-seconds",
            str(args.poll_seconds),
        ]
    )
    return f"cd {shlex.quote(args.workdir)} && exec {inner_cmd}"


def cmd_start(args: argparse.Namespace) -> int:
    _require_session(args)
    _require_devices(args)
    devices = _parse_devices(args.devices)
    _preflight_start(args, devices)
    if _session_exists(args.host, args.session):
        if not args.replace:
            raise SystemExit(
                f"tmux session already exists: {args.session!r}; verify ownership before --replace"
            )
        _stop_session(args.host, args.session)
    payload = _build_session_payload(args)
    command = f"tmux new-session -d -s {shlex.quote(args.session)} {shlex.quote(payload)}"
    _run_shell(command, args.host, check=True)
    if not args.no_wait:
        _wait_for_session(args.host, devices, args.min_mib, args.timeout_secs)
    return 0


def cmd_stop(args: argparse.Namespace) -> int:
    _require_session(args)
    _stop_session(args.host, args.session)
    return 0


def cmd_wait(args: argparse.Namespace) -> int:
    _require_session(args)
    _require_devices(args)
    devices = _parse_devices(args.devices)
    _wait_for_session(args.host, devices, args.min_mib, args.timeout_secs)
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    _require_session(args)
    _require_devices(args)
    devices = _parse_devices(args.devices)
    usage = _query_gpu_memory(args.host)
    session_state = "present" if _session_exists(args.host, args.session) else "missing"
    print(f"host={args.host or 'local'} session={args.session} status={session_state}")
    for device in devices:
        print(f"gpu={device} memory_used_mib={usage.get(device, 0)}")
    return 0


def main() -> int:
    args = parse_args()
    if args.command == "start":
        return cmd_start(args)
    if args.command == "stop":
        return cmd_stop(args)
    if args.command == "wait":
        return cmd_wait(args)
    if args.command == "status":
        return cmd_status(args)
    raise SystemExit(f"unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
