# Codex Workflows Plugin Migration Design

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the current Gemini/Antigravity-flavored workflow bundle into a real Codex plugin with a shared policy core, host-specific adapters, and a client-aware installer that can generate the right integration for Codex and other supported agents.

**Architecture:** Keep policy decisions transport-agnostic. A canonical policy engine will decide allow/deny/actions from normalized tool events, while host adapters translate between Codex/Gemini/other client payloads and the shared event model. Installation should be capability-aware: it can target a specific client, a universal skill location, or all supported clients, but each host gets only the config that host actually understands.

**Tech Stack:** Python for hook/install tooling, Bash for install wrapper, Markdown skills and workflows, Codex plugin manifest/config, pytest or unittest for contract tests, shell-based installer tests, CI.

---

## Problem Statement

The repository currently behaves like a single-host workflow bundle:

- It installs hook config into `~/.gemini/config/hooks.json`.
- It expects obsolete tool names such as `run_command` and `write_to_file`.
- It hard-codes project paths, session naming conventions, and ticket folder rules.
- It packages many unrelated workflow rules into one generic bundle.

That shape is not sustainable if the goal is to support multiple coding clients without duplicating policy logic. The right split is:

1. a shared policy engine,
2. thin host adapters,
3. configurable installation targets,
4. optional profiles for workspace- or domain-specific rules,
5. focused skill bundles rather than one large omnibus bundle.

## Proposed Design

### 1. Plugin Packaging

Create a proper Codex plugin layout:

- `.codex-plugin/plugin.json`
- `hooks/hooks.json`
- `skills/`
- `scripts/`
- optional `assets/`

The plugin manifest should describe the plugin as a reusable workflow and enforcement package, not as a single hard-coded workspace integration. It should only declare fields supported by Codex plugin validation.

### 2. Shared Policy Core

Extract all decision logic into a host-neutral policy layer.

Inputs:

- normalized tool name
- normalized command or file operation
- absolute path
- workspace root
- ticket metadata
- session state
- optional profile selection

Outputs:

- `allow`
- `deny(reason)`
- optional `rewrite` or `warn` actions if a host supports them

This core should not know whether the request came from Codex, Gemini, Claude, or a future client.

### 3. Host Adapters

Implement host adapters as translation layers only.

Codex adapter responsibilities:

- map `Bash` and `apply_patch` events into the canonical policy event
- read `tool_input.command`, path fields, and hook metadata
- emit the correct Codex hook response schema, including `hookSpecificOutput` when the Codex runtime expects it
- preserve Codex-native matcher behavior and event naming

Other adapters should be added as the repository grows:

- Gemini/Antigravity adapter for the existing legacy behavior
- future client adapters only when a real payload contract exists

### 4. Installer And Client Targeting

Installation should be explicit about the target surface:

- `--codex`
- `--gemini`
- `--claude`
- `--universal`
- `--all-agents`
- or an interactive selection flow

The installer should not interpret this as model selection. It is client targeting.

Recommended behavior:

- `--universal` installs only the portable skill/profile assets that can be shared across clients.
- `--all-agents` installs universal assets plus every supported client-specific adapter/config the package knows how to write.
- client-specific targets install only the integration artifacts for that host.

Installation must merge with existing config when possible, not overwrite it blindly.

### 5. Profiles

Move project-specific assumptions into optional profiles:

- generic governance
- Flutter/Dart workspace
- ticket lifecycle enforcement
- repository sync policy

Profiles may configure:

- vault location
- project name
- ticket folder names
- tracker integration
- branch names
- verification commands
- allowed destructive operations, if any, with explicit opt-in

This keeps the core reusable while still supporting workspace-specific conventions.

### 6. Skill Bundling

Split the current omnibus skill into focused skills:

- bootstrap
- start-ticket
- resolve-ticket
- repository-sync
- commit-prep
- automated-tests

Each skill should be small enough to understand and install independently. Shared rules can live in reusable profile or reference files.

## Data Flow

1. Client emits a tool event.
2. Adapter normalizes the event.
3. Policy engine evaluates against the active profile and session state.
4. Adapter converts the decision back into the host-specific response.
5. Installer writes the correct host config and registers the relevant skills or hooks.

## Error Handling

- Invalid or unknown host payloads should fail closed.
- Missing session bootstrap should deny write operations, not warn and continue.
- Unknown profile names should abort installation with a clear message.
- Unsupported client targets should be reported as unsupported, not silently ignored.

## Testing Strategy

Add tests in layers:

- contract tests for Codex payloads and responses
- adapter tests for normalized event translation
- policy tests for path, session, and ticket rules
- installer tests for target selection and config merging
- bypass tests that prove destructive or malformed payloads do not slip through
- CI to run validation, unit tests, and config checks

## Scope Boundary

This design does not yet:

- rewrite the enforcement logic
- add all future client adapters
- split every workflow into its final skill package
- introduce project-specific migration knowledge folders beyond the lean vault
- solve the entire multi-client ecosystem in one pass

The first implementation phase should make Codex a real plugin and move the policy core behind an adapter boundary. Everything else builds on that.

## Success Criteria

- The repository validates as a Codex plugin.
- Codex-specific hook behavior uses Codex-native payloads and response shapes.
- The policy engine can be exercised without any host-specific code.
- The installer can target at least one client and a universal location without hard-coded Gemini assumptions.
- The migration path is documented in the active ledger and can be executed incrementally.
