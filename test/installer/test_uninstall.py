import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).parent.parent.parent


def _run_bootstrap(home: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "scripts.installer.bootstrap", *args],
        cwd=PLUGIN_ROOT,
        capture_output=True,
        text=True,
        env={**os.environ, "HOME": str(home)},
    )


def _prepare_hosts(home: Path) -> None:
    for rel in (
        ".claude",
        ".cursor",
        ".gemini",
        ".gemini/config",
        ".gemini/antigravity-cli",
        ".gemini/antigravity-ide/plugins",
        ".gemini/config/plugins",
        "Antigravity_IDE/.agents",
    ):
        (home / rel).mkdir(parents=True, exist_ok=True)
    (home / "Antigravity_IDE" / "antigravity-ide").write_text("#!/bin/sh\n", encoding="utf-8")


class TestBootstrapUninstall(unittest.TestCase):
    def test_uninstall_removes_host_interventions_and_runtime_by_default(self):
        with tempfile.TemporaryDirectory() as temp_home:
            home = Path(temp_home)
            install_dir = home / ".codex-workflows"
            _prepare_hosts(home)
            marketplace = home / ".agents" / "plugins" / "marketplace.json"
            marketplace.parent.mkdir(parents=True)
            marketplace.write_text(
                json.dumps(
                    {
                        "name": "personal",
                        "plugins": [
                            {"name": "other-plugin"},
                            {"name": "codex-workflows-plugin", "source": {"path": "stale"}},
                        ],
                    }
                ),
                encoding="utf-8",
            )

            install = _run_bootstrap(home, "--install-dir", str(install_dir), "--target", "all-agents")
            self.assertEqual(install.returncode, 0, install.stdout + install.stderr)
            self.assertTrue(install_dir.is_dir())
            self.assertTrue((home / ".claude" / "plugins" / "installed_plugins.json").exists())
            self.assertTrue((home / ".cursor" / "plugins" / "cache" / "local" / "codex-workflows-plugin").exists())

            uninstall = _run_bootstrap(home, "--install-dir", str(install_dir), "--uninstall")
            self.assertEqual(uninstall.returncode, 0, uninstall.stdout + uninstall.stderr)

            self.assertFalse(install_dir.exists())
            self.assertFalse((home / ".claude" / "settings.json").exists())
            self.assertFalse((home / ".cursor" / "hooks.json").exists())
            self.assertFalse((home / ".gemini" / "settings.json").exists())
            self.assertFalse((home / ".gemini" / "config" / "hooks.json").exists())
            self.assertFalse((home / ".gemini" / "antigravity-cli" / "settings.json").exists())
            self.assertFalse((home / "Antigravity_IDE" / ".agents" / "hooks.json").exists())
            self.assertFalse((home / ".claude" / "plugins" / "cache" / "local" / "codex-workflows-plugin").exists())
            self.assertFalse((home / ".cursor" / "plugins" / "cache" / "local" / "codex-workflows-plugin").exists())
            self.assertFalse((home / ".gemini" / "antigravity-ide" / "plugins" / "local.codex-workflows-plugin.codex-workflows-plugin").exists())
            self.assertFalse((home / ".gemini" / "config" / "plugins" / "codex-workflows-plugin").exists())

            cleaned_marketplace = json.loads(marketplace.read_text(encoding="utf-8"))
            self.assertEqual([plugin["name"] for plugin in cleaned_marketplace["plugins"]], ["other-plugin"])

            registry = json.loads((home / ".claude" / "plugins" / "installed_plugins.json").read_text(encoding="utf-8"))
            self.assertNotIn("codex-workflows-plugin@local", registry["plugins"])

    def test_uninstall_dest_removes_generated_project_assets_and_preserves_unrelated_files(self):
        with tempfile.TemporaryDirectory() as temp_home, tempfile.TemporaryDirectory() as temp_project:
            home = Path(temp_home)
            project = Path(temp_project)
            install_dir = home / ".codex-workflows"
            _prepare_hosts(home)

            custom_rule = project / ".agent" / "rules" / "custom.md"
            custom_rule.parent.mkdir(parents=True)
            custom_rule.write_text("keep me\n", encoding="utf-8")

            install = _run_bootstrap(
                home,
                "--install-dir",
                str(install_dir),
                "--target",
                "all-agents",
                "--dest",
                str(project),
            )
            self.assertEqual(install.returncode, 0, install.stdout + install.stderr)
            self.assertTrue((project / ".agent" / "workflows").is_dir())
            self.assertTrue((project / ".agent" / "rules" / "rules-dart-functional-style.md").exists())
            claude_config = project / ".claude" / "settings.json"
            claude_settings = json.loads(claude_config.read_text(encoding="utf-8"))
            claude_settings["hooks"]["PreToolUse"].append(
                {
                    "matcher": "custom",
                    "hooks": [{"type": "command", "command": "echo keep"}],
                }
            )
            claude_config.write_text(json.dumps(claude_settings), encoding="utf-8")

            uninstall = _run_bootstrap(home, "--install-dir", str(install_dir), "--uninstall", "--dest", str(project))
            self.assertEqual(uninstall.returncode, 0, uninstall.stdout + uninstall.stderr)

            self.assertTrue(custom_rule.exists())
            self.assertEqual(custom_rule.read_text(encoding="utf-8"), "keep me\n")
            self.assertFalse((project / ".agent" / "workflows").exists())
            self.assertFalse((project / ".agent" / "rules" / "rules-dart-functional-style.md").exists())

            cleaned_claude = json.loads(claude_config.read_text(encoding="utf-8"))
            self.assertEqual(cleaned_claude["hooks"]["PreToolUse"][0]["matcher"], "custom")
            self.assertFalse((project / ".cursor" / "hooks.json").exists())

    def test_keep_runtime_removes_host_interventions_but_leaves_runtime_dir(self):
        with tempfile.TemporaryDirectory() as temp_home:
            home = Path(temp_home)
            install_dir = home / ".codex-workflows"
            _prepare_hosts(home)

            install = _run_bootstrap(home, "--install-dir", str(install_dir), "--target", "claude")
            self.assertEqual(install.returncode, 0, install.stdout + install.stderr)
            uninstall = _run_bootstrap(home, "--install-dir", str(install_dir), "--uninstall", "--keep-runtime")
            self.assertEqual(uninstall.returncode, 0, uninstall.stdout + uninstall.stderr)

            self.assertTrue(install_dir.is_dir())
            self.assertFalse((home / ".claude" / "settings.json").exists())
            registry = json.loads((home / ".claude" / "plugins" / "installed_plugins.json").read_text(encoding="utf-8"))
            self.assertNotIn("codex-workflows-plugin@local", registry["plugins"])

    def test_dry_run_does_not_change_filesystem(self):
        with tempfile.TemporaryDirectory() as temp_home:
            home = Path(temp_home)
            install_dir = home / ".codex-workflows"
            _prepare_hosts(home)

            install = _run_bootstrap(home, "--install-dir", str(install_dir), "--target", "claude")
            self.assertEqual(install.returncode, 0, install.stdout + install.stderr)
            before_settings = (home / ".claude" / "settings.json").read_text(encoding="utf-8")
            before_registry = (home / ".claude" / "plugins" / "installed_plugins.json").read_text(encoding="utf-8")

            uninstall = _run_bootstrap(home, "--install-dir", str(install_dir), "--uninstall", "--dry-run")
            self.assertEqual(uninstall.returncode, 0, uninstall.stdout + uninstall.stderr)

            self.assertTrue(install_dir.is_dir())
            self.assertEqual((home / ".claude" / "settings.json").read_text(encoding="utf-8"), before_settings)
            self.assertEqual((home / ".claude" / "plugins" / "installed_plugins.json").read_text(encoding="utf-8"), before_registry)
            self.assertIn("DRY RUN", uninstall.stdout)


if __name__ == "__main__":
    unittest.main()
