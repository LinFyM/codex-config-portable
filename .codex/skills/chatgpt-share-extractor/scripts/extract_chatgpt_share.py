#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
from datetime import datetime, timezone
import html
import json
from pathlib import Path
import re
import sys
from typing import Any
from urllib.request import Request, urlopen


ENQUEUE_RE = re.compile(r"streamController\.enqueue\((\"(?:\\.|[^\"\\])*\")\)")
REDACTED_MARKER = "The output of this plugin was redacted."


def fetch_text(url: str) -> str:
    request = Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "Chrome/122.0 Safari/537.36"
            )
        },
    )
    with urlopen(request, timeout=30) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def extract_stream_array(html_text: str) -> list[Any]:
    chunks = [ast.literal_eval(match.group(1)) for match in ENQUEUE_RE.finditer(html_text)]
    if not chunks:
        raise ValueError("could not find React Router streamController.enqueue chunks in share HTML")
    stream_text = "".join(chunks)
    json_line = stream_text.splitlines()[0]
    return json.loads(json_line)


def _key(data: list[Any], raw_key: str) -> Any:
    if raw_key.startswith("_") and raw_key[1:].isdigit():
        index = int(raw_key[1:])
        if 0 <= index < len(data):
            return data[index]
    return raw_key


def _value(data: list[Any], raw_value: Any) -> Any:
    if isinstance(raw_value, int):
        if raw_value < 0:
            return None
        if raw_value < len(data):
            return data[raw_value]
    return raw_value


def _object_from(data: list[Any], raw_value: Any) -> Any:
    value = _value(data, raw_value)
    if not isinstance(value, dict):
        return value
    return {_key(data, key): _value(data, child) for key, child in value.items()}


def _string_from_ref(data: list[Any], raw_value: Any) -> str | None:
    value = _value(data, raw_value)
    return value if isinstance(value, str) else None


def extract_messages(data: list[Any]) -> list[dict[str, Any]]:
    try:
        linear_key_index = data.index("linear_conversation")
    except ValueError as exc:
        raise ValueError("could not find linear_conversation in share payload") from exc
    raw_linear = data[linear_key_index + 1]
    if not isinstance(raw_linear, list):
        raise ValueError("linear_conversation did not resolve to a list")

    messages: list[dict[str, Any]] = []
    for linear_index, node_ref in enumerate(raw_linear):
        node = _object_from(data, node_ref)
        if not isinstance(node, dict):
            continue
        message = _object_from(data, node.get("message"))
        if not isinstance(message, dict):
            continue

        author = _object_from(data, message.get("author"))
        role = None
        if isinstance(author, dict):
            role = _string_from_ref(data, author.get("role"))

        content = _object_from(data, message.get("content"))
        content_type = None
        parts = None
        if isinstance(content, dict):
            content_type = _string_from_ref(data, content.get("content_type"))
            parts = content.get("parts")

        text_parts: list[str] = []
        if isinstance(parts, list):
            for part in parts:
                value = _value(data, part)
                if isinstance(value, str):
                    text_parts.append(value)

        text = "\n".join(text_parts).strip()
        if not text:
            continue

        messages.append(
            {
                "linear_index": linear_index,
                "role": role or "unknown",
                "content_type": content_type or "unknown",
                "text": text,
                "text_length": len(text),
            }
        )
    return messages


def is_redacted_message(message: dict[str, Any]) -> bool:
    return REDACTED_MARKER in str(message.get("text", ""))


