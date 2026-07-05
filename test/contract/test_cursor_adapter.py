import unittest
import json
from pathlib import Path

from scripts.adapters import format_cursor_decision, parse_cursor_payload
from scripts.policy import PolicyDecision


FIXTURE_PATH = Path(__file__).resolve().parents[1] / "fixtures" / "cursor_pretooluse.json"


class TestCursorAdapter(unittest.TestCase):
    def test_parses_cursor_payload_shape(self):
        payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

        event = parse_cursor_payload(payload, project_root="/workspace/project", vault_dir="/workspace/project/AI_Codex")

        self.assertEqual(event.client, "cursor")
        self.assertEqual(event.tool_name, "run_command")
        self.assertEqual(
            event.command,
            "mv /workspace/project/AI_Codex/Tickets/Active/task-123.md /workspace/project/AI_Codex/Tickets/Closed/task-123.md",
        )
        self.assertEqual(event.source_path, "/workspace/project/AI_Codex/Tickets/Active/task-123.md")
        self.assertEqual(event.destination_path, "/workspace/project/AI_Codex/Tickets/Closed/task-123.md")

    def test_normalizes_write_tool_name(self):
        payload = {
            "tool_name": "Write",
            "tool_input": {"path": "/workspace/project/src/main.py"},
        }

        event = parse_cursor_payload(payload, project_root="/workspace/project", vault_dir="/workspace/project/AI_Codex")

        self.assertEqual(event.tool_name, "write_to_file")
        self.assertEqual(event.file_path, "/workspace/project/src/main.py")

    def test_formats_cursor_decision(self):
        decision = PolicyDecision.deny("Blocked by policy")

        response = format_cursor_decision(decision)

        self.assertEqual(response["permission"], "deny")
        self.assertEqual(response["user_message"], "Blocked by policy")
        self.assertEqual(response["agent_message"], "Blocked by policy")

    def test_formats_allow_decision(self):
        response = format_cursor_decision(PolicyDecision.allow())

        self.assertEqual(response, {"permission": "allow"})


if __name__ == "__main__":
    unittest.main()
