"""Start-ticket spec generation hook.

Invoked by the start-ticket orchestrator handler when a ticket is activated.
Returns a structured directive for the agent to run write-spec when specs are missing.
"""

from __future__ import annotations

from typing import Any

from scripts.spec_runtime import SpecPlan


def on_start_ticket(spec_plan: SpecPlan) -> dict[str, Any] | None:
    if not spec_plan.generation_required:
        return None
    return {
        "hook": "start-ticket-spec",
        "action": "invoke-write-spec",
        "ticket_id": spec_plan.ticket_id,
        "specs_dir": spec_plan.specs_dir,
        "missing_kinds": list(spec_plan.missing_kinds),
        "source_hints": spec_plan.source_hints,
        "message": (
            f"Ticket {spec_plan.ticket_id} has no spec coverage under {spec_plan.specs_dir}. "
            f"Generate: {', '.join(spec_plan.missing_kinds)} via /write-spec before coding."
        ),
    }
