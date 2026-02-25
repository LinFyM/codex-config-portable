# Codex Global Config (Portable)

This repo stores reusable Codex global instructions and custom skills so they can be shared across machines (server and local laptop).

## Included

- `.codex/AGENTS.md`
- `.codex/config.template.toml` (sanitized template)
- `.codex/skills/` custom/reusable skills:
  - `artifact-manager`
  - `draw-io`
  - `git-autopilot`
  - `gpu-preflight`
  - `longrun-orchestrator`
  - `memory-flush`
  - `memory-recall`
  - `project-alignment`
  - `workspace-cleanup`

## Not Included (intentionally)

- Auth/session/cache files, for example:
  - `.codex/auth.json`
  - `.codex/.credentials.json`
  - `.codex/history.jsonl`
  - `.codex/sessions/`
  - `.codex/archived_sessions/`
  - `.codex/models_cache.json`

## Local Setup

1. Clone this repository on your local machine.
2. Copy files to your local Codex home:

```bash
mkdir -p ~/.codex
rsync -a .codex/ ~/.codex/
```

3. Use template config as a starting point:

```bash
cp ~/.codex/config.template.toml ~/.codex/config.toml
```

4. Edit local-only fields in `~/.codex/config.toml`:
   - model/review settings
   - proxy settings (if needed)
   - local project trust paths
   - local MCP endpoints (if different)

## Notes

- `AGENTS.md` may contain server-specific policies (for example GPU node naming). Keep or override them based on your local environment.
- Keep secrets out of git. Never commit tokens, credentials, or private keys.
