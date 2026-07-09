import json
import subprocess
import sys
import unittest
from pathlib import Path


HOOK_PATH = Path(__file__).resolve().parents[2] / "skills" / "codex_workflows" / "scripts" / "claude_enforce_hook.py"
PROJECT_ROOT = Path(__file__).resolve().parents[2]


class TestClaudeHookSubprocess(unittest.TestCase):
    def _run_hook(self, payload: dict) -> dict:
        process = subprocess.Popen(
            [sys.executable, str(HOOK_PATH)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=PROJECT_ROOT,
        )
        stdout, stderr = process.communicate(input=json.dumps(payload))

        self.assertEqual(process.returncode, 0, stderr)
        return json.loads(stdout.strip())

    def test_bash_allow_output_matches_claude_pretooluse_schema(self):
        response = self._run_hook({"tool_name": "Bash", "tool_input": {"command": "echo hi"}})

        self.assertEqual(
            response,
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "allow",
                }
            },
        )

    def test_denied_markdown_read_uses_claude_permission_fields(self):
        response = self._run_hook(
            {
                "tool_name": "Read",
                "tool_input": {"file_path": str(PROJECT_ROOT / "docs" / "private.md")},
            }
        )

        hook_output = response["hookSpecificOutput"]
        self.assertEqual(hook_output["hookEventName"], "PreToolUse")
        self.assertEqual(hook_output["permissionDecision"], "deny")
        self.assertIn("permissionDecisionReason", hook_output)


if __name__ == "__main__":
    unittest.main()
