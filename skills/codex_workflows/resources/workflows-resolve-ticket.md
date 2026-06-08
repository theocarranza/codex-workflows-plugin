---
description: Finalize a ticket, distill knowledge into the Codex, archive the Ledger, and move work to Done
---

# Resolve Ticket Workflow

This workflow defines the step-by-step procedure when done with a ticket to ensure code quality, repository synchronization, pull request creation, YouTrack updates, and Codex documentation.

## Phase 1: Local Verification & Quality Gate
1. **Execute Pre-Merge Check**: Run the project's pre-merge check script to ensure code formatting, static analysis, and production build checks are fully passing:
   ```bash
   npm run ensure-can-merge
   ```
2. **Handle Warnings/Failures**: If `ensure-can-merge` fails or reports errors, the workflow MUST stop here. Fix the issues before proceeding.

## Phase 2: Commit, Push & Pull Request Creation
1. **Commit Remaining Changes**: Use Conventional Commits to commit any remaining local changes:
   ```bash
   git add .
   git commit -m "<type>(<scope>): <subject>" -m "<body>"
   ```
2. **Push Branch**: Push the active local branch to the remote repository:
   ```bash
   git push origin <branch_name>
   ```
3. **Create Pull Request**: Create the Pull Request targeting the `unstable` branch on GitHub.

## Phase 3: PR Review & Tracking (Conditional/Optional)
1. **Execute PR Code Review** (Optional, user's discretion): Perform or request a PR review.
2. **Move YouTrack Card**: Skip moving to the "testing" lane for the current effort. We only move the card to testing when code review/qa/testing is actively taking place. For the current effort, we are not using the test lane, move the card straight into done.
3. **Address Comments**:
   - Address PR comments by changing PR thread status to either *resolved* or *wont fix* (or equivalent).
   - If changes are implemented to satisfy comments, repeat **Phase 1 (ensure-can-merge)**, commit, and push.

## Phase 4: Merge & Synchronization
1. **Merge Pull Request**: Once approved, merge the pull request into the `unstable` branch.
2. **Update YouTrack Card**: Move the corresponding YouTrack card straight to "Done" using `youtrack/update_issue`. You must set the `'State'` custom field to `'Done'`, set the `'Timer'` custom field to `'Stop'`, and update the `'Spent time'` custom field (formatted as hours/days/weeks, e.g. `'2h 30m'`).
3. **Update Codex Ledger & Session**:
   - If the ticket is a bugfix, move it from `AI_Codex_SeuMeiSimples/Tickets/Active/` to `AI_Codex_SeuMeiSimples/Tickets/Resolved/`.
   - Otherwise (for feature/task tickets), move it to `AI_Codex_SeuMeiSimples/Tickets/Closed/`.
   - Update the ledger ticket YAML frontmatter `status` to `resolved` (or `closed` as appropriate).
   - Append the `Tasks` and `Walkthrough` sections directly to the ledger ticket, saving both the `task.md` and `walkthrough.md` artifacts contents inside it (under `## Tasks` and `## Walkthrough` respectively).
   - Close the current session file in `Agent_Sessions` and update links.
4. **Sync Local Workspace**: Checkout the local `unstable` branch and pull the latest changes from origin:
   ```bash
   git checkout unstable
   git pull origin unstable
   ```
