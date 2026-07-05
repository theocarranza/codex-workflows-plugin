"""Resolve-ticket pre-archive hook.

Returns a structured directive when specs or the resolution report are missing.
"""

from __future__ import annotations

from typing import Any

from scripts.resolution_runtime import ResolutionPlan


def on_resolve_ticket(plan: ResolutionPlan) -> dict[str, Any] | None:
    if plan.specs_missing:
        return {
            "hook": "resolve-ticket-specs",
            "action": "invoke-write-spec",
            "ticket_id": plan.ticket_id,
            "specs_dir": plan.specs_dir,
            "message": (
                f"Ticket {plan.ticket_id} has no specs under {plan.specs_dir}. "
                "Run /write-spec before /resolve-ticket."
            ),
        }

    if plan.resolution_required:
        return {
            "hook": "resolve-ticket-report",
            "action": "invoke-resolve-report",
            "ticket_id": plan.ticket_id,
            "resolution_report_path": plan.resolution_report_path,
            "spec_files": list(plan.spec_files),
            "source_hints": plan.source_hints,
            "message": (
                f"Ticket {plan.ticket_id} needs a resolution report at {plan.resolution_report_path} "
                "before archival. Draft via Actor-Critic, then persist when the Critic is clean."
            ),
        }

    return None
