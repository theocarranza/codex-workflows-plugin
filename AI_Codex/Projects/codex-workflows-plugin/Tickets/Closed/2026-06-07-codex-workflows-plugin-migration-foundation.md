---
timestamp: 2026-06-07T08:36:39-03:00
project: codex-workflows-plugin
branch: master
status: closed
type: task
tags: [codex-workflows-plugin, migration, plugin, model-agnostic]
---

# Codex Workflows Plugin Migration Foundation

## Goal

Establish the repository-local Codex ledger that will govern the migration to a real Codex plugin and a model-agnostic, client-adaptive architecture.

## Current Findings

- The repository currently behaves like a Gemini/Antigravity hook bundle rather than a valid Codex plugin.
- The model-agnostic direction should be implemented as client adapters plus a shared policy engine, not as model branching inside the policy layer.
- The first migration milestone is to formalize the vault, then drive the plugin conversion from an active ledger.

## Scope Boundary

- Do not implement plugin migration code yet.
- Do not split the bundle into new skills yet.
- Do not create project-wide knowledge folders until the migration needs them.

## Codex Context

- [AI_Codex root index](../../../../README.md)
- [codex-workflows-plugin README](../../../../../README.md)

## Next Steps

1. Review the migration design brief in `docs/superpowers/specs/2026-06-07-codex-workflows-plugin-migration-design.md`.
2. Review the implementation plan in `docs/superpowers/plans/2026-06-07-codex-workflows-plugin-migration.md`.
3. Break the migration into implementation tasks after the plan execution mode is selected.

## Design Brief

- The plugin should become a real Codex plugin with `.codex-plugin/plugin.json` and Codex-native hooks.
- The enforcement logic should be split into a shared policy core plus host adapters.
- Installation should be client-targeted, not model-targeted.
- Optional profiles should hold workspace-specific paths, ticket rules, and verification commands.
- The existing workflow bundle should be split into smaller focused skills.

## Dependency Tree

1. Codex plugin packaging and manifest correctness
2. Codex adapter and canonical tool-event normalization
3. Shared policy engine
4. Installer targeting and config merging
5. Optional profiles
6. Skill splitting
7. Contract tests and CI

## Plan Reference

- [Implementation plan](../../../../../docs/superpowers/plans/2026-06-07-codex-workflows-plugin-migration.md)

## Task 1 Outcome

- Added `.codex-plugin/plugin.json` with Codex-valid plugin metadata.
- Added `hooks/hooks.json` for bundled Codex hook routing.
- Updated the repository README and skill docs to describe the packaging boundary.
- Added manifest smoke tests to `test_plugin.py`.
- Restored the `Ready -> non-Active` deny guard in `skills/codex_workflows/scripts/codex_enforce_hook.py` while preserving the YouTrack auto-update side effect already introduced in the working tree.

## Deviations

- The existing hook script modification was incomplete when task execution began; the deny path had to be restored to keep the current contract tests valid.

## Task 2 Outcome

- Added a shared policy package under `scripts/policy/` with `CanonicalToolEvent`, `PolicyDecision`, and a reusable `evaluate()` function.
- Added contract tests in `test/contract/test_policy_engine.py` for destructive commands, markdown allowlist behavior, session gating, and ticket path validation.
- Refactored `skills/codex_workflows/scripts/codex_enforce_hook.py` to delegate generic policy checks to the shared core while leaving YouTrack transcript validation in the hook for now.
- Confirmed the full Python test suite and plugin validation pass after the extraction.

## Deviations

- YouTrack-specific transcript validation stays in the hook until the Codex adapter is fully split from the policy core.

## Task 3 Outcome

- Added `scripts/adapters/codex_adapter.py` to translate Codex payloads into canonical events and format responses with `hookSpecificOutput`.
- Modified `skills/codex_workflows/scripts/codex_enforce_hook.py` to consume the adapter for payload parsing and response emission.
- Added contract tests in `test/contract/test_codex_adapter.py` for parsing and response formatting.
- Confirmed the full Python test suite and plugin validation pass after adapter integration.

