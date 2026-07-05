import unittest
import json
from pathlib import Path

from scripts.adapters import format_claude_decision, parse_claude_payload
from scripts.policy import PolicyDecision


FIXTURE_PATH = Path(__file__).resolve().parents[1] / "fixtures" / "claude_pretooluse.json"


class TestClaudeAdapter(unittest.TestCase):
    def test_parses_claude_payload_shape(self):
        payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

        event = parse_claude_payload(payload, project_root="/workspace/project", vault_dir="/workspace/project/AI_Codex")

        self.assertEqual(event.client, "claude")
        self.assertEqual(event.tool_name, "Bash")
        self.assertEqual(event.command, "mv /workspace/project/AI_Codex/Tickets/Active/task-123.md /workspace/project/AI_Codex/Tickets/Closed/task-123.md")
        self.assertEqual(event.source_path, "/workspace/project/AI_Codex/Tickets/Active/task-123.md")
        self.assertEqual(event.destination_path, "/workspace/project/AI_Codex/Tickets/Closed/task-123.md")

    def test_formats_claude_decision(self):
        decision = PolicyDecision.deny("Blocked by policy")

        response = format_claude_decision(decision)

        self.assertNotIn("decision", response)
        self.assertNotIn("reason", response)
        self.assertEqual(
            response["hookSpecificOutput"],
            {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": "Blocked by policy",
            },
        )

    def test_formats_allowed_claude_decision_without_reason(self):
        response = format_claude_decision(PolicyDecision.allow())

        self.assertEqual(
            response["hookSpecificOutput"],
            {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
            },
        )

    def test_parses_claude_read_tool_input_file_path(self):
        payload = {
            "tool_name": "Read",
            "tool_input": {"file_path": "/workspace/project/docs/private.md"},
        }

        event = parse_claude_payload(payload, project_root="/workspace/project", vault_dir="/workspace/project/AI_Codex")

        self.assertEqual(event.tool_name, "Read")
        self.assertEqual(event.file_path, "/workspace/project/docs/private.md")


if __name__ == "__main__":
    unittest.main()
