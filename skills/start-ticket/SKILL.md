---
name: start-ticket
description: Start a ticket by creating the active ledger, session record, and required specs.
---

# start-ticket

Create or update the active ticket ledger and session record for a new work item.

## Spec generation hook

After activating the ticket, the runtime checks `<vault>/Specs/<ticket-slug>/` for required spec files.

**Given** a ticket to be implemented  
**When** `/start-ticket` is issued  
**If** corresponding spec files are missing  
**Then** initiate `/write-spec` for each missing kind before any code changes.

The orchestrator returns `write_spec_directive` with `missing_kinds` and `source_hints` extracted from the ticket ledger (requirements, description, implementation plan).

Required spec kinds depend on ticket signal:
- **bugfix** → `bugfix-spec`, `adr`
- **feature** → `design-doc`, `tech-spec`
- **task** → `implementation-plan`, `tech-spec`
- **default** → `tech-spec`, `implementation-plan`

Consult `skills/write-spec/SKILL.md` for the Actor-Critic workflow.
