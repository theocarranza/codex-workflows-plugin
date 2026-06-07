from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from datetime import datetime
from typing import Any, Callable

from scripts.adapters import (
    format_antigravity_decision,
    format_claude_decision,
    format_codex_decision,
    format_gemini_decision,
    parse_antigravity_payload,
    parse_claude_payload,
    parse_codex_payload,
    parse_gemini_payload,
)
from scripts.policy import CanonicalToolEvent, PolicyDecision, evaluate

LOG_FILE = "/tmp/codex_hook_debug.log"


AdapterParser = Callable[[dict[str, Any]], CanonicalToolEvent]
AdapterFormatter = Callable[[PolicyDecision], dict[str, Any]]


def log_debug(msg: str) -> None:
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as file:
            file.write(f"{datetime.now().isoformat()} - {msg}\n")
    except Exception:
        pass


def get_project_root() -> str:
    cwd = os.getcwd()
    while cwd != os.path.dirname(cwd):
        if os.path.exists(os.path.join(cwd, ".git")):
            return cwd
        cwd = os.path.dirname(cwd)
    return os.getcwd()


def get_vault_dir(project_root: str) -> str:
    for name in os.listdir(project_root):
        if name.startswith("AI_Codex") and os.path.isdir(os.path.join(project_root, name)):
            return os.path.join(project_root, name)
    return os.path.join(project_root, "AI_Codex")


def get_today_date_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def is_allowed_markdown(path: str, vault_dir: str, project_root: str) -> bool:
    normalized_path = os.path.abspath(path)
    basename = os.path.basename(normalized_path)
    if basename in ["CLAUDE.md", "GEMINI.md"]:
        return True
    if normalized_path.startswith(os.path.abspath(vault_dir)):
        return True
    agent_dir = os.path.join(project_root, ".agent")
    return normalized_path.startswith(os.path.abspath(agent_dir))


