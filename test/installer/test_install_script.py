import os
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


class TestInstallScript(unittest.TestCase):
    def _make_release_zip(self, directory: Path) -> Path:
        zip_path = directory / "codex-workflows-plugin-test.zip"
        bootstrap = """
from __future__ import annotations

import os
import sys
from pathlib import Path

Path(os.environ["CODEX_WORKFLOWS_TEST_ARGV_OUT"]).write_text("\\n".join(sys.argv[1:]), encoding="utf-8")
"""
        with zipfile.ZipFile(zip_path, "w") as archive:
            archive.writestr("scripts/installer/bootstrap.py", bootstrap)
        return zip_path

    def _run_install_script(self, *args: str) -> list[str]:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            zip_path = self._make_release_zip(root)
            argv_path = root / "argv.txt"
            env = {
                **os.environ,
                "CODEX_WORKFLOWS_RELEASE_ZIP": str(zip_path),
                "CODEX_WORKFLOWS_TEST_ARGV_OUT": str(argv_path),
            }

            result = subprocess.run(
                ["bash", str(REPO_ROOT / "install.sh"), *args],
                cwd=REPO_ROOT,
                env=env,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            return argv_path.read_text(encoding="utf-8").splitlines()

    def test_defaults_to_all_agents_when_no_target_is_supplied(self):
        argv = self._run_install_script("--dest", "/tmp/project")

        self.assertTrue(argv[0].endswith(".zip"))
        self.assertEqual(argv[1:], ["--target", "all-agents", "--dest", "/tmp/project"])

    def test_preserves_explicit_target(self):
        argv = self._run_install_script("--target", "claude")

        self.assertEqual(argv[1:], ["--target", "claude"])

    def test_uninstall_does_not_add_default_target(self):
        argv = self._run_install_script("--uninstall", "--keep-runtime")

        self.assertEqual(argv[1:], ["--uninstall", "--keep-runtime"])


if __name__ == "__main__":
    unittest.main()
