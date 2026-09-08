#!/usr/bin/env python3
"""Live, identity-aware NVIDIA GPU preflight for local or SSH nodes."""

from __future__ import annotations

import argparse
import json
import socket
import subprocess
import sys
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class GpuRow:
    index: int
    uuid: str
    serial: str
    name: str
    mem_total_mib: int
    mem_used_mib: int
    util_gpu_pct: int
    compute_mode: str
    driver_version: str

    @property
    def mem_free_mib(self) -> int:
        return max(0, self.mem_total_mib - self.mem_used_mib)


@dataclass(frozen=True)
class ProcessRow:
    gpu_uuid: str
    pid: int
    process_name: str
    used_memory_mib: int
    owner: str


def run(cmd: List[str], timeout_s: float) -> Tuple[int, str, str]:
    proc = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout_s,
    )
    return proc.returncode, proc.stdout, proc.stderr


def is_local_node(node: str) -> bool:
    hostname = socket.gethostname()
    names = {
        hostname,
        hostname.split(".")[0],
        socket.getfqdn(),
        "localhost",
        "127.0.0.1",
    }
    return node in names


def node_command(node: str, command: str) -> List[str]:
    if is_local_node(node):
        return ["bash", "-lc", command]
    return [
        "ssh",
        "-o",
        "BatchMode=yes",
        "-o",
        "ConnectTimeout=6",
        node,
        "--",
        command,
    ]


def first_error(rc: int, out: str, err: str) -> str:
    lines = (err or out).strip().splitlines()
    return lines[0] if lines else f"exit_code={rc}"


def query_gpus(node: str, timeout_s: float) -> Tuple[Optional[List[GpuRow]], Optional[str]]:
    fields = (
        "index,uuid,serial,name,memory.total,memory.used,utilization.gpu,"
        "compute_mode,driver_version"
    )
    command = f"nvidia-smi --query-gpu={fields} --format=csv,noheader,nounits"
    try:
        rc, out, err = run(node_command(node, command), timeout_s)
    except subprocess.TimeoutExpired:
        return None, f"GPU query timed out after {timeout_s:.1f}s"
    if rc != 0:
        return None, first_error(rc, out, err)

    rows: List[GpuRow] = []
    for line in out.splitlines():
        if not line.strip():
            continue
        parts = [part.strip() for part in line.split(",", 8)]
        if len(parts) != 9:
            return None, f"unexpected nvidia-smi GPU row: {line!r}"
        try:
            rows.append(
                GpuRow(
                    index=int(parts[0]),
                    uuid=parts[1],
                    serial=parts[2],
                    name=parts[3],
                    mem_total_mib=int(float(parts[4])),
                    mem_used_mib=int(float(parts[5])),
                    util_gpu_pct=int(float(parts[6])),
                    compute_mode=parts[7],
                    driver_version=parts[8],
                )
            )
        except ValueError:
            return None, f"failed to parse nvidia-smi GPU row: {line!r}"
    if not rows:
        return None, "nvidia-smi returned no GPUs"
    return rows, None


def query_owners(node: str, pids: List[int], timeout_s: float) -> Tuple[Dict[int, str], Optional[str]]:
    if not pids:
        return {}, None
    pid_csv = ",".join(str(pid) for pid in sorted(set(pids)))
    command = f"ps -o pid=,user= -p {pid_csv}"
    try:
        rc, out, err = run(node_command(node, command), timeout_s)
    except subprocess.TimeoutExpired:
        return {}, f"process-owner query timed out after {timeout_s:.1f}s"
    if rc not in (0, 1):
        return {}, first_error(rc, out, err)
    owners: Dict[int, str] = {}
    for line in out.splitlines():
        parts = line.strip().split(None, 1)
        if len(parts) != 2:
            continue
        try:
            owners[int(parts[0])] = parts[1]
        except ValueError:
            continue
    return owners, None


def query_processes(
    node: str,
    timeout_s: float,
) -> Tuple[Optional[List[ProcessRow]], Optional[str]]:
    fields = "gpu_uuid,pid,process_name,used_memory"
    command = f"nvidia-smi --query-compute-apps={fields} --format=csv,noheader,nounits"
    try:
        rc, out, err = run(node_command(node, command), timeout_s)
    except subprocess.TimeoutExpired:
        return None, f"compute-process query timed out after {timeout_s:.1f}s"
    if rc != 0:
        return None, first_error(rc, out, err)

    parsed: List[Tuple[str, int, str, int]] = []
    for line in out.splitlines():
        if not line.strip() or line.lower().startswith("no running"):
            continue
        parts = [part.strip() for part in line.split(",", 3)]
        if len(parts) != 4:
            return None, f"unexpected nvidia-smi process row: {line!r}"
        try:
            parsed.append((parts[0], int(parts[1]), parts[2], int(float(parts[3]))))
        except ValueError:
            return None, f"failed to parse nvidia-smi process row: {line!r}"

    owners, owner_error = query_owners(node, [item[1] for item in parsed], timeout_s)
    if owner_error:
        return None, owner_error
    return [
        ProcessRow(uuid, pid, name, memory, owners.get(pid, "<exited-or-unknown>"))
        for uuid, pid, name, memory in parsed
    ], None


