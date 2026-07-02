from .state import QueueState, Event, TaskState

def cli_ui_hook(state: QueueState, event: Event, stream):
    """A side-effect hook that prints task transitions to the terminal."""
    print(f"[*] Event Processed: {event.type}")
    if event.payload and "task_id" in event.payload:
        task_id = event.payload["task_id"]
        if task_id in state.tasks:
            task = state.tasks[task_id]
            print(f"    Task [{task_id}] is now {task.state.value}")
            if task.state == TaskState.BLOCKED_REQUIRES_REVIEW:
                print(f"    Critiques length: {len(task.critiques)}")

def authorization_hook(state: QueueState, event: Event, stream):
    """A side-effect hook that halts execution for human review when the circuit breaker trips."""
    # We only trigger this side effect when a TaskFailedEvent causes a task to become blocked
    if event.type == "TaskFailedEvent":
        task_id = event.payload.get("task_id")
        task = state.tasks.get(task_id)
        
        if task and task.state == TaskState.BLOCKED_REQUIRES_REVIEW:
            print(f"\n[!] ALERT: Circuit Breaker tripped for task '{task_id}'.")
            print("[!] The task failed to complete successfully after max retries.")
            print("Type 'IMPLEMENTATION APPROVED' to authorize new instructions and resume.")
            
            # Blocking I/O side effect (In a real async harness, this would be an MCP prompt)
            try:
                user_input = input("> ")
            except EOFError:
                # Handle test environments where stdin is not available
                user_input = ""
                
            if user_input.strip() == "IMPLEMENTATION APPROVED":
                print(f"[+] Authorization received for task '{task_id}'. Resuming queue...")
                # Dispatch the event back into the stream to trigger the next state transition
                auth_event = Event(type="AuthorizationReceivedEvent", payload={"task_id": task_id, "token": user_input.strip()})
                stream.dispatch(auth_event)
            else:
                print("[-] Authorization denied. Task remains blocked.")
