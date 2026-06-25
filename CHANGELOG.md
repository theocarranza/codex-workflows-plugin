# Changelog

All notable changes to `codex-workflows-plugin` are documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

_(nothing yet)_

---

## [0.3.0] — 2026-06-25

### Added
- **`review-pr` skill** (`skills/review-pr/`): four-phase skill that retrieves Azure DevOps pull request review threads, classifies each comment as comply or reject, presents a structured report for user review, then acts on confirmed decisions — applying code edits for comply items and posting rejection replies for reject items. Thread status is never mutated; only a reply is added. Results are persisted to `AI_Codex/Agent_Reports/YYYY-MM-DD-pr-review-<PR#>.md`.
- **`.mcp.json`**: Azure DevOps MCP server config (`@azure-devops/mcp`, org `bhave-tecnologia-comportamental`) for local development of `review-pr`.

---

## [0.2.8] — 2026-06-23

### Added
- **Claude Code plugin registration** (`scripts/installer/bootstrap.py`): bootstrap now copies the plugin's `skills/` tree into `~/.claude/plugins/cache/local/codex-workflows-plugin/<version>/` and adds a `codex-workflows-plugin@local` entry to `~/.claude/plugins/installed_plugins.json`. The plugin now appears in Claude's plugin manager and all skills are discoverable in any Claude session after restarting. The `installPath` is placed inside the standard Claude cache directory — the same structure used by marketplace plugins — which is required for skills to load.
- `strip_managed_hooks(config, script_names)` in `bootstrap.py`: strips all hook entries whose command references any of this plugin's known hook scripts before re-wiring. Prevents stale entries (e.g. paths from previous temp directories or old install locations) from accumulating across bootstrap runs.

### Fixed
- **Hook deduplication** (`scripts/installer/merge.py`): `deep_merge` previously concatenated hook-group lists unconditionally, causing a new duplicate hook entry to be appended to the target config on every bootstrap run. Hook-group lists (arrays whose elements each contain a `"hooks"` key) are now deduplicated by command string — only the first occurrence of each unique command is kept. Existing configs with accumulated duplicates are cleaned on the next bootstrap run via `strip_managed_hooks`.

---

## [0.2.7] — 2026-06-21

### Added
- Standardized templates for issue/ticket creation (`feature-template.md`, `bug-template.md`, `task-template.md`) under `.agent/workflows/templates/`.
- Workflow guide `workflows-create-issue.md` under `.agent/workflows/` detailing the step-by-step issue creation, YouTrack MCP registration, and local ticket lifecycle file movements.
- Script harness `scripts/create_ticket.py` to scaffold local ticket drafts and generate YouTrack MCP payload.

### Changed
- Refactored `sync_shared_assets(dest_root)` in `scripts/installer/cli.py` to recursively copy subdirectories under `.agent/workflows/` (allowing `templates/` folder to sync to the target project).

---

## [0.2.6] — 2026-06-09

### Added
- `target_global_config_path(target)` in `scripts/installer/targets.py`: returns the machine-global hook config location for each supported host, encoding the knowledge gathered about each host's internals:
  - Claude Code → `~/.claude/settings.json`
  - Gemini CLI → `~/.gemini/settings.json`
  - Codex → `~/.gemini/config/hooks.json` (Codex uses the Gemini CLI config layer)
  - Antigravity → `<ide-install>/.agents/hooks.json` (IDE install dir auto-discovered from `~/Antigravity_IDE/`, `~/antigravity-ide/`, `/opt/…`)
- `bootstrap.py` global install mode: `--dest` is now optional. When omitted, `wire()` writes hooks directly to each host's global config location. No project path knowledge required from the user.

### Changed
- README Step 2 rewritten: primary example wires all agents globally (`--target all-agents` with no `--dest`); project-level wiring documented as Step 2b.
- Global Claude settings (`~/.claude/settings.json`) hook deduplicated and updated to reference `~/.codex-workflows/` instead of the project clone path.

---

## [0.2.5] — 2026-06-09

