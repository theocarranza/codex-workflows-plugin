from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

PLACEHOLDER_PATTERN = re.compile(r"\b(TODO|TBD|FIXME|XXX|\?\?\?|<fill[- ]?in>)\b", re.I)
MISTAKES_FILENAME = "mistakes.json"
LEGACY_SPEC_MISTAKES = ("Specs", "_mistakes", MISTAKES_FILENAME)


@dataclass
class ReflectionState:
    attempt: int = 0
    last_critiques: tuple[str, ...] = ()
    blocked: bool = False
    recorded_mistake: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "attempt": self.attempt,
            "last_critiques": list(self.last_critiques),
            "blocked": self.blocked,
            "recorded_mistake": self.recorded_mistake,
        }


@dataclass(frozen=True)
class ArtifactContext:
    """Inputs for one Actor-Critic evaluation pass."""

    skill_name: str
    artifact_kind: str
    ticket_id: str
    slug: str
    draft: str
    ground_truth: dict[str, Any] = field(default_factory=dict)
    max_attempts: int = 3

    @property
    def has_draft(self) -> bool:
        return bool(self.draft.strip())


@dataclass(frozen=True)
class CriticProfile:
    """Rule-based Critic configuration for a skill/artifact kind."""

    skill_name: str
    artifact_kind: str
    min_length: int = 120
    required_headings: tuple[str, ...] = ()
    extra_checks: tuple[Callable[[str, ArtifactContext], list[str]], ...] = ()

    def evaluate(self, draft: str, context: ArtifactContext, mistakes: list[dict[str, Any]]) -> list[str]:
        critiques: list[str] = []
        text = draft.strip()
        if len(text) < self.min_length:
            critiques.append(f"Draft is too short to be actionable (minimum ~{self.min_length} characters).")

        for heading in self.required_headings:
            if not re.search(rf"(?im)^#{{1,3}}\s+{re.escape(heading)}\s*$", text):
                critiques.append(f"Missing required section heading: '{heading}'.")

        if PLACEHOLDER_PATTERN.search(text):
            critiques.append("Draft contains placeholder tokens (TODO/TBD/FIXME) — resolve before persisting.")

        for check in self.extra_checks:
            critiques.extend(check(text, context))

        for mistake in mistakes:
            flaw = str(mistake.get("flaw", "")).strip()
            if flaw and flaw.lower() in text.lower():
                critiques.append(f"Repeats a recorded flaw from mistakes repo: {flaw}")

        return critiques


@dataclass(frozen=True)
class ArtifactDecision:
    critiques: list[str]
    reflection: ReflectionState
    mode: str
    blocked: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "critiques": self.critiques,
            "reflection": self.reflection.to_dict(),
            "mode": self.mode,
            "blocked": self.blocked,
        }


def mistakes_path(vault_folder: str, project_root: Path | None) -> Path | None:
    if project_root is None:
        return None
    return project_root / vault_folder / "_mistakes" / MISTAKES_FILENAME


def legacy_spec_mistakes_path(vault_folder: str, project_root: Path | None) -> Path | None:
    if project_root is None:
        return None
    return project_root.joinpath(vault_folder, *LEGACY_SPEC_MISTAKES)


def load_mistakes(
    vault_folder: str,
    project_root: Path | None,
    *,
    skill_name: str | None = None,
    artifact_kind: str | None = None,
) -> list[dict[str, Any]]:
    paths: list[Path] = []
    primary = mistakes_path(vault_folder, project_root)
    legacy = legacy_spec_mistakes_path(vault_folder, project_root)
    if primary is not None:
        paths.append(primary)
    if legacy is not None:
        paths.append(legacy)

    merged: list[dict[str, Any]] = []
    seen: set[str] = set()
    for path in paths:
        if not path.is_file():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for item in data.get("mistakes", []):
            if not isinstance(item, dict):
                continue
            if skill_name and item.get("skill") not in {None, skill_name}:
                if item.get("skill") is not None:
                    continue
            if artifact_kind and item.get("artifact_kind") not in {None, artifact_kind}:
                if item.get("artifact_kind") is not None and item.get("spec_kind") != artifact_kind:
                    continue
            key = json.dumps(item, sort_keys=True)
            if key in seen:
                continue
            seen.add(key)
            merged.append(item)
    return merged


def append_mistake(
    vault_folder: str,
    project_root: Path | None,
    *,
    flaw: str,
    skill_name: str,
    artifact_kind: str,
    ticket_id: str,
) -> bool:
    path = mistakes_path(vault_folder, project_root)
    if path is None:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = load_mistakes(vault_folder, project_root)
    existing.append(
        {
            "flaw": flaw,
            "skill": skill_name,
            "artifact_kind": artifact_kind,
            "ticket": ticket_id,
        }
    )
    try:
        path.write_text(json.dumps({"mistakes": existing}, indent=2) + "\n", encoding="utf-8")
    except OSError:
        return False
    return True


def advance_reflection(
    state: ReflectionState,
    critiques: list[str],
    *,
    max_attempts: int = 3,
) -> ReflectionState:
    attempt = state.attempt + 1
    normalized = tuple(critiques)
    identical = normalized and normalized == state.last_critiques
    blocked = bool(critiques) and (attempt >= max_attempts or identical)
    return ReflectionState(
        attempt=attempt,
        last_critiques=normalized,
        blocked=blocked,
        recorded_mistake=state.recorded_mistake,
    )


class ReflectionEngine:
    """Generic Actor-Critic reflection loop for skill artifacts."""

    def __init__(self, profile: CriticProfile):
        self.profile = profile

    def evaluate_draft(
        self,
        context: ArtifactContext,
        *,
        state: ReflectionState | None = None,
        mistakes: list[dict[str, Any]] | None = None,
    ) -> ArtifactDecision:
        current = state or ReflectionState()
        if not context.has_draft:
            return ArtifactDecision(
                critiques=[],
                reflection=current,
                mode="instructions",
                blocked=False,
            )

        critiques = self.profile.evaluate(context.draft, context, mistakes or [])
        next_state = advance_reflection(current, critiques, max_attempts=context.max_attempts)
        blocked = next_state.blocked and bool(critiques)

        if not critiques:
            mode = "completed"
        elif blocked:
            mode = "blocked_requires_review"
        else:
            mode = "instructions"

        return ArtifactDecision(
            critiques=critiques,
            reflection=next_state,
            mode=mode,
            blocked=blocked,
        )

    def run_with_mistakes(
        self,
        context: ArtifactContext,
        vault_folder: str,
        project_root: Path | None,
        *,
        state: ReflectionState | None = None,
        record_on_block: bool = True,
    ) -> ArtifactDecision:
        mistakes = load_mistakes(
            vault_folder,
            project_root,
            skill_name=self.profile.skill_name,
            artifact_kind=self.profile.artifact_kind,
        )
        decision = self.evaluate_draft(context, state=state, mistakes=mistakes)
        reflection = decision.reflection

        if (
            decision.blocked
            and record_on_block
            and project_root is not None
            and not reflection.recorded_mistake
        ):
            append_mistake(
                vault_folder,
                project_root,
                flaw="; ".join(decision.critiques)[:500],
                skill_name=self.profile.skill_name,
                artifact_kind=self.profile.artifact_kind,
                ticket_id=context.ticket_id,
            )
            reflection = ReflectionState(
                attempt=reflection.attempt,
                last_critiques=reflection.last_critiques,
                blocked=True,
                recorded_mistake=True,
            )
            decision = ArtifactDecision(
                critiques=decision.critiques,
                reflection=reflection,
                mode=decision.mode,
                blocked=decision.blocked,
            )

        return decision