def has_active_session_today(vault_dir: str) -> bool:
    sessions_dir = os.path.join(vault_dir, "Agent_Sessions")
    if not os.path.exists(sessions_dir):
        log_debug(f"Sessions directory {sessions_dir} does not exist.")
        return False

    today_prefix = get_today_date_str()
    log_debug(f"Checking for sessions starting with {today_prefix}")

    for filename in os.listdir(sessions_dir):
        if filename.startswith(today_prefix) and filename.endswith(".md"):
            filepath = os.path.join(sessions_dir, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as file:
                    content = file.read()
                if re.search(r"next:\s*(null|['\"]['\"]|~|)\s*$", content, re.MULTILINE):
                    log_debug(f"Found active session record: {filename}")
                    return True
            except Exception as exc:
                log_debug(f"Error reading session file {filename}: {exc}")

    return False


def check_youtrack_state_in_transcript(transcript_path: str | None, issue_id: str, expected_states: list[str]) -> bool:
    if not transcript_path or not os.path.exists(transcript_path):
        log_debug(f"Transcript path '{transcript_path}' not found.")
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
                        state = str(custom_fields.get("State") or "").strip('"\'')

                        if tid == issue_id and state in expected_states:
                            log_debug(f"Found matching YouTrack update: {issue_id} -> {state}")
                            return True
                except Exception:
                    pass
    except Exception as exc:
        log_debug(f"Error reading transcript: {exc}")

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
    except Exception as exc:
        log_debug(f"Error reading ticket frontmatter: {exc}")
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
        except Exception as exc:
            log_debug(f"Error inferring bugfix ticket state from {file_path}: {exc}")
    return is_bugfix


def _parse_ticket_paths(command: str) -> tuple[str | None, str | None]:
    tokens = command.split()
    ticket_paths = [token.strip("'\"") for token in tokens if "Tickets/" in token]
    if len(ticket_paths) < 2:
        return None, None
    return ticket_paths[0], ticket_paths[1]


def select_adapter(client: str) -> tuple[Callable[[dict[str, Any], str, str], CanonicalToolEvent], AdapterFormatter]:
    normalized = client.strip().lower()
    if normalized == "gemini":
        return parse_gemini_payload, format_gemini_decision
    if normalized == "antigravity":
        return parse_antigravity_payload, format_antigravity_decision
    if normalized == "claude":
        return parse_claude_payload, format_claude_decision
    return parse_codex_payload, format_codex_decision


def emit_decision(client: str, decision: PolicyDecision) -> None:
    _, formatter = select_adapter(client)
    print(json.dumps(formatter(decision)))


def run(client: str, input_data: dict[str, Any]) -> int:
    project_root = get_project_root()
    vault_dir = get_vault_dir(project_root)
    parser, _ = select_adapter(client)
    codex_event = parser(input_data, project_root=project_root, vault_dir=vault_dir)
    tool_name = codex_event.tool_name
    arguments = input_data.get("tool_input") or input_data.get("arguments") or input_data.get("args") or {}
    file_path = codex_event.file_path or arguments.get("AbsolutePath") or arguments.get("TargetFile") or arguments.get("path") or arguments.get("file") or ""

    if tool_name == "run_command":
        cmd = codex_event.command or arguments.get("CommandLine") or arguments.get("command") or ""
        destructive_decision = evaluate(
            CanonicalToolEvent(
                client=client,
                tool_name=tool_name,
                command=cmd,
                workspace_root=project_root,
                vault_dir=vault_dir,
            )
        )
        if destructive_decision.is_denied():
            log_debug(f"DENIED: {destructive_decision.reason}")
            emit_decision(client, PolicyDecision.deny(destructive_decision.reason or "Denied"))
            return 0

        cmd_tokens = cmd.split()
        ticket_paths = [t for t in cmd_tokens if "Tickets/" in t]
        if len(ticket_paths) >= 2 and any(m in cmd_tokens for m in ["mv", "git"]):
            src_path = ticket_paths[0].strip("'\"")
            dst_path = ticket_paths[1].strip("'\"")
            abs_src = os.path.abspath(os.path.join(project_root, src_path))
            abs_dst = os.path.abspath(os.path.join(project_root, dst_path))
            is_bugfix = codex_event.is_bugfix_ticket or infer_is_bugfix_ticket(abs_src)
            if "Tickets/Ready/" in abs_src and "Tickets/Active/" not in abs_dst:
                issue_id = get_youtrack_issue_id_from_ticket(abs_src)
                if issue_id:
                    transcript_path = input_data.get("transcriptPath")
                    if not check_youtrack_state_in_transcript(transcript_path, issue_id, ["In Progress"]):
                        try:
                            subprocess.run(
                                [
                                    "youtrack",
                                    "update_issue",
                                    "--issueId",
                                    issue_id,
                                    "--customFields",
                                    "{\"State\":\"In Progress\"}",
                                ],
                                check=False,
                            )
                            log_debug(f"Auto-updated YouTrack issue {issue_id} to In Progress")
                        except Exception as exc:
                            log_debug(f"Auto-update failed for issue {issue_id}: {exc}")

            decision = evaluate(
                CanonicalToolEvent(
                    client=client,
                    tool_name=tool_name,
                    command=cmd,
                    source_path=abs_src,
                    destination_path=abs_dst,
                    workspace_root=project_root,
                    vault_dir=vault_dir,
                    is_bugfix_ticket=is_bugfix,
                )
            )
            if decision.is_denied():
                log_debug(f"DENIED: {decision.reason}")
                emit_decision(client, PolicyDecision.deny(decision.reason or "Denied"))
                return 0

            issue_id = get_youtrack_issue_id_from_ticket(abs_src)
            if issue_id:
                transcript_path = input_data.get("transcriptPath")
                allowed_end_states = ["Done", "Fixed", "Test", "Testing", "Resolved"]
                if not check_youtrack_state_in_transcript(transcript_path, issue_id, allowed_end_states):
                    reason = (
                        f"Move blocked. You must update YouTrack issue {issue_id} state to 'Done', 'Fixed', or 'Test'/'Testing'/'Resolved' via call_mcp_tool before moving the ticket to Resolved/Closed."
                    )
                    log_debug(f"DENIED: {reason}")
                    emit_decision(client, PolicyDecision.deny(reason))
                    return 0

    markdown_allowed = is_allowed_markdown(file_path, vault_dir, project_root)
    markdown_decision = evaluate(
        CanonicalToolEvent(
            client=client,
            tool_name=tool_name,
            file_path=file_path,
            workspace_root=project_root,
            vault_dir=vault_dir,
            markdown_allowed=markdown_allowed,
            session_active=has_active_session_today(vault_dir),
            is_bugfix_ticket=infer_is_bugfix_ticket(file_path),
        )
    )
    if markdown_decision.is_denied() and isinstance(file_path, str) and file_path.endswith(".md") and not markdown_allowed:
        log_debug(f"DENIED: {markdown_decision.reason}")
        emit_decision(client, PolicyDecision.deny(markdown_decision.reason or "Denied"))
        return 0

    write_tools = ["write_to_file", "replace_file_content", "multi_replace_file_content"]
    if tool_name in write_tools:
        write_decision = evaluate(
            CanonicalToolEvent(
                client=client,
                tool_name=tool_name,
                file_path=file_path,
                workspace_root=project_root,
                vault_dir=vault_dir,
                markdown_allowed=markdown_allowed,
                session_active=has_active_session_today(vault_dir),
                is_bugfix_ticket=infer_is_bugfix_ticket(file_path),
            )
        )
        if write_decision.is_denied():
            log_debug(f"DENIED: {write_decision.reason}")
            emit_decision(client, PolicyDecision.deny(write_decision.reason or "Denied"))
            return 0

        abs_file_path = os.path.abspath(file_path)
        if any(marker in abs_file_path for marker in ["Tickets/Active/", "Tickets/Closed/", "Tickets/Resolved/"]):
            issue_id = get_youtrack_issue_id_from_write(abs_file_path, arguments)
            if issue_id:
                transcript_path = input_data.get("transcriptPath")
                if "Tickets/Active/" in abs_file_path:
                    expected_states = ["In Progress"]
                    state_desc = "'In Progress'"
                else:
                    expected_states = ["Done", "Fixed", "Test", "Testing", "Resolved"]
                    state_desc = "'Done', 'Fixed', or 'Test'/'Testing'/'Resolved'"
                if not check_youtrack_state_in_transcript(transcript_path, issue_id, expected_states):
                    reason = f"Write blocked. You must update YouTrack issue {issue_id} state to {state_desc} via call_mcp_tool before saving/moving the ticket."
                    log_debug(f"DENIED: {reason}")
                    emit_decision(client, PolicyDecision.deny(reason))
                    return 0

        if "Agent_Sessions" not in file_path and not has_active_session_today(vault_dir):
            reason = "Write blocked. You must initialize today's Agent Session log in AI_Codex_SeuMeiSimples/Agent_Sessions/ before making code modifications."
            log_debug(f"DENIED: {reason}")
            emit_decision(client, PolicyDecision.deny(reason))
            return 0

    log_debug("ALLOWED")
    emit_decision(client, PolicyDecision.allow())
    return 0
