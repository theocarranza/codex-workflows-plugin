from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class WorkspaceProfile:
    name: str
    vault_name: str
    project_name: str
    ticket_root: str
    agent_sessions_root: str
    tracker_name: str
    branch_name: str
    verify_command: str


def _generic_profile() -> WorkspaceProfile:
    return WorkspaceProfile(
        name="generic",
        vault_name="AI_Codex",
        project_name="codex-workflows-plugin",
        ticket_root="AI_Codex/Projects/codex-workflows-plugin/Tickets",
        agent_sessions_root="AI_Codex/Projects/codex-workflows-plugin/Agent_Sessions",
        tracker_name="none",
        branch_name="master",
        verify_command="python3 -m unittest -v",
    )


def _flutter_profile() -> WorkspaceProfile:
    return WorkspaceProfile(
        name="flutter",
        vault_name="AI_Codex",
        project_name="flutter-workspace",
        ticket_root="AI_Codex/Projects/flutter-workspace/Tickets",
        agent_sessions_root="AI_Codex/Projects/flutter-workspace/Agent_Sessions",
        tracker_name="none",
        branch_name="develop",
        verify_command="flutter test",
    )


def _repository_profile() -> WorkspaceProfile:
    return WorkspaceProfile(
        name="repository",
        vault_name="AI_Codex",
        project_name="codex-workflows-plugin",
        ticket_root="AI_Codex/Projects/codex-workflows-plugin/Tickets",
        agent_sessions_root="AI_Codex/Projects/codex-workflows-plugin/Agent_Sessions",
        tracker_name="none",
        branch_name="master",
        verify_command="python3 -m unittest -v",
    )


_PROFILE_FACTORIES: dict[str, Callable[[], WorkspaceProfile]] = {
    "generic": _generic_profile,
    "flutter": _flutter_profile,
    "repository": _repository_profile,
}


def load_profile(name: str) -> WorkspaceProfile:
    try:
        return _PROFILE_FACTORIES[name]()
    except KeyError as error:
        raise ValueError(f"Unknown profile: {name}") from error
