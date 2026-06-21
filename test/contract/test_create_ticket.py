import json
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch

from scripts.create_ticket import kebab_case, get_git_user_name


class TestCreateTicket(unittest.TestCase):
    def test_kebab_case(self):
        self.assertEqual(kebab_case("Hello World"), "hello-world")
        self.assertEqual(kebab_case("Redesign: card! on page."), "redesign-card-on-page")
        self.assertEqual(kebab_case("Already-Kebab"), "already-kebab")

    def test_get_git_user_name(self):
        name = get_git_user_name()
        self.assertTrue(len(name) > 0)

    @patch("scripts.create_ticket.find_templates_dir")
    @patch("scripts.create_ticket.find_vault_dir")
    @patch("sys.stdout")
    def test_create_ticket_scaffolding(self, mock_stdout, mock_find_vault, mock_find_templates):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            templates_dir = tmp_path / "templates"
            templates_dir.mkdir()
            
            task_template = templates_dir / "task-template.md"
            task_template.write_text(
                "---\nstatus: ready\ntype: task\nyoutrack: {YOUTRACK_ID}\narea: {AREA}\ncreated: {CREATED_DATE}\ncreator: {CREATOR}\n---\n# {YOUTRACK_ID}: {TITLE}", 
                encoding="utf-8"
            )
            
            vault_dir = tmp_path / "AI_Codex"
            vault_dir.mkdir()
            
            mock_find_templates.return_value = templates_dir
            mock_find_vault.return_value = vault_dir

            # We can run the script by calling main.
            # Let's import main and run it with args.
            import sys
            from scripts.create_ticket import main

            test_args = [
                "create_ticket.py",
                "--summary", "Test issue summary",
                "--type", "task",
                "--area", "db",
                "--story-points", "5",
                "--status", "ready",
            ]
            
            with patch.object(sys, "argv", test_args):
                exit_code = main()
                self.assertEqual(exit_code, 0)
            
            # Check draft file created
            ready_dir = vault_dir / "Tickets" / "Ready"
            draft_file = ready_dir / "draft-test-issue-summary.md"
            self.assertTrue(draft_file.is_file())
            
            content = draft_file.read_text(encoding="utf-8")
            self.assertIn("youtrack: DRAFT", content)
            self.assertIn("area: db", content)
            self.assertIn("Test issue summary", content)


if __name__ == "__main__":
    unittest.main()
