---
name: "doc"
description: "Use when the task involves reading, creating, or editing `.docx` documents, especially when formatting or layout fidelity matters; prefer `python-docx` plus the bundled `scripts/render_docx.py` for visual checks."
---


# DOCX Skill

## When to use
- Read or review DOCX content where layout matters (tables, diagrams, pagination).
- Create or edit DOCX files with professional formatting.
- Validate visual layout before delivery.

## Workflow
1. Prefer visual review (layout, tables, diagrams).
   - If `soffice` and `pdftoppm` are available, convert DOCX -> PDF -> PNGs.
   - Or use `scripts/render_docx.py` (requires `pdf2image` and Poppler).
   - Use an available renderer or an appropriate authorized local installation. If rendering remains unavailable, complete structural/content checks and report the specific unverified layout scope.
2. Use `python-docx` for edits and structured creation (headings, styles, tables, lists).
3. After layout changes, render and inspect affected pages. Inspect the full final render for a new document or global style/pagination changes.
4. If visual review is not possible, extract text with `python-docx` as a fallback and call out layout risk.
5. Remove task-owned intermediate files after verification and delivery unless needed for a requested revision or the user asked to retain them.

## Temp and output conventions
- Use `tmp/docs/` for intermediate files; delete when done.
- Write final artifacts under `output/doc/` when working in this repo.
- Keep filenames stable and descriptive.

## Dependencies (install if missing)
Prefer `uv` for dependency management.

Python packages:
```
uv pip install python-docx pdf2image
```
If `uv` is unavailable:
```
python3 -m pip install python-docx pdf2image
```
System tools (for rendering):
```
# macOS (Homebrew)
brew install libreoffice poppler

# Ubuntu/Debian
sudo apt-get install -y libreoffice poppler-utils
```

If installation isn't possible in this environment, tell the user which dependency is missing and how to install it locally.

## Environment
No required environment variables.

## Rendering commands
DOCX -> PDF:
```
soffice -env:UserInstallation=file:///tmp/lo_profile_$$ --headless --convert-to pdf --outdir $OUTDIR $INPUT_DOCX
```

PDF -> PNGs:
```
pdftoppm -png $OUTDIR/$BASENAME.pdf $OUTDIR/$BASENAME
```

Bundled helper:
```
python3 scripts/render_docx.py /path/to/file.docx --output_dir /tmp/docx_pages
```

## Quality expectations
- Deliver a client-ready document: consistent typography, spacing, margins, and clear hierarchy.
- Avoid formatting defects: clipped/overlapping text, broken tables, unreadable characters, or default-template styling.
- Charts, tables, and visuals must be legible in rendered pages with correct alignment.
- Use fonts that render the requested language and punctuation correctly; replace unsupported glyphs only when observed.
- Citations and references must be human-readable; never leave tool tokens or placeholder strings.

## Final checks
- Inspect affected pages in the final render; inspect every page for a new document or global style/pagination changes. If rendering is unavailable, report the unverified scope.
- Fix observed spacing, alignment, or pagination issues and recheck affected pages. Stop repeating checks once the relevant checks pass.
- Confirm there are no leftovers (temp files, duplicate renders) unless the user asks to keep them.
