#!/usr/bin/env python3
import sys
import json
import os
import re
from datetime import datetime

LOG_FILE = "/tmp/codex_hook_debug.log"

def log_debug(msg):
    try:
        with open(LOG_FILE, "a") as f:
            f.write(f"{datetime.now().isoformat()} - {msg}\n")
    except:
        pass

def get_project_root():
    # Walk up from current working directory to find git root
    cwd = os.getcwd()
    while cwd != os.path.dirname(cwd):
        if os.path.exists(os.path.join(cwd, ".git")):
            return cwd
        cwd = os.path.dirname(cwd)
    return os.getcwd()

def get_vault_dir(project_root):
    for name in os.listdir(project_root):
        if name.startswith("AI_Codex") and os.path.isdir(os.path.join(project_root, name)):
            return os.path.join(project_root, name)
    return os.path.join(project_root, "AI_Codex")

def get_today_date_str():
    return datetime.now().strftime("%Y-%m-%d")

def is_allowed_markdown(path, vault_dir, project_root):
    normalized_path = os.path.abspath(path)

    # Allow CLAUDE.md and GEMINI.md at root
    basename = os.path.basename(normalized_path)
    if basename in ["CLAUDE.md", "GEMINI.md"]:
        return True

    # Allow anything under the Codex vault
    if normalized_path.startswith(os.path.abspath(vault_dir)):
        return True

    # Allow anything under .agent/rules or .agent/workflows
    agent_dir = os.path.join(project_root, ".agent")
    if normalized_path.startswith(os.path.abspath(agent_dir)):
        return True

    return False

def has_active_session_today(vault_dir):
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
                with open(filepath, "r") as f:
                    content = f.read()
                # Parse frontmatter to check if "next" is null
                if re.search(r"next:\s*(null|['\"]['\"]|~|)\s*$", content, re.MULTILINE):
                    log_debug(f"Found active session record: {filename}")
                    return True
            except Exception as e:
                log_debug(f"Error reading session file {filename}: {e}")

    return False

def check_youtrack_state_in_transcript(transcript_path, issue_id, expected_states):
    if not transcript_path or not os.path.exists(transcript_path):
        log_debug(f"Transcript path '{transcript_path}' not found.")
        return False

    try:
        with open(transcript_path, "r") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    step = json.loads(line)
                    if step.get("status") != "DONE":
                        continue
                    
                    tool_calls = step.get("tool_calls") or []
                    for tc in tool_calls:
                        if tc.get("name") == "call_mcp_tool":
                            args = tc.get("args") or {}
                            server = args.get("ServerName") or ""
                            tool = args.get("ToolName") or ""
                            
                            server = server.strip('"\'')
                            tool = tool.strip('"\'')
                            
                            if server == "youtrack" and tool == "update_issue":
                                tc_args_str = args.get("Arguments") or "{}"
                                if isinstance(tc_args_str, str):
                                    try:
                                        tc_args = json.loads(tc_args_str)
                                    except:
                                        tc_args = {}
                                else:
                                    tc_args = tc_args_str
                                
                                tid = tc_args.get("issueId") or ""
                                custom_fields = tc_args.get("customFields") or {}
                                state = custom_fields.get("State") or ""
                                
                                tid = str(tid).strip('"\'')
                                state = str(state).strip('"\'')
                                
                                if tid == issue_id and state in expected_states:
                                    log_debug(f"Found matching YouTrack update: {issue_id} -> {state}")
                                    return True
                except Exception:
                    pass
    except Exception as e:
        log_debug(f"Error reading transcript: {e}")

    return False

def get_youtrack_issue_id_from_ticket(filepath):
    if not filepath or not os.path.exists(filepath):
        return None
    try:
        with open(filepath, "r") as f:
            content = f.read()
        match = re.search(r"^youtrack:\s*(SEUMEI-\d+|[A-Z]+-\d+)", content, re.MULTILINE)
        if match:
            return match.group(1)
    except Exception as e:
        log_debug(f"Error reading ticket frontmatter: {e}")
    return None

def get_youtrack_issue_id_from_write(file_path, arguments):
    code_content = arguments.get("CodeContent") or ""
    if code_content:
        match = re.search(r"^youtrack:\s*(SEUMEI-\d+|[A-Z]+-\d+)", code_content, re.MULTILINE)
        if match:
            return match.group(1)
    if os.path.exists(file_path):
        return get_youtrack_issue_id_from_ticket(file_path)
    return None

