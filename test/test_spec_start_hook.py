import unittest

from scripts.spec_runtime import SpecPlan
from scripts.spec_start_hook import on_start_ticket


class TestSpecStartHook(unittest.TestCase):
    def test_returns_none_when_specs_exist(self):
        plan = SpecPlan(
            ticket_id="T-1",
            slug="t-1",
            specs_dir="AI_Codex/Specs/t-1",
            existing_specs=("tech-spec.md",),
            missing_kinds=(),
            generation_required=False,
        )
        self.assertIsNone(on_start_ticket(plan))

    def test_returns_directive_when_specs_missing(self):
        plan = SpecPlan(
            ticket_id="T-2",
            slug="t-2",
            specs_dir="AI_Codex/Specs/t-2",
            existing_specs=(),
            missing_kinds=("tech-spec",),
            generation_required=True,
            source_hints={"description": "Build feature X"},
        )
        directive = on_start_ticket(plan)
        self.assertIsNotNone(directive)
        self.assertEqual(directive["action"], "invoke-write-spec")
        self.assertIn("tech-spec", directive["missing_kinds"])


if __name__ == "__main__":
    unittest.main()
