# Rule: Run Integrated Test

---
triggers:

- "run integration test"
- "run tests on emulator"

---

## Context

Running integration tests requires an active Android emulator. This rule ensures that an emulator is running before tests execute and manages the entire lifecycle of the test run.

## Protocol

### 1. Emulator Detection & Creation

1. **Check for active emulators:**
    Run `flutter emulators` (or `flutter emulators --launch` isn't a check, so `flutter emulators` lists them).
    Actually, `flutter emulators` lists available emulators. `flutter devices` lists running devices.
    The requirement says: "detect the presence of an android emulador by issuing the `flutter emulators list` command". Wait, `flutter emulators` lists *available* emulators, not *running* ones.
    However, the prompt says: "detect the presence of an android emulador by issuing the `flutter emulators list`command". I should follow this instruction, but interpretation is needed. If the user means "is one configured?", then `list` works. If they mean "is one running?", `flutter devices` is correct.
    Given step 2 says "in the abscence of an android emulator, the agent will then create one", implying *existence*, not necessarily *running*.
    So checks:
    - Run `flutter emulators`.
    - If no android emulator exists in the list, create one: `flutter emulators --create --name integration_tester`.

### 2. Emulator Launch (Implicit)

- If an emulator exists but is not running (check `flutter devices`), you should launch it. Use `flutter emulators --launch <emulator_id>`.

### 3. Test Execution

- Run the test file provided by the user.
- **Critical**: You MUST provide a flavor and dart-define. Default to `qa` if unsure.
- Command: `flutter test integration_test/<test_file>.dart --flavor qa --dart-define=FLAVOR=qa`
- **Monitor**: Watch for "Connect to device", "Installing", and test results.

### 4. Reporting

- **Success**: Report "Test Passed" with duration.
- **Failure**: Report "Test Failed" with the specific error message and stack trace snippet.
- **Formatting**: Use a code block for the output to ensure legibility.

### 5. Rerun Option

- After reporting, explicitly ask the user if they want to rerun the test.

## Mandatory Steps for Agent

When asking to run integration tests:

1. Verify emulator existence/state.
2. Launch/Create if necessary.
3. Run the test.
4. Report results clearly.
