---
description: Handles Pull Request code reviews, evaluates feedback, and applies necessary changes based on the Codex Ledger
---

# Pull Request Review Workflow

This workflow provides a structured approach to handling PR code review comments, ensuring that changes align with the original architectural intent logged in the AI_Codex.

## 1. Intake & Context Restoration (Stage I & II)

1.  **Fetch PR Details**: Ask the user for the PR URL or ID.
2.  **Restore Context**: 
    - Identify the original ticket ID associated with the PR.
    - Locate the original Codex Ledger (usually in `AI_Codex/Tickets/Resolved/`).
    - If the Ledger exists, read it to restore the original architectural intent (`### Codex Context`).
3.  **Fetch Threads**: Request the user to provide the raw text of the PR comments, or use the `azure-devops` MCP if configured to fetch PR threads.

## 2. Analysis & Resolution Plan (Stage III)

1.  **Draft Resolution Strategy**: In the original Codex Ledger (or a new Appendix Ledger in `Active/`), create a new section: `### PR Review Resolution`.
2.  **Evaluate Comments**: For each reviewer comment, the agent MUST explicitly decide:
    - **Comply**: Agree with the reviewer and plan the code change.
    - **Decline/Discuss**: Disagree based on architectural rules found in the Codex, and draft a response explaining the rationale.
3.  **Architect Review**: Present the Resolution Strategy to the user. Do NOT proceed with code generation until you receive: **"IMPLEMENTATION APPROVED"**.

## 3. Execution (Stage IV)

1.  **Prepare Repository**: Ensure you are on the correct PR branch and `git pull` the latest changes.
2.  **Sequential Execution**: Apply the approved "Comply" changes file-by-file.
3.  **Static Analysis**: Run `fvm flutter analyze` to ensure new changes don't break existing logic.
4.  **Testing**: Run `fvm flutter test` on the modified modules.

## 4. Handoff & Archival (Stage V)

1.  **Commit**: Run the `/commit` workflow. The commit message MUST reference the PR feedback (e.g., `fix(auth): address PR review comments`).
2.  **Reply Generation**: Draft the responses for the "Decline/Discuss" items so the user can paste them into Azure DevOps.
3.  **Re-Archive Ledger**: Ensure the updated Codex Ledger is saved and remains in (or is moved back to) `AI_Codex/Tickets/Resolved/`.

## Usage & Invocation Examples

- `/review-pr`
- `/review-pr https://dev.azure.com/.../pullrequest/606`

**Architect Tip**: Do not blindly comply with all review comments. Evaluate them against the `AI_Codex/Knowledge/` rules. If a reviewer suggests a pattern that violates a canonical rule, you must push back and draft a technical defense.
