from __future__ import annotations

from enum import Enum


class Target(str, Enum):
    CODEX = "codex"
    GEMINI = "gemini"
    ANTIGRAVITY = "antigravity"
    CLAUDE = "claude"
    UNIVERSAL = "universal"
    ALL_AGENTS = "all-agents"


def normalize_target(target: str | Target) -> Target:
    if isinstance(target, Target):
        return target
    normalized = target.strip().lower().replace("_", "-")
    for candidate in Target:
        if candidate.value == normalized:
            return candidate
    raise ValueError(f"Unsupported installer target: {target}")


def target_config_paths(target: str | Target) -> tuple[str, ...]:
    normalized = normalize_target(target)
    if normalized == Target.CODEX:
        return ("hooks/hooks.json",)
    if normalized == Target.GEMINI:
        return (".gemini/settings.json",)
    if normalized == Target.ANTIGRAVITY:
        return (".agents/hooks.json",)
    if normalized == Target.CLAUDE:
        return (".claude/settings.json",)
    if normalized in {Target.UNIVERSAL, Target.ALL_AGENTS}:
        return ()
    return ()


def target_hook_command(target: str | Target) -> str | None:
    normalized = normalize_target(target)
    if normalized == Target.CODEX:
        return "python3 skills/codex_workflows/scripts/codex_enforce_hook.py"
    if normalized == Target.GEMINI:
        return "python3 skills/codex_workflows/scripts/gemini_enforce_hook.py"
    if normalized == Target.ANTIGRAVITY:
        return "python3 skills/codex_workflows/scripts/antigravity_enforce_hook.py"
    if normalized == Target.CLAUDE:
        return "python3 skills/codex_workflows/scripts/claude_enforce_hook.py"
    return None
