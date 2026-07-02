import json
import os
import tempfile
import unittest
from pathlib import Path

from scripts.orchestrator.engine import OrchestratorEngine
from scripts.orchestrator.mcp_server import process_message


class TestMCPServer(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.skills_dir = Path(self.test_dir.name)

        skill_path = self.skills_dir / "mock-skill"
        skill_path.mkdir()
        manifest_path = skill_path / "manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "name": "mock-skill",
                    "description": "A mock skill for testing",
                    "input_schema": {
                        "type": "object",
                        "properties": {"arg1": {"type": "string"}},
                    },
                    "output_signature": {"type": "object", "properties": {}},
                },
                f,
            )
        (skill_path / "SKILL.md").write_text("# Mock skill\n\nRun mock.\n", encoding="utf-8")
        self.engine = OrchestratorEngine(self.skills_dir)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_initialize(self):
        request = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
        response_str = process_message(request, self.engine)

        response = json.loads(response_str)
        self.assertEqual(response["id"], 1)
        self.assertIn("capabilities", response["result"])
        self.assertEqual(response["result"]["serverInfo"]["name"], "agentic-orchestrator")

    def test_tools_list(self):
        request = json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        response_str = process_message(request, self.engine)

        response = json.loads(response_str)
        tools = response["result"]["tools"]

        self.assertEqual(len(tools), 1)
        self.assertEqual(tools[0]["name"], "mock-skill")
        self.assertEqual(tools[0]["description"], "A mock skill for testing")
        self.assertIn("arg1", tools[0]["inputSchema"]["properties"])

    def test_tools_call(self):
        request = json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "mock-skill",
                    "arguments": {"arg1": "value"},
                },
            }
        )
        response_str = process_message(request, self.engine)

        response = json.loads(response_str)
        content = response["result"]["content"]

        self.assertEqual(len(content), 1)
        payload = json.loads(content[0]["text"])
        self.assertEqual(payload["status"], "completed")
        self.assertEqual(payload["output"]["skill"], "mock-skill")
        self.assertIn("prompt", payload["output"])


if __name__ == "__main__":
    unittest.main()
