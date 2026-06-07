# Changelog

All notable changes to `codex-workflows-plugin` are documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased] — v0.2.0-dev

### Planned
- Wire `WorkspaceProfile` from `scripts/profiles/` into `hook_runtime.py` and installer CLI so a single `--profile` flag controls all runtime behaviour.
- Installer `--all-agents` target: install for all supported hosts in one pass.
- Configurable ticket folder names (currently hard-coded as `Ready/Active/Closed/Resolved`).
- Support for GitLab issue tracker alongside YouTrack.

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
