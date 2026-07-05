import tempfile
import unittest
from pathlib import Path

from scripts.artifact_profiles.resolution import resolution_profile
from scripts.artifact_profiles.spec import spec_profile
from scripts.artifact_reflection import (
    ArtifactContext,
    ReflectionEngine,
    ReflectionState,
    advance_reflection,
    append_mistake,
    load_mistakes,
)
from scripts.resolution_runtime import plan_resolution
from scripts.resolve_ticket_hook import on_resolve_ticket


class TestReflectionEngine(unittest.TestCase):
    def test_spec_profile_flags_missing_adr_sections(self):
        engine = ReflectionEngine(spec_profile("adr"))
        context = ArtifactContext(
            skill_name="write-spec",
            artifact_kind="adr",
            ticket_id="T-1",
            slug="t-1",
            draft="# Draft\n\nNo sections",
        )
        decision = engine.evaluate_draft(context)
        self.assertTrue(any("Status" in c for c in decision.critiques))

    def test_circuit_breaker_on_identical_critiques(self):
        state = ReflectionState(attempt=2, last_critiques=("same issue",))
        next_state = advance_reflection(state, ["same issue"], max_attempts=3)
        self.assertTrue(next_state.blocked)

    def test_unified_mistakes_repository(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertTrue(
                append_mistake(
                    "AI_Codex",
                    root,
                    flaw="Missing rollback",
                    skill_name="write-spec",
                    artifact_kind="tech-spec",
                    ticket_id="T-1",
                )
            )
            mistakes = load_mistakes("AI_Codex", root, skill_name="write-spec")
            self.assertEqual(len(mistakes), 1)
            self.assertEqual(mistakes[0]["artifact_kind"], "tech-spec")


class TestResolutionRuntime(unittest.TestCase):
    def test_plan_requires_resolution_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec_dir = root / "AI_Codex" / "Specs" / "feat-1"
            spec_dir.mkdir(parents=True)
            (spec_dir / "tech-spec.md").write_text("# spec", encoding="utf-8")
            plan = plan_resolution(root, vault_folder="AI_Codex", ticket_id="FEAT-1")
            self.assertFalse(plan.specs_missing)
            self.assertTrue(plan.resolution_required)
            directive = on_resolve_ticket(plan)
            self.assertIsNotNone(directive)
            self.assertEqual(directive["action"], "invoke-resolve-report")

    def test_resolution_critic_requires_spec_references(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec_dir = root / "AI_Codex" / "Specs" / "feat-1"
            spec_dir.mkdir(parents=True)
            (spec_dir / "tech-spec.md").write_text("# spec", encoding="utf-8")
            plan = plan_resolution(root, vault_folder="AI_Codex", ticket_id="FEAT-1")
            engine = ReflectionEngine(resolution_profile())
            context = ArtifactContext(
                skill_name="resolve-ticket",
                artifact_kind="resolution-report",
                ticket_id="FEAT-1",
                slug="feat-1",
                draft="# Short draft without required sections or evidence",
                ground_truth=plan.ground_truth(),
            )
            decision = engine.evaluate_draft(context)
            self.assertTrue(decision.critiques)


if __name__ == "__main__":
    unittest.main()
