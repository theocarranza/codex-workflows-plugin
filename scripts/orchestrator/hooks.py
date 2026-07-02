import sys

from .state import Event, QueueState, TaskState


def _log(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def cli_ui_hook(state: QueueState, event: Event, stream):
    """Log task transitions to stderr (safe for MCP stdio transport)."""
    _log(f"[*] Event Processed: {event.type}")
    if event.payload and "task_id" in event.payload:
        task_id = event.payload["task_id"]
        if task_id in state.tasks:
            task = state.tasks[task_id]
            _log(f"    Task [{task_id}] is now {task.state.value}")
            if task.state == TaskState.BLOCKED_REQUIRES_REVIEW:
                _log(f"    Critiques length: {len(task.critiques)}")


def authorization_hook(state: QueueState, event: Event, stream):
    """Halt execution for human review when the circuit breaker trips (interactive mode only)."""
    if event.type != "TaskFailedEvent":
        return

    task_id = event.payload.get("task_id")
    task = state.tasks.get(task_id)
    if not task or task.state != TaskState.BLOCKED_REQUIRES_REVIEW:
        return

    _log(f"\n[!] ALERT: Circuit Breaker tripped for task '{task_id}'.")
    _log("[!] The task failed to complete successfully after max retries.")
    _log("Type 'IMPLEMENTATION APPROVED' to authorize new instructions and resume.")

    try:
        user_input = input("> ")
    except EOFError:
        user_input = ""

    if user_input.strip() == "IMPLEMENTATION APPROVED":
        _log(f"[+] Authorization received for task '{task_id}'. Resuming queue...")
        auth_event = Event(
            type="AuthorizationReceivedEvent",
            payload={"task_id": task_id, "token": user_input.strip()},
        )
        stream.dispatch(auth_event)
    else:
        _log("[-] Authorization denied. Task remains blocked.")
