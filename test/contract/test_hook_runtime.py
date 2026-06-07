import unittest

from scripts.adapters import (
    format_antigravity_decision,
    format_claude_decision,
    format_codex_decision,
    format_gemini_decision,
    parse_antigravity_payload,
    parse_claude_payload,
    parse_codex_payload,
    parse_gemini_payload,
)
from scripts.hook_runtime import select_adapter


class TestHookRuntime(unittest.TestCase):
    def test_select_adapter_maps_clients_to_expected_handlers(self):
        parser, formatter = select_adapter("codex")
        self.assertIs(parser, parse_codex_payload)
        self.assertIs(formatter, format_codex_decision)

        parser, formatter = select_adapter("gemini")
        self.assertIs(parser, parse_gemini_payload)
        self.assertIs(formatter, format_gemini_decision)

        parser, formatter = select_adapter("antigravity")
        self.assertIs(parser, parse_antigravity_payload)
        self.assertIs(formatter, format_antigravity_decision)

        parser, formatter = select_adapter("claude")
        self.assertIs(parser, parse_claude_payload)
        self.assertIs(formatter, format_claude_decision)


if __name__ == "__main__":
    unittest.main()
