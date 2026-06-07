# AI Codex Workflows Plugin

A workspace automation plugin that registers git and tool hooks, enforces session bootstrapping, and mandates ticket lifecycle folder movements across the AI Codex vault.

## Purpose

To ensure that autonomous agents consistently follow strict repository governance protocols:
1. **Mandatory Session Bootstrap**: Initializing today's session record before editing files.
2. **Commit Pipeline Verification**: Running pre-merge checks (`ensure-can-merge`) before commits/PRs.
3. **Structured Ticket Progression**: Validating and gating ticket status folder transitions, YouTrack moves, and code verification.

---

## 🗂️ Ticket Lifecycle & Status Folders

Tickets are tracked as Markdown files inside the `AI_Codex/Projects/<project_name>/Tickets/` directory and progress through the following states:

1. **`Ready/` (Backlog / Groomed)**
   - Tickets that are groomed and ready for implementation.
   - Status represents that a ticket can be picked up.
2. **`Active/` (In Progress)**
   - When a ticket starts, it is moved from `Ready/` to `Active/` by `/start-ticket`.
   - The ticket YAML frontmatter `status` must be set to `active`.
3. **`Resolved/` (Completed Bugfixes)**
   - If a ticket is a **bugfix**, it is moved from `Active/` to `Resolved/` upon resolution.
   - The ticket YAML frontmatter `status` must be updated to `resolved`.
4. **`Closed/` (Completed Tasks & Features)**
   - If a ticket is a **feature** or standard **task**, it is moved from `Active/` to `Closed/` upon completion.
   - The ticket YAML frontmatter `status` must be updated to `closed`.

---

## ⚙️ Enforced Rules & Hooks

The plugin installs a custom `PreToolUse` hook script (`codex_enforce_hook.py`) that intercepts agent operations:

* **No Destructive Deletions**: Restricts using destructive command-line utilities (like `rm` or `rmdir`) within the Codex vault. Status transitions must always be done via file moves.
* **Markdown Allowlist**: Restricts file modifications only to files specified in the workspace allowlist (e.g. `CLAUDE.md`, `GEMINI.md`, and directories under `.agent/` or the vault).
* **Mandatory Session Bootstrapping**: Blocks all write tools from modifying codebase files unless today's agent session log has been initialized.
* **Ticket Status & Destination Validation**:
  - Blocks starting tickets unless they are moved from `Ready/` to `Active/`.
  - Blocks resolving bugfix tickets if they are not moved to `Resolved/`.
  - Blocks resolving tasks/features if they are not moved to `Closed/`.
  - Restricts direct write operations (`write_to_file`) to ensure task/feature tickets are never written to `Resolved/` and bugfix tickets are never written to `Closed/`.
* **YouTrack State Verification**:
  - Enforces that the corresponding YouTrack card has been updated to 'In Progress' before a ticket can be started (moved or saved to `Active/`).
  - Enforces that the YouTrack card has been updated to 'Done', 'Fixed', or 'Test'/'Testing'/'Resolved' before a ticket can be completed (moved or saved to `Closed/` or `Resolved/`).

---

## 🛠️ Installation & Syncing

To sync rules and install hooks into a project:
1. Ensure the workspace has a `.agent/workflows/` and `.agent/rules/` structure.
2. Execute the install script or run the hook script with the `install` argument:
   ```bash
   python3 skills/codex_workflows/scripts/codex_enforce_hook.py --install
   ```
   This will:
   - Make the hook script executable.
   - Register hook rules in `~/.gemini/config/hooks.json`.
   - Synchronize reference workflows to the project's `.agent/workflows/` directory.
   - Synchronize coding rules to the project's `.agent/rules/` directory.