### Changed
- `bootstrap.py` now accepts `--target` and `--dest` to install and wire in a single command:
  `python3 bootstrap.py plugin.zip --target all-agents --dest /my/project`
- Added `--install-dir` flag to override the default install location (`~/.codex-workflows/`).
- Wire-only mode: if `~/.codex-workflows/` already exists and only `--target`/`--dest` are passed, the install step is skipped.

---

## [0.2.4] — 2026-06-09

### Added
- `scripts/installer/bootstrap.py`: one-time install script that copies the plugin runtime to `~/.codex-workflows/` from either a release zip or the source tree. Running the hook-wiring CLI from that stable location ensures hook commands reference `~/.codex-workflows/` rather than wherever the repo happens to be cloned.
- 10 new tests for `bootstrap.py` (source install, zip install, CLI, pycache exclusion, idempotent replace, and the key property: hook commands generated from the installed location point back to `~/.codex-workflows/`). Total: 85 tests.

### Changed
- README Installation section rewritten as a two-step flow: bootstrap once (Step 1), then wire each project (Step 2). Includes update instructions.

---

## [0.2.3] — 2026-06-09

### Fixed
- **Installer portability**: hook commands are now written as absolute paths to the plugin's own scripts directory, so the hook fires correctly from any `--dest` project regardless of working directory. Previously the relative path `python3 skills/codex_workflows/scripts/<host>_enforce_hook.py` would fail in any project that didn't contain the plugin's `skills/` folder.

---

## [0.2.2] — 2026-06-09

### Added
- Timer and Spent time verification to the pre-tool hook (`check_youtrack_state_in_transcript` in `ticket_runtime.py`):
  - Active tickets must have `Timer: "Start"` and `State: "In Progress"`.
  - Finished (Resolved/Closed) tickets must have `Timer: "Stop"`, `State: "Done"` or `"Fixed"`, and a non-empty `Spent time` value.
- **Git safety enforcement on ticket start** (`scripts/policy/git_utils.py` + `engine.py`):
  - Blocks starting a ticket if another ticket is already active in `Tickets/Active/`.
  - Blocks starting a ticket while checked out on the base integration branch.
  - Base branch is dynamically resolved (checks `origin/HEAD` symref → `remote show origin` → known branch names: `unstable`, `develop`, `main`, `master`).
  - Blocks starting a ticket if the current branch is behind `origin/<base>` (performs a fast `git fetch` with a 2 s timeout before comparing).
  - Blocks starting a ticket if the current branch contains unmerged commits from another local feature/bugfix/techdebt branch.
- 24 new tests covering git safety enforcement (base-branch check, out-of-sync check, unmerged commits check, active-ticket limit); total 75 tests.

### Changed
- Bypassed the YouTrack testing lane, allowing finished tickets to move straight to `Done` or `Fixed` (removing `Test`/`Testing`/`Resolved` from allowed finished states).
- Updated `workflows-start-ticket.md`, `workflows-ai-codex-finish-ticket.md`, and `workflows-resolve-ticket.md` to instruct agents on starting the timer, filling Story points, stopping the timer, logging spent time, and bypassing the testing lane.
- Updated `workflows-git-origin-sync.md` and `rules-git-workflow.md` to reference the dynamically resolved base branch instead of the hardcoded `develop`.
- Auto-update block conditional in `hook_runtime.py` corrected to trigger when moving a ticket from `Ready` to `Active`.

### Fixed
- Workflow cycle execution gap: pre-tool hooks now actively verify YouTrack timer start/stop and spent time logging.

---

## [0.2.0] — 2026-06-07

### Added
- `sync_shared_assets(dest_root)` in `installer/cli.py`: copies `.agent/workflows/*.md` and `.agent/rules/*.md` to the destination project.
- `write_target_config(merged_config, config_path, dest_root)` in `installer/cli.py`: writes merged hook JSON at the correct relative config path.
- `--dest` flag on `scripts.installer.cli`: triggers real filesystem writes (hook config + shared asset sync) when provided.
- `YouTrackCheckResult` dataclass in `ticket_runtime.py`: structured return from transcript scanner with `reason` field (`ok` | `transcript_missing` | `state_not_found`).
- `CHANGELOG.md`.

