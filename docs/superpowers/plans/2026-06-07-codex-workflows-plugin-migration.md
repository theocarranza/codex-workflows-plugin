# Codex Workflows Plugin Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the current Gemini/Antigravity-flavored workflow bundle into a real Codex plugin with a shared policy core, host-specific adapters, and a client-aware installer that can generate the right integration for Codex and other supported agents.

**Architecture:** Keep policy decisions transport-agnostic. A canonical policy engine will decide allow/deny/actions from normalized tool events, while host adapters translate between Codex/Gemini/other client payloads and the shared event model. Installation should be capability-aware: it can target a specific client, a universal skill location, or all supported clients, but each host gets only the config that host actually understands.

**Tech Stack:** Python for hook/install tooling, Bash for install wrapper, Markdown skills and workflows, Codex plugin manifest/config, `unittest`/pytest-style contract tests, shell-based installer tests, CI.

---

## File Map

- Create: `AI_Codex/Projects/codex-workflows-plugin/Tickets/Active/2026-06-07-codex-workflows-plugin-migration-foundation.md`
- Modify: `skills/codex_workflows/scripts/codex_enforce_hook.py`
- Modify: `skills/codex_workflows/scripts/install_codex_hooks.sh`
- Modify: `skills/codex_workflows/SKILL.md`
- Modify: `README.md`
- Create: `.codex-plugin/plugin.json`
- Create: `hooks/hooks.json`
- Create: `hooks/` support files as needed for Codex-native hook wiring
- Create: `scripts/policy/` shared policy modules
- Create: `scripts/adapters/` host adapters
- Create: `scripts/installer/` client-aware installer helpers
- Create: `scripts/profiles/` optional profile loaders and defaults
- Create: `skills/bootstrap/SKILL.md`
- Create: `skills/start-ticket/SKILL.md`
- Create: `skills/resolve-ticket/SKILL.md`
- Create: `skills/repository-sync/SKILL.md`
- Create: `skills/commit-prep/SKILL.md`
- Create: `skills/automated-tests/SKILL.md`
- Create: `test/contract/` adapter and policy tests
- Create: `test/installer/` installer and config merge tests
- Create: `.github/workflows/ci.yml`

---

### Task 1: Codex plugin packaging

**Files:**
- Create: `.codex-plugin/plugin.json`
- Create: `hooks/hooks.json`
- Modify: `README.md`
- Modify: `skills/codex_workflows/SKILL.md`
- Modify: `AI_Codex/Projects/codex-workflows-plugin/Tickets/Active/2026-06-07-codex-workflows-plugin-migration-foundation.md`

- [ ] **Step 1: Write the failing validation test**

```python
def test_plugin_manifest_matches_codex_contract():
    assert Path(".codex-plugin/plugin.json").exists()
    manifest = json.loads(Path(".codex-plugin/plugin.json").read_text())
    assert manifest["name"] == "codex-workflows-plugin"
    assert "skills" in manifest
    assert "hooks" not in manifest
```

- [ ] **Step 2: Run validation to confirm the current repo fails the Codex plugin contract**

Run:

```bash
python3 /home/agentrick/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py .
```

Expected: FAIL with missing `.codex-plugin/plugin.json`.

- [ ] **Step 3: Add the minimal plugin manifest and Codex hook config**

```json
{
  "name": "codex-workflows-plugin",
  "version": "0.1.0",
  "description": "Client-adaptive workflow and enforcement plugin for Codex-style agent hosts",
  "author": {
    "name": "OpenAI"
  },
  "skills": "./skills/",
  "interface": {
    "displayName": "Codex Workflows",
    "shortDescription": "Workflow enforcement and session governance",
    "longDescription": "A client-adaptive plugin for workflow enforcement, session bootstrapping, and ticket lifecycle coordination.",
    "developerName": "OpenAI",
    "category": "Productivity",
    "capabilities": ["Interactive", "Write"],
    "defaultPrompt": ["Manage sessions and workflows"],
    "brandColor": "#3B82F6",
    "composerIcon": "./assets/icon.png",
    "logo": "./assets/logo.png",
    "screenshots": []
  }
}
```

- [ ] **Step 4: Re-run validation and confirm the manifest passes**

Run:

```bash
python3 /home/agentrick/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py .
```

Expected: PASS.

- [ ] **Step 5: Commit the packaging baseline**

```bash
git add .codex-plugin/plugin.json hooks/hooks.json README.md skills/codex_workflows/SKILL.md AI_Codex/Projects/codex-workflows-plugin/Tickets/Active/2026-06-07-codex-workflows-plugin-migration-foundation.md
git commit -m "feat(plugin): add codex plugin packaging baseline"
```

