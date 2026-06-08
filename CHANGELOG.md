# Changelog

All notable changes to `codex-workflows-plugin` are documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

_(nothing yet)_

---

## [0.2.1] — 2026-06-08

### Added
- Timer and Spent time verification to the pre-tool Hook (`check_youtrack_state_in_transcript` in `ticket_runtime.py`):
  - Active tickets must have `Timer: "Start"` and `State: "In Progress"`.
  - Finished (Resolved/Closed) tickets must have `Timer: "Stop"`, `State: "Done"` or `"Fixed"`, and a non-empty `Spent time` value.
- Unit/contract tests for Timer and Spent time verification (3 new tests, total of 51 tests).

### Changed
- Bypassed the YouTrack testing lane for the current effort, allowing and expecting finished tickets to move straight to `Done` or `Fixed` (removing `Test`/`Testing`/`Resolved` from allowed finished states in hook validation).
- Updated workflows (`workflows-start-ticket.md`, `workflows-ai-codex-finish-ticket.md`, and `workflows-resolve-ticket.md`) to instruct agents on starting the timer, filling Story points, stopping the timer, logging spent time, and bypassing the testing lane.
- Auto-update block conditional in `hook_runtime.py` corrected to trigger when moving a ticket from `Ready` to `Active` (fixed typo `"Tickets/Active/" not in abs_dst` to `in abs_dst`).

### Fixed
- Workflow cycle execution gap: fixed pre-tool hooks to actively verify YouTrack timer start/stop and spent time logging.

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
