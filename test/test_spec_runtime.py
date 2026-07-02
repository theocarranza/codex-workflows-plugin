import tempfile
import unittest
from pathlib import Path

from scripts.spec_actor_critic import (
    ReflectionState,
    actor_critic_loop,
    append_mistake,
    critic_review,
    load_mistakes,
)
from scripts.spec_runtime import infer_ticket_signal, kinds_for_signal, plan_spec_generation, slug_ticket_id


class TestSpecRuntime(unittest.TestCase):
    def test_slug_ticket_id(self):
        self.assertEqual(slug_ticket_id("PROJ-42"), "proj-42")

    def test_infer_bugfix_signal(self):
        self.assertEqual(infer_ticket_signal("BUG-1", "type: bug"), "bugfix")

    def test_plan_detects_missing_specs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan = plan_spec_generation(root, vault_folder="AI_Codex", ticket_id="FEATURE-9")
            self.assertTrue(plan.generation_required)
            self.assertIn("design-doc", plan.missing_kinds)
            (root / "AI_Codex" / "Specs" / plan.slug).mkdir(parents=True)
            (root / "AI_Codex" / "Specs" / plan.slug / "design-doc.md").write_text("# ok", encoding="utf-8")
            plan2 = plan_spec_generation(root, vault_folder="AI_Codex", ticket_id="FEATURE-9")
            self.assertIn("tech-spec", plan2.missing_kinds)
            self.assertNotIn("design-doc", plan2.missing_kinds)


class TestSpecActorCritic(unittest.TestCase):
    def test_critic_flags_missing_sections(self):
        critiques = critic_review("# Draft\n\nNo sections", spec_kind="adr")
        self.assertTrue(any("Status" in c for c in critiques))

    def test_circuit_breaker_on_identical_critiques(self):
        from scripts.spec_actor_critic import advance_reflection

        state = ReflectionState(attempt=2, last_critiques=("same issue",))
        next_state = advance_reflection(state, ["same issue"], max_attempts=3)
        self.assertTrue(next_state.blocked)

    def test_mistakes_repository_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertTrue(append_mistake("AI_Codex", root, flaw="Missing rollback", spec_kind="tech-spec", ticket_id="T-1"))
            mistakes = load_mistakes("AI_Codex", root)
            self.assertEqual(len(mistakes), 1)
            self.assertEqual(mistakes[0]["flaw"], "Missing rollback")


class TestSpecKinds(unittest.TestCase):
    def test_bugfix_kinds(self):
        self.assertIn("bugfix-spec", kinds_for_signal("bugfix"))


if __name__ == "__main__":
    unittest.main()
