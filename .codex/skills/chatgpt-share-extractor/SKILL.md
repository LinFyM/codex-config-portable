---
name: chatgpt-share-extractor
description: Extract and archive transcripts from public ChatGPT share links. Use when Codex is given a chatgpt.com/share URL and needs to recover the visible conversation text, summarize it, convert it to Markdown/JSONL, or preserve a raw transcript; especially useful when ordinary web.open only shows the login shell.
---

# ChatGPT Share Extractor

## Quick Start

Use the bundled script first:

```bash
python3 ~/.codex/skills/chatgpt-share-extractor/scripts/extract_chatgpt_share.py \
  "https://chatgpt.com/share/SHARE_ID" \
  --markdown /path/to/transcript.md \
  --jsonl /path/to/transcript.jsonl
```

The script uses only the Python standard library. It fetches the share HTML,
extracts the embedded React Router stream chunks, rebuilds the compact
`linear_conversation` message list, and writes the visible text messages.

Default output is a clean transcript: it keeps user/assistant messages and
filters tool-role noise plus redacted placeholders such as
`The output of this plugin was redacted.` For audit-grade full exports, add
`--raw`; to selectively preserve tool messages or redacted placeholders, use
`--include-tools` or `--include-redacted`.

## Workflow

1. Fetch the share URL with a browser-like `User-Agent`.
2. If normal page text is empty or shows a login shell, parse embedded stream
   data rather than relying on rendered DOM.
3. Extract calls matching `streamController.enqueue("...")`.
4. Decode the string chunks, parse the first JSON array before any later
   `P...:` promise lines, then locate `linear_conversation`.
5. Reconstruct each node shallowly by resolving `_123` keys and integer value
   references against the array.
6. Filter non-useful tool/redaction messages by default, then preserve each
   useful message with its linear index, role, content type, and raw text.

## Limits

- Tool/plugin outputs in shared conversations may be intentionally redacted by
  ChatGPT as `The output of this plugin was redacted.` The default clean export
  filters those markers because they cannot recover the hidden content.
- If a share page changes its serialization format, inspect the HTML for new
  stream/bootstrap variables and update the script rather than hand-parsing a
  long transcript.
- Do not paste long raw transcripts into the final chat response. Save them to
  a file and summarize the location and counts.

## Output Guidance

- Prefer Markdown for human reading and JSONL for later processing.
- In Markdown, keep raw message text inside fenced blocks so formatting is not
  accidentally interpreted.
- Record the source URL, page title when available, extraction timestamp,
  parsed-message count, written-message count, and filtered-message counts.
