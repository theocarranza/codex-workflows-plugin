from typing import Dict, Any
from .state import QueueState, Task, TaskState, Event

def handle_task_spawned(state: QueueState, event: Event) -> QueueState:
    task_id = event.payload.get("task_id")
    if not task_id or task_id not in state.tasks:
        return state
    
    task = state.tasks[task_id]
    new_task = task.copy_with(state=TaskState.IN_PROGRESS)
    
    new_tasks = state.tasks.copy()
    new_tasks[task_id] = new_task
    
    return state.copy_with(
        tasks=new_tasks,
        events_history=state.events_history + [event]
    )

def handle_task_completed(state: QueueState, event: Event) -> QueueState:
    task_id = event.payload.get("task_id")
    output = event.payload.get("output")
    
    if not task_id or task_id not in state.tasks:
        return state
        
    # Mark current task as completed
    task = state.tasks[task_id]
    completed_task = task.copy_with(state=TaskState.COMPLETED, output=output)
    
    new_tasks = state.tasks.copy()
    new_tasks[task_id] = completed_task
    
    # Queue Resolution: Check if this unblocks any downstream dependencies
    for t_id, t in new_tasks.items():
        if t.state == TaskState.BLOCKED and task_id in t.dependencies:
            # Check if ALL dependencies for this task are now COMPLETED
            all_deps_completed = all(
                new_tasks[dep].state == TaskState.COMPLETED for dep in t.dependencies
            )
            if all_deps_completed:
                new_tasks[t_id] = t.copy_with(state=TaskState.READY)
                
    return state.copy_with(
        tasks=new_tasks,
        events_history=state.events_history + [event]
    )

def handle_task_failed(state: QueueState, event: Event, max_retries: int = 3) -> QueueState:
    task_id = event.payload.get("task_id")
    critique = event.payload.get("critique")
    
    if not task_id or task_id not in state.tasks:
        return state
        
    task = state.tasks[task_id]
    new_retry_count = task.retry_count + 1
    new_critiques = task.critiques + [critique] if critique else task.critiques
    
    # Circuit Breaker: If max retries reached, block and require human review
    if new_retry_count >= max_retries:
        new_task_state = TaskState.BLOCKED_REQUIRES_REVIEW
    else:
        # Reflection Loop: Inject back into ready queue with new critique
        new_task_state = TaskState.READY 
        
    failed_task = task.copy_with(
        state=new_task_state,
        retry_count=new_retry_count,
        critiques=new_critiques
    )
    
    new_tasks = state.tasks.copy()
    new_tasks[task_id] = failed_task
    
    return state.copy_with(
        tasks=new_tasks,
        events_history=state.events_history + [event]
    )

def handle_authorization_received(state: QueueState, event: Event) -> QueueState:
    task_id = event.payload.get("task_id")
    token = event.payload.get("token")
    
    if not task_id or task_id not in state.tasks:
        return state
        
    if token == "IMPLEMENTATION APPROVED":
        task = state.tasks[task_id]
        if task.state == TaskState.BLOCKED_REQUIRES_REVIEW:
            # The Meta-Agent evolved the instructions. 
            # We clear critiques and retries, and push back to Ready queue.
            approved_task = task.copy_with(
                state=TaskState.READY,
                retry_count=0,
                critiques=[]
            )
            new_tasks = state.tasks.copy()
            new_tasks[task_id] = approved_task
            
            return state.copy_with(
                tasks=new_tasks,
                events_history=state.events_history + [event]
            )
            
    return state

def reduce_queue_state(state: QueueState, event: Event, max_retries: int = 3) -> QueueState:
    """The main pure functional reducer pipeline."""
    if event.type == "TaskSpawnedEvent":
        return handle_task_spawned(state, event)
    elif event.type == "TaskCompletedEvent":
        return handle_task_completed(state, event)
    elif event.type == "TaskFailedEvent":
        return handle_task_failed(state, event, max_retries)
    elif event.type == "AuthorizationReceivedEvent":
        return handle_authorization_received(state, event)
    else:
        # Unhandled events still get recorded in history immutably
        return state.copy_with(events_history=state.events_history + [event])
