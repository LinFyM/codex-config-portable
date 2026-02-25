#!/usr/bin/env python3
"""
Run a long command and optional follow-ups with resumable logs/state in WORKSPACE/.codex/longrun/.

No external deps. Designed for:
- foreground runs (poll to completion in-session)
- detached runs (spawn background orchestrator, return a run_id immediately)
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shlex
import subprocess
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional


def resolve_workspace_root(explicit: Optional[str]) -> Path:
    """
    Workspace-scoped by default:
    - Prefer git toplevel.
    - If not in a git repo, require --workspace (avoid writing under $HOME accidentally).
    """
    if explicit:
        return Path(explicit).resolve()
    try:
        p = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            check=True,
        )
        root = p.stdout.strip()
        if root:
            return Path(root).resolve()
    except Exception:
        pass
    raise SystemExit("Not in a git repo. Pass --workspace to choose the workspace root explicitly.")


@dataclass
class RunState:
    run_id: str
    label: str
    workspace: str
    created_at: str
    status: str  # created|running|completed|failed
    main_cmd: str
    then_cmds: List[str]
    main_pid: Optional[int] = None
    main_rc: Optional[int] = None
    then_rcs: Optional[List[int]] = None
    error: Optional[str] = None


def write_json(path: Path, obj) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def now_tag() -> str:
    return dt.datetime.now().strftime("%Y%m%d_%H%M%S")


def make_run_dir(root: Path, label: str) -> Path:
    run_id = f"{label}_{now_tag()}"
    run_dir = root / ".codex" / "longrun" / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    return run_dir


def spawn_detached(argv: List[str], log_path: Path) -> int:
    # Start a background process, redirecting stdout/stderr to a log file.
    with log_path.open("ab", buffering=0) as f:
        p = subprocess.Popen(
            argv,
            stdin=subprocess.DEVNULL,
            stdout=f,
            stderr=subprocess.STDOUT,
            close_fds=True,
            start_new_session=True,
        )
    return p.pid


def run_shell(cmd: str, stdout_path: Path, stderr_to_stdout: bool = True) -> int:
    # Run via bash -lc so users can pass env exports/complex pipelines.
    stderr = subprocess.STDOUT if stderr_to_stdout else None
    with stdout_path.open("ab", buffering=0) as f:
        p = subprocess.Popen(
            ["bash", "-lc", cmd],
            stdin=subprocess.DEVNULL,
            stdout=f,
            stderr=stderr,
            start_new_session=False,
        )
        return p.wait()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True, help="short label for this run (used in run_id)")
    ap.add_argument("--workspace", default=None, help="workspace root; default: git root or CWD")
    ap.add_argument("--cmd", required=True, help="main command to run (bash -lc)")
    ap.add_argument("--then", action="append", default=[], help="follow-up command(s) to run after success")
    ap.add_argument("--detach", action="store_true", help="spawn orchestrator in background and return immediately")
    args = ap.parse_args()

    ws = resolve_workspace_root(args.workspace)

    # If we are the detached worker, we should reuse the run directory created by the parent.
    env_run_dir = os.environ.get("LONGRUN_RUN_DIR")
    if env_run_dir:
        run_dir = Path(env_run_dir).resolve()
        run_dir.mkdir(parents=True, exist_ok=True)
    else:
        run_dir = make_run_dir(ws, args.label)

    state_path = run_dir / "state.json"
    orch_log = run_dir / "orchestrator.log"
    main_log = run_dir / "main.log"
    then_log = run_dir / "then.log"

    state = RunState(
        run_id=run_dir.name,
        label=args.label,
        workspace=str(ws),
        created_at=dt.datetime.now().isoformat(timespec="seconds"),
        status="created",
        main_cmd=args.cmd,
        then_cmds=list(args.then),
    )
    write_json(state_path, asdict(state))

    if args.detach:
        # Spawn a background orchestrator (this same script) without --detach.
        argv = [
            sys.executable,
            str(Path(__file__).resolve()),
            "--label",
            args.label,
            "--workspace",
            str(ws),
            "--cmd",
            args.cmd,
        ]
        for t in args.then:
            argv += ["--then", t]

        # We want the spawned process to reuse the already-created run_dir.
        # Pass it via env; it will detect and run in-place.
        env = os.environ.copy()
        env["LONGRUN_RUN_DIR"] = str(run_dir)

        with orch_log.open("ab", buffering=0) as f:
            p = subprocess.Popen(
                argv,
                env=env,
                stdin=subprocess.DEVNULL,
                stdout=f,
                stderr=subprocess.STDOUT,
                close_fds=True,
                start_new_session=True,
            )

        # Record the detached orchestrator PID.
        write_json(run_dir / "detached.json", {"orchestrator_pid": p.pid})
        print(state.run_id)
        return 0

    # Non-detached execution path.
    if env_run_dir:
        # Reload state written by the detacher.
        state = RunState(**json.loads(state_path.read_text(encoding="utf-8")))

    state.status = "running"
    write_json(state_path, asdict(state))

    # Run main command.
    main_rc = run_shell(state.main_cmd, stdout_path=main_log)
    state.main_rc = main_rc

    if main_rc != 0:
        state.status = "failed"
        state.error = f"main command failed with rc={main_rc}"
        write_json(state_path, asdict(state))
        return 1

    # Run follow-ups.
    then_rcs: List[int] = []
    for i, cmd in enumerate(state.then_cmds, start=1):
        rc = run_shell(cmd, stdout_path=then_log)
        then_rcs.append(rc)
        if rc != 0:
            state.status = "failed"
            state.then_rcs = then_rcs
            state.error = f"follow-up failed at step {i} rc={rc}"
            write_json(state_path, asdict(state))
            return 1

    state.then_rcs = then_rcs
    state.status = "completed"
    write_json(state_path, asdict(state))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
