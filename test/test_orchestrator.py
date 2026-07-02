import unittest
from scripts.orchestrator.state import QueueState, Task, TaskState, Event
from scripts.orchestrator.reducers import reduce_queue_state

class TestOrchestratorReducers(unittest.TestCase):
    def setUp(self):
        self.initial_tasks = {
            "task_a": Task(id="task_a", skill_name="parse_ast", state=TaskState.READY),
            "task_b": Task(id="task_b", skill_name="write_test", state=TaskState.BLOCKED, dependencies=["task_a"])
        }
        self.initial_state = QueueState(tasks=self.initial_tasks)

    def test_queue_resolution_on_completion(self):
        state = self.initial_state
        
        # 1. Spawn Task A
        event_spawn = Event(type="TaskSpawnedEvent", payload={"task_id": "task_a"})
        state = reduce_queue_state(state, event_spawn)
        self.assertEqual(state.tasks["task_a"].state, TaskState.IN_PROGRESS)
        self.assertEqual(state.tasks["task_b"].state, TaskState.BLOCKED)
        
        # 2. Complete Task A -> Should unblock Task B
        event_complete = Event(type="TaskCompletedEvent", payload={"task_id": "task_a", "output": "AST parsed"})
        state = reduce_queue_state(state, event_complete)
        
        self.assertEqual(state.tasks["task_a"].state, TaskState.COMPLETED)
        self.assertEqual(state.tasks["task_a"].output, "AST parsed")
        self.assertEqual(state.tasks["task_b"].state, TaskState.READY, "Task B should be unblocked and READY")

    def test_circuit_breaker_and_reflection_loop(self):
        state = self.initial_state
        
        # Fail Task A (Retry 1)
        event_fail_1 = Event(type="TaskFailedEvent", payload={"task_id": "task_a", "critique": "Failed compilation"})
        state = reduce_queue_state(state, event_fail_1)
        
        self.assertEqual(state.tasks["task_a"].state, TaskState.READY)
        self.assertEqual(state.tasks["task_a"].retry_count, 1)
        self.assertEqual(len(state.tasks["task_a"].critiques), 1)
        
        # Fail Task A (Retry 2)
        event_fail_2 = Event(type="TaskFailedEvent", payload={"task_id": "task_a", "critique": "Missing import"})
        state = reduce_queue_state(state, event_fail_2)
        
        # Fail Task A (Retry 3) - Should trip circuit breaker (default max_retries=3)
        event_fail_3 = Event(type="TaskFailedEvent", payload={"task_id": "task_a", "critique": "Still failing"})
        state = reduce_queue_state(state, event_fail_3)
        
        self.assertEqual(state.tasks["task_a"].state, TaskState.BLOCKED_REQUIRES_REVIEW, "Circuit breaker should block task")
        self.assertEqual(state.tasks["task_a"].retry_count, 3)
        
        # Authorize Task A after manual review / instruction update
        event_auth = Event(type="AuthorizationReceivedEvent", payload={"task_id": "task_a", "token": "IMPLEMENTATION APPROVED"})
        state = reduce_queue_state(state, event_auth)
        
        self.assertEqual(state.tasks["task_a"].state, TaskState.READY, "Task should be READY after authorization")
        self.assertEqual(state.tasks["task_a"].retry_count, 0, "Retries should be reset")
        self.assertEqual(len(state.tasks["task_a"].critiques), 0, "Critiques should be cleared")

if __name__ == '__main__':
    unittest.main()
