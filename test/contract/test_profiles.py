import unittest

from scripts.profiles import load_profile


class TestProfiles(unittest.TestCase):
    def test_generic_profile_resolves_workspace_paths(self):
        profile = load_profile("generic")

        self.assertEqual(profile.vault_name, "AI_Codex")
        self.assertTrue(profile.ticket_root.endswith("Tickets"))
        self.assertTrue(profile.agent_sessions_root.endswith("Agent_Sessions"))

    def test_flutter_profile_uses_flutter_verification(self):
        profile = load_profile("flutter")

        self.assertEqual(profile.branch_name, "develop")
        self.assertEqual(profile.verify_command, "flutter test")

    def test_unknown_profile_raises(self):
        with self.assertRaises(ValueError):
            load_profile("unknown")


if __name__ == "__main__":
    unittest.main()
