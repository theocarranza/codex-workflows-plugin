import os
import sys
import json
import tempfile
import shutil
import unittest
import subprocess
from datetime import datetime

# Resolve hook path relative to this test file
HOOK_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "skills", "codex_workflows", "scripts", "codex_enforce_hook.py")

class TestCodexEnforceHook(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory structure representing a project
        self.test_dir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        # Create git root mock
        os.makedirs(os.path.join(self.test_dir, ".git"))
        self.vault_dir = os.path.join(self.test_dir, "AI_Codex_SeuMeiSimples")
        os.makedirs(self.vault_dir)
        
    def tearDown(self):
        os.chdir(self.old_cwd)
        shutil.rmtree(self.test_dir)
        
    def run_hook(self, stdin_data):
        process = subprocess.Popen(
            [sys.executable, HOOK_PATH],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate(input=json.dumps(stdin_data))
        return json.loads(stdout.strip())
        
    def test_allow_generic_tool(self):
        stdin = {
            "name": "view_file",
            "arguments": {
                "AbsolutePath": os.path.join(self.test_dir, "lib", "main.dart")
            }
        }
        res = self.run_hook(stdin)
        self.assertEqual(res["permissionDecision"], "allow")
        
    def test_deny_destructive_delete(self):
        stdin = {
            "name": "run_command",
            "arguments": {
                "CommandLine": f"rm -rf {self.vault_dir}"
            }
        }
        res = self.run_hook(stdin)
        self.assertEqual(res["permissionDecision"], "deny")
        self.assertIn("Destructive deletions", res["reason"])
        
    def test_deny_unallowed_markdown(self):
        unallowed_path = os.path.join(self.test_dir, "docs", "notes.md")
        stdin = {
            "name": "view_file",
            "arguments": {
                "AbsolutePath": unallowed_path
            }
        }
        res = self.run_hook(stdin)
        self.assertEqual(res["permissionDecision"], "deny")
        self.assertIn("blocked", res["reason"])
        
    def test_allow_allowed_markdown(self):
        allowed_path = os.path.join(self.test_dir, "CLAUDE.md")
        stdin = {
            "name": "view_file",
            "arguments": {
                "AbsolutePath": allowed_path
            }
        }
        res = self.run_hook(stdin)
        self.assertEqual(res["permissionDecision"], "allow")
        
    def test_deny_write_without_session(self):
        code_file = os.path.join(self.test_dir, "lib", "utils.dart")
        stdin = {
            "name": "write_to_file",
            "arguments": {
                "TargetFile": code_file
            }
        }
        res = self.run_hook(stdin)
        self.assertEqual(res["permissionDecision"], "deny")
        self.assertIn("Write blocked. You must initialize today's Agent Session", res["reason"])
        
    def test_allow_write_with_session(self):
        # Create an active session file for today
        sessions_dir = os.path.join(self.vault_dir, "Agent_Sessions")
        os.makedirs(sessions_dir)
        today_str = datetime.now().strftime("%Y-%m-%d")
        session_file = os.path.join(sessions_dir, f"{today_str}-120000-session.md")
        with open(session_file, "w") as f:
            f.write("---\nnext: null\n---")
            
        code_file = os.path.join(self.test_dir, "lib", "utils.dart")
        stdin = {
            "name": "write_to_file",
            "arguments": {
                "TargetFile": code_file
            }
        }
        res = self.run_hook(stdin)
        self.assertEqual(res["permissionDecision"], "allow")

if __name__ == "__main__":
    unittest.main()
