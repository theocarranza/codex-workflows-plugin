from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

SPEC_KINDS = (
    "rfc",
    "adr",
    "design-doc",
    "tech-spec",
    "srs",
    "implementation-plan",
    "bugfix-spec",
    "api-contract",
)

DEFAULT_KINDS_BY_SIGNAL = {
    "bugfix": ("bugfix-spec", "adr"),
    "feature": ("design-doc", "tech-spec"),
    "task": ("implementation-plan", "tech-spec"),
    "refactor": ("adr", "tech-spec"),
    "default": ("tech-spec", "implementation-plan"),
}


@dataclass(frozen=True)
class SpecPlan:
    ticket_id: str
    slug: str
    specs_dir: str
    existing_specs: tuple[str, ...]
    missing_kinds: tuple[str, ...]
    generation_required: bool
    source_hints: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ticket_id": self.ticket_id,
            "slug": self.slug,
            "specs_dir": self.specs_dir,
            "existing_specs": list(self.existing_specs),
            "missing_kinds": list(self.missing_kinds),
            "generation_required": self.generation_required,
            "source_hints": dict(self.source_hints),
        }


def slug_ticket_id(ticket_id: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ticket_id.strip()).strip("-").lower()
    return slug or "ticket"


def specs_root(vault_folder: str, project_root: Path | None) -> Path | None:
    if project_root is None:
        return None
    return project_root / vault_folder / "Specs"


def spec_dir_for_ticket(vault_folder: str, project_root: Path | None, slug: str) -> Path | None:
    root = specs_root(vault_folder, project_root)
    if root is None:
        return None
    return root / slug


def list_existing_specs(spec_dir: Path) -> list[str]:
    if not spec_dir.exists():
        return []
    files = sorted(p.name for p in spec_dir.glob("*.md") if p.is_file())
    if files:
        return files
    single = spec_dir.with_suffix(".md")
    if single.is_file():
        return [single.name]
    return []


def infer_ticket_signal(ticket_id: str, ledger_text: str = "") -> str:
    combined = f"{ticket_id}\n{ledger_text}".lower()
    if re.search(r"\bbug(fix)?\b", combined) or "type: bug" in combined:
        return "bugfix"
    if re.search(r"\brefactor\b", combined):
        return "refactor"
    if re.search(r"\bfeature\b", combined):
        return "feature"
    if re.search(r"\btask\b", combined):
        return "task"
    return "default"


def kinds_for_signal(signal: str) -> tuple[str, ...]:
    return DEFAULT_KINDS_BY_SIGNAL.get(signal, DEFAULT_KINDS_BY_SIGNAL["default"])


def missing_spec_kinds(existing_files: list[str], desired_kinds: tuple[str, ...]) -> list[str]:
    existing = {name.removesuffix(".md").lower() for name in existing_files}
    return [kind for kind in desired_kinds if kind not in existing]


def read_ticket_ledger(project_root: Path | None, ledger_rel: str) -> str:
    if project_root is None:
        return ""
    path = project_root / ledger_rel
    if not path.is_file():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def plan_spec_generation(
    project_root: Path | None,
    *,
    vault_folder: str,
    ticket_id: str,
    ledger_rel: str | None = None,
) -> SpecPlan:
    slug = slug_ticket_id(ticket_id)
    rel_specs_dir = f"{vault_folder}/Specs/{slug}"
    spec_dir = spec_dir_for_ticket(vault_folder, project_root, slug)
    ledger_text = read_ticket_ledger(project_root, ledger_rel or f"{vault_folder}/Tickets/Active/{slug}.md")
    signal = infer_ticket_signal(ticket_id, ledger_text)
    desired = kinds_for_signal(signal)
    existing = list_existing_specs(spec_dir) if spec_dir is not None else []
    missing = missing_spec_kinds(existing, desired)
    hints = _extract_source_hints(ledger_text)
    return SpecPlan(
        ticket_id=ticket_id,
        slug=slug,
        specs_dir=rel_specs_dir,
        existing_specs=tuple(existing),
        missing_kinds=tuple(missing),
        generation_required=bool(missing),
        source_hints=hints,
    )


def _extract_source_hints(ledger_text: str) -> dict[str, str]:
    hints: dict[str, str] = {}
    for label, pattern in (
        ("requirements", r"(?im)^(?:##\s*)?requirements?\s*[:\n](.+?)(?:\n##|\Z)"),
        ("description", r"(?im)^(?:##\s*)?description\s*[:\n](.+?)(?:\n##|\Z)"),
        ("implementation_plan", r"(?im)^(?:##\s*)?implementation\s+plan\s*[:\n](.+?)(?:\n##|\Z)"),
    ):
        match = re.search(pattern, ledger_text, re.DOTALL)
        if match:
            hints[label] = match.group(1).strip()[:2000]
    if not hints and ledger_text.strip():
        hints["description"] = ledger_text.strip()[:2000]
    return hints


def template_path(skills_dir: Path, kind: str) -> Path:
    return skills_dir / "write-spec" / "references" / "templates" / f"{kind}.md"


def load_template(skills_dir: Path, kind: str) -> str:
    path = template_path(skills_dir, kind)
    if not path.is_file():
        raise FileNotFoundError(f"Missing spec template for kind '{kind}': {path}")
    return path.read_text(encoding="utf-8")