def filter_useful_messages(
    messages: list[dict[str, Any]], *, include_tools: bool, include_redacted: bool
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    stats = {
        "parsed_messages": len(messages),
        "redacted_markers": sum(is_redacted_message(message) for message in messages),
        "filtered_redacted": 0,
        "filtered_tools": 0,
    }
    kept: list[dict[str, Any]] = []
    for message in messages:
        if not include_redacted and is_redacted_message(message):
            stats["filtered_redacted"] += 1
            continue
        if not include_tools and message.get("role") == "tool":
            stats["filtered_tools"] += 1
            continue
        kept.append(message)
    stats["written_messages"] = len(kept)
    return kept, stats


def extract_title(html_text: str) -> str | None:
    match = re.search(r"<title>(.*?)</title>", html_text, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return None
    return html.unescape(re.sub(r"\s+", " ", match.group(1)).strip())


def fence_text(text: str) -> str:
    fence = "```"
    while fence in text:
        fence += "`"
    return f"{fence}text\n{text}\n{fence}"


def write_markdown(
    path: Path,
    *,
    url: str,
    title: str | None,
    messages: list[dict[str, Any]],
    stats: dict[str, int],
    include_tools: bool,
    include_redacted: bool,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    mode = "raw" if include_tools and include_redacted else "clean"
    lines = [
        "# ChatGPT Share Transcript",
        "",
        f"- Source URL: {url}",
        f"- Page title: {title or 'unknown'}",
        f"- Extracted at: {timestamp}",
        f"- Export mode: {mode}",
        f"- Parsed readable text messages: {stats['parsed_messages']}",
        f"- Written useful messages: {stats['written_messages']}",
        f"- Redacted plugin/tool markers found: {stats['redacted_markers']}",
        f"- Filtered redacted messages: {stats['filtered_redacted']}",
        f"- Filtered tool messages: {stats['filtered_tools']}",
        "",
        "Note: By default this extractor writes the useful user/assistant dialogue and filters tool outputs/redacted placeholders. Use `--include-tools` or `--include-redacted` when an audit-grade raw export is needed.",
        "",
        "## Raw Conversation",
        "",
    ]
    for ordinal, message in enumerate(messages, start=1):
        lines.extend(
            [
                f"### Message {ordinal} | linear_index={message['linear_index']} | "
                f"role={message['role']} | content_type={message['content_type']} | "
                f"chars={message['text_length']}",
                "",
                fence_text(str(message["text"])),
                "",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def write_jsonl(path: Path, *, messages: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for message in messages:
            handle.write(json.dumps(message, ensure_ascii=False) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Extract visible text messages from a ChatGPT share URL.")
    parser.add_argument("url", help="ChatGPT share URL")
    parser.add_argument("--markdown", type=Path, help="Write transcript Markdown to this path")
    parser.add_argument("--jsonl", type=Path, help="Write message JSONL to this path")
    parser.add_argument("--print-summary", action="store_true", help="Print a compact JSON summary")
    parser.add_argument("--include-tools", action="store_true", help="Include tool-role messages in outputs")
    parser.add_argument("--include-redacted", action="store_true", help="Include redacted plugin/tool placeholders in outputs")
    parser.add_argument("--raw", action="store_true", help="Preserve all readable messages; equivalent to --include-tools --include-redacted")
    args = parser.parse_args(argv)
    if args.raw:
        args.include_tools = True
        args.include_redacted = True

    html_text = fetch_text(args.url)
    title = extract_title(html_text)
    data = extract_stream_array(html_text)
    messages = extract_messages(data)
    if not messages:
        raise ValueError("share payload was parsed, but no readable text messages were found")
    useful_messages, stats = filter_useful_messages(
        messages,
        include_tools=args.include_tools,
        include_redacted=args.include_redacted,
    )
    if not useful_messages:
        raise ValueError(
            "share payload was parsed, but no useful messages remained after filtering; "
            "try --raw or --include-tools"
        )

    if args.markdown is not None:
        write_markdown(
            args.markdown,
            url=args.url,
            title=title,
            messages=useful_messages,
            stats=stats,
            include_tools=args.include_tools,
            include_redacted=args.include_redacted,
        )
    if args.jsonl is not None:
        write_jsonl(args.jsonl, messages=useful_messages)

    if args.print_summary or (args.markdown is None and args.jsonl is None):
        summary = {
            "url": args.url,
            "title": title,
            "messages_parsed": stats["parsed_messages"],
            "messages_written": stats["written_messages"],
            "redacted_markers": stats["redacted_markers"],
            "filtered_redacted": stats["filtered_redacted"],
            "filtered_tools": stats["filtered_tools"],
            "roles_written": sorted({item["role"] for item in useful_messages}),
        }
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
