from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class YouTrackCheckResult:
    """Result of a YouTrack state verification against the conversation transcript."""

    verified: bool
    reason: str  # "ok" | "transcript_missing" | "state_not_found"

    @classmethod
    def ok(cls) -> "YouTrackCheckResult":
        """Returns a passing result."""
        return cls(verified=True, reason="ok")

    @classmethod
    def transcript_missing(cls) -> "YouTrackCheckResult":
        """Returns a failure result when the transcript file is absent."""
        return cls(verified=False, reason="transcript_missing")

    @classmethod
    def state_not_found(cls) -> "YouTrackCheckResult":
        """Returns a failure result when the required state was not recorded."""
        return cls(verified=False, reason="state_not_found")


def extract_ticket_paths(command: str) -> tuple[str | None, str | None]:
    """Extracts source and destination Ticket paths from a mv or git mv command."""
    tokens = command.split()
    ticket_paths = [token.strip("'\"") for token in tokens if "Tickets/" in token]
    if len(ticket_paths) < 2:
        return None, None
    return ticket_paths[0], ticket_paths[1]


def check_youtrack_state_in_transcript(
    transcript_path: str | None,
    issue_id: str,
    expected_states: list[str],
) -> YouTrackCheckResult:
    """Checks whether a YouTrack issue was moved to an expected state in the transcript.

    Scans the JSONL conversation transcript for a completed `call_mcp_tool`
    call targeting the `youtrack/update_issue` tool with the given issue ID
    and a `State` field matching one of [expected_states].

    Returns a [YouTrackCheckResult] distinguishing three outcomes:
    transcript absent, state not found, or verified.
    """
    if not transcript_path or not os.path.exists(transcript_path):
        return YouTrackCheckResult.transcript_missing()

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
                            return YouTrackCheckResult.ok()
                except Exception:
                    pass
    except Exception:
        pass

    return YouTrackCheckResult.state_not_found()


def get_youtrack_issue_id_from_ticket(filepath: str | None) -> str | None:
    """Extracts the YouTrack issue ID from a ticket's YAML frontmatter."""
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
    """Extracts the YouTrack issue ID from write arguments or from the file on disk."""
    code_content = arguments.get("CodeContent") or ""
    if code_content:
        match = re.search(r"^youtrack:\s*(SEUMEI-\d+|[A-Z]+-\d+)", code_content, re.MULTILINE)
        if match:
            return match.group(1)
    if os.path.exists(file_path):
        return get_youtrack_issue_id_from_ticket(file_path)
    return None


def infer_is_bugfix_ticket(file_path: str | None, content: str | None = None) -> bool:
    """Whether the ticket file declares itself a bugfix via YAML frontmatter.

    Reads the `type:` field from the ticket's frontmatter and returns `True`
    only when it is `bug` or `bugfix`. Filename heuristics are intentionally
    excluded to avoid false positives (e.g. a file named `debug-something.md`).
    Returns `False` when the file is absent or unreadable.
    """
    if content:
        return "type: bug" in content or "type: bugfix" in content
    if not file_path or not os.path.exists(file_path):
        return False
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            file_content = file.read()
        return "type: bug" in file_content or "type: bugfix" in file_content
    except Exception:
        return False
