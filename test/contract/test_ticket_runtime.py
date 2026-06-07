import tempfile
import unittest
from pathlib import Path

from scripts.ticket_runtime import extract_ticket_paths, get_youtrack_issue_id_from_ticket


class TestTicketRuntime(unittest.TestCase):
    def test_extracts_ticket_paths_from_command_with_quotes(self):
        command = (
            'mv "/workspace/project/AI_Codex/Tickets/Ready/task-123.md" '
            '"/workspace/project/AI_Codex/Tickets/Active/task-123.md"'
        )

        source_path, destination_path = extract_ticket_paths(command)

        self.assertEqual(source_path, "/workspace/project/AI_Codex/Tickets/Ready/task-123.md")
        self.assertEqual(destination_path, "/workspace/project/AI_Codex/Tickets/Active/task-123.md")

    def test_extracts_youtrack_issue_id_from_ticket_frontmatter(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ticket_path = Path(tmpdir) / "task-123.md"
            ticket_path.write_text(
                "---\n"
                "youtrack: SEUMEI-42\n"
                "type: task\n"
                "---\n",
                encoding="utf-8",
            )

            issue_id = get_youtrack_issue_id_from_ticket(str(ticket_path))

            self.assertEqual(issue_id, "SEUMEI-42")


if __name__ == "__main__":
    unittest.main()
