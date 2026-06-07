---
description: Specialized workflow for delegating large or complex tasks to Jules
---

# Workflow: Jules Asynchronous Task Delegation

This workflow is used to offload heavy implementation, refactoring, or testing tasks to the Jules MCP server.

## 1. Task Assessment (Phase I)

1.  **Analyze Scope**: Evaluate the task's complexity and scope (Rule 1: Delegation Criteria).
2.  **Select Worker Role**: Determine the best role (`MAESTRO`, `CREW`, `FREELANCER`, `EVALUATOR`) for the task.
3.  **Prepare Task Description**: Create a high-signal prompt for the Jules worker.
    - **Required**: Repo Source (`sources/github/owner/repo`), Title, and detailed Task Description.

## 2. Initialization & Branching (Phase II)

1.  **Source Discovery**:
    - **Tool**: `jules_list_sources`
    - **Action**: Verify the repository is available to Jules.
2.  **Create Branch**:
    - **Tool**: `jules_create_branch`
    - **Action**: Create a new branch for the task (e.g., `feature/jules-refactor-auth`).
3.  **Spawn Worker**:
    - **Tool**: `jules_create_worker`
    - **Action**: Send the task to Jules.
    - **Capture**: Store the `session_id` for monitoring.

## 3. Monitoring & Coordination (Phase III)

1.  **Status Checks**:
    - **Tool**: `jules_get_status`
    - **Interval**: Check every 2-5 minutes or upon user inquiry.
2.  **Shared Memory (Optional)**:
    - **Tool**: `jules_store_memory`
    - **Action**: Pass any dynamic context (e.g., discovered API changes) to the worker.
3.  **User Notification**: Update the user on the worker's progress: "Jules (CREW) is currently implementing the Domain layer. Session: XXX-YYY".

## 4. Review & Integration (Phase IV)

1.  **Completion Verification**:
    - **Tool**: `jules_get_status`
    - **Condition**: Status == "COMPLETED"
2.  **Code Review**:
    - **Tool**: `jules_review_code`
    - **Action**: Run a final automated check on the changes.
3.  **Merging**:
    - **Tool**: `jules_merge_branch`
    - **Action**: Integrate the approved changes into the target branch.

## Usage & Invocation Examples

To trigger an asynchronous task, use the following commands:

- **Refactoring**: `/jules-async "Refactor the authentication layer to use clean architecture"`
- **Bug Fix**: `/jules-fix "Memory leak in the dashboard scroll listener"`
- **Review**: `/jules-review "Review the latest changes in the infrastructure layer"`

**Architect Tip**: Use Jules for tasks that can run in parallel while you (the main agent) focus on time-sensitive UI tweaks or requirements refinement.