### Changed
- Session-gate denial messages now use the dynamically resolved vault directory name — no project-specific strings remain in the runtime.
- `check_youtrack_state_in_transcript` returns `YouTrackCheckResult` instead of `bool`; denial messages now include the reason.
- `infer_is_bugfix_ticket` uses frontmatter-only inference — filename heuristic removed.
- README rewritten to reflect current architecture, correct installer CLI, test count, and release instructions.
- `plugin.json` author corrected from `"OpenAI"` to `"agentrick"`.
- `scripts/profiles/base.py` documented as v0.3 scaffolding.

### Fixed
- Portability: project-specific vault name no longer leaks into error messages delivered to other projects.
- Installer gap: `--dest` now delivers what the README promised.
- Bugfix false-positive: `debug-something.md` no longer routed to `Resolved/`.

> **Roadmap for v0.3**: wire `WorkspaceProfile` into `hook_runtime.py` and installer CLI; `--all-agents` target; configurable ticket folder names; GitLab tracker support.

---

## [0.1.1] — 2026-06-07

### Added
- Multi-host adapter hardening: `antigravity`, `claude`, `gemini`, and `codex` adapters now independently parse host-specific payload shapes and format decisions.
- `scripts/installer/` module with `cli.py`, `targets.py`, `merge.py`: non-destructive hook config merging per target host.
- `scripts/profiles/` scaffolding: `WorkspaceProfile` dataclass with `generic`, `flutter`, and `repository` presets (v0.2 wiring planned).
- `scripts/payload_capture.py`: debug payload capture utility gated by `CODEX_WORKFLOW_CAPTURE_DIR` env var.
- `scripts/release_packager.py`: versioned zip release builder.
- Contract test suite: 33 automated tests across adapters, policy engine, ticket runtime, profiles, and installer.

### Changed
- Refactored ticket lifecycle helpers into dedicated `scripts/ticket_runtime.py` module.
- `YouTrackCheckResult` dataclass replaces bare `bool` return from transcript scanner — callers now receive a structured reason (`ok` | `transcript_missing` | `state_not_found`).
- `infer_is_bugfix_ticket` uses frontmatter-only inference — filename heuristic removed to prevent false positives on files like `debug-something.md`.
- Session-gate denial messages now use the dynamically resolved vault directory name instead of the hard-coded `AI_Codex_SeuMeiSimples`.
- Installer `install()` gains `dest_root` parameter; when provided, writes hook config and syncs `.agent/workflows/` and `.agent/rules/` to the target project.
- Installer CLI gains `--dest` flag for real filesystem writes (existing `--output` flag retained for dry-run single-file output).
- `.codex-plugin/plugin.json` author corrected from `"OpenAI"` to `"agentrick"`.

### Fixed
- Portability bug: project-specific vault name no longer appears in error messages emitted to other projects.
- Installer promise gap: `--dest` now actually syncs workflows and writes the host config file as documented in the README.
- YouTrack denial messages now include diagnostic context (transcript missing vs. state not recorded).

---

## [0.1.0] — 2026-05-30

### Added
- Initial release of `codex-workflows-plugin`.
- `PreToolUse` hook enforcing session bootstrapping, destructive-deletion guard, markdown allowlist, and ticket lifecycle path validation (`Ready → Active → Closed/Resolved`).
- YouTrack state gating: blocks ticket moves/writes unless the corresponding card has been moved to the expected state in the conversation transcript.
- `hooks/hooks.json` for Codex host wiring.
- `.agent/workflows/` with 11 workflow markdown guides (start-ticket, resolve-ticket, atomic-commits, automated-tests, feature-implementation, git-origin-sync, jules-async, review-pr, tdd-bug-fix, ai-codex-finish-ticket, nano-banana).
- `.agent/rules/` with 27 coding and governance rule files.
- Plugin self-governance: the plugin's own `AI_Codex/` vault follows the conventions it enforces.
