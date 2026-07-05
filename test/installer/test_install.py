import json
import os
import shutil
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

from scripts.installer.bootstrap import INSTALL_DIR, install_from_source, install_from_zip


PLUGIN_ROOT = Path(__file__).parent.parent.parent


class TestInstallFromSource(unittest.TestCase):
    def setUp(self):
        self.dest = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.dest)

    def test_copies_runtime_dirs(self):
        install_from_source(PLUGIN_ROOT, self.dest)

        self.assertTrue((self.dest / "scripts").is_dir())
        self.assertTrue((self.dest / "skills").is_dir())
        self.assertTrue((self.dest / "commands").is_dir())
        self.assertTrue((self.dest / ".codex-plugin").is_dir())

    def test_copies_hook_entrypoints(self):
        install_from_source(PLUGIN_ROOT, self.dest)

        hook = self.dest / "skills" / "codex_workflows" / "scripts" / "antigravity_enforce_hook.py"
        self.assertTrue(hook.exists())
        cursor_hook = self.dest / "skills" / "codex_workflows" / "scripts" / "cursor_enforce_hook.py"
        self.assertTrue(cursor_hook.exists())

    def test_copies_policy_engine(self):
        install_from_source(PLUGIN_ROOT, self.dest)

        self.assertTrue((self.dest / "scripts" / "policy" / "engine.py").exists())

    def test_excludes_pycache(self):
        install_from_source(PLUGIN_ROOT, self.dest)

        pycache_dirs = list(self.dest.rglob("__pycache__"))
        self.assertEqual(pycache_dirs, [], "no __pycache__ dirs should be copied")

    def test_replaces_existing_install(self):
        (self.dest / "stale.txt").write_text("stale")
        install_from_source(PLUGIN_ROOT, self.dest)

        self.assertFalse((self.dest / "stale.txt").exists())

    def test_installed_cli_hook_command_points_to_dest(self):
        # When the CLI is run from the installed location, hook commands must
        # reference the installed path — not the original source repo.
        install_from_source(PLUGIN_ROOT, self.dest)

        import json
        import subprocess

        result = subprocess.run(
            [sys.executable, "-m", "scripts.installer.cli", "--target", "antigravity"],
            capture_output=True,
            text=True,
            cwd=self.dest,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        output = json.loads(result.stdout)
        cmd = output["mergedConfig"]["codex-enforcer"]["PreToolUse"][0]["hooks"][0]["command"]
        self.assertIn(str(self.dest), cmd, "hook command should reference the installed dest, not the source repo")


class TestInstallFromZip(unittest.TestCase):
    def setUp(self):
        self.dest = Path(tempfile.mkdtemp())
        self.zip_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.dest)
        shutil.rmtree(self.zip_dir)

    def _make_zip(self, files: dict[str, str]) -> Path:
        zip_path = self.zip_dir / "plugin.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            for name, content in files.items():
                zf.writestr(name, content)
        return zip_path

    def test_extracts_zip_contents(self):
        zip_path = self._make_zip({
            "scripts/hook_runtime.py": "# runtime",
            "skills/codex_workflows/scripts/antigravity_enforce_hook.py": "# hook",
            ".codex-plugin/plugin.json": json.dumps({"name": "test"}),
        })
        install_from_zip(zip_path, self.dest)

        self.assertTrue((self.dest / "scripts" / "hook_runtime.py").exists())
        self.assertTrue((self.dest / "skills" / "codex_workflows" / "scripts" / "antigravity_enforce_hook.py").exists())

    def test_replaces_existing_install(self):
        (self.dest / "stale.txt").write_text("stale")
        zip_path = self._make_zip({"scripts/foo.py": "# new"})
        install_from_zip(zip_path, self.dest)

        self.assertFalse((self.dest / "stale.txt").exists())
        self.assertTrue((self.dest / "scripts" / "foo.py").exists())


class TestInstallCLI(unittest.TestCase):
    def _run(self, *args) -> tuple[int, str]:
        import subprocess
        with tempfile.TemporaryDirectory() as home:
            result = subprocess.run(
                [sys.executable, "-m", "scripts.installer.bootstrap", *args],
                capture_output=True,
                text=True,
                env={**os.environ, "HOME": home},
            )
        return result.returncode, result.stdout + result.stderr

    def test_missing_zip_returns_error(self):
        with tempfile.TemporaryDirectory() as dest:
            code, output = self._run("/nonexistent/plugin.zip", "--dest", dest)
            self.assertNotEqual(code, 0)
            self.assertIn("not found", output)

    def test_install_from_source_via_cli(self):
        with tempfile.TemporaryDirectory() as dest:
            code, output = self._run("--install-dir", dest)
            self.assertEqual(code, 0)
            self.assertIn("Installed to", output)
            self.assertTrue((Path(dest) / "scripts").is_dir())


if __name__ == "__main__":
    unittest.main()
