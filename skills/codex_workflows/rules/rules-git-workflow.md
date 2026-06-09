# GIT & BRANCHING PROTOCOL (MONOREPO GLOBAL)

## I. Commit Standards
1. **Conventional Commits**: MUST follow the specification (feat, fix, chore, refactor, etc.).
2. **Atomic Commits**: Each commit must represent a single, verifiable change.
3. **Descriptive Body**: Use the optional body for complex explanations.
4. **Scope**: Use scope when applicable (e.g., `feat(auth): ...`).

## II. Branching Strategy
1. **Source of Truth**: The base branch is dynamically resolved (e.g., `unstable` or `develop`).
   - **MANDATE (VERY HIGH SIGNAL)**: NEVER commit directly to the base branch! Always create a feature, bugfix, or techdebt branch first.
2. **Synchronization**: Before starting work or creating a branch, always sync with the remote origin of the resolved base branch.
3. **Naming Convention**: MUST follow the pattern `{type}/{descricao-em-pt-br}`.
   - **Types**: `feature/`, `bugfix/`, `techdebt/`.
   - **Language**: Portuguese (pt-br), kebab-case.
   - **Example**: `feature/implementacao-login`, `techdebt/refatoracao-database`.

## III. Safe Sync Policy
- **LAW**: Always use the `/git-origin-sync` workflow to update the current branch.
- **Manual Restriction**: DO NOT run `git merge` or `git rebase` manually unless fixing a conflict that the agent cannot resolve.
- **Failsafe**: A mandatory stash step must be performed before any sync operation.
