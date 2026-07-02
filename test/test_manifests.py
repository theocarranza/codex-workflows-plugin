import json
import tempfile
import unittest
from pathlib import Path

from scripts.orchestrator.manifests import manifest_by_name, read_manifests


class TestManifests(unittest.TestCase):
    def test_ignores_non_object_manifest_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir) / "bad-skill"
            skill_dir.mkdir()
            (skill_dir / "manifest.json").write_text(json.dumps(["not", "a", "dict"]), encoding="utf-8")

            good_dir = Path(tmpdir) / "good-skill"
            good_dir.mkdir()
            (good_dir / "manifest.json").write_text(
                json.dumps({"name": "good-skill", "description": "ok"}),
                encoding="utf-8",
            )

            manifests = read_manifests(tmpdir)
            self.assertEqual(len(manifests), 1)
            self.assertEqual(manifest_by_name(tmpdir)["good-skill"]["name"], "good-skill")


if __name__ == "__main__":
    unittest.main()
