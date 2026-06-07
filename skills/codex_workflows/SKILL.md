---
name: codex_workflows
description: "Manage, enforce, and execute AI Codex workflows (Start Ticket, Resolve Ticket, etc.) and git/session hooks for standard development compliance."
---

# Codex Workflows Skill

This skill provides a standardized way to define, install, and execute development workflows based on the AI Codex architecture. It packages git/session hooks, local session bootstrap enforcement, and standardized workflow checklists.

## Purpose

To ensure that autonomous agents consistently follow strict repository governance protocols:
1. **Mandatory Session Bootstrap**: Initializing today's session record before editing files.
2. **Commit Pipeline Verification**: Running pre-merge checks (`ensure-can-merge`) before commits/PRs.
3. **Structured Ticket Progression**: Gating ticket status moves, YouTrack transitions, and code verification.

## Workflows Included

The following workflows are bundled in the skill's `resources/` folder:
- **`workflows-start-ticket.md`**: Initializing a ticket, setting up a branch, and creating the Codex Ledger.
- **`workflows-ai-codex-finish-ticket.md`**: Resolving a ticket (verifying code quality, push, PR review, YouTrack updating, merging, and syncing unstable).
- **`workflows-resolve-ticket.md`**: Standard reference for ticket completion and archival.
- **`workflows-atomic-commits.md`**: Guidelines for clean Conventional Commits.
- **`workflows-tdd-bug-fix.md`**: Red-Green bug fixing steps.
- **`workflows-git-origin-sync.md`**: Keeping branches in sync with upstream.

## Hooks Installed

The skill contains pre-tool git/session execution hooks:
- **`codex_enforce_hook.py`**: Intercepts tool calls to prevent destructive deletions in the vault, enforce markdown read/write allowlists, and enforce session bootstrapping prior to code modification.

## Sync Command / Usage

To install or sync these workflows into a project's `.agent/workflows/` directory:
1. Copy the markdown templates from this skill's `resources/` directory to the target project's `.agent/workflows/` directory.
2. Run the `scripts/install_codex_hooks.sh` script to set up the PreToolUse hook configuration in the system `hooks.json`.
