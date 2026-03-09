#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


def parse_timestamp(value: str | int | float | None) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip()
    if not text:
        return None
    if text.isdigit():
        return float(text)
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(text).timestamp()
    except ValueError:
        return None


def canonicalize_workspace(workspace: str | None) -> str | None:
    if not workspace:
        return None
    return str(Path(workspace).expanduser().resolve())


@dataclass
class Candidate:
    session_id: str
    workspace: str | None
    session_file: str
    session_timestamp: float | None
    file_mtime: float
    history_count: int
    history_last_ts: float | None

    @property
    def freshness(self) -> float:
        return self.history_last_ts or self.session_timestamp or self.file_mtime


@dataclass
class HistoryEvent:
    session_id: str
    ts: float


def load_history(history_path: Path) -> tuple[dict[str, dict[str, float | int]], list[HistoryEvent]]:
    history: dict[str, dict[str, float | int]] = {}
    events: list[HistoryEvent] = []
    if not history_path.exists():
        return history, events

    with history_path.open() as handle:
        for raw_line in handle:
            raw_line = raw_line.strip()
            if not raw_line:
                continue
            try:
                record = json.loads(raw_line)
            except json.JSONDecodeError:
                continue
            session_id = record.get("session_id")
            ts = parse_timestamp(record.get("ts"))
            if not session_id:
                continue
            entry = history.setdefault(session_id, {"count": 0, "last_ts": 0.0})
            entry["count"] = int(entry["count"]) + 1
            if ts is not None:
                events.append(HistoryEvent(session_id=session_id, ts=ts))
                if ts > float(entry["last_ts"]):
                    entry["last_ts"] = ts
    return history, events


def iter_rollout_files(root: Path) -> Iterable[Path]:
    if not root.exists():
        return []
    files = list(root.rglob("rollout-*.jsonl"))
    files.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    return files


def read_candidate(path: Path, history: dict[str, dict[str, float | int]]) -> Candidate | None:
    try:
        with path.open() as handle:
            for raw_line in handle:
                raw_line = raw_line.strip()
                if not raw_line:
                    continue
                record = json.loads(raw_line)
                if record.get("type") != "session_meta":
                    continue
                payload = record.get("payload") or {}
                session_id = payload.get("id")
                if not session_id:
                    return None
                workspace = payload.get("cwd")
                session_ts = parse_timestamp(payload.get("timestamp")) or parse_timestamp(record.get("timestamp"))
                stats = history.get(session_id, {})
                return Candidate(
                    session_id=session_id,
                    workspace=workspace,
                    session_file=str(path),
                    session_timestamp=session_ts,
                    file_mtime=path.stat().st_mtime,
                    history_count=int(stats.get("count", 0)),
                    history_last_ts=parse_timestamp(stats.get("last_ts")),
                )
    except (OSError, json.JSONDecodeError):
        return None
    return None


def choose_candidate(
    candidates: list[Candidate],
    history_events: list[HistoryEvent],
    history_stats: dict[str, dict[str, float | int]],
    workspace: str | None,
    created_after: float | None,
    max_age_seconds: float,
    latest: bool,
) -> tuple[Candidate | None, str]:
    filtered = candidates
    reason = "latest_session"

    if workspace:
        filtered = [candidate for candidate in filtered if candidate.workspace == workspace]
        reason = "latest_workspace_session"

    if latest:
        if not filtered:
            return None, reason
        filtered.sort(
            key=lambda candidate: (
                candidate.freshness,
                candidate.history_count,
                candidate.file_mtime,
            ),
            reverse=True,
        )
        return filtered[0], reason

    if created_after is not None:
        matches: list[tuple[float, Candidate]] = []
        tolerance_before = 5.0
        for candidate in filtered:
            reference_ts = candidate.session_timestamp or candidate.file_mtime
            delta = reference_ts - created_after
            if delta < -tolerance_before:
                continue
            if delta > max_age_seconds:
                continue
            matches.append((delta, candidate))

        if not matches:
            unique_history: dict[str, float] = {}
            for event in history_events:
                delta = event.ts - created_after
                if delta < -tolerance_before:
                    continue
                if delta > max_age_seconds:
                    continue
                unique_history[event.session_id] = max(event.ts, unique_history.get(event.session_id, 0.0))

            if len(unique_history) == 1:
                session_id, ts = next(iter(unique_history.items()))
                stats = history_stats.get(session_id, {})
                return (
                    Candidate(
                        session_id=session_id,
                        workspace=workspace,
                        session_file=str(Path.home() / ".codex/history.jsonl"),
                        session_timestamp=ts,
                        file_mtime=ts,
                        history_count=int(stats.get("count", 0)),
                        history_last_ts=parse_timestamp(stats.get("last_ts")),
                    ),
                    "unique_history_session_after_created_at",
                )
            return None, "no_session_after_created_at"

        matches.sort(
            key=lambda item: (
                item[0],
                -item[1].history_count,
                -item[1].file_mtime,
            )
        )
        return matches[0][1], "closest_rollout_after_created_at"

    if not filtered:
        return None, reason

    filtered.sort(
        key=lambda candidate: (
            candidate.freshness,
            candidate.history_count,
            candidate.file_mtime,
        ),
        reverse=True,
    )
    return filtered[0], reason


def emit_json(payload: dict[str, object]) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Find a Codex SESSION_ID from ~/.codex history and rollout files.",
    )
    parser.add_argument("--workspace", help="Workspace path to match against session_meta.cwd")
    parser.add_argument(
        "--created-after",
        help="Find the closest session created at or after this ISO-8601 or epoch timestamp",
    )
    parser.add_argument(
        "--max-age-seconds",
        type=float,
        default=1800.0,
        help="Maximum allowed age delta when using --created-after",
    )
    parser.add_argument(
        "--latest",
        action="store_true",
        help="Return the latest matching session instead of matching by created time",
    )
    parser.add_argument(
        "--format",
        choices=("json", "id"),
        default="json",
        help="Output full JSON or only the resolved session id",
    )
    args = parser.parse_args()

    workspace = canonicalize_workspace(args.workspace)
    created_after = parse_timestamp(args.created_after)
    codex_home = Path(os.path.expanduser("~/.codex"))
    history_stats, history_events = load_history(codex_home / "history.jsonl")

    candidates = []
    for path in iter_rollout_files(codex_home / "sessions"):
        candidate = read_candidate(path, history_stats)
        if candidate is not None:
            candidates.append(candidate)

    selected, reason = choose_candidate(
        candidates=candidates,
        history_events=history_events,
        history_stats=history_stats,
        workspace=workspace,
        created_after=created_after,
        max_age_seconds=args.max_age_seconds,
        latest=args.latest,
    )

    if selected is None:
        if args.format == "json":
            emit_json(
                {
                    "ok": False,
                    "error": "No matching session id found",
                    "reason": reason,
                    "workspace": workspace,
                    "created_after": args.created_after,
                }
            )
        else:
            print("No matching session id found", file=sys.stderr)
        return 1

    payload = {
        "ok": True,
        "session_id": selected.session_id,
        "workspace": selected.workspace,
        "reason": reason,
        "session_file": selected.session_file,
        "session_timestamp": (
            datetime.fromtimestamp(selected.session_timestamp, tz=timezone.utc)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z")
            if selected.session_timestamp is not None
            else None
        ),
        "history_count": selected.history_count,
        "history_last_ts": selected.history_last_ts,
    }

    if args.format == "id":
        print(selected.session_id)
    else:
        emit_json(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
