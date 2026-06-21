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


def wire(install_dir: Path, target: str, project_dest: str | None) -> int:
    """Run the hook-wiring installer from the installed location.

    When project_dest is None the installer writes to each host's machine-global
    config location (e.g. ~/.claude/settings.json, ~/Antigravity_IDE/.agents/hooks.json).
    When project_dest is given, it writes project-level hook configs under that path.
    """
    # Load the installed cli module with its plugin_root resolved to install_dir.
    if str(install_dir) not in sys.path:
        sys.path.insert(0, str(install_dir))

    # Force a fresh load from the installed location regardless of cached modules.
    for mod_name in list(sys.modules):
        if mod_name.startswith("scripts.installer") or mod_name == "scripts":
            del sys.modules[mod_name]

    from scripts.installer.cli import install  # noqa: PLC0415
    from scripts.installer.merge import merge_hook_configs  # noqa: PLC0415
    from scripts.installer.targets import Target, target_global_config_path  # noqa: PLC0415

    client_names = {
        "claude": "Claude Code (claude-cli)",
        "gemini": "Gemini CLI (gemini)",
        "codex": "Codex CLI (codex-cli)",
        "antigravity": "Antigravity IDE (antigravity-cli)",
    }

    if target == "all-agents":
        targets = [t.value for t in Target if t not in {Target.UNIVERSAL, Target.ALL_AGENTS}]
    else:
        targets = [target]

    successful_wirings = []
    skipped_wirings = []

    for t in targets:
        client_name = client_names.get(t, t)
        if project_dest is not None:
            # Local project install
            try:
                result = install(t, dest_root=project_dest, plugin_root=install_dir)
                if result.config_paths:
                    config_path = Path(project_dest) / result.config_paths[0]
                    cmd = result.merged_config and _extract_command(result.merged_config)
                    successful_wirings.append((client_name, str(config_path), cmd))
                else:
                    skipped_wirings.append((client_name, "No config paths defined for target"))
            except Exception as e:
                if target != "all-agents":
                    print(f"Error wiring local target {t}: {e}", file=sys.stderr)
                    return 1
                skipped_wirings.append((client_name, f"Failed: {e}"))
        else:
            # Global machine install
            global_path = target_global_config_path(t)
            if global_path is None:
                if target != "all-agents":
                    print(f"Error: Could not locate the global configuration path for '{client_name}'.", file=sys.stderr)
                    print("Make sure the CLI/IDE client is installed or run once to initialize its config directory.", file=sys.stderr)
                    return 1
                skipped_wirings.append((client_name, "Config directory/installation not found on this machine"))
                continue

            try:
                # Compute desired config then write to the known global path.
                result = install(t, plugin_root=install_dir)  # dry-run to get merged_config
                on_disk = json.loads(global_path.read_text()) if global_path.exists() else None
                final_config = merge_hook_configs(on_disk, result.merged_config)
                global_path.parent.mkdir(parents=True, exist_ok=True)
                global_path.write_text(json.dumps(final_config, indent=2), encoding="utf-8")
                
                cmd = _extract_command(final_config)
                successful_wirings.append((client_name, str(global_path), cmd))
            except Exception as e:
                if target != "all-agents":
                    print(f"Error wiring global target {t}: {e}", file=sys.stderr)
                    return 1
                skipped_wirings.append((client_name, f"Failed to write config: {e}"))

    # If --target all-agents was specified, but we could not wire anything, exit with an error.
    if target == "all-agents" and not successful_wirings:
        print("Error: None of the agent CLI clients could be successfully wired.", file=sys.stderr)
        print("We checked the global configuration paths but none of the CLI/IDE installs were detected.", file=sys.stderr)
        print("Please check your installations or install clients (e.g. Claude Code or Gemini CLI) first.", file=sys.stderr)
        return 1

    # Print a beautiful summary of the wiring status
    print("\n" + "=" * 70)
    print("                      WIRING INSTALLATION SUMMARY                      ")
    print("=" * 70)
    
    if successful_wirings:
        print("Successfully Wired Clients:")
        for client, path, cmd in successful_wirings:
            print(f"  ✔ {client}")
            print(f"    Config file: {path}")
            if cmd:
                print(f"    Hook command: {cmd}")
            print()
    
    if skipped_wirings:
        print("Skipped Clients (not configured or missing):")
        for client, reason in skipped_wirings:
            print(f"  ✗ {client}")
            print(f"    Reason: {reason}")
            print()

    print("Further Instructions:")
    print("  1. Restart your active CLI / IDE client session to load the new hooks.")
    print("  2. To wire a local project with workflows and rules guides, run:")
    print(f"     python3 -m scripts.installer.bootstrap --target all-agents --dest /path/to/project")
    print("  3. To scaffold ticket drafts and generate YouTrack registration payloads:")
    print("     python3 scripts/create_ticket.py --summary \"Your ticket title\"")
    print("=" * 70 + "\n")

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

    # --dest is optional: omitting it wires the host's machine-global config location.

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
        dest_label = args.dest or "global config"
        print(f"\nWiring {args.target} → {dest_label} ...")
        return wire(install_dir, args.target, args.dest)
    else:
        # Better help message if no target is specified
        print("\n" + "=" * 70)
        print("                  INSTALLATION COMPLETED SUCCESSFULLY                  ")
        print("=" * 70)
        print(f"The plugin runtime assets have been installed to:")
        print(f"  {install_dir}")
        print()
        print("To wire the plugin to your agent hosts, run:")
        print(f"  python3 -m scripts.installer.bootstrap --target all-agents")
        print()
        print("To wire a specific local project repository (with rules and guides):")
        print(f"  python3 -m scripts.installer.bootstrap --target all-agents --dest /path/to/project")
        print("=" * 70 + "\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
