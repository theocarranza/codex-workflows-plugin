from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
import dataclasses

class TaskState(Enum):
    READY = "Ready"
    IN_PROGRESS = "In_Progress"
    COMPLETED = "Completed"
    BLOCKED = "Blocked"
    BLOCKED_REQUIRES_REVIEW = "Blocked_Requires_Review"

@dataclass(frozen=True)
class Event:
    """An immutable record of a state change in the system."""
    type: str
    payload: Dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class Task:
    """An immutable representation of a unit of work (a skill execution)."""
    id: str
    skill_name: str
    state: TaskState = TaskState.READY
    inputs: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list) # List of task ids that must be completed first
    retry_count: int = 0
    critiques: List[str] = field(default_factory=list)
    output: Optional[Any] = None

    def copy_with(self, **kwargs) -> 'Task':
        """Returns a new immutable Task with updated fields."""
        return dataclasses.replace(self, **kwargs)

@dataclass(frozen=True)
class QueueState:
    """An immutable representation of the entire task graph and event history."""
    tasks: Dict[str, Task] = field(default_factory=dict) # Map of task_id -> Task
    events_history: List[Event] = field(default_factory=list)

    def copy_with(self, **kwargs) -> 'QueueState':
        """Returns a new immutable QueueState with updated fields."""
        return dataclasses.replace(self, **kwargs)
