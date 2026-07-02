from __future__ import annotations

from typing import Any

from .adapters import to_anthropic_dialect
from .handlers import get_handler
from .manifests import load_skill_instructions
from .schema import validate_inputs
from .state import Task, TaskState


def execute_skill(
    skill_name: str,
    arguments: dict[str, Any],
    *,
    skills_dir: str,
    manifest: dict[str, Any],
    task: Task,
) -> dict[str, Any]:
    """Run a skill handler and return structured output for evaluation."""
    input_critiques = validate_inputs(arguments, manifest)
    if input_critiques:
        raise ValueError("; ".join(input_critiques))

    instructions = load_skill_instructions(skills_dir, skill_name)
    handler = get_handler(skill_name)
    output = handler(arguments, manifest, instructions)

    if output.get("mode") == "instructions" and "prompt" not in output:
        output = {
            **output,
            "prompt": to_anthropic_dialect(instructions, task.copy_with(state=TaskState.IN_PROGRESS)),
        }
    return output
