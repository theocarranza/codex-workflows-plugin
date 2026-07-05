from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .targets import Target, target_config_paths, target_global_config_path


PLUGIN_NAME = "codex-workflows-plugin"
_MANAGED_HOOK_SCRIPTS = {
    "codex_enforce_hook.py",
    "gemini_enforce_hook.py",
    "antigravity_enforce_hook.py",
    "claude_enforce_hook.py",
    "cursor_enforce_hook.py",
}


@dataclass
class UninstallPlan:
    remove_paths: list[Path] = field(default_factory=list)
    prune_stops: dict[Path, Path] = field(default_factory=dict)
    write_json: dict[Path, dict[str, Any]] = field(default_factory=dict)
    messages: list[str] = field(default_factory=list)


def uninstall(
    install_dir: Path,
    *,
    dest: Path | None = None,
    keep_runtime: bool = False,
    dry_run: bool = False,
) -> UninstallPlan:
    plan = UninstallPlan()
    install_dir = install_dir.expanduser().resolve()
    plugin_name, version, author = _manifest_fields(install_dir)

    for config_path in _global_hook_paths():
        _plan_clean_hook_config(plan, config_path, prune_stop=Path.home())

    if dest is not None:
        project_root = dest.expanduser().resolve()
        for config_path in _project_hook_paths(project_root):
            _plan_clean_hook_config(plan, config_path, prune_stop=project_root)
        _plan_project_asset_cleanup(plan, project_root, install_dir)

    _plan_claude_registry_cleanup(plan, plugin_name)
    _plan_codex_marketplace_cleanup(plan, plugin_name)
    _plan_plugin_cache_cleanup(plan, plugin_name, version, author)

    if not keep_runtime:
        _plan_remove_path(plan, install_dir, prune_stop=install_dir.parent)

    if dry_run:
        plan.messages.insert(0, "DRY RUN: no filesystem changes applied.")
        return plan

    _apply_plan(plan)
    return plan


def strip_managed_hooks(config: dict[str, Any]) -> dict[str, Any]:
    return _strip_value(config)


def _strip_hook_entry(entry: dict[str, Any]) -> dict[str, Any] | None:
    command = entry.get("command")
    if isinstance(command, str) and _is_managed_command(command):
        return None

    if "hooks" not in entry or not isinstance(entry["hooks"], list):
        return dict(entry)

    hooks = []
    for hook in entry["hooks"]:
        if isinstance(hook, dict):
            command = hook.get("command")
            if isinstance(command, str) and _is_managed_command(command):
                continue
        hooks.append(hook)

    if not hooks:
        return None
    return {**entry, "hooks": hooks}


def _strip_value(value: Any) -> Any:
    if isinstance(value, dict):
        stripped_hook = _strip_hook_entry(value)
        if stripped_hook is None:
            return {}
        result = {}
        for key, child in stripped_hook.items():
            if key == "command":
                result[key] = child
                continue
            stripped = _strip_value(child)
            if not _is_empty(stripped):
                result[key] = stripped
        return result
    if isinstance(value, list):
        cleaned = []
        for entry in value:
            stripped = _strip_value(entry)
            if not _is_empty(stripped):
                cleaned.append(stripped)
        return cleaned
    return value


def _is_managed_command(command: str) -> bool:
    return any(script_name in command for script_name in _MANAGED_HOOK_SCRIPTS)


def _is_empty(value: Any) -> bool:
    if value == {} or value == []:
        return True
    return isinstance(value, dict) and set(value) <= {"enabled", "version"}


def _manifest_fields(install_dir: Path) -> tuple[str, str | None, str]:
    manifest_path = install_dir / ".codex-plugin" / "plugin.json"
    if not manifest_path.exists():
        manifest_path = install_dir / "plugin.json"
    if not manifest_path.exists():
        return PLUGIN_NAME, None, "local"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return PLUGIN_NAME, None, "local"

    name = manifest.get("name") or PLUGIN_NAME
    version = manifest.get("version")
    author_value = manifest.get("author")
    author = author_value.get("name", "local") if isinstance(author_value, dict) else "local"
    return name, version, author


def _global_hook_paths() -> list[Path]:
    paths = []
    for target in (
        Target.CODEX,
        Target.GEMINI,
        Target.ANTIGRAVITY,
        Target.ANTIGRAVITY_CLI,
        Target.CLAUDE,
        Target.CURSOR,
    ):
        path = target_global_config_path(target)
        if path is not None:
            paths.append(path)
    return paths


def _project_hook_paths(project_root: Path) -> list[Path]:
    paths = []
    for target in (
        Target.CODEX,
        Target.GEMINI,
        Target.ANTIGRAVITY,
        Target.ANTIGRAVITY_CLI,
        Target.CLAUDE,
        Target.CURSOR,
    ):
        for relative_path in target_config_paths(target):
            paths.append(project_root / relative_path)
    return paths


