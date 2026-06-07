# Roadmap

Date: 2026-06-07

## Status

The migration and multi-host hardening work for `codex-workflows-plugin` is complete and published as `v0.1.0`.

This roadmap captures the next post-release workstream so future changes stay small, explicit, and testable.

## Completed Foundation

- Real Codex plugin packaging is in place.
- Shared policy evaluation is split from host adapters.
- Host adapters exist for Codex, Gemini CLI, Antigravity, and Claude Code.
- Installer targets are host-aware and config-merging is covered by smoke tests.
- Fixture-backed contract tests exist for supported hosts.
- CI and an architecture ADR are in place.

## Next Roadmap

1. Capture real host payloads from live usage.
   - Replace any remaining synthetic assumptions with recorded fixtures.
   - Keep one contract fixture per supported host.
2. Trim legacy heuristics out of the shared runtime.
   - Move host-neutral policy rules into smaller modules where it improves clarity.
   - Keep host-specific behavior inside adapters.
3. Harden release packaging.
   - Make the installer and plugin metadata easier to consume as a versioned release artifact.
   - Preserve idempotent configuration writes.
4. Reassess host coverage only when a real contract exists.
   - Add new adapters only for documented host surfaces.
   - Avoid speculative client support.
5. Cut the next release after a meaningful change lands.
   - Prefer `v0.1.1` for hardening work.
   - Prefer `v0.2.0` for new host or packaging surface area.

## Non-Goals

- Do not add new host adapters without a verified hook/config contract.
- Do not reintroduce model-specific branching in the policy core.
- Do not expand the bundle with unrelated workflows unless they are required by the roadmap.
