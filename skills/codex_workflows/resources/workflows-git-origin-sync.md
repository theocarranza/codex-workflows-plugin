---
description: Synchronize the current branch with the latest develop branch
---

# Git Origin Sync Workflow

1. **Safety Check**
   - Ensure the `rules-git.md` is active.
   - Verify current branch is NOT `develop`.

2. **Failsafe Stash**
   - Stash current changes with a timestamped message to prevent data loss.
   - Command: `git stash push -u -m "$(git branch --show-current)_failsafe_$(date +%s)"`

3. **Update Base Branch**
   - Switch to `develop` and pull latest changes from remote.
   - Command: `git checkout develop && git pull origin develop`

4. **Merge Base into Current**
   - Switch back to the previous branch.
   - Command: `git checkout -`
   - Merge the updated `develop` branch.
   - Command: `git merge develop`
   - *Note*: If conflicts occur, resolve them following the Architect Protocol or ask the user for guidance.

5. **Restore Work**
   - Apply the failsafe stash.
   - Command: `git stash pop`

6. **Workspace Maintenance**
   - Change directory to `projects/aplicatudo`.
   - Command: `cd projects/aplicatudo`
   - Refresh dependencies: `fvm flutter pub get`
   - Generate code: `npm run auto-generate` (or equivalent build_runner command).
   - Validation: `fvm flutter analyze` and `fvm dart format .`

7. **Verification**
   - Run unit tests to ensure the merge didn't break existing logic.
   - Command: `fvm flutter test`
