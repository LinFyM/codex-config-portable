#!/usr/bin/env python3
from __future__ import annotations

import argparse
import signal
import time

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Allocate large tensors on selected CUDA devices and keep them alive."
    )
    parser.add_argument("--devices", required=True, help="Comma separated CUDA device indices.")
    parser.add_argument("--gib-per-device", type=float, default=30.0)
    parser.add_argument("--dtype", choices=("float16", "bfloat16", "float32"), default="float16")
    parser.add_argument("--poll-seconds", type=float, default=30.0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    import torch

    dtype = getattr(torch, args.dtype)
    element_size = torch.tensor([], dtype=dtype).element_size()
    target_bytes = int(args.gib_per_device * (1024**3))
    numel = target_bytes // element_size
    buffers: list[torch.Tensor] = []
    stop = False

    def _stop(_signum: int, _frame: object) -> None:
        nonlocal stop
        stop = True

    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)

    for raw_device in args.devices.split(","):
        device = f"cuda:{raw_device.strip()}"
        buffers.append(torch.empty((numel,), dtype=dtype, device=device))

    while not stop:
        for buffer in buffers:
            buffer.fill_(0)
        time.sleep(args.poll_seconds)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
