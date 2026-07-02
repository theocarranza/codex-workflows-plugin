from __future__ import annotations

import os
import re
from typing import Any, Callable

Handler = Callable[[dict[str, Any], dict[str, Any], str], dict[str, Any]]


def _slug_ticket_id(ticket_id: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ticket_id.strip()).strip("-").lower()
    return slug or "ticket"


def handle_start_ticket(arguments: dict[str, Any], manifest: dict[str, Any], instructions: str) -> dict[str, Any]:
    ticket_id = arguments["ticket_id"]
    vault = os.environ.get("CODEX_VAULT_FOLDER", "AI_Codex")
    slug = _slug_ticket_id(ticket_id)
    return {
        "active_ledger_path": f"{vault}/Tickets/Active/{slug}.md",
        "ticket_id": ticket_id,
        "instructions": instructions,
    }


def handle_review_pr(arguments: dict[str, Any], manifest: dict[str, Any], instructions: str) -> dict[str, Any]:
    return {
        "pr_number": arguments["pr_number"],
        "mode": "instructions",
        "instructions": instructions,
    }


def handle_instruction_only(arguments: dict[str, Any], manifest: dict[str, Any], instructions: str) -> dict[str, Any]:
    return {
        "mode": "instructions",
        "skill": manifest.get("name", ""),
        "inputs": arguments,
        "instructions": instructions,
    }


_HANDLERS: dict[str, Handler] = {
    "start-ticket": handle_start_ticket,
    "review-pr": handle_review_pr,
}


def get_handler(skill_name: str) -> Handler:
    return _HANDLERS.get(skill_name, handle_instruction_only)
