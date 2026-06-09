"""Install and wire codex-workflows-plugin in one command.

Usage
-----
From the release zip:
    python3 bootstrap.py codex-workflows-plugin-0.2.4.zip --target all-agents --dest /path/to/project

From source after cloning:
    python3 -m scripts.installer.bootstrap --target claude --dest /path/to/project

Install only (no wiring):
    python3 bootstrap.py codex-workflows-plugin-0.2.4.zip
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import zipfile
from pathlib import Path

INSTALL_DIR = Path.home() / ".codex-workflows"

_RUNTIME_DIRS = ["scripts", "skills", ".agent", "hooks", ".codex-plugin"]


def install_from_zip(zip_path: Path, dest: Path) -> None:
    """Extract a release zip to dest, replacing any prior installation."""
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(dest)


def install_from_source(source_root: Path, dest: Path) -> None:
    """Copy runtime directories from source_root to dest."""
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    for dirname in _RUNTIME_DIRS:
        src = source_root / dirname
        if not src.exists():
            continue
        shutil.copytree(
            src,
            dest / dirname,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )


def wire(install_dir: Path, target: str, project_dest: str) -> int:
    """Run the hook-wiring installer from the installed location."""
    import importlib.util
    import types

    # Load the installed cli module with its plugin_root resolved to install_dir.
    # We insert install_dir into sys.path so its relative imports resolve correctly.
    if str(install_dir) not in sys.path:
        sys.path.insert(0, str(install_dir))

    # Force a fresh load from the installed location regardless of cached modules.
    for mod_name in list(sys.modules):
        if mod_name.startswith("scripts.installer") or mod_name == "scripts":
            del sys.modules[mod_name]

    from scripts.installer.cli import install  # noqa: PLC0415
    from scripts.installer.targets import Target  # noqa: PLC0415

    if target == "all-agents":
        targets = [t.value for t in Target if t not in {Target.UNIVERSAL, Target.ALL_AGENTS}]
    else:
        targets = [target]

    for t in targets:
        result = install(t, dest_root=project_dest, plugin_root=install_dir)
        output = {
            "target": result.target.value,
            "configPaths": list(result.config_paths),
            "command": (
                result.merged_config and
                _extract_command(result.merged_config)
            ),
        }
        print(json.dumps(output, indent=2))

    return 0


def _extract_command(config: dict) -> str | None:
    """Pull the first hook command out of any supported config shape."""
    for section in ("hooks", "codex-enforcer"):
        block = config.get(section, {})
        for event_hooks in block.values():
            if isinstance(event_hooks, list):
                for entry in event_hooks:
                    for hook in entry.get("hooks", []):
                        if "command" in hook:
                            return hook["command"]
    return None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Install and wire codex-workflows-plugin.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  # install + wire in one step\n"
            "  python3 bootstrap.py plugin.zip --target all-agents --dest /my/project\n\n"
            "  # install only\n"
            "  python3 bootstrap.py plugin.zip\n\n"
            "  # wire only (plugin already installed)\n"
            "  python3 bootstrap.py --target claude --dest /my/project"
        ),
    )
    parser.add_argument(
        "zip",
        nargs="?",
        help="Path to a release zip. Omit to install from the current source tree.",
    )
    parser.add_argument(
        "--install-dir",
        default=str(INSTALL_DIR),
        help=f"Where to install the plugin (default: {INSTALL_DIR})",
    )
    parser.add_argument(
        "--target",
        help="Agent host to wire: claude, codex, gemini, antigravity, all-agents.",
    )
    parser.add_argument(
        "--dest",
        help="Target project root to wire hooks into.",
    )
    args = parser.parse_args()

    if args.target and not args.dest:
        parser.error("--dest is required when --target is specified")

    install_dir = Path(args.install_dir).expanduser().resolve()

    # ── install step ──────────────────────────────────────────────────────────
    if args.zip:
        zip_path = Path(args.zip).expanduser().resolve()
        if not zip_path.exists():
            print(f"error: zip not found: {zip_path}", file=sys.stderr)
            return 1
        print(f"Installing {zip_path} → {install_dir} ...")
        install_from_zip(zip_path, install_dir)
        print(f"Installed to {install_dir}")
    elif args.target and install_dir.exists():
        pass  # wire-only: skip install
    else:
        source_root = Path(__file__).parent.parent.parent
        print(f"Installing from source → {install_dir} ...")
        install_from_source(source_root, install_dir)
        print(f"Installed to {install_dir}")

    # ── wire step ─────────────────────────────────────────────────────────────
    if args.target:
        print(f"\nWiring {args.target} → {args.dest} ...")
        return wire(install_dir, args.target, args.dest)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
