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

    def test_allow_ticket_move_ready_to_active(self):
        stdin = {
            "name": "run_command",
            "arguments": {
                "CommandLine": f"mv {self.vault_dir}/Tickets/Ready/task-123.md {self.vault_dir}/Tickets/Active/task-123.md"
            }
        }
        res = self.run_hook(stdin)
        self.assertEqual(res["permissionDecision"], "allow")

    def test_deny_ticket_move_ready_to_resolved(self):
        stdin = {
            "name": "run_command",
            "arguments": {
                "CommandLine": f"mv {self.vault_dir}/Tickets/Ready/task-123.md {self.vault_dir}/Tickets/Resolved/task-123.md"
            }
        }
        res = self.run_hook(stdin)
        self.assertEqual(res["permissionDecision"], "deny")
        self.assertIn("must be moved to Tickets/Active/", res["reason"])

    def test_allow_bugfix_move_active_to_resolved(self):
        stdin = {
            "name": "run_command",
            "arguments": {
                "CommandLine": f"mv {self.vault_dir}/Tickets/Active/bug-123.md {self.vault_dir}/Tickets/Resolved/bug-123.md"
            }
        }
        res = self.run_hook(stdin)
        self.assertEqual(res["permissionDecision"], "allow")

    def test_deny_bugfix_move_active_to_closed(self):
        stdin = {
            "name": "run_command",
            "arguments": {
                "CommandLine": f"mv {self.vault_dir}/Tickets/Active/bug-123.md {self.vault_dir}/Tickets/Closed/bug-123.md"
            }
        }
        res = self.run_hook(stdin)
        self.assertEqual(res["permissionDecision"], "deny")
        self.assertIn("must be moved to Tickets/Resolved/", res["reason"])

    def test_allow_task_move_active_to_closed(self):
        stdin = {
            "name": "run_command",
            "arguments": {
                "CommandLine": f"mv {self.vault_dir}/Tickets/Active/task-123.md {self.vault_dir}/Tickets/Closed/task-123.md"
            }
        }
        res = self.run_hook(stdin)
        self.assertEqual(res["permissionDecision"], "allow")

    def test_deny_task_move_active_to_resolved(self):
        stdin = {
            "name": "run_command",
            "arguments": {
                "CommandLine": f"mv {self.vault_dir}/Tickets/Active/task-123.md {self.vault_dir}/Tickets/Resolved/task-123.md"
            }
        }
        res = self.run_hook(stdin)
        self.assertEqual(res["permissionDecision"], "deny")
        self.assertIn("must be moved to Tickets/Closed/", res["reason"])

    def test_deny_write_task_to_resolved(self):
        stdin = {
            "name": "write_to_file",
            "arguments": {
                "TargetFile": f"{self.vault_dir}/Tickets/Resolved/task-123.md"
            }
        }
        res = self.run_hook(stdin)
        self.assertEqual(res["permissionDecision"], "deny")
        self.assertIn("Only bugfix tickets can be written to Tickets/Resolved/", res["reason"])

    def test_deny_write_bugfix_to_closed(self):
        stdin = {
            "name": "write_to_file",
            "arguments": {
                "TargetFile": f"{self.vault_dir}/Tickets/Closed/bug-123.md"
            }
        }
        res = self.run_hook(stdin)
        self.assertEqual(res["permissionDecision"], "deny")
        self.assertIn("Bugfix tickets cannot be written to Tickets/Closed/", res["reason"])

    def create_mock_transcript(self, issue_id, state):
        transcript_file = os.path.join(self.test_dir, "mock_transcript.jsonl")
        step = {
            "status": "DONE",
            "tool_calls": [
                {
                    "name": "call_mcp_tool",
                    "args": {
                        "ServerName": "youtrack",
                        "ToolName": "update_issue",
                        "Arguments": json.dumps({
                            "issueId": issue_id,
                            "customFields": {"State": state}
                        })
                    }
                }
            ]
        }
        with open(transcript_file, "w") as f:
            f.write(json.dumps(step) + "\n")
        return transcript_file

    def test_deny_write_active_without_youtrack_update(self):
        # Create ticket content with YouTrack ID
        content = "---\nyoutrack: SEUMEI-501\ntype: task\nstatus: active\n---"
        stdin = {
            "name": "write_to_file",
            "arguments": {
                "TargetFile": f"{self.vault_dir}/Tickets/Active/task-123.md",
                "CodeContent": content
            },
            "transcriptPath": os.path.join(self.test_dir, "nonexistent.jsonl")
        }
        res = self.run_hook(stdin)
        self.assertEqual(res["permissionDecision"], "deny")
        self.assertIn("You must update YouTrack issue", res["reason"])

    def test_allow_write_active_with_youtrack_update(self):
        # Create an active session file for today to pass session check
        sessions_dir = os.path.join(self.vault_dir, "Agent_Sessions")
        os.makedirs(sessions_dir, exist_ok=True)
        today_str = datetime.now().strftime("%Y-%m-%d")
        session_file = os.path.join(sessions_dir, f"{today_str}-120000-session.md")
        with open(session_file, "w") as f:
            f.write("---\nnext: null\n---")

        transcript_path = self.create_mock_transcript("SEUMEI-501", "In Progress")
        content = "---\nyoutrack: SEUMEI-501\ntype: task\nstatus: active\n---"
        stdin = {
            "name": "write_to_file",
            "arguments": {
                "TargetFile": f"{self.vault_dir}/Tickets/Active/task-123.md",
                "CodeContent": content
            },
            "transcriptPath": transcript_path
        }
        res = self.run_hook(stdin)
        self.assertEqual(res["permissionDecision"], "allow")

    def test_deny_write_closed_without_youtrack_done(self):
        content = "---\nyoutrack: SEUMEI-501\ntype: task\nstatus: closed\n---"
        stdin = {
            "name": "write_to_file",
            "arguments": {
                "TargetFile": f"{self.vault_dir}/Tickets/Closed/task-123.md",
                "CodeContent": content
            },
            "transcriptPath": os.path.join(self.test_dir, "nonexistent.jsonl")
        }
        res = self.run_hook(stdin)
        self.assertEqual(res["permissionDecision"], "deny")
        self.assertIn("You must update YouTrack issue", res["reason"])

    def test_allow_write_closed_with_youtrack_done(self):
        sessions_dir = os.path.join(self.vault_dir, "Agent_Sessions")
        os.makedirs(sessions_dir, exist_ok=True)
        today_str = datetime.now().strftime("%Y-%m-%d")
        session_file = os.path.join(sessions_dir, f"{today_str}-120000-session.md")
        with open(session_file, "w") as f:
            f.write("---\nnext: null\n---")

        transcript_path = self.create_mock_transcript("SEUMEI-501", "Done")
        content = "---\nyoutrack: SEUMEI-501\ntype: task\nstatus: closed\n---"
        stdin = {
            "name": "write_to_file",
            "arguments": {
                "TargetFile": f"{self.vault_dir}/Tickets/Closed/task-123.md",
                "CodeContent": content
            },
            "transcriptPath": transcript_path
        }
        res = self.run_hook(stdin)
        self.assertEqual(res["permissionDecision"], "allow")

if __name__ == "__main__":
    unittest.main()
