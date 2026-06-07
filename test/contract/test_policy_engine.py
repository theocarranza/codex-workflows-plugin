import os
import unittest

from scripts.policy import CanonicalToolEvent, evaluate


class TestPolicyEngine(unittest.TestCase):
    def test_denies_destructive_rm_inside_vault(self):
        event = CanonicalToolEvent(
            client="codex",
            tool_name="Bash",
            command="rm -rf AI_Codex",
            workspace_root="/tmp/project",
            vault_dir="/tmp/project/AI_Codex",
        )

        decision = evaluate(event)

        self.assertTrue(decision.is_denied())

    def test_denies_markdown_outside_allowlist(self):
        event = CanonicalToolEvent(
            client="codex",
            tool_name="view_file",
            file_path="/tmp/project/docs/notes.md",
            markdown_allowed=False,
        )

        decision = evaluate(event)

        self.assertTrue(decision.is_denied())

    def test_denies_write_without_active_session(self):
        event = CanonicalToolEvent(
            client="codex",
            tool_name="write_to_file",
            file_path="/tmp/project/lib/utils.dart",
            session_active=False,
        )

        decision = evaluate(event)

        self.assertTrue(decision.is_denied())

    def test_denies_ready_ticket_move_to_resolved(self):
        event = CanonicalToolEvent(
            client="codex",
            tool_name="Bash",
            command="mv /tmp/project/AI_Codex/Tickets/Ready/task-123.md /tmp/project/AI_Codex/Tickets/Resolved/task-123.md",
            source_path="/tmp/project/AI_Codex/Tickets/Ready/task-123.md",
            destination_path="/tmp/project/AI_Codex/Tickets/Resolved/task-123.md",
        )

        decision = evaluate(event)

        self.assertTrue(decision.is_denied())

    def test_allows_active_task_move_to_closed(self):
        event = CanonicalToolEvent(
            client="codex",
            tool_name="Bash",
            command="mv /tmp/project/AI_Codex/Tickets/Active/task-123.md /tmp/project/AI_Codex/Tickets/Closed/task-123.md",
            source_path="/tmp/project/AI_Codex/Tickets/Active/task-123.md",
            destination_path="/tmp/project/AI_Codex/Tickets/Closed/task-123.md",
            is_bugfix_ticket=False,
        )

        decision = evaluate(event)

        self.assertFalse(decision.is_denied())


if __name__ == "__main__":
    unittest.main()