### Task 2: Shared policy core

**Files:**
- Create: `scripts/policy/events.py`
- Create: `scripts/policy/engine.py`
- Create: `scripts/policy/session_state.py`
- Create: `scripts/policy/ticket_state.py`
- Create: `test/contract/test_policy_engine.py`
- Modify: `skills/codex_workflows/scripts/codex_enforce_hook.py`

- [ ] **Step 1: Write failing policy tests for canonical events**

```python
def test_policy_denies_rm_inside_vault():
    event = CanonicalToolEvent(
        client="codex",
        tool_name="Bash",
        command="rm -rf AI_Codex",
        path=None,
        workspace_root="/tmp/project",
    )
    decision = evaluate(event, profile=GenericProfile())
    assert decision.is_denied()
```

- [ ] **Step 2: Run the tests and verify they fail before the core exists**

Run:

```bash
python3 -m unittest test.contract.test_policy_engine
```

Expected: FAIL because the policy engine module does not exist yet.

- [ ] **Step 3: Implement the canonical event model and policy engine**

```python
@dataclass(frozen=True)
class CanonicalToolEvent:
    client: str
    tool_name: str
    command: str | None
    path: str | None
    workspace_root: str
```

```python
def evaluate(event: CanonicalToolEvent, profile: Profile) -> PolicyDecision:
    if event.tool_name == "Bash" and event.command and "rm " in event.command:
        return PolicyDecision.deny("Destructive deletions are forbidden")
    return PolicyDecision.allow()
```

- [ ] **Step 4: Re-run the policy tests and confirm they pass**

Run:

```bash
python3 -m unittest test.contract.test_policy_engine
```

Expected: PASS.

- [ ] **Step 5: Commit the core extraction**

```bash
git add scripts/policy test/contract/test_policy_engine.py skills/codex_workflows/scripts/codex_enforce_hook.py
git commit -m "refactor(policy): extract shared enforcement core"
```

### Task 3: Codex adapter

**Files:**
- Create: `scripts/adapters/codex_adapter.py`
- Create: `test/contract/test_codex_adapter.py`
- Modify: `skills/codex_workflows/scripts/codex_enforce_hook.py`

- [ ] **Step 1: Write failing adapter tests for Codex event translation**

```python
def test_codex_bash_event_translates_to_canonical_event():
    payload = {"tool_name": "Bash", "tool_input": {"command": "rm -rf AI_Codex"}}
    event = parse_codex_event(payload)
    assert event.tool_name == "Bash"
```

- [ ] **Step 2: Run the tests and verify the adapter does not yet exist**

Run:

```bash
python3 -m unittest test.contract.test_codex_adapter
```

Expected: FAIL.

- [ ] **Step 3: Implement Codex payload parsing and response formatting**

```python
def parse_codex_event(payload: dict[str, Any]) -> CanonicalToolEvent:
    return CanonicalToolEvent(
        client="codex",
        tool_name=payload.get("name", ""),
        command=(payload.get("arguments") or payload.get("tool_input") or {}).get("command"),
        path=(payload.get("arguments") or payload.get("tool_input") or {}).get("AbsolutePath"),
        workspace_root=os.getcwd(),
    )

def format_codex_decision(decision: PolicyDecision) -> dict[str, Any]:
    return {"permissionDecision": "deny" if decision.is_denied() else "allow", "reason": decision.reason}
```

- [ ] **Step 4: Re-run the adapter tests and confirm they pass**

Run:

```bash
python3 -m unittest test.contract.test_codex_adapter
```

Expected: PASS.

- [ ] **Step 5: Commit the adapter layer**

```bash
git add scripts/adapters test/contract/test_codex_adapter.py skills/codex_workflows/scripts/codex_enforce_hook.py
git commit -m "feat(codex): add codex host adapter"
```

### Task 4: Client-aware installer

**Files:**
- Create: `scripts/installer/cli.py`
- Create: `scripts/installer/merge.py`
- Create: `scripts/installer/targets.py`
- Modify: `skills/codex_workflows/scripts/install_codex_hooks.sh`
- Create: `test/installer/test_installer_targets.py`

- [ ] **Step 1: Write failing tests for target selection and config merging**

```python
def test_universal_target_installs_shared_assets_only():
    result = install(target="universal")
    assert result.written_codex_config is False
```

- [ ] **Step 2: Run the installer tests and verify they fail**

Run:

```bash
python3 -m unittest test.installer.test_installer_targets
```

Expected: FAIL.

- [ ] **Step 3: Implement target-specific installation and merge behavior**

