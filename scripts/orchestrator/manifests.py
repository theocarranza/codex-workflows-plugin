from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def read_manifests(skills_dir: str | Path) -> list[dict[str, Any]]:
    """Discover all manifest.json files under skills/."""
    manifests: list[dict[str, Any]] = []
    base_path = Path(skills_dir)
    if not base_path.is_dir():
        return manifests

    for skill_path in sorted(base_path.iterdir()):
        if not skill_path.is_dir():
            continue
        manifest_file = skill_path / "manifest.json"
        if not manifest_file.is_file():
            continue
        try:
            data = json.loads(manifest_file.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                manifests.append(data)
        except (json.JSONDecodeError, OSError):
            continue
    return manifests


def manifest_by_name(skills_dir: str | Path) -> dict[str, dict[str, Any]]:
    return {m["name"]: m for m in read_manifests(skills_dir) if m.get("name")}


def load_skill_instructions(skills_dir: str | Path, skill_name: str) -> str:
    skill_md = Path(skills_dir) / skill_name / "SKILL.md"
    if not skill_md.is_file():
        raise FileNotFoundError(f"Missing SKILL.md for skill '{skill_name}'")
    return skill_md.read_text(encoding="utf-8")
