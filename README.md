# Codex Global Config (Portable)

Reusable global instructions, current skills, and a sanitized configuration template for moving Codex preferences between machines.

Last synchronized: **2026-09-08**.

## Included

- `.codex/AGENTS.md`: current collaboration, execution, scientific-work, storage, and verification principles. Machine-specific hosts, proxy ports, account paths, and quota observations are generalized for this public copy.
- `.codex/config.template.toml`: current model/reasoning, execution, UI, feature, memory, MCP, and plugin-enablement preferences. The snapshot uses `gpt-6-astra` with `high` reasoning and leaves context limits to Codex defaults.
- `.codex/skills/`: the current local skill files, helper scripts, references, assets, and licenses. Skills removed from the local installation are removed from this snapshot too; earlier versions remain in Git history.
- `.codex/skills/.system/`: snapshots of the installed system skills, including local adjustments. These are available for reference or deliberate restoration; normal setup below preserves the receiving installation's system skills.

The skills directory is the authoritative inventory. Plugin-managed skill packages are installed through Codex and are not duplicated into this bundle.

## Excluded

Authentication and OAuth credentials, real API keys, live `config.toml`, project trust paths, proxy endpoints, local marketplace paths, command-approval rules, UI onboarding state, conversations, history, memory contents, databases, logs, caches, backups, and plugin runtime files are excluded. Project-specific instructions remain in their project repositories.

Memory and plugin preferences in the template describe settings only. They do not transfer memory contents, plugin installations, or account connections.

## Local Setup

Clone the repository and review the instructions and configuration before copying them. From the repository root:

```bash
# Set this to the Codex home used by the target installation.
codex_target_dir="${CODEX_HOME:-$HOME/.codex}"
mkdir -p "$codex_target_dir/skills"

cp .codex/AGENTS.md "$codex_target_dir/AGENTS.md"
cp .codex/config.template.toml "$codex_target_dir/config.template.toml"
rsync -a --exclude='.system/' .codex/skills/ "$codex_target_dir/skills/"
```

For a new installation, use the template as the starting configuration:

```bash
cp "$codex_target_dir/config.template.toml" "$codex_target_dir/config.toml"
```

For an existing installation, merge the desired settings into its current `config.toml`. Keep machine-specific trust entries, proxies, marketplace paths, and authentication local. Model availability, experimental features, and plugin identifiers depend on the installed Codex version and account; install and connect the desired plugins separately.

The template records full filesystem access and no interactive approvals as current preferences. Review those settings for the target environment before using the template.

The skill copy does not delete destination-only skills. When updating an existing installation, review old skill folders separately so retired workflows do not remain active accidentally. Restore a system skill from `.system/` only when that version or local adjustment is intended; Codex updates can replace system-skill files.

## Updating This Repository

Refresh the instructions and skill snapshot from the active Codex home, remove snapshot entries for skills that are no longer installed, and update the sanitized template and synchronization date. Keep the public copy portable: generalize host-specific facts, retain explicit example credentials only, preserve licenses, and exclude runtime files. Review the scoped diff and parse the TOML template before committing.
