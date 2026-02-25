#!/usr/bin/env python3
"""
GPU preflight across multiple nodes.

Design goals:
- Fast, non-interactive (no SSH password prompts).
- Works when executed on a GPU node (runs locally) or from a login node (SSH).
- Outputs a concise human summary by default, optionally JSON.
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class GpuRow:
    index: int
    name: str
    mem_total_mib: int
    mem_used_mib: int
    util_gpu_pct: int

    @property
    def mem_free_mib(self) -> int:
        return max(0, self.mem_total_mib - self.mem_used_mib)


def _run(cmd: List[str], timeout_s: float) -> Tuple[int, str, str]:
    p = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout_s,
    )
    return p.returncode, p.stdout, p.stderr


def _ssh_cmd(node: str, remote_cmd: str) -> List[str]:
    # BatchMode avoids password prompts; ConnectTimeout keeps it snappy.
    return [
        "ssh",
        "-o",
        "BatchMode=yes",
        "-o",
        "ConnectTimeout=6",
        node,
        "--",
        remote_cmd,
    ]


def _is_local_node(node: str) -> bool:
    hn = socket.gethostname()
    short = hn.split(".")[0]
    return node == short


def query_node_gpus(node: str, timeout_s: float) -> Tuple[Optional[List[GpuRow]], Optional[str]]:
    query = "index,name,memory.total,memory.used,utilization.gpu"
    remote = f"nvidia-smi --query-gpu={query} --format=csv,noheader,nounits"
    if _is_local_node(node):
        cmd = ["bash", "-lc", remote]
    else:
        cmd = _ssh_cmd(node, remote)

    try:
        rc, out, err = _run(cmd, timeout_s=timeout_s)
    except subprocess.TimeoutExpired:
        return None, f"timeout after {timeout_s:.1f}s"

    if rc != 0:
        msg = (err or out).strip().splitlines()[:1]
        detail = msg[0] if msg else f"exit_code={rc}"
        return None, detail

    rows: List[GpuRow] = []
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) != 5:
            return None, f"unexpected nvidia-smi output: {line!r}"
        try:
            idx = int(parts[0])
            name = parts[1]
            mem_total = int(float(parts[2]))
            mem_used = int(float(parts[3]))
            util = int(float(parts[4]))
        except ValueError:
            return None, f"failed to parse nvidia-smi row: {line!r}"
        rows.append(GpuRow(idx, name, mem_total, mem_used, util))

    return rows, None


def pick_candidates(
    all_rows: Dict[str, List[GpuRow]],
    max_util: int,
    max_mem_used_mib: int,
) -> List[Tuple[str, GpuRow]]:
    cands: List[Tuple[str, GpuRow]] = []
    for node, rows in all_rows.items():
        for r in rows:
            if r.util_gpu_pct <= max_util and r.mem_used_mib <= max_mem_used_mib:
                cands.append((node, r))
    # Prefer more free memory, then lower util, then stable ordering.
    cands.sort(key=lambda x: (-x[1].mem_free_mib, x[1].util_gpu_pct, x[0], x[1].index))
    return cands


def _print_human(
    results: Dict[str, Any],
    top_k: int,
) -> None:
    ok_nodes = results["ok_nodes"]
    bad_nodes = results["bad_nodes"]
    candidates = results["candidates"][:top_k]
    recommendation = results.get("recommendation")

    for node in sorted(ok_nodes.keys()):
        print(f"{node}:")
        for r in ok_nodes[node]:
            print(
                f"  gpu{r['index']}: util={r['util_gpu_pct']}% "
                f"mem={r['mem_used_mib']}/{r['mem_total_mib']} MiB"
            )

    if bad_nodes:
        print("\nUnreachable/failed nodes:")
        for node in sorted(bad_nodes.keys()):
            print(f"  {node}: {bad_nodes[node]}")

    print("\nCandidates:")
    if not candidates:
        print("  (none)")
    else:
        for c in candidates:
            print(
                f"  {c['node']}:{c['gpu_index']} "
                f"(util={c['util_gpu_pct']}%, mem_used={c['mem_used_mib']} MiB)"
            )

    print("\nRecommendation:")
    if recommendation is None:
        print("  (none)")
    else:
        print(f"  {recommendation['node']}:{recommendation['gpu_index']}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--nodes", default="gpu01,gpu02", help="comma-separated node list")
    ap.add_argument("--timeout-s", type=float, default=8.0, help="per-node query timeout")
    ap.add_argument("--max-util", type=int, default=5, help="candidate threshold (percent)")
    ap.add_argument(
        "--max-mem-used-mib",
        type=int,
        default=1000,
        help="candidate threshold (MiB)",
    )
    ap.add_argument("--top-k", type=int, default=5, help="max candidates to print")
    ap.add_argument("--json", action="store_true", help="print JSON")
    args = ap.parse_args()

    nodes = [n.strip() for n in args.nodes.split(",") if n.strip()]
    if not nodes:
        print("No nodes specified", file=sys.stderr)
        return 2

    ok_nodes: Dict[str, List[Dict[str, Any]]] = {}
    bad_nodes: Dict[str, str] = {}
    parsed_rows: Dict[str, List[GpuRow]] = {}

    for node in nodes:
        rows, err = query_node_gpus(node, timeout_s=args.timeout_s)
        if err is not None or rows is None:
            bad_nodes[node] = err or "unknown error"
            continue
        parsed_rows[node] = rows
        ok_nodes[node] = [asdict(r) | {"mem_free_mib": r.mem_free_mib} for r in rows]

    candidates = pick_candidates(
        parsed_rows,
        max_util=args.max_util,
        max_mem_used_mib=args.max_mem_used_mib,
    )

    cand_payload = [
        {
            "node": node,
            "gpu_index": r.index,
            "util_gpu_pct": r.util_gpu_pct,
            "mem_used_mib": r.mem_used_mib,
            "mem_total_mib": r.mem_total_mib,
            "mem_free_mib": r.mem_free_mib,
            "name": r.name,
        }
        for node, r in candidates
    ]

    recommendation = cand_payload[0] if cand_payload else None
    results = {
        "nodes": nodes,
        "ok_nodes": ok_nodes,
        "bad_nodes": bad_nodes,
        "candidates": cand_payload,
        "recommendation": recommendation,
    }

    if args.json:
        json.dump(results, sys.stdout, indent=2, ensure_ascii=True)
        sys.stdout.write("\n")
    else:
        _print_human(results, top_k=args.top_k)

    # Non-zero exit if any node failed: force the caller to notice.
    return 1 if bad_nodes else 0


if __name__ == "__main__":
    raise SystemExit(main())