## Deviations

- The adapter currently preserves the legacy top-level `permissionDecision` field for compatibility while also emitting `hookSpecificOutput` for the Codex-native path.

## Task 4 Outcome

- Added `scripts/installer/targets.py`, `scripts/installer/merge.py`, and `scripts/installer/cli.py` to support client-target selection and hook config merging.
- Updated `skills/codex_workflows/scripts/install_codex_hooks.sh` to delegate to the installer CLI and accept a target/profile.
- Added installer contract tests in `test/installer/test_installer_targets.py` for universal, codex, and merge behavior.
- Confirmed the full Python test suite and plugin validation pass after installer integration.

## Deviations

- The installer currently writes merged config for the selected target but still defaults to the repository-local Codex hooks path for Codex-compatible targets; broader multi-client file layouts will come with the profile expansion work.

## Task 5 Outcome

- Added profile modules under `scripts/profiles/` for generic, flutter, and repository presets.
- Added focused skill manifests for `bootstrap`, `start-ticket`, `resolve-ticket`, `repository-sync`, `commit-prep`, and `automated-tests`.
- Updated the repository README and the Codex workflows skill to describe the split.
- Added profile contract tests in `test/contract/test_profiles.py`.
- Confirmed the full Python test suite and plugin validation pass after the profile and skill split.

## Deviations

- The focused skills are currently instruction-only manifests; they are the packaging boundary for the migration, not yet fully behavior-rich workflows.

## Task 6 Outcome

- Added `test/contract/test_bypass_cases.py` to prove malformed hook payloads fail closed.
- Added `.github/workflows/ci.yml` to run plugin validation and the Python test suite on push and pull request.
- Tightened the hook parse-error path so malformed JSON payloads are denied with a structured adapter response.
- Confirmed the full Python test suite and plugin validation pass with 34 tests total.

## Deviations

- CI currently validates the repository through Python unittest and the plugin validator; broader target-specific installer smoke tests can be added once the profile matrix expands.

## Task 6 Complete

- The malformed-payload bypass test is in place and the hook now fails closed on invalid JSON.
- CI is wired to run plugin validation and the Python test suite on push and pull request.
- The migration foundation is complete at the repository level and is ready for any follow-up review, packaging, or archive step.

## Host Target Follow-up

- Added explicit Gemini CLI and Antigravity hook adapters.
- Added target-specific installer paths for Codex, Gemini, and Antigravity.
- Updated the installer wrapper and docs to match the official host config locations.
- Verified the full Python test suite now passes with 40 tests total, and plugin validation still passes.

## Claude Host Support

- Added a Claude Code adapter and wrapper that reuse the shared policy core.
- Added a Claude installer target that writes `.claude/settings.json`.
- Updated the installer wrapper and docs to include Claude in the supported target matrix.
- Verified the full Python test suite now passes with 43 tests total, plugin validation still passes, and the Claude wrapper smoke test returns `{"decision": "allow"}` for a valid payload.

## Runtime Extraction

- Extracted the shared hook decision flow into `scripts/hook_runtime.py`.
- Collapsed `skills/codex_workflows/scripts/codex_enforce_hook.py` into a thin entrypoint that delegates to the shared runtime.
- Added a runtime dispatch contract test for Codex, Gemini, Antigravity, and Claude adapter selection.
- Verified the full Python test suite now passes with 44 tests total, plugin validation still passes, and direct wrapper smoke tests returned allow decisions for Codex, Gemini, Antigravity, and Claude.

## Fixture And Smoke Hardening

- Added fixture-backed payload tests for Codex, Gemini, Antigravity, and Claude.
- Added installer smoke tests that write actual target config files in temporary workspaces and verify their contents.
- Cleaned generated `__pycache__` directories from the worktree.
- Added the host adapter architecture ADR at `docs/adr/2026-06-07-host-adapter-architecture.md`.
- Verified the full Python test suite now passes with 48 tests total, plugin validation still passes, and the installer smoke tests succeed for all supported host targets.

## Closure

- The plugin migration and host-hardening work is complete and ready for release/tagging.
