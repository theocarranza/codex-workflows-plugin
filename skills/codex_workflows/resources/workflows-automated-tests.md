---
description: Standard workflow for creating or updating automated tests
---

# Workflow: Create Automated Tests

This workflow ensures that all new tests adhere to the project's strict testing standards, specifically regarding layer-specific strategies (Sociable vs Solitary).

## Prerequisites
- The agent must have identified the file(s) that need testing.

## Steps

1.  **Ingest Rules**
    *   **Action**: Read and internalize the testing rules: @rules-automated-tests.md and @rules-flutter-testing.md
    *   **Command**: `view_file .agent/rules/rules_automated_tests.md`
    *   **Constraint**: You **MUST** read this file before writing a single line of test code.

2.  **Analyze Target Layer**
    *   **Action**: Determine which architectural layer the code belongs to:
        *   *Domain* (Entities, Value Objects)? -> Plan for **Sociable** tests (No mocks).
        *   *Application* (Use Cases)? -> Plan for **Solitary** tests (Mock repositories).
        *   *Infrastructure* (Repositories, Mappers)? -> Plan for **Hybrid** tests.

3.  **Plan Test Scenarios**
    *   **Action**: Create a brief plan of "Happy Path" and "Edge Cases".
    *   **Constraint**: Use "Given-When-Then" phrasing for scenarios.

4.  **Implement Tests**
    *   **Action**: Write the test code.
    *   **Constraint**:
        *   Use `groups` for "Given" contexts.
        *   Use `test` for "should" assertions.
        *   Use parameterized tests (Dart Records) for repeated logic.

5.  **Verify**
    *   **Action**: Run the tests.
    *   **Command**: `flutter test path/to/new_test.dart`

6.  **Refine**
    *   **Action**: If tests fail, fix the *implementation* or the *test* (if the test was wrong). Ensure all tests pass before completing.