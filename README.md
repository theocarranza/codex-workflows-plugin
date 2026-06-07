# AI Codex Workflows Plugin

A portable, multi-host workspace automation plugin that enforces session bootstrapping, ticket lifecycle governance, and YouTrack state gating across agent-driven development workflows.

> **v0.2.0** — Fully portable. The installer now writes hook configs and syncs workflow/rules assets to target projects in a single command. No project-specific names are hard-coded anywhere in the runtime.

## Purpose

To ensure that autonomous agents consistently follow strict repository governance protocols:
1. **Mandatory Session Bootstrap**: Blocks all codebase writes until today's session record is initialized in the vault.
2. **Structured Ticket Progression**: Validates and gates ticket folder transitions (`Ready -> Active -> Closed/Resolved`), enforcing YouTrack state synchronization at each step.
3. **Destructive-Op Guard**: Prevents `rm`/`rmdir` against the Codex vault — status transitions must always be expressed as file moves.

## Architecture

```
scripts/
├── hook_runtime.py       # Entry point — orchestrates all policy checks
├── ticket_runtime.py     # Path extraction, YouTrack transcript scanner, bugfix inference
├── policy/               # Pure policy engine (engine.py + events.py) — no I/O
├── adapters/             # 4 host adapters: codex, gemini, claude, antigravity
├── installer/            # Multi-target hook wiring (cli.py, targets.py, merge.py)
└── profiles/             # Workspace profiles (v0.2 scaffolding — not yet wired into runtime)
skills/                   # 7 skill folders consumed by agent hosts
.agent/workflows/         # 11 workflow guides synced to target projects on install
.agent/rules/             # 27 coding & governance rule files synced to target projects
```

## Packaging Boundary

- Plugin metadata: `.codex-plugin/plugin.json`
- Codex host wiring: `hooks/hooks.json`
- Shared skill bundles: `skills/`
- Release packager: `scripts/release_packager.py` emits `dist/codex-workflows-plugin-<version>.zip`

---

## Ticket Lifecycle & Status Folders

Tickets live in `<vault>/Tickets/` and progress through four states:

| Folder | Status | Transition |
|---|---|---|
| `Ready/` | Groomed, pickable | — |
| `Active/` | In progress | `/start-ticket` moves from `Ready/` |
| `Closed/` | Feature/task complete | Moved from `Active/` on completion |
| `Resolved/` | Bugfix complete | Moved from `Active/` on resolution |

**Bugfix detection** reads `type: bug` or `type: bugfix` from YAML frontmatter exclusively. Filename heuristics are intentionally excluded to avoid false positives (e.g. `debug-something.md`).

---

## Enforced Rules & Hooks

The plugin installs a `PreToolUse` / `BeforeTool` hook that intercepts every agent tool call:

* **No Destructive Deletions**: `rm`/`rmdir` against vault paths are denied.
* **Markdown Allowlist**: Only `CLAUDE.md`, `GEMINI.md`, `.agent/`, and the vault may be written.
* **Mandatory Session Bootstrapping**: Write tools are blocked until `<vault>/Agent_Sessions/YYYY-MM-DD*.md` exists (with `next: null` frontmatter). Error messages include the actual vault directory name — no project names are hard-coded.
* **Ticket Destination Validation**: Wrong folder for the ticket type is denied with a specific reason message.
* **YouTrack State Verification**: Scans the JSONL conversation transcript for a completed `call_mcp_tool(youtrack/update_issue)` call. Denial messages distinguish between:
  - `transcript_missing` — transcript path was absent from the hook payload
  - `state_not_found` — transcript present but the required state was not recorded

---

## Installation

Run from the plugin's repository root, pointing `--dest` at your target project:

```bash
# Antigravity: writes .agents/hooks.json + syncs .agent/workflows/ and .agent/rules/
python3 -m scripts.installer.cli --target antigravity --dest /path/to/your/project

# Gemini: writes .gemini/settings.json + syncs shared assets
python3 -m scripts.installer.cli --target gemini --dest /path/to/your/project

# Claude: writes .claude/settings.json + syncs shared assets
python3 -m scripts.installer.cli --target claude --dest /path/to/your/project

# Codex: writes hooks/hooks.json + syncs shared assets
python3 -m scripts.installer.cli --target codex --dest /path/to/your/project

# Dry-run: print merged config without writing anything
python3 -m scripts.installer.cli --target gemini --output /tmp/preview.json
```

### Host Targets

| Target | Config Path | Hook Event |
|---|---|---|
| `codex` | `hooks/hooks.json` | `PreToolUse` |
| `gemini` | `.gemini/settings.json` | `BeforeTool` |
| `antigravity` | `.agents/hooks.json` | `PreToolUse` |
| `claude` | `.claude/settings.json` | `PreToolUse` |
| `universal` | _(shared assets only)_ | — |

All targets also sync `.agent/workflows/*.md` and `.agent/rules/*.md` into the destination project. Existing hook configs are merged non-destructively.

---

## Tests

```bash
python3 -m unittest discover -s test -p "test_*.py" -v
```

**48 tests**, all passing. Coverage spans: policy engine, all 4 host adapters, ticket runtime (path extraction, YouTrack transcript scanning with all 3 result reasons, bugfix frontmatter inference), installer (dry-run and live `--dest` write), profiles, and release packager.

---

## Release

```bash
python3 -m scripts.release_packager --output-dir dist/
```

Emits `dist/codex-workflows-plugin-<version>.zip`. Version is read from `.codex-plugin/plugin.json`. The archive includes plugin metadata, hooks, skills, scripts, and docs — `__pycache__` and test directories are excluded.

See [CHANGELOG.md](./CHANGELOG.md) for full version history.
