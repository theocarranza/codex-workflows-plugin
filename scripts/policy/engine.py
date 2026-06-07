from __future__ import annotations

from .events import CanonicalToolEvent, PolicyDecision


def evaluate(event: CanonicalToolEvent) -> PolicyDecision:
    if _is_destructive_command(event):
        return PolicyDecision.deny(
            "Destructive deletions (rm) are forbidden on the AI Codex vault. Use 'mv' to change status."
        )

    if _is_markdown_denied(event):
        filename = (event.file_path or "").rsplit("/", 1)[-1]
        return PolicyDecision.deny(
            f"Read/write of {filename} blocked. Markdown files not in CLAUDE.md allowlist are forbidden."
        )

    ticket_decision = _evaluate_ticket_paths(event)
    if ticket_decision.is_denied():
        return ticket_decision

    if _requires_session(event) and not event.session_active and not _is_ticket_path(event):
        return PolicyDecision.deny(
            "Write blocked. You must initialize today's Agent Session log in AI_Codex_SeuMeiSimples/Agent_Sessions/ before making code modifications."
        )

    return PolicyDecision.allow()


def _is_destructive_command(event: CanonicalToolEvent) -> bool:
    command = (event.command or "").strip()
    if not command:
        return False
    vault_markers = {
        event.vault_dir,
        event.vault_dir.rsplit("/", 1)[-1] if event.vault_dir else "",
        "AI_Codex",
    }
    if any(marker and marker in command for marker in vault_markers):
        return "rm " in command or "rmdir " in command
    return False


def _is_markdown_denied(event: CanonicalToolEvent) -> bool:
    return bool(event.file_path and event.file_path.endswith(".md") and not event.markdown_allowed)


def _requires_session(event: CanonicalToolEvent) -> bool:
    return event.tool_name in {"write_to_file", "replace_file_content", "multi_replace_file_content"}


def _evaluate_ticket_paths(event: CanonicalToolEvent) -> PolicyDecision:
    if event.file_path:
        if "Tickets/Resolved/" in event.file_path and not event.is_bugfix_ticket:
            return PolicyDecision.deny(
                "Only bugfix tickets can be written to Tickets/Resolved/. Feature/Task tickets must go to Tickets/Closed/."
            )
        if "Tickets/Closed/" in event.file_path and event.is_bugfix_ticket:
            return PolicyDecision.deny(
                "Bugfix tickets cannot be written to Tickets/Closed/. They must go to Tickets/Resolved/."
            )

    if event.source_path and event.destination_path:
        if "Tickets/Ready/" in event.source_path and "Tickets/Active/" not in event.destination_path:
            return PolicyDecision.deny(
                f"Tickets from Tickets/Ready/ must be moved to Tickets/Active/ when started, not {event.destination_path.rsplit('/', 1)[-1]}."
            )
        if "Tickets/Active/" in event.source_path:
            if event.is_bugfix_ticket and "Tickets/Resolved/" not in event.destination_path:
                return PolicyDecision.deny(
                    f"Bugfix ticket {event.source_path.rsplit('/', 1)[-1]} must be moved to Tickets/Resolved/, not {event.destination_path.rsplit('/', 1)[-1]}."
                )
            if not event.is_bugfix_ticket and "Tickets/Closed/" not in event.destination_path:
                return PolicyDecision.deny(
                    f"Feature/Task ticket {event.source_path.rsplit('/', 1)[-1]} must be moved to Tickets/Closed/, not {event.destination_path.rsplit('/', 1)[-1]}."
                )

    return PolicyDecision.allow()


def _is_ticket_path(event: CanonicalToolEvent) -> bool:
    return any(
        path and "Tickets/" in path
        for path in (event.file_path, event.source_path, event.destination_path)
    )
