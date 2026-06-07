---
description: Rigorous flow for fixing bugs with reproduction tests anchored in the Codex
---

# TDD Bug Fix Workflow

This workflow enforces a strict Red-Green-Refactor cycle for bug fixes, with all findings and plans logged in the **AI_Codex**.

## 1. Analysis & Reproduction Plan

1.  **Read Active Ledger**: Locate the ticket file in `AI_Codex/Tickets/Active/`.
2.  **Root Cause Analysis**: Use **Sequential Thinking** to identify the failure point.
3.  **Reproduction Plan**: Document the strategy to reproduce the bug in the Codex Ledger.
    - **Codex Anchor**: `### Reproduction Strategy`

## 2. Create Reproduction Test (Red Phase)

1.  **Implement Test**: Create a new test file in `test/` that reproduces the bug.
2.  **Verify Failure**: Run the test. It MUST fail.
    - **Command**: `fvm flutter test path/to/repro_test.dart`
3.  **Sync Ledger**: Update the Codex Ledger with the test failure confirmation.

## 3. Implement Fix (Green Phase)

1.  **Write Code**: Apply the minimal change needed to pass the test.
2.  **Verify Pass**: Run the reproduction test again.
    - **Command**: `fvm flutter test path/to/repro_test.dart`
3.  **Sync Ledger**: Document the fix outcome in the Codex.

## 4. Final Verification & Cleanup

1.  **Regression Check**: Run all project tests.
    - **Command**: `fvm flutter test`
2.  **Static Analysis**: `fvm flutter analyze`.
3.  **Handoff**: Finalize the Ledger and run `/commit`.

## Usage & Invocation Examples

- `/fix-bug` (Assumes a ticket is already active)
