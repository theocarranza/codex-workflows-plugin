#!/usr/bin/env python3
"""Script to scaffold a local ticket draft and generate a YouTrack MCP registration payload."""

import argparse
import datetime
import getpass
import json
import os
import re
import subprocess
from pathlib import Path


def get_git_user_name() -> str:
    """Attempts to get the user's name from git config, falling back to system username."""
    try:
        result = subprocess.run(
            ["git", "config", "user.name"],
            capture_output=True,
            text=True,
            check=True,
        )
        name = result.stdout.strip()
        if name:
            return name
    except Exception:
        pass
    return getpass.getuser()


def kebab_case(text: str) -> str:
    """Converts text to kebab-case, removing special characters."""
    # Replace non-alphanumeric characters with hyphens
    s = re.sub(r"[^a-zA-Z0-9]+", "-", text)
    # Strip leading/trailing hyphens and lowercase
    return s.strip("-").lower()


def find_templates_dir() -> Path:
    """Finds the templates directory, checking common locations."""
    script_dir = Path(__file__).parent.resolve()
    repo_root = script_dir.parent

    # Candidate paths
    candidates = [
        repo_root / ".agent" / "workflows" / "templates",
        repo_root / "skills" / "codex_workflows" / "resources" / "templates",
        Path(".") / ".agent" / "workflows" / "templates",
    ]

    for candidate in candidates:
        if candidate.is_dir():
            return candidate

    raise FileNotFoundError(
        "Templates directory not found. Checked:\n"
        + "\n".join(str(c) for c in candidates)
    )


def find_vault_dir() -> Path:
    """Finds the AI_Codex vault directory in the current working directory."""
    cwd = Path(".").resolve()
    # Search for directories starting with AI_Codex
    for item in cwd.iterdir():
        if item.is_dir() and item.name.startswith("AI_Codex"):
            return item
    return cwd / "AI_Codex"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Scaffold a local ticket draft and generate YouTrack MCP payload."
    )
    parser.add_argument(
        "--summary", required=True, help="The issue title/summary."
    )
    parser.add_argument(
        "--type",
        choices=["task", "feature", "bug", "user-story"],
        default="task",
        help="Type of the issue (default: task).",
    )
    parser.add_argument(
        "--area", default="general", help="Comma-separated area names (default: general)."
    )
    parser.add_argument(
        "--story-points", type=int, help="Optional integer story points estimate."
    )
    parser.add_argument(
        "--status",
        choices=["ready", "backlog"],
        default="ready",
        help="Initial ticket status (default: ready).",
    )
    parser.add_argument(
        "--desc", default="", help="Optional description of the issue."
    )
    parser.add_argument(
        "--project", default="SEUMEI", help="YouTrack project ID (default: SEUMEI)."
    )

    args = parser.parse_args()

    # Determine templates dir and find appropriate template
    try:
        templates_dir = find_templates_dir()
    except Exception as e:
        print(f"Error: {e}")
        return 1

    template_name = f"{args.type}-template.md"
    if args.type == "user-story":
        template_name = "feature-template.md"

    template_file = templates_dir / template_name
    if not template_file.is_file():
        # Fallback to task-template.md if specific template not found
        template_file = templates_dir / "task-template.md"

    if not template_file.is_file():
        print(f"Error: Template file not found at {template_file}")
        return 1

    # Load template content
    template_content = template_file.read_text(encoding="utf-8")

    # Resolve date, creator, and kebab-cased summary
    created_date = datetime.date.today().isoformat()
    creator = get_git_user_name()
    filename_kebab = kebab_case(args.summary)
    filename = f"draft-{filename_kebab}.md"

    # Replace placeholders
    content = template_content
    content = content.replace("{YOUTRACK_ID}", "DRAFT")
    content = content.replace("{AREA}", args.area)
    content = content.replace("{CREATED_DATE}", created_date)
    content = content.replace("{CREATOR}", creator)
    content = content.replace("{TITLE}", args.summary)

    # Resolve vault directory and subfolder
    vault_dir = find_vault_dir()
    subfolder_name = "Ready" if args.status == "ready" else "Backlog"
    dest_dir = vault_dir / "Tickets" / subfolder_name
    dest_path = dest_dir / filename

    # Write file
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path.write_text(content, encoding="utf-8")

    print(f"Scaffolded ticket draft at: {dest_path}\n")

    # Generate YouTrack MCP tool call arguments
    custom_fields = {
        "Type": args.type.capitalize() if args.type != "user-story" else "User Story",
        "State": "Ready" if args.status == "ready" else "Open",
    }
    if args.story_points is not None:
        custom_fields["Story points"] = args.story_points

    # Standard tool call JSON output format
    mcp_call = {
        "ServerName": "youtrack",
        "ToolName": "create_issue",
        "Arguments": {
            "project": args.project,
            "summary": args.summary,
            "description": f"See ticket details in local {vault_dir.name}: Tickets/{subfolder_name}/{filename}",
            "customFields": custom_fields,
        },
    }

    print("Execute the following MCP tool call to register the issue in YouTrack:")
    print(json.dumps(mcp_call, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
