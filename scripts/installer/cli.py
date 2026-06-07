from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .merge import merge_hook_configs
from .targets import Target, normalize_target, target_config_paths, target_hook_command


@dataclass(frozen=True)
class InstallResult:
    target: Target
    written_codex_config: bool
    written_shared_assets: bool
    written_target_config: bool
    config_paths: tuple[str, ...] = ()
    merged_config: dict[str, Any] | None = None


def install(
    target: str | Target,
    profile: str = "generic",
    *,
    existing_hooks: dict[str, Any] | None = None,
) -> InstallResult:
    normalized_target = normalize_target(target)
    shared_assets = normalized_target in {Target.UNIVERSAL, Target.ALL_AGENTS}
    codex_config = normalized_target in {Target.CODEX, Target.ALL_AGENTS}
    target_config = normalized_target in {Target.CODEX, Target.GEMINI, Target.ANTIGRAVITY, Target.CLAUDE}
    config_paths = target_config_paths(normalized_target)
    merged_config = None

    if target_config:
        hook_command = target_hook_command(normalized_target)
        if normalized_target == Target.ANTIGRAVITY:
            desired_hooks = {
                "codex-enforcer": {
                    "enabled": True,
                    "PreToolUse": [
                        {
                            "matcher": ".*",
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": hook_command,
                                    "timeout": 5,
                                }
                            ],
                        }
                    ],
                }
            }
        elif normalized_target == Target.GEMINI:
            desired_hooks = {
                "hooks": {
                    "BeforeTool": [
                        {
                            "matcher": "*",
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": hook_command,
                                    "timeout": 5,
                                }
                            ],
                        }
                    ]
                }
            }
        elif normalized_target == Target.CLAUDE:
            desired_hooks = {
                "hooks": {
                    "PreToolUse": [
                        {
                            "matcher": "*",
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": hook_command,
                                    "timeout": 5,
                                }
                            ],
                        }
                    ]
                }
            }
        else:
            desired_hooks = {
                "hooks": {
                    "PreToolUse": [
                        {
                            "matcher": "^(Bash|apply_patch)$",
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": hook_command,
                                    "timeout": 5,
                                    "statusMessage": "Checking workflow policy",
                                }
                            ],
                        }
                    ]
                }
            }
        merged_config = merge_hook_configs(existing_hooks, desired_hooks)

    return InstallResult(
        target=normalized_target,
        written_codex_config=codex_config,
        written_shared_assets=shared_assets or target_config,
        written_target_config=target_config,
        config_paths=config_paths,
        merged_config=merged_config,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Install Codex workflow assets for a specific client target.")
    parser.add_argument("--target", default="codex", help="Target client: codex, gemini, antigravity, claude, universal, all-agents")
    parser.add_argument("--profile", default="generic", help="Installer profile name")
    parser.add_argument("--output", help="Optional path to write the merged hooks config")
    args = parser.parse_args()

    result = install(args.target, profile=args.profile)
    if args.output and result.merged_config is not None:
        output_path = Path(args.output).expanduser()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(result.merged_config, indent=2), encoding="utf-8")

    print(
        json.dumps(
            {
                "target": result.target.value,
                "writtenCodexConfig": result.written_codex_config,
                "writtenSharedAssets": result.written_shared_assets,
                "writtenTargetConfig": result.written_target_config,
                "configPaths": list(result.config_paths),
                "mergedConfig": result.merged_config,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
