---
name: draw-io
description: "Create, edit, and review diagrams.net (draw.io) files. Use for .drawio XML edits, layout/coordinate adjustments, exporting .drawio to PNG/SVG/PDF, and AWS icon lookups (mxgraph.aws4.*)."
---

# Draw.io (diagrams.net)

## Rules

- Edit only `.drawio` files (XML).
- Do not manually edit generated preview images such as `*.drawio.png`.
- Prefer small, targeted edits; keep diagram style consistent.

## Quick Tasks

### Export PNG previews

Use the bundled script:

```bash
bash ~/.codex/skills/draw-io/scripts/convert-drawio-to-png.sh path/to/diagram.drawio
```

Internal command (draw.io Desktop CLI):

```bash
drawio -x -f png -s 2 -t -o output.drawio.png input.drawio --no-sandbox
```

Notes:
- On some servers/IDEs, `ELECTRON_RUN_AS_NODE=1` may be set globally, which breaks draw.io export flags.
  The script unsets it for you.
- On headless servers, export requires an X display. The script will reuse `$DISPLAY` if valid, otherwise it
  will try `xvfb-run`, then fall back to a temporary `Xvnc` display if available.
- This repo's global guidelines prefer not to auto-stage files; the script does not run `git add`.

### Find AWS icons

```bash
python ~/.codex/skills/draw-io/scripts/find_aws_icon.py ec2
```

If you need more results or official names, inspect:
- `references/aws-icons.md`

## Editing Guidance (XML)

### Fonts

If you need a consistent font across the diagram, set `defaultFontFamily` in `mxGraphModel`:

```xml
<mxGraphModel defaultFontFamily="Noto Sans JP" ...>
```

If specific text nodes render inconsistently, set `fontFamily` explicitly in the element style:

```xml
style="text;html=1;fontSize=27;fontFamily=Noto Sans JP;"
```

### Layout / Coordinates

Workflow:

1. Open the `.drawio` XML.
2. Find the relevant `mxCell` (often by searching `value=` for a label).
3. Adjust `mxGeometry` (`x`, `y`, `width`, `height`).
4. Export a PNG and visually verify alignment.

Tips:
- Center Y = `y + height/2` (useful for vertical alignment across elements).
- Keep arrows behind foreground boxes/labels by ordering edges earlier in the XML (back layer).

## Attribution

Adapted from the Claude Code templates draw.io skill (MIT): `davila7/claude-code-templates`.
