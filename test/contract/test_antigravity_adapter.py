import unittest
import json
from pathlib import Path

from scripts.adapters import format_antigravity_decision, parse_antigravity_payload
from scripts.policy import PolicyDecision


FIXTURE_PATH = Path(__file__).resolve().parents[1] / "fixtures" / "antigravity_pretooluse.json"


class TestAntigravityAdapter(unittest.TestCase):
    def test_parses_antigravity_payload_shape(self):
        payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

        event = parse_antigravity_payload(payload, project_root="/workspace/project", vault_dir="/workspace/project/AI_Codex")

        self.assertEqual(event.client, "antigravity")
        self.assertEqual(event.tool_name, "run_command")
        self.assertEqual(event.command, "mv /workspace/project/AI_Codex/Tickets/Active/task-123.md /workspace/project/AI_Codex/Tickets/Closed/task-123.md")
        self.assertEqual(event.source_path, "/workspace/project/AI_Codex/Tickets/Active/task-123.md")
        self.assertEqual(event.destination_path, "/workspace/project/AI_Codex/Tickets/Closed/task-123.md")

    def test_formats_antigravity_decision(self):
        decision = PolicyDecision.allow()

        response = format_antigravity_decision(decision)

        self.assertEqual(response["decision"], "allow")
        self.assertNotIn("reason", response)


if __name__ == "__main__":
    unittest.main()
