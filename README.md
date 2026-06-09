# AI Codex Workflows Plugin

A portable, multi-host workspace automation plugin that enforces session bootstrapping, ticket lifecycle governance, YouTrack state gating, and git safety checks across agent-driven development workflows.

> **v0.2.4** — Enforces YouTrack timer start/stop, spent time logging, git safety on ticket start, and bypasses the testing lane straight to Done/Fixed. No project-specific names are hard-coded anywhere in the runtime.

## Purpose

To ensure that autonomous agents consistently follow strict repository governance protocols:
1. **Mandatory Session Bootstrap**: Blocks all codebase writes until today's session record is initialized in the vault.
2. **Structured Ticket Progression**: Validates and gates ticket folder transitions (`Ready -> Active -> Closed/Resolved`), enforcing YouTrack state synchronization at each step.
3. **Git Safety on Ticket Start**: Before activating a ticket, enforces that no other ticket is already active, the branch is not the base integration branch, the branch is synced with `origin/<base>`, and no unmerged commits from other feature branches are present.
4. **Destructive-Op Guard**: Prevents `rm`/`rmdir` against the Codex vault — status transitions must always be expressed as file moves.

## Architecture

```
scripts/
├── hook_runtime.py       # Entry point — orchestrates all policy checks
├── ticket_runtime.py     # Path extraction, YouTrack transcript scanner, bugfix inference
├── policy/               # Pure policy engine (engine.py, events.py, git_utils.py) — no I/O
├── adapters/             # 4 host adapters: codex, gemini, claude, antigravity
├── installer/            # Multi-target hook wiring (cli.py, targets.py, merge.py)
└── profiles/             # Workspace profiles (v0.3 scaffolding — not yet wired into runtime)
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
* **Git Safety on Ticket Start**: When moving a ticket from `Ready/` to `Active/` (or writing a new file into `Active/`), the hook enforces:
  - No other ticket is already active in `Tickets/Active/`
  - Current branch is not the base integration branch (dynamically resolved — checks `origin/HEAD`, `remote show origin`, and known branch names in order)
  - Branch is not behind `origin/<base>` (fetches with a 2 s timeout before checking)
  - Branch contains no unmerged commits from another local feature/bugfix/techdebt branch
* **YouTrack State Verification**: Scans the JSONL conversation transcript for a completed `call_mcp_tool(youtrack/update_issue)` call. Enforces that: (a) starting tickets requires `State: In Progress` and `Timer: Start`, (b) resolving/closing tickets requires `State: Done/Fixed` (bypassing the testing lane), `Timer: Stop`, and a recorded `Spent time` value. Denial messages distinguish between:
  - `transcript_missing` — transcript path was absent from the hook payload
  - `state_not_found` — transcript present but the required state/fields were not recorded correctly

---

## Installation

### Prerequisites

- Python 3.11+
- Git (required for git safety checks at ticket-start time)
- The **target project** must be a git repository

### Step 1 — Bootstrap the plugin (one-time, per machine)

Download the [latest release zip](https://github.com/theocarranza/codex-workflows-plugin/releases/latest) and run the bootstrap script to install the plugin to `~/.codex-workflows/`:

```bash
python3 bootstrap.py codex-workflows-plugin-0.2.3.zip
```

Or, if you prefer to work from a clone:

```bash
git clone https://github.com/theocarranza/codex-workflows-plugin.git
cd codex-workflows-plugin
python3 -m scripts.installer.bootstrap
```

No additional Python dependencies are needed — the plugin uses only the standard library.

### Step 2 — Wire your agent host(s)

Run the installer **from the installed location**, pointing `--dest` at your target project:

```bash
# Claude Code
python3 ~/.codex-workflows/scripts/installer/cli.py --target claude --dest /path/to/your/project

# Codex
python3 ~/.codex-workflows/scripts/installer/cli.py --target codex --dest /path/to/your/project

# Gemini CLI
python3 ~/.codex-workflows/scripts/installer/cli.py --target gemini --dest /path/to/your/project

# Antigravity
python3 ~/.codex-workflows/scripts/installer/cli.py --target antigravity --dest /path/to/your/project

# All supported hosts at once
python3 ~/.codex-workflows/scripts/installer/cli.py --target all-agents --dest /path/to/your/project
```

Running from `~/.codex-workflows/` ensures hook commands in the written config files point back to the installed location — not the repo. This makes the setup portable across projects and independent of where or whether the repo is cloned.

### What Gets Installed in Your Project

For every `--dest` install:

1. **Writes or merges the hook config** into the host-specific file — existing hooks are preserved non-destructively.
2. **Syncs `.agent/workflows/*.md`** — workflow guides the agent loads as context.
3. **Syncs `.agent/rules/*.md`** — coding and governance rule files.

### Host Target Reference

| Target | Config written | Hook event |
|---|---|---|
| `claude` | `.claude/settings.json` | `PreToolUse` |
| `codex` | `hooks/hooks.json` | `PreToolUse` |
| `gemini` | `.gemini/settings.json` | `BeforeTool` |
| `antigravity` | `.agents/hooks.json` | `PreToolUse` |
| `all-agents` | all four above | — |
| `universal` | _(shared assets only — no hook config)_ | — |

### Dry-run

Preview the merged hook config without writing any files:

```bash
python3 ~/.codex-workflows/scripts/installer/cli.py --target claude --output /tmp/preview.json
```

### Updating the plugin

Re-run the bootstrap script with the new zip to replace `~/.codex-workflows/`, then re-run the wiring step for each project:

```bash
python3 bootstrap.py codex-workflows-plugin-<new-version>.zip
python3 ~/.codex-workflows/scripts/installer/cli.py --target all-agents --dest /path/to/your/project
```

---

## Tests

```bash
python3 -m unittest discover -s test -p "test_*.py" -v
```

**75 tests**, all passing. Coverage spans: policy engine (including git safety checks), all 4 host adapters, ticket runtime (path extraction, YouTrack transcript scanning with all 3 result reasons, timer/spent time verification, bugfix frontmatter inference), installer (dry-run and live `--dest` write), profiles, and release packager.

---

## Release

```bash
python3 -m scripts.release_packager --output-dir dist/
```

Emits `dist/codex-workflows-plugin-<version>.zip`. Version is read from `.codex-plugin/plugin.json`. The archive includes plugin metadata, hooks, skills, scripts, and docs — `__pycache__` and test directories are excluded.

See [CHANGELOG.md](./CHANGELOG.md) for full version history.