def _plan_clean_hook_config(plan: UninstallPlan, config_path: Path, *, prune_stop: Path) -> None:
    if not config_path.exists():
        return
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        plan.messages.append(f"Skipped invalid JSON config: {config_path}")
        return
    if not isinstance(config, dict):
        return

    cleaned = strip_managed_hooks(config)
    if cleaned == config:
        return
    if _is_empty(cleaned):
        _plan_remove_path(plan, config_path, prune_stop=prune_stop)
    else:
        plan.write_json[config_path] = cleaned
        plan.messages.append(f"Write cleaned config: {config_path}")


def _plan_claude_registry_cleanup(plan: UninstallPlan, plugin_name: str) -> None:
    registry_path = Path.home() / ".claude" / "plugins" / "installed_plugins.json"
    if not registry_path.exists():
        return
    try:
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        plan.messages.append(f"Skipped invalid JSON registry: {registry_path}")
        return

    plugins = registry.get("plugins")
    plugin_key = f"{plugin_name}@local"
    if not isinstance(plugins, dict) or plugin_key not in plugins:
        return

    cleaned = dict(registry)
    cleaned_plugins = dict(plugins)
    cleaned_plugins.pop(plugin_key, None)
    cleaned["plugins"] = cleaned_plugins
    plan.write_json[registry_path] = cleaned
    plan.messages.append(f"Write cleaned Claude registry: {registry_path}")


def _plan_codex_marketplace_cleanup(plan: UninstallPlan, plugin_name: str) -> None:
    marketplace_path = Path.home() / ".agents" / "plugins" / "marketplace.json"
    if not marketplace_path.exists():
        return
    try:
        marketplace = json.loads(marketplace_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        plan.messages.append(f"Skipped invalid JSON marketplace: {marketplace_path}")
        return

    plugins = marketplace.get("plugins")
    if not isinstance(plugins, list):
        return
    cleaned_plugins = [plugin for plugin in plugins if not (isinstance(plugin, dict) and plugin.get("name") == plugin_name)]
    if cleaned_plugins == plugins:
        return
    cleaned = dict(marketplace)
    cleaned["plugins"] = cleaned_plugins
    plan.write_json[marketplace_path] = cleaned
    plan.messages.append(f"Write cleaned Codex marketplace: {marketplace_path}")


def _plan_plugin_cache_cleanup(plan: UninstallPlan, plugin_name: str, version: str | None, author: str) -> None:
    home = Path.home()
    _plan_remove_path(plan, home / ".claude" / "plugins" / "cache" / "local" / plugin_name, prune_stop=home)
    _plan_remove_path(plan, home / ".cursor" / "plugins" / "cache" / "local" / plugin_name, prune_stop=home)
    if version:
        _plan_remove_path(plan, home / ".claude" / "plugins" / "cache" / "local" / plugin_name / version, prune_stop=home)
        _plan_remove_path(plan, home / ".cursor" / "plugins" / "cache" / "local" / plugin_name / version, prune_stop=home)
    _plan_remove_path(plan, home / ".gemini" / "antigravity-ide" / "plugins" / f"{author}.{plugin_name}.{plugin_name}", prune_stop=home)
    _plan_remove_path(plan, home / ".gemini" / "config" / "plugins" / plugin_name, prune_stop=home)
    _plan_remove_path(plan, home / ".codex" / "plugins" / "cache" / "local" / plugin_name, prune_stop=home)
    _plan_remove_path(plan, home / ".codex" / "plugins" / "cache" / "personal" / plugin_name, prune_stop=home)


def _plan_project_asset_cleanup(plan: UninstallPlan, project_root: Path, install_dir: Path) -> None:
    asset_root = install_dir / ".agent"
    if not asset_root.is_dir():
        return

    for rel in ("workflows", "rules"):
        source_dir = asset_root / rel
        project_dir = project_root / ".agent" / rel
        if not source_dir.is_dir() or not project_dir.exists():
            continue
        for source_file in source_dir.rglob("*"):
            if source_file.is_file():
                relative = source_file.relative_to(source_dir)
                _plan_remove_path(plan, project_dir / relative, prune_stop=project_root)


def _plan_remove_path(plan: UninstallPlan, path: Path, *, prune_stop: Path) -> None:
    if path in plan.remove_paths:
        return
    if path.exists() or path.is_symlink():
        plan.remove_paths.append(path)
        plan.prune_stops[path] = prune_stop
        plan.messages.append(f"Remove: {path}")


def _apply_plan(plan: UninstallPlan) -> None:
    for path, content in plan.write_json.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(content, indent=2), encoding="utf-8")

    for path in sorted(plan.remove_paths, key=lambda item: len(item.parts), reverse=True):
        if path.is_symlink() or path.is_file():
            path.unlink()
            _prune_empty_parents(path.parent, plan.prune_stops[path])
        elif path.is_dir():
            shutil.rmtree(path)
            _prune_empty_parents(path.parent, plan.prune_stops[path])


def _prune_empty_parents(start: Path, stop: Path) -> None:
    stop = stop.resolve()
    current = start
    while current.resolve() != stop and stop in current.resolve().parents:
        try:
            current.rmdir()
        except OSError:
            return
        current = current.parent
