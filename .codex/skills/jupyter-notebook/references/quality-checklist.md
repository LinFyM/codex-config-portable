# Quality Checklist

Before delivering a notebook:

- Validate edited cells and their dependencies. Run top-to-bottom for a new notebook or execution-state changes within the authorized resource budget; prose/formatting edits do not justify expensive training, paid calls, or external writes.
- Ensure early cells set all required state; avoid hidden state from prior runs.
- Keep outputs tidy. Avoid giant outputs when a short summary works.
- Prefer small tables, key metrics, or short printouts.
- Keep the narrative skimmable. Use headings and short bullets, and avoid long paragraphs.
- Leave helpful TODOs only when necessary, and label them clearly.
- If execution is not possible, call out the risk and how to validate locally.
