# Roadmap

Date: 2026-06-07

## Status

The migration, hardening, payload-capture, and release-packaging work for `codex-workflows-plugin` is complete and published as `v0.1.1`.

This roadmap captured the post-release hardening workstream and is now closed.

## Completed Foundation

- Real Codex plugin packaging is in place.
- Shared policy evaluation is split from host adapters.
- Host adapters exist for Codex, Gemini CLI, Antigravity, and Claude Code.
- Installer targets are host-aware and config-merging is covered by smoke tests.
- Fixture-backed contract tests exist for supported hosts.
- CI and an architecture ADR are in place.

## Completed Roadmap

1. Capture real host payloads from live usage.
   - Added an opt-in payload capture path in `scripts/payload_capture.py`.
   - The hook runtime now records live payloads when `CODEX_WORKFLOW_CAPTURE_DIR` is set.
2. Trim legacy heuristics out of the shared runtime.
   - Extracted ticket parsing and YouTrack lookup helpers into `scripts/ticket_runtime.py`.
   - `scripts/hook_runtime.py` now focuses on orchestration.
3. Harden release packaging.
   - Added `scripts/release_packager.py` to build a versioned zip archive from the plugin layout.
   - The release archive includes a machine-readable `release-manifest.json`.
4. Reassess host coverage only when a real contract exists.
   - Host coverage remains limited to documented surfaces already in the repo.
   - No speculative adapters were added.
5. Cut the next release after a meaningful change lands.
   - Bumped the plugin version to `0.1.1`.
   - The follow-up release can be published from the packaged artifact.

## Non-Goals

- Do not add new host adapters without a verified hook/config contract.
- Do not reintroduce model-specific branching in the policy core.
- Do not expand the bundle with unrelated workflows unless they are required by the roadmap.
