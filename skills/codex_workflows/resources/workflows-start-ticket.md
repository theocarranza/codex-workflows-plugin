---
description: Automates the intake and initialization of a task using the Research Mandate and Codex Ledger
---

# Start Ticket Workflow

This workflow integrates Azure DevOps MCP with the Antigravity "Construction" Protocol, forcing a documentation-first discovery phase via the AI_Codex.

## 1. Intake & Requirement Clarity (Stage I)

1.  **Fetch Work Item**: Ask the user for the Azure DevOps Work Item ID.
2.  **Retrieve Data**: Use the `azure-devops` MCP to fetch the work item details.
    - **Tool**: `mcp_azure_devops_wit_get_work_item`
3.  **Clarity Check**: Analyze requirements. If clarity < 0.8, **Pause and Query**.
4.  **Status Update**: Move the YouTrack card to "In Progress" using `call_mcp_tool` with `youtrack/update_issue`. You must set the `'State'` custom field to `'In Progress'` and set the `'Timer'` custom field to `'Start'`. Also verify or set the `'Story points'` custom field (estimation field, integer) as appropriate.

## 2. Knowledge Discovery (The Research Mandate)

1.  **Read Map of Content**: Read `AI_Codex/README.md` to identify relevant architectural areas (Infrastructure, Patterns, Protocols).
2.  **Semantic Search**: Search `AI_Codex/Architecture/` and `AI_Codex/Features/` for keywords found in the ticket description.
3.  **Identify Anchors**: Select at least one ADR or Technical Note to serve as the architectural anchor for this task.

## 3. Strategy & Implementation Lock (Stage II)

1.  **Create Codex Ledger**: Move the ledger ticket file from `AI_Codex/Projects/<project_name>/Tickets/Ready/` (where tickets reside when they are ready to be picked for implementation) to `AI_Codex/Projects/<project_name>/Tickets/Active/`.
    - **Path**: `AI_Codex/Projects/<project_name>/Tickets/Active/<ID>-<Kebab-Case-Title>.md`
    - **Status**: Update the YAML frontmatter `status` of the ticket to `active`.
2.  **Branch Creation**: `{feature, bugfix, refactor, test}/{ticket number}-{ticket-name}`.
3.  **Prepare Repository**: `git checkout develop && git pull origin develop`.
4.  **Construct Implementation Plan**: 
    - Construct the plan directly in the **Codex Ledger** file.
    - **Mandatory Content**: 
        - `### Codex Context`: List the anchors identified in Section 2.
        - `### Scope Boundary`: What is NOT being built.
        - `### Dependency Tree`: Order of operations.
    - **Architect Review**: Present the Codex link to the user for approval (Rule 8).

## 4. Logic & Task Breakdown (Stage III)

1.  **Task Listing**: Append a discrete, serial task list to the Codex Ledger.
2.  **Shadow Context**: This Codex file now serves as your "Shadow Context" State Machine.

## 5. Execution (Stage IV)

1.  **Serial Execution**: Adhere to **Rule 14 (Mandatory Checkpoints)**.
2.  **Sync**: After each task, update the Codex Ledger with technical outcomes and deviations.

## 6. Verification & PR (Stage V)

1.  **Integrated Review**: Verify fulfillment against the Ledger's criteria.
2.  **Finalize Ledger**: Append final considerations and technical debt notes.
3.  **Transition**: Inform the user that the ticket is ready for `/resolve-ticket`.

## Usage & Invocation Examples

- `/start-ticket 12345`

**Architect Tip**: You are documentation-driven. If the Codex search yields no results, perform a broader search in the codebase before assuming no standards exist. Additionally, the Codex Ledger is your permanent memory; if you crash or restart, read the file in `AI_Codex/Tickets/Active/` to instantly regain context.
