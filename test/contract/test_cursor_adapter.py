import unittest

from scripts.adapters import format_cursor_decision, parse_cursor_payload
from scripts.policy import PolicyDecision


class TestCursorAdapter(unittest.TestCase):
    def test_parses_cursor_pretooluse_payload(self):
        event = parse_cursor_payload(
            {
                "tool_name": "Read",
                "tool_input": {"path": "/workspace/project/README.md"},
            },
            project_root="/workspace/project",
            vault_dir="/workspace/project/AI_Codex",
        )

        self.assertEqual(event.client, "cursor")
        self.assertEqual(event.tool_name, "Read")
        self.assertEqual(event.file_path, "/workspace/project/README.md")

    def test_formats_deny_as_permission_deny(self):
        response = format_cursor_decision(PolicyDecision.deny("Blocked by policy"))
        self.assertEqual(response["permission"], "deny")
        self.assertIn("Blocked by policy", response["agent_message"])

    def test_formats_allow(self):
        response = format_cursor_decision(PolicyDecision.allow())
        self.assertEqual(response["permission"], "allow")


if __name__ == "__main__":
    unittest.main()
