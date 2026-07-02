from typing import Callable, List
from .state import Event, QueueState
from .reducers import reduce_queue_state

class OrchestratorStream:
    """A reactive state container that manages the event stream and state transitions."""
    def __init__(self, initial_state: QueueState):
        self.state = initial_state
        self.listeners: List[Callable[[QueueState, Event, 'OrchestratorStream'], None]] = []
        
    def subscribe(self, listener: Callable[[QueueState, Event, 'OrchestratorStream'], None]):
        """Register a hook to listen for state changes and events."""
        self.listeners.append(listener)
        
    def dispatch(self, event: Event):
        """Processes an event, computes the new immutable state, and notifies listeners."""
        # 1. Pure Functional State Transition (No side effects)
        new_state = reduce_queue_state(self.state, event)
        self.state = new_state
        
        # 2. Side Effects Boundary (Hooks)
        # We pass the stream itself so hooks can emit subsequent events if needed
        for listener in self.listeners:
            listener(new_state, event, self)
