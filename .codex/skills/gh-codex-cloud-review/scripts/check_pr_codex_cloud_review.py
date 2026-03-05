#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional


CODEX_BOT_LOGIN = "chatgpt-codex-connector[bot]"


def _run_json(cmd: list[str]) -> Any:
    cp = subprocess.run(cmd, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if cp.returncode != 0:
        raise RuntimeError(f"command failed ({cp.returncode}): {' '.join(cmd)}\n{cp.stderr.strip()}")
    out = cp.stdout.strip()
    return json.loads(out) if out else None


def _run_text(cmd: list[str]) -> str:
    cp = subprocess.run(cmd, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if cp.returncode != 0:
        raise RuntimeError(f"command failed ({cp.returncode}): {' '.join(cmd)}\n{cp.stderr.strip()}")
    return cp.stdout


def _parse_pr_number(value: str) -> int:
    m = re.search(r"/pull/(\d+)", value)
    if m:
        return int(m.group(1))
    if value.isdigit():
        return int(value)
    raise ValueError(f"unsupported PR identifier: {value!r} (expected PR number or URL containing /pull/<n>)")


@dataclass
class CodexReaction:
    content: str
    created_at: str

    def created_at_dt(self) -> Optional[datetime]:
        try:
            return datetime.fromisoformat(self.created_at.replace("Z", "+00:00"))
        except Exception:
            return None


def _latest_codex_reaction(reactions: list[dict[str, Any]]) -> Optional[CodexReaction]:
    items: list[CodexReaction] = []
    for r in reactions:
        user = r.get("user") or {}
        if str(user.get("login") or "") != CODEX_BOT_LOGIN:
            continue
        items.append(CodexReaction(content=str(r.get("content") or ""), created_at=str(r.get("created_at") or "")))
    if not items:
        return None
    items.sort(key=lambda x: x.created_at_dt() or datetime.min, reverse=True)
    return items[0]


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Check Codex cloud review signals (thumbs up / comments / reviews / checks) on a GitHub PR."
    )
    ap.add_argument("pr", help="PR number or PR URL (must contain /pull/<n>)")
    ap.add_argument(
        "--repo",
        default="",
        help="Override repo in OWNER/REPO format. Default: current repo from `gh repo view`.",
    )
    args = ap.parse_args()

    pr_number = _parse_pr_number(str(args.pr))

    if args.repo:
        name_with_owner = str(args.repo).strip()
    else:
        repo_info = _run_json(["gh", "repo", "view", "--json", "nameWithOwner"])
        name_with_owner = str((repo_info or {}).get("nameWithOwner") or "").strip()
        if not name_with_owner:
            raise RuntimeError("failed to resolve repo via `gh repo view --json nameWithOwner`; pass --repo explicitly")

    owner, repo = name_with_owner.split("/", 1)

    pr = _run_json(
        [
            "gh",
            "pr",
            "view",
            str(pr_number),
            "--repo",
            name_with_owner,
            "--json",
            "title,url,state,comments,reviews,reactionGroups,statusCheckRollup",
        ]
    )
    title = str((pr or {}).get("title") or "")
    url = str((pr or {}).get("url") or "")
    state = str((pr or {}).get("state") or "")

    reactions = _run_json(
        [
            "gh",
            "api",
            "-H",
            "Accept: application/vnd.github+json",
            f"repos/{owner}/{repo}/issues/{pr_number}/reactions",
        ]
    )
    latest = _latest_codex_reaction(list(reactions or []))

    comments = list((pr or {}).get("comments") or [])
    codex_comments = [
        c
        for c in comments
        if str(((c or {}).get("author") or {}).get("login") or "") == CODEX_BOT_LOGIN
    ]

    reviews = list((pr or {}).get("reviews") or [])
    codex_reviews = [
        r
        for r in reviews
        if str(((r or {}).get("author") or {}).get("login") or "") == CODEX_BOT_LOGIN
    ]

    reaction_groups = list((pr or {}).get("reactionGroups") or [])
    thumbs_up_total = 0
    for g in reaction_groups:
        if str((g or {}).get("content") or "") == "THUMBS_UP":
            thumbs_up_total = int((((g or {}).get("users") or {}).get("totalCount") or 0))
            break

    checks = list((pr or {}).get("statusCheckRollup") or [])

    print(f"PR #{pr_number} [{state}] {title}")
    if url:
        print(f"url: {url}")
    print(f"repo: {name_with_owner}")
    print("")
    print("codex-cloud:")
    if latest is None:
        print(f"- reaction: none from {CODEX_BOT_LOGIN} (thumbs_up_total={thumbs_up_total})")
    else:
        print(f"- reaction: {latest.content} at {latest.created_at} by {CODEX_BOT_LOGIN}")
    print(f"- comments: {len(codex_comments)}")
    print(f"- reviews: {len(codex_reviews)}")
    print(f"- checks: {len(checks)} (gh may show none even when cloud review is done)")
    print("")
    if latest is not None and latest.content == "+1" and len(codex_comments) == 0 and len(codex_reviews) == 0:
        print("interpretation: likely 'pass' (thumbs-up only).")
    elif latest is None and len(codex_comments) == 0 and len(codex_reviews) == 0:
        print("interpretation: no visible Codex signal yet; wait 10-15 minutes, or re-trigger via PR comment if your org uses mention-trigger.")
    else:
        print("interpretation: check comments/reviews/checks for actionable feedback.")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        raise SystemExit(2)