```python
def install(target: Target, profile: Profile) -> InstallResult:
    if target == Target.UNIVERSAL:
        return InstallResult(written_codex_config=False, written_shared_assets=True)
    return InstallResult(written_codex_config=True, written_shared_assets=True)
```

- [ ] **Step 4: Re-run the installer tests and confirm they pass**

Run:

```bash
python3 -m unittest test.installer.test_installer_targets
```

Expected: PASS.

- [ ] **Step 5: Commit installer support**

```bash
git add scripts/installer skills/codex_workflows/scripts/install_codex_hooks.sh test/installer/test_installer_targets.py
git commit -m "feat(install): add client-aware installation targets"
```

### Task 5: Profiles and focused skills

**Files:**
- Create: `scripts/profiles/base.py`
- Create: `scripts/profiles/generic.py`
- Create: `scripts/profiles/flutter.py`
- Create: `scripts/profiles/repository.py`
- Create: `skills/bootstrap/SKILL.md`
- Create: `skills/start-ticket/SKILL.md`
- Create: `skills/resolve-ticket/SKILL.md`
- Create: `skills/repository-sync/SKILL.md`
- Create: `skills/commit-prep/SKILL.md`
- Create: `skills/automated-tests/SKILL.md`
- Modify: `skills/codex_workflows/SKILL.md`
- Modify: `README.md`

- [ ] **Step 1: Write failing tests for profile loading and skill discovery**

```python
def test_generic_profile_resolves_workspace_paths():
    profile = load_profile("generic")
    assert profile.vault_name == "AI_Codex"
    assert profile.ticket_root.endswith("Tickets")
```

- [ ] **Step 2: Run the profile and skill tests and verify they fail**

Run:

```bash
python3 -m unittest test.contract.test_profiles
```

Expected: FAIL.

- [ ] **Step 3: Add the profile models and the focused skill manifests**

```yaml
---
name: bootstrap
description: Initialize a repository-local AI Codex session and ledger.
policy:
  allow_implicit_invocation: true
---
```

- [ ] **Step 4: Re-run the tests and confirm they pass**

Run:

```bash
python3 -m unittest test.contract.test_profiles
```

Expected: PASS.

- [ ] **Step 5: Commit the profile and skill split**

```bash
git add scripts/profiles skills/bootstrap skills/start-ticket skills/resolve-ticket skills/repository-sync skills/commit-prep skills/automated-tests README.md skills/codex_workflows/SKILL.md
git commit -m "feat(skills): split workflow bundle into focused skills"
```

### Task 6: Contract tests, bypass tests, and CI

**Files:**
- Create: `test/contract/test_bypass_cases.py`
- Create: `test/contract/test_manifest_validation.py`
- Create: `.github/workflows/ci.yml`
- Modify: `README.md`

- [ ] **Step 1: Write failing bypass and manifest tests**

```python
def test_destructive_rm_is_denied_for_codex_payloads():
    response = run_hook({"tool_name": "Bash", "tool_input": {"command": "rm -rf AI_Codex"}})
    assert response["permissionDecision"] == "deny"
```

- [ ] **Step 2: Run the tests and confirm the existing implementation fails at least one contract**

Run:

```bash
python3 -m unittest test.contract.test_bypass_cases test.contract.test_manifest_validation
```

Expected: FAIL until the adapter and policy changes are complete.

- [ ] **Step 3: Add CI to run validation, unit tests, and config checks**

```yaml
name: ci
on:
  push:
  pull_request:
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: python3 -m unittest
```

- [ ] **Step 4: Re-run the tests and confirm they pass**

Run:

```bash
python3 -m unittest
```

Expected: PASS.

- [ ] **Step 5: Commit the quality gate**

```bash
git add test .github/workflows/ci.yml README.md
git commit -m "test(ci): add contract coverage and ci workflow"
```

## Self-Review

### Spec coverage

- Plugin packaging is covered by Task 1.
- Shared policy core is covered by Task 2.
- Codex adapter work is covered by Task 3.
- Client-aware installation is covered by Task 4.
- Profiles and focused skills are covered by Task 5.
- Contract tests and CI are covered by Task 6.

### Placeholder scan

- No TODO/TBD placeholders remain.
- All code-changing steps include concrete snippets or exact commands.

### Type consistency

- The plan uses `CanonicalToolEvent`, `PolicyDecision`, `Profile`, `Target`, and `InstallResult` consistently.
- File names are scoped to one responsibility per task.

## Execution Notes

- Keep the existing unrelated modification in `skills/codex_workflows/scripts/codex_enforce_hook.py` intact unless the migration work must touch it.
- Update the active ledger after each completed task with outcomes, deviations, and any adapter-specific gotchas.
- Prefer small commits after each task rather than one large migration commit.
