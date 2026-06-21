---
description: Standard workflow for creating and registering issues/tickets in the AI Codex vault and YouTrack
---

# Workflow: Create Issue/Ticket

This workflow standardizes the creation and lifecycle tracking of tasks, features, and bugs. By integrating a local markdown-based draft system with the YouTrack MCP server, it ensures that all issues are fully documented locally and synchronized in the issue tracker.

## Prerequisites
- The agent or operator must have identified the goal or bug that requires tracking.
- The `youtrack` MCP server must be active in the environment.

---

## 🚀 Step-by-Step Execution

### 1. Scaffold Local Ticket Draft
Run the helper script `scripts/create_ticket.py` from the project root with the issue details. This will parse your options, copy the matching template, create a local draft markdown file, and output the YouTrack registration command.

```bash
python3 scripts/create_ticket.py \
  --summary "Redesign the card on tax invoice receipt detail page" \
  --type feature \
  --area "ui, routing" \
  --story-points 3 \
  --status ready \
  --desc "Improve visual compliance with Material 3 guidelines and add action buttons."
```

Parameters:
- `--summary` (Required): The issue title.
- `--type` (Optional): `feature` | `bug` | `task` | `user-story` (default: `task`).
- `--area` (Optional): Comma-separated area names (default: `general`).
- `--story-points` (Optional): Integer estimate points.
- `--status` (Optional): `ready` (places file under `Tickets/Ready/`) | `backlog` (places file under `Tickets/Backlog/`).
- `--desc` (Optional): High-level description of the issue.

### 2. Register Issue in YouTrack
Execute the exact MCP `youtrack/create_issue` tool call printed by the script in Step 1.
For example:

```json
{
  "ServerName": "youtrack",
  "ToolName": "create_issue",
  "Arguments": {
    "project": "SEUMEI",
    "summary": "Redesign the card on tax invoice receipt detail page",
    "description": "See ticket details in local AI_Codex: Tickets/Ready/draft-redesign-the-card-on-tax-invoice-receipt-detail-page.md",
    "customFields": {
      "Type": "Feature",
      "State": "Ready",
      "Story points": 3
    }
  }
}
```

### 3. Finalize Local Ticket Path & Content
Once the YouTrack MCP tool returns the new YouTrack ID (e.g., `SEUMEI-572`):
1. **Update ID in File**: Open the newly created draft file and change `youtrack: DRAFT` in the frontmatter to `youtrack: SEUMEI-572`.
2. **Rename File**: Rename the file to prepend the YouTrack ID and use kebab-case:
   ```bash
   git mv AI_Codex_SeuMeiSimples/Tickets/Ready/draft-redesign-the-card-on-tax-invoice-receipt-detail-page.md \
          AI_Codex_SeuMeiSimples/Tickets/Ready/SEUMEI-572-redesign-the-card-on-tax-invoice-receipt-detail-page.md
   ```

---

## 📋 Ticket Lifecycle & Event Rules

The AI Codex policy engine enforces the following rules for each issue event:

### 1. On Create (Backlog / Ready)
- **Path**: Saved under `Tickets/Backlog/` (for later triage) or `Tickets/Ready/` (if groomed and ready to start).
- **Frontmatter Status**: `backlog` or `ready`.
- **YouTrack State**: `Open` (for backlog) or `Ready` (for ready).
- **Timer Status**: Unstarted / Off.
- **Constraints**: Creating a ticket in these directories is allowed at any time, even without an active development session.

### 2. On Update (Start / Activate)
- **Path**: Moved from `Ready/` to `Tickets/Active/`.
- **Frontmatter Status**: `active`.
- **YouTrack State**: Must be moved to `In Progress` with `Timer: Start` using the `youtrack/update_issue` MCP tool.
- **Constraints**:
  - Only one ticket can be active at any given time.
  - Checked out branch must NOT be the base integration branch (e.g. `unstable` or `develop`).
  - Checked out branch must be fully synced with its remote counterpart (no commits behind base).
  - No unmerged commits from other local feature/bugfix branches can be present.
  - Today's Agent Session log must be initialized.

### 3. On Complete (Close / Resolve)
- **Path**:
  - Features/Tasks: Moved to `Tickets/Closed/`.
  - Bugs/Bugfixes: Moved to `Tickets/Resolved/`.
- **Frontmatter Status**: `closed` or `resolved`.
- **YouTrack State**: Must be moved to `Done` or `Fixed`, with `Timer: Stop`, and a recorded `Spent time` value.
- **Constraints**:
  - Standard features/tasks cannot go to `Resolved/` and bugs cannot go to `Closed/`.
  - Verification plan must be executed and all automated tests passed.
