from __future__ import annotations

from typing import Any

from scripts.policy.events import CanonicalToolEvent, PolicyDecision

_CURSOR_TOOL_ALIASES = {
    "Shell": "run_command",
    "Write": "write_to_file",
    "StrReplace": "replace_file_content",
    "Edit": "replace_file_content",
}


def parse_cursor_payload(payload: dict[str, Any], *, project_root: str, vault_dir: str) -> CanonicalToolEvent:
    tool_call = payload.get("toolCall") or payload.get("tool_call") or {}
    tool_input = (
        payload.get("tool_input")
        or payload.get("arguments")
        or payload.get("args")
        or tool_call.get("args")
        or tool_call.get("input")
        or {}
    )
    raw_tool_name = (
        payload.get("tool_name")
        or payload.get("tool")
        or payload.get("name")
        or tool_call.get("name")
        or ""
    )
    tool_name = _CURSOR_TOOL_ALIASES.get(raw_tool_name, raw_tool_name)
    command = tool_input.get("command") or tool_input.get("CommandLine")
    file_path = (
        tool_input.get("path")
        or tool_input.get("file")
        or tool_input.get("file_path")
        or tool_input.get("AbsolutePath")
        or tool_input.get("TargetFile")
    )
    source_path, destination_path = _parse_ticket_paths(command or "")

    if not file_path and tool_name == "run_command" and source_path:
        file_path = source_path

    return CanonicalToolEvent(
        client="cursor",
        tool_name=tool_name,
        command=command,
        file_path=file_path,
        source_path=source_path,
        destination_path=destination_path,
        workspace_root=project_root,
        vault_dir=vault_dir,
        is_bugfix_ticket=_infer_is_bugfix_ticket(file_path or source_path or ""),
    )


def format_cursor_decision(decision: PolicyDecision) -> dict[str, Any]:
    if decision.is_denied():
        reason = decision.reason or "Denied"
        return {
            "permission": "deny",
            "user_message": reason,
            "agent_message": reason,
        }
    return {"permission": "allow"}


def _parse_ticket_paths(command: str) -> tuple[str | None, str | None]:
    tokens = command.split()
    ticket_paths = [token.strip("'\"") for token in tokens if "Tickets/" in token]
    if len(ticket_paths) < 2:
        return None, None
    return ticket_paths[0], ticket_paths[1]


def _infer_is_bugfix_ticket(path: str) -> bool:
    filename = path.rsplit("/", 1)[-1].lower()
    return "bug" in filename