def install_hook():
    script_path = os.path.abspath(__file__)
    # The skill's root is two levels up from the script
    skill_root = os.path.dirname(os.path.dirname(script_path))
    resources_dir = os.path.join(skill_root, "resources")
    rules_dir = os.path.join(skill_root, "rules")
    
    # 1. Ensure hook script is executable
    os.chmod(script_path, 0o755)
    
    # 2. Sync workflows to the current project's .agent/workflows/
    project_root = get_project_root()
    target_workflows_dir = os.path.join(project_root, ".agent", "workflows")
    os.makedirs(target_workflows_dir, exist_ok=True)
    
    if os.path.exists(resources_dir):
        print(f"Syncing workflows from {resources_dir} to {target_workflows_dir}...")
        for name in os.listdir(resources_dir):
            if name.endswith(".md"):
                src = os.path.join(resources_dir, name)
                dst = os.path.join(target_workflows_dir, name)
                with open(src, "r") as s_file:
                    content = s_file.read()
                with open(dst, "w") as d_file:
                    d_file.write(content)
                print(f"  Synced workflow: {name}")

    # 3. Sync rules to the current project's .agent/rules/
    target_rules_dir = os.path.join(project_root, ".agent", "rules")
    os.makedirs(target_rules_dir, exist_ok=True)
    
    if os.path.exists(rules_dir):
        print(f"Syncing rules from {rules_dir} to {target_rules_dir}...")
        for name in os.listdir(rules_dir):
            if name.endswith(".md"):
                src = os.path.join(rules_dir, name)
                dst = os.path.join(target_rules_dir, name)
                with open(src, "r") as s_file:
                    content = s_file.read()
                with open(dst, "w") as d_file:
                    d_file.write(content)
                print(f"  Synced rule: {name}")
                
    # 4. Write hooks.json configuration to ~/.gemini/config/hooks.json
    config_dir = os.path.expanduser("~/.gemini/config")
    os.makedirs(config_dir, exist_ok=True)
    hooks_json_path = os.path.join(config_dir, "hooks.json")
    
    hook_config = {
        "codex-enforcer": {
            "enabled": True,
            "PreToolUse": [
                {
                    "matcher": ".*",
                    "hooks": [
                        {
                            "type": "command",
                            "command": script_path,
                            "timeout": 5
                        }
                    ]
                }
            ]
        }
    }
    
    with open(hooks_json_path, "w") as f:
        json.dump(hook_config, f, indent=2)
    print(f"Hooks registered successfully at {hooks_json_path}")
    print("Setup complete!")