def prohibited(mode: str) -> bool:
    return mode.strip().lower() == "prohibited"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--nodes",
        default=socket.gethostname().split(".")[0],
        help="comma-separated node list; default is the current host",
    )
    parser.add_argument("--timeout-s", type=float, default=8.0)
    parser.add_argument("--max-util", type=int, default=5)
    parser.add_argument("--max-mem-used-mib", type=int, default=1000)
    parser.add_argument("--top-k", type=int, default=8)
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def gpu_reasons(
    gpu: GpuRow,
    active: List[ProcessRow],
    process_error: Optional[str],
    max_util: int,
    max_mem_used_mib: int,
) -> List[str]:
    reasons: List[str] = []
    if prohibited(gpu.compute_mode):
        reasons.append("compute_mode=Prohibited")
    if gpu.util_gpu_pct > max_util:
        reasons.append(f"utilization>{max_util}%")
    if gpu.mem_used_mib > max_mem_used_mib:
        reasons.append(f"memory_used>{max_mem_used_mib}MiB")
    if active:
        owners = sorted({process.owner for process in active})
        reasons.append(f"active_compute_processes owners={owners}")
    if process_error:
        reasons.append(f"process_check_failed: {process_error}")
    return reasons


def build_gpu_payload(
    gpu: GpuRow,
    active: List[ProcessRow],
    process_error: Optional[str],
    args: argparse.Namespace,
) -> Dict[str, Any]:
    reasons = gpu_reasons(
        gpu,
        active,
        process_error,
        args.max_util,
        args.max_mem_used_mib,
    )
    state = "candidate" if not reasons else (
        "prohibited" if prohibited(gpu.compute_mode) else "busy"
    )
    return asdict(gpu) | {
        "mem_free_mib": gpu.mem_free_mib,
        "state": state,
        "reasons": reasons,
        "processes": [asdict(process) for process in active],
    }


def inspect_node(
    node: str,
    args: argparse.Namespace,
) -> Tuple[Optional[Dict[str, Any]], Optional[str], List[Dict[str, Any]]]:
    gpus, gpu_error = query_gpus(node, args.timeout_s)
    if gpu_error or gpus is None:
        return None, gpu_error or "unknown GPU query error", []
    processes, process_error = query_processes(node, args.timeout_s)
    processes = processes or []
    process_by_uuid: Dict[str, List[ProcessRow]] = {}
    for process in processes:
        process_by_uuid.setdefault(process.gpu_uuid, []).append(process)

    rows = [
        build_gpu_payload(
            gpu,
            process_by_uuid.get(gpu.uuid, []),
            process_error,
            args,
        )
        for gpu in gpus
    ]
    candidates = [{"node": node, **row} for row in rows if row["state"] == "candidate"]
    result = {
        "gpus": rows,
        "processes": [asdict(process) for process in processes],
        "process_check_error": process_error,
    }
    return result, None, candidates


def collect_results(
    nodes: List[str],
    args: argparse.Namespace,
) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, str], List[Dict[str, Any]]]:
    node_results: Dict[str, Dict[str, Any]] = {}
    bad_nodes: Dict[str, str] = {}
    candidates: List[Dict[str, Any]] = []
    for node in nodes:
        result, error, node_candidates = inspect_node(node, args)
        if error or result is None:
            bad_nodes[node] = error or "unknown node inspection error"
            continue
        node_results[node] = result
        candidates.extend(node_candidates)
    candidates.sort(
        key=lambda row: (
            -row["mem_free_mib"],
            row["util_gpu_pct"],
            row["node"],
            row["index"],
        )
    )
    return node_results, bad_nodes, candidates


def print_gpu(node: str, gpu: Dict[str, Any]) -> None:
    uuid_short = gpu["uuid"][-12:]
    reason = "; ".join(gpu["reasons"]) if gpu["reasons"] else "eligible"
    print(
        f"  gpu{gpu['index']} uuid=...{uuid_short} serial={gpu['serial']} "
        f"mode={gpu['compute_mode']} util={gpu['util_gpu_pct']}% "
        f"mem={gpu['mem_used_mib']}/{gpu['mem_total_mib']}MiB "
        f"state={gpu['state']} ({reason})"
    )
    for process in gpu["processes"]:
        print(
            f"    pid={process['pid']} owner={process['owner']} "
            f"mem={process['used_memory_mib']}MiB process={process['process_name']}"
        )


def print_human(
    nodes: List[str],
    node_results: Dict[str, Dict[str, Any]],
    bad_nodes: Dict[str, str],
    candidates: List[Dict[str, Any]],
    top_k: int,
) -> None:
    for node in nodes:
        if node in bad_nodes:
            print(f"{node}: FAILED: {bad_nodes[node]}")
            continue
        print(f"{node}:")
        for gpu in node_results[node]["gpus"]:
            print_gpu(node, gpu)

    print("\nCandidates:")
    for row in candidates[:top_k]:
        print(
            f"  {row['node']}:{row['index']} uuid={row['uuid']} serial={row['serial']} "
            f"free={row['mem_free_mib']}MiB"
        )
    if not candidates:
        print("  (none)")


def main() -> int:
    args = parse_args()

    nodes = [node.strip() for node in args.nodes.split(",") if node.strip()]
    if not nodes:
        print("No nodes specified", file=sys.stderr)
        return 2
    node_results, bad_nodes, candidates = collect_results(nodes, args)
    results = {
        "nodes": nodes,
        "node_results": node_results,
        "bad_nodes": bad_nodes,
        "candidates": candidates,
        "recommendation": candidates[0] if candidates else None,
    }

    if args.json:
        json.dump(results, sys.stdout, indent=2, ensure_ascii=True)
        sys.stdout.write("\n")
    else:
        print_human(nodes, node_results, bad_nodes, candidates, args.top_k)

    process_failures = any(
        result.get("process_check_error") for result in node_results.values()
    )
    return 1 if bad_nodes or process_failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
