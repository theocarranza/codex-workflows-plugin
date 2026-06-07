from __future__ import annotations

import json
import os
import re
from typing import Any


def extract_ticket_paths(command: str) -> tuple[str | None, str | None]:
    tokens = command.split()
    ticket_paths = [token.strip("'\"") for token in tokens if "Tickets/" in token]
    if len(ticket_paths) < 2:
        return None, None
    return ticket_paths[0], ticket_paths[1]


def check_youtrack_state_in_transcript(transcript_path: str | None, issue_id: str, expected_states: list[str]) -> bool:
    if not transcript_path or not os.path.exists(transcript_path):
        return False

    try:
        with open(transcript_path, "r", encoding="utf-8") as file:
            for line in file:
                if not line.strip():
                    continue
                try:
                    step = json.loads(line)
                    if step.get("status") != "DONE":
                        continue

                    tool_calls = step.get("tool_calls") or []
                    for tc in tool_calls:
                        if tc.get("name") != "call_mcp_tool":
                            continue
                        args = tc.get("args") or {}
                        server = str(args.get("ServerName") or "").strip('"\'')
                        tool = str(args.get("ToolName") or "").strip('"\'')
                        if server != "youtrack" or tool != "update_issue":
                            continue

                        tc_args_str = args.get("Arguments") or "{}"
                        if isinstance(tc_args_str, str):
                            try:
                                tc_args = json.loads(tc_args_str)
                            except Exception:
                                tc_args = {}
                        else:
                            tc_args = tc_args_str

                        tid = str(tc_args.get("issueId") or "").strip('"\'')
                        custom_fields = tc_args.get("customFields") or {}
                        state = str(custom_fields.get("State") or "").strip("\"'")

                        if tid == issue_id and state in expected_states:
                            return True
                except Exception:
                    pass
    except Exception:
        pass

    return False


def get_youtrack_issue_id_from_ticket(filepath: str | None) -> str | None:
    if not filepath or not os.path.exists(filepath):
        return None
    try:
        with open(filepath, "r", encoding="utf-8") as file:
            content = file.read()
        match = re.search(r"^youtrack:\s*(SEUMEI-\d+|[A-Z]+-\d+)", content, re.MULTILINE)
        if match:
            return match.group(1)
    except Exception:
        pass
    return None


def get_youtrack_issue_id_from_write(file_path: str, arguments: dict[str, Any]) -> str | None:
    code_content = arguments.get("CodeContent") or ""
    if code_content:
        match = re.search(r"^youtrack:\s*(SEUMEI-\d+|[A-Z]+-\d+)", code_content, re.MULTILINE)
        if match:
            return match.group(1)
    if os.path.exists(file_path):
        return get_youtrack_issue_id_from_ticket(file_path)
    return None


def infer_is_bugfix_ticket(file_path: str | None) -> bool:
    filename = os.path.basename(file_path or "")
    is_bugfix = "bug" in filename.lower()
    if file_path and os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()
            if "type: bug" in content or "type: bugfix" in content:
                is_bugfix = True
        except Exception:
            pass
    return is_bugfix
