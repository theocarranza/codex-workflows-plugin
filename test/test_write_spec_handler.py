import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts.orchestrator.handlers import handle_start_ticket, handle_write_spec


class TestWriteSpecHandler(unittest.TestCase):
    def test_write_spec_returns_instructions_without_draft(self):
        result = handle_write_spec(
            {"ticket_id": "T-1", "spec_kind": "tech-spec"},
            {"name": "write-spec"},
            "# write-spec\n",
        )
        self.assertEqual(result["mode"], "instructions")
        self.assertIn("template", result)

    def test_write_spec_critic_flags_bad_draft(self):
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.dict(os.environ, {"CODEX_PROJECT_ROOT": tmp}):
                result = handle_write_spec(
                    {
                        "ticket_id": "T-1",
                        "spec_kind": "adr",
                        "draft_content": "too short",
                    },
                    {"name": "write-spec"},
                    "# write-spec\n",
                )
                self.assertEqual(result["mode"], "instructions")
                self.assertTrue(result["critiques"])


class TestStartTicketSpecHook(unittest.TestCase):
    def test_start_ticket_triggers_spec_directive_when_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.dict(os.environ, {"CODEX_PROJECT_ROOT": tmp}):
                result = handle_start_ticket(
                    {"ticket_id": "FEATURE-100"},
                    {"name": "start-ticket"},
                    "# start-ticket\n",
                )
                self.assertTrue(result["generation_required"])
                self.assertIsNotNone(result["write_spec_directive"])
                self.assertIn("tech-spec", result["write_spec_directive"]["missing_kinds"])


if __name__ == "__main__":
    unittest.main()
