"""Install codex-workflows-plugin to a stable local path (~/.codex-workflows/).

Usage
-----
From the release zip (recommended for end-users):
    python3 scripts/installer/bootstrap.py codex-workflows-plugin-0.2.3.zip

From source after cloning:
    python3 -m scripts.installer.bootstrap

After installation, wire the hook for each agent host from the installed location:
    python3 ~/.codex-workflows/scripts/installer/cli.py --target <target> --dest /path/to/project
"""

from __future__ import annotations

import argparse
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


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Install codex-workflows-plugin to a stable local path.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "After installation, wire your agent host:\n"
            "  python3 ~/.codex-workflows/scripts/installer/cli.py"
            " --target <claude|codex|gemini|antigravity|all-agents>"
            " --dest /path/to/your/project"
        ),
    )
    parser.add_argument(
        "zip",
        nargs="?",
        help="Path to a release zip. Omit to install from the current source tree.",
    )
    parser.add_argument(
        "--dest",
        default=str(INSTALL_DIR),
        help=f"Install destination (default: {INSTALL_DIR})",
    )
    args = parser.parse_args()
    dest = Path(args.dest).expanduser().resolve()

    if args.zip:
        zip_path = Path(args.zip).expanduser().resolve()
        if not zip_path.exists():
            print(f"error: zip not found: {zip_path}", file=sys.stderr)
            return 1
        print(f"Installing from {zip_path} → {dest} ...")
        install_from_zip(zip_path, dest)
    else:
        source_root = Path(__file__).parent.parent.parent
        print(f"Installing from source {source_root} → {dest} ...")
        install_from_source(source_root, dest)

    print(f"Done. Plugin installed to: {dest}")
    print()
    print("Next — wire the hook for your agent host:")
    print(
        f"  python3 {dest}/scripts/installer/cli.py"
        " --target <claude|codex|gemini|antigravity|all-agents>"
        " --dest /path/to/your/project"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
