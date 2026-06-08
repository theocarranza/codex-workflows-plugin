# AI Codex Finish Ticket Workflow

## 1. Spec (Goal)
Sync the git repository, ensure code quality, ensure there are no regressions, update the YouTrack agile board, and archive the local ledger records.

## 2. Implementation Plan (Roadmap)
When we are done with a ticket, we execute the following workflow:
- [ ] Task 1. Execute `ensure-can-merge` script from `package.json`
- [ ] Task 2. Commit remaining changes
- [ ] Task 3. Push the branch to the remote repo
- [ ] Task 4. Create the Pull Request
- [ ] Task 5. (Optional, user's discretion) Execute the PR code review
- [ ] Task 6. Skip moving the corresponding YouTrack card to "testing" (for the current effort, we are not using the test lane and move the card straight into done). Only use the "testing" lane when code review/qa/testing is actively taking place.
- [ ] Task 7. (Conditional) Address the PR comments, if any, changing the PR thread comment status to either *resolved* or *wont fix* (or equivalent)
- [ ] Task 8. Repeat steps 1, 2, and 3 when all comments selected for implementation are satisfied
- [ ] Task 9. Merge the pull request
- [ ] Task 10. Move the corresponding YouTrack card straight to "done" using `youtrack/update_issue`. You must set the `'State'` custom field to `'Done'`, set the `'Timer'` custom field to `'Stop'`, and update the `'Spent time'` custom field (formatted as hours/days/weeks, e.g. `'2h 30m'`).
- [ ] Task 11. Update the ledger ticket (including Tasks and Walkthrough sections with the saved artifacts) and agent session
- [ ] Task 12. Checkout the local `unstable` branch and pull from origin to sync it

## 3. Technical Constraints
- **Relevant Rules:** [`.agent/rules/rules-git-workflow.md`]
- **Other Details:** IMPORTANT: task 3 requires the user permission, unless the token `FULL WORKFLOW` is issued.

## 4. Verification Plan
- [ ] **Tests:** The unit/integration tests must be all green.
- [ ] **Visual Proof:** The checked out branch must be `unstable` and it must contain the merged PR git history entry.