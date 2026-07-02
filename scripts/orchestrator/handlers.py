from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Callable

Handler = Callable[[dict[str, Any], dict[str, Any], str], dict[str, Any]]


def _slug_ticket_id(ticket_id: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ticket_id.strip()).strip("-").lower()
    return slug or "ticket"


def _project_root() -> Path | None:
    for key in ("CODEX_PROJECT_ROOT", "CURSOR_PROJECT_DIR", "CLAUDE_PROJECT_DIR"):
        value = os.environ.get(key, "").strip()
        if value:
            return Path(value)
    return None


def handle_start_ticket(arguments: dict[str, Any], manifest: dict[str, Any], instructions: str) -> dict[str, Any]:
    ticket_id = arguments["ticket_id"]
    vault = os.environ.get("CODEX_VAULT_FOLDER", "AI_Codex")
    slug = _slug_ticket_id(ticket_id)
    rel_path = f"{vault}/Tickets/Active/{slug}.md"
    created = False

    root = _project_root()
    if root is not None:
        ledger_path = root / rel_path
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        if not ledger_path.exists():
            ledger_path.write_text(
                f"---\ntype: ticket\nticket: {ticket_id}\n---\n\n# Ticket {ticket_id}\n",
                encoding="utf-8",
            )
            created = True

    return {
        "active_ledger_path": rel_path,
        "ticket_id": ticket_id,
        "created": created,
        "mode": "completed" if created else "instructions",
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
