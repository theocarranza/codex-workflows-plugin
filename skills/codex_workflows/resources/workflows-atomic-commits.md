---
description: Enforce Conventional Commits and Codex Synchronization. Atomic commits mean small sized, indivisible chunks of work, each representing a meaningful and verifiable change to the repository, grouped by layer or commit type.
---

# Atomic Commits Workflow

Triggers: `/commit`

## Prerequisites
- **Git Protocol**: Adhere to `rules-git-workflow.md`.
- **Codex Sync**: Ensure the active Ledger in `AI_Codex/Tickets/Active/` is up to date with the latest sub-task outcomes.

## Steps

### 1. Discovery & Logical Grouping
Analyze staged (`git diff --cached`) and unstaged (`git diff --stat`) changes.

1.  **Group Units**: Separate changes into logical commits (UI, Core, Tests).
2.  **Atomicity**: If unrelated changes are staged, unstage and commit them sequentially. **Refactoring** MUST be committed separately from behavior changes.

### 2. Validation
- Run `fvm flutter analyze` on the staged changes to ensure stability.

### 3. Commit Message Generation
Format: `<type>(<scope>): <subject>`

- **Types**: `feat`, `fix`, `chore`, `refactor`, `style`, `test`, `docs`.
- **Body**: Explain **WHY** the change was made.
- **Reference**: Link the ticket ID (e.g., `Ref: #1234`).

### 4. Codex Checkpoint
Before final execution, perform a **Mandatory Checkpoint** update to the Codex Ledger:
- Log the commit hash (once generated) and the specific logic finalized in this unit.

### 5. Execute
```bash
git commit -m "<type>(<scope>): <subject>" -m "<body>"
```

## Usage & Invocation Examples

- `/commit`
