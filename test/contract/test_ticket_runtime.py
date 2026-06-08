import json
import tempfile
import unittest
from pathlib import Path

from scripts.ticket_runtime import (
    YouTrackCheckResult,
    check_youtrack_state_in_transcript,
    extract_ticket_paths,
    get_youtrack_issue_id_from_ticket,
    infer_is_bugfix_ticket,
)


class TestExtractTicketPaths(unittest.TestCase):
    def test_extracts_ticket_paths_from_command_with_quotes(self):
        command = (
            'mv "/workspace/project/AI_Codex/Tickets/Ready/task-123.md" '
            '"/workspace/project/AI_Codex/Tickets/Active/task-123.md"'
        )

        source_path, destination_path = extract_ticket_paths(command)

        self.assertEqual(source_path, "/workspace/project/AI_Codex/Tickets/Ready/task-123.md")
        self.assertEqual(destination_path, "/workspace/project/AI_Codex/Tickets/Active/task-123.md")

    def test_returns_none_for_command_with_single_ticket_path(self):
        """Returns (None, None) when fewer than 2 Tickets/ tokens are present."""
        command = "mv /project/AI_Codex/Tickets/Ready/task-123.md /project/lib/other.dart"

        source_path, destination_path = extract_ticket_paths(command)

        self.assertIsNone(source_path)
        self.assertIsNone(destination_path)

    def test_handles_git_mv_syntax(self):
        """Handles `git mv` commands that also contain Tickets/ paths."""
        command = (
            "git mv AI_Codex/Tickets/Active/bug-456.md "
            "AI_Codex/Tickets/Resolved/bug-456.md"
        )

        source_path, destination_path = extract_ticket_paths(command)

        self.assertEqual(source_path, "AI_Codex/Tickets/Active/bug-456.md")
        self.assertEqual(destination_path, "AI_Codex/Tickets/Resolved/bug-456.md")

    def test_returns_none_for_non_ticket_command(self):
        """Returns (None, None) when no Tickets/ paths are present at all."""
        source_path, destination_path = extract_ticket_paths("flutter test --coverage")

        self.assertIsNone(source_path)
        self.assertIsNone(destination_path)


class TestYouTrackTranscriptCheck(unittest.TestCase):
    def _write_transcript(self, tmpdir: str, steps: list[dict]) -> str:
        path = str(Path(tmpdir) / "transcript.jsonl")
        with open(path, "w", encoding="utf-8") as f:
            for step in steps:
                f.write(json.dumps(step) + "\n")
        return path

    def test_returns_transcript_missing_when_path_is_none(self):
        result = check_youtrack_state_in_transcript(None, "SEUMEI-42", ["In Progress"])

        self.assertFalse(result.verified)
        self.assertEqual(result.reason, "transcript_missing")

    def test_returns_transcript_missing_when_file_absent(self):
        result = check_youtrack_state_in_transcript("/nonexistent/path.jsonl", "SEUMEI-42", ["In Progress"])

        self.assertFalse(result.verified)
        self.assertEqual(result.reason, "transcript_missing")

    def test_returns_state_not_found_when_no_matching_call(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            transcript_path = self._write_transcript(tmpdir, [
                {"status": "DONE", "tool_calls": []}
            ])

            result = check_youtrack_state_in_transcript(transcript_path, "SEUMEI-42", ["In Progress"])

        self.assertFalse(result.verified)
        self.assertEqual(result.reason, "state_not_found")

    def test_returns_ok_when_state_matches(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            transcript_path = self._write_transcript(tmpdir, [
                {
                    "status": "DONE",
                    "tool_calls": [
                        {
                            "name": "call_mcp_tool",
                            "args": {
                                "ServerName": "youtrack",
                                "ToolName": "update_issue",
                                "Arguments": json.dumps({
                                    "issueId": "SEUMEI-42",
                                    "customFields": {"State": "In Progress"},
                                }),
                            },
                        }
                    ],
                }
            ])

            result = check_youtrack_state_in_transcript(transcript_path, "SEUMEI-42", ["In Progress"])

        self.assertTrue(result.verified)
        self.assertEqual(result.reason, "ok")

    def test_returns_timer_incorrect_when_timer_does_not_match(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            transcript_path = self._write_transcript(tmpdir, [
                {
                    "status": "DONE",
                    "tool_calls": [
                        {
                            "name": "call_mcp_tool",
                            "args": {
                                "ServerName": "youtrack",
                                "ToolName": "update_issue",
                                "Arguments": json.dumps({
                                    "issueId": "SEUMEI-42",
                                    "customFields": {"State": "In Progress", "Timer": "Stop"},
                                }),
                            },
                        }
                    ],
                }
            ])

            result = check_youtrack_state_in_transcript(
                transcript_path, "SEUMEI-42", ["In Progress"], expected_timer="Start"
            )

        self.assertFalse(result.verified)
        self.assertEqual(result.reason, "timer_incorrect")

    def test_returns_spent_time_missing_when_required_but_absent(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            transcript_path = self._write_transcript(tmpdir, [
                {
                    "status": "DONE",
                    "tool_calls": [
                        {
                            "name": "call_mcp_tool",
                            "args": {
                                "ServerName": "youtrack",
                                "ToolName": "update_issue",
                                "Arguments": json.dumps({
                                    "issueId": "SEUMEI-42",
                                    "customFields": {"State": "Done", "Timer": "Stop"},
                                }),
                            },
                        }
                    ],
                }
            ])

            result = check_youtrack_state_in_transcript(
                transcript_path, "SEUMEI-42", ["Done"], expected_timer="Stop", require_spent_time=True
            )

        self.assertFalse(result.verified)
        self.assertEqual(result.reason, "spent_time_missing")

    def test_returns_ok_when_timer_and_spent_time_match_and_exist(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            transcript_path = self._write_transcript(tmpdir, [
                {
                    "status": "DONE",
                    "tool_calls": [
                        {
                            "name": "call_mcp_tool",
                            "args": {
                                "ServerName": "youtrack",
                                "ToolName": "update_issue",
                                "Arguments": json.dumps({
                                    "issueId": "SEUMEI-42",
                                    "customFields": {"State": "Done", "Timer": "Stop", "Spent time": "3h 30m"},
                                }),
                            },
                        }
                    ],
                }
            ])

            result = check_youtrack_state_in_transcript(
                transcript_path, "SEUMEI-42", ["Done"], expected_timer="Stop", require_spent_time=True
            )

        self.assertTrue(result.verified)
        self.assertEqual(result.reason, "ok")


class TestYouTrackIssueIdFromTicket(unittest.TestCase):
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


class TestInferIsBugfixTicket(unittest.TestCase):
    def test_infer_bugfix_false_for_filename_with_bug_word_but_no_frontmatter(self):
        """A file named debug-something.md must NOT be inferred as a bugfix."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ticket_path = Path(tmpdir) / "debug-something.md"
            ticket_path.write_text(
                "---\ntype: task\n---\n# Debug something\n",
                encoding="utf-8",
            )

            result = infer_is_bugfix_ticket(str(ticket_path))

        self.assertFalse(result)

    def test_infer_bugfix_true_for_frontmatter_type_bugfix(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ticket_path = Path(tmpdir) / "my-fix.md"
            ticket_path.write_text(
                "---\ntype: bugfix\nyoutrack: SEUMEI-99\n---\n",
                encoding="utf-8",
            )

            result = infer_is_bugfix_ticket(str(ticket_path))

        self.assertTrue(result)

    def test_infer_bugfix_false_for_absent_file(self):
        result = infer_is_bugfix_ticket("/nonexistent/path/ticket.md")

        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()

