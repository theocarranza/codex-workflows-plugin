import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


CLI = [sys.executable, "-m", "scripts.installer.cli"]


class TestInstallerSmoke(unittest.TestCase):
    def _run_installer(self, target: str, output_path: Path) -> dict:
        completed = subprocess.run(
            CLI + ["--target", target, "--profile", "generic", "--output", str(output_path)],
            check=True,
            capture_output=True,
            text=True,
        )
        return json.loads(completed.stdout)

    def test_codex_target_writes_hooks_file(self):
        with tempfile.TemporaryDirectory() as tempdir:
            output_path = Path(tempdir) / "hooks.json"
            result = self._run_installer("codex", output_path)

            self.assertTrue(output_path.exists())
            self.assertEqual(result["configPaths"], ["hooks/hooks.json"])
            content = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(
                content["hooks"]["PreToolUse"][0]["hooks"][0]["command"],
                "python3 skills/codex_workflows/scripts/codex_enforce_hook.py",
            )

    def test_gemini_target_writes_settings_file(self):
        with tempfile.TemporaryDirectory() as tempdir:
            output_path = Path(tempdir) / "settings.json"
            result = self._run_installer("gemini", output_path)

            self.assertTrue(output_path.exists())
            self.assertEqual(result["configPaths"], [".gemini/settings.json"])
            content = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(
                content["hooks"]["BeforeTool"][0]["hooks"][0]["command"],
                "python3 skills/codex_workflows/scripts/gemini_enforce_hook.py",
            )

    def test_antigravity_target_writes_hooks_file(self):
        with tempfile.TemporaryDirectory() as tempdir:
            output_path = Path(tempdir) / "hooks.json"
            result = self._run_installer("antigravity", output_path)

            self.assertTrue(output_path.exists())
            self.assertEqual(result["configPaths"], [".agents/hooks.json"])
            content = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(
                content["codex-enforcer"]["PreToolUse"][0]["hooks"][0]["command"],
                "python3 skills/codex_workflows/scripts/antigravity_enforce_hook.py",
            )

    def test_claude_target_writes_settings_file(self):
        with tempfile.TemporaryDirectory() as tempdir:
            output_path = Path(tempdir) / "settings.json"
            result = self._run_installer("claude", output_path)

            self.assertTrue(output_path.exists())
            self.assertEqual(result["configPaths"], [".claude/settings.json"])
            content = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(
                content["hooks"]["PreToolUse"][0]["hooks"][0]["command"],
                "python3 skills/codex_workflows/scripts/claude_enforce_hook.py",
            )


if __name__ == "__main__":
    unittest.main()