def main():
    log_debug("Hook invoked")
    project_root = get_project_root()
    vault_dir = get_vault_dir(project_root)

    try:
        input_data = json.load(sys.stdin)
        log_debug(f"Input JSON: {json.dumps(input_data)}")
    except Exception as e:
        log_debug(f"Failed to parse stdin JSON: {e}")
        print(json.dumps({"permissionDecision": "allow"}))
        sys.exit(0)

    tool_name = input_data.get("tool_name") or input_data.get("tool") or input_data.get("name") or ""
    arguments = input_data.get("tool_input") or input_data.get("arguments") or input_data.get("args") or {}

    # RULE 1: Destructive Deletions on Vault
    if tool_name == "run_command":
        cmd = arguments.get("CommandLine") or arguments.get("command") or ""
        if ("rm " in cmd or "rmdir " in cmd) and os.path.basename(vault_dir) in cmd:
            reason = "Destructive deletions (rm) are forbidden on the AI Codex vault. Use 'mv' to change status."
            log_debug(f"DENIED: {reason}")
            print(json.dumps({"permissionDecision": "deny", "reason": reason}))
            sys.exit(0)

        # Check mv/git mv commands affecting Tickets
        cmd_tokens = cmd.split()
        ticket_paths = [t for t in cmd_tokens if "Tickets/" in t]
        if len(ticket_paths) >= 2 and any(m in cmd_tokens for m in ["mv", "git"]):
            src_path = ticket_paths[0].strip("'\"")
            dst_path = ticket_paths[1].strip("'\"")
            
            abs_src = os.path.abspath(os.path.join(project_root, src_path))
            abs_dst = os.path.abspath(os.path.join(project_root, dst_path))
            
            if "Tickets/Ready/" in abs_src:
                if "Tickets/Active/" not in abs_dst:
                    reason = f"Tickets from Tickets/Ready/ must be moved to Tickets/Active/ when started, not {os.path.basename(abs_dst)}."
                    log_debug(f"DENIED: {reason}")
                    print(json.dumps({"permissionDecision": "deny", "reason": reason}))
                    sys.exit(0)
                
                # Check YouTrack status for starting ticket
                issue_id = get_youtrack_issue_id_from_ticket(abs_src)
                if issue_id:
                    transcript_path = input_data.get("transcriptPath")
                    if not check_youtrack_state_in_transcript(transcript_path, issue_id, ["In Progress"]):
                        reason = f"Move blocked. You must update YouTrack issue {issue_id} state to 'In Progress' via call_mcp_tool before moving the ticket to Active."
                        log_debug(f"DENIED: {reason}")
                        print(json.dumps({"permissionDecision": "deny", "reason": reason}))
                        sys.exit(0)
            elif "Tickets/Active/" in abs_src:
                is_bugfix = "bug" in os.path.basename(abs_src).lower()
                if os.path.exists(abs_src):
                    try:
                        with open(abs_src, "r") as f:
                            content = f.read()
                        if "type: bug" in content or "type: bugfix" in content:
                            is_bugfix = True
                    except:
                        pass
                
                if is_bugfix:
                    if "Tickets/Resolved/" not in abs_dst:
                        reason = f"Bugfix ticket {os.path.basename(abs_src)} must be moved to Tickets/Resolved/, not {os.path.basename(abs_dst)}."
                        log_debug(f"DENIED: {reason}")
                        print(json.dumps({"permissionDecision": "deny", "reason": reason}))
                        sys.exit(0)
                else:
                    if "Tickets/Closed/" not in abs_dst:
                        reason = f"Feature/Task ticket {os.path.basename(abs_src)} must be moved to Tickets/Closed/, not {os.path.basename(abs_dst)}."
                        log_debug(f"DENIED: {reason}")
                        print(json.dumps({"permissionDecision": "deny", "reason": reason}))
                        sys.exit(0)

                # Check YouTrack status for closing/resolving ticket
                issue_id = get_youtrack_issue_id_from_ticket(abs_src)
                if issue_id:
                    transcript_path = input_data.get("transcriptPath")
                    allowed_end_states = ["Done", "Fixed", "Test", "Testing", "Resolved"]
                    if not check_youtrack_state_in_transcript(transcript_path, issue_id, allowed_end_states):
                        reason = f"Move blocked. You must update YouTrack issue {issue_id} state to 'Done', 'Fixed', or 'Test'/'Testing'/'Resolved' via call_mcp_tool before moving the ticket to Resolved/Closed."
                        log_debug(f"DENIED: {reason}")
                        print(json.dumps({"permissionDecision": "deny", "reason": reason}))
                        sys.exit(0)

    # RULE 2: Markdown Allowlist
    file_path = arguments.get("AbsolutePath") or arguments.get("TargetFile") or arguments.get("path") or arguments.get("file") or ""
    if isinstance(file_path, str) and file_path.endswith(".md"):
        if not is_allowed_markdown(file_path, vault_dir, project_root):
            reason = f"Read/write of {os.path.basename(file_path)} blocked. Markdown files not in CLAUDE.md allowlist are forbidden."
            log_debug(f"DENIED: {reason}")
            print(json.dumps({"permissionDecision": "deny", "reason": reason}))
            sys.exit(0)

    # RULE 3: Session Bootstrap Enforcer (for write operations)
    write_tools = ["write_to_file", "replace_file_content", "multi_replace_file_content"]
    if tool_name in write_tools:
        # Prevent writing resolved/closed tickets in the wrong folder
        if "Tickets/" in file_path:
            abs_file_path = os.path.abspath(file_path)
            filename = os.path.basename(abs_file_path)
            is_bugfix = "bug" in filename.lower()
            
            if "Tickets/Resolved/" in abs_file_path and not is_bugfix:
                reason = "Only bugfix tickets can be written to Tickets/Resolved/. Feature/Task tickets must go to Tickets/Closed/."
                log_debug(f"DENIED: {reason}")
                print(json.dumps({"permissionDecision": "deny", "reason": reason}))
                sys.exit(0)
            if "Tickets/Closed/" in abs_file_path and is_bugfix:
                reason = "Bugfix tickets cannot be written to Tickets/Closed/. They must go to Tickets/Resolved/."
                log_debug(f"DENIED: {reason}")
                print(json.dumps({"permissionDecision": "deny", "reason": reason}))
                sys.exit(0)

            # Check YouTrack status when writing active/closed/resolved tickets
            if "Tickets/Active/" in abs_file_path or "Tickets/Closed/" in abs_file_path or "Tickets/Resolved/" in abs_file_path:
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
                        print(json.dumps({"permissionDecision": "deny", "reason": reason}))
                        sys.exit(0)

        if not is_allowed_markdown(file_path, vault_dir, project_root) or "Agent_Sessions" not in file_path:
            if not has_active_session_today(vault_dir):
                reason = "Write blocked. You must initialize today's Agent Session log in AI_Codex_SeuMeiSimples/Agent_Sessions/ before making code modifications."
                log_debug(f"DENIED: {reason}")
                print(json.dumps({"permissionDecision": "deny", "reason": reason}))
                sys.exit(0)

    log_debug("ALLOWED")
    print(json.dumps({"permissionDecision": "allow"}))
    sys.exit(0)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ["--install", "install"]:
        install_hook()
    else:
        main()
