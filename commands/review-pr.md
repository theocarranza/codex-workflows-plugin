---
name: review-pr
description: >
  Retrieve Azure DevOps pull request review threads, classify each as comply or
  reject, present a consolidated report for user confirmation, apply code edits
  for comply items, post rejection replies to Azure threads (without changing
  thread status), and persist results to the AI Codex vault.
  Invoke with a PR number: /review-pr <number>.
  Repo and branch are always inferred from git remote origin and active branch.
disable-model-invocation: true
allowed-tools: >
  Read Write Edit Glob Grep Bash
  mcp__azure-devops__repo_get_pull_request_by_id
  mcp__azure-devops__repo_list_pull_request_threads
  mcp__azure-devops__repo_get_pull_request_changes
  mcp__azure-devops__repo_reply_to_comment
---

# review-pr

Classify Azure DevOps PR review threads and act on the results. Load reference files as each phase needs them.

References (in `skills/review-pr/references/`):
- `skills/review-pr/references/azure-pr-mechanics.md` — exact MCP tool names, parameters, and gotchas.
- `skills/review-pr/references/report-format.md` — terminal output template and vault note template.

---

## PHASE 1 — INGEST

Read `skills/review-pr/references/azure-pr-mechanics.md` before making any MCP calls.

**Input:** PR number passed as the skill argument (e.g. `42`). If multiple numbers given, process only the first and warn: `"review-pr processes one PR per invocation."`.

**1. Infer repo and branch from git:**

```bash
git remote get-url origin
git branch --show-current
```

Parse the repo name from the remote URL: take the last path segment and strip the `.git` suffix.
Strip `refs/heads/` prefix from branch names returned by Azure APIs.

**2. Fetch PR metadata:**

Call `mcp__azure-devops__repo_get_pull_request_by_id` with `repositoryId` = inferred repo name, `pullRequestId` = PR number.

Extract: `title`, `description`, `targetRefName` (strip `refs/heads/`), `createdBy.displayName`.

If this call fails, STOP and report: `"INGEST failed — could not fetch PR #<n>: <error>"`. Do not proceed.

**3. Fetch review threads:**

Call `mcp__azure-devops__repo_list_pull_request_threads` with `repositoryId` and `pullRequestId`.

For each thread, extract:
- `id` → `thread_id`
- `status` → `status`
- `threadContext.filePath` → `file` (null if threadContext is null)
- `threadContext.rightFileStart.line` → `line` (null if threadContext is null)
- `comments[0].content` → `comment_text`
- `comments[0].author.displayName` → `reviewer`

**Filter:** skip threads where `status` is `resolved` or `wontFix`. Count skipped threads separately.

**4. Fetch PR diff:**

Call `mcp__azure-devops__repo_get_pull_request_changes` with `repositoryId` and `pullRequestId`.

Store the list of changed file paths. Use during CLASSIFY to locate relevant diff hunks by reading the file from the working tree with `Read(<file-path>)`.

If this call fails, log a warning and continue — CLASSIFY will note absence of diff context.

**5. Report INGEST summary to terminal:**

```
PR #<n> — "<title>"
Branch: <active-branch> → <target>
<N> threads fetched · <S> skipped · <A> active — proceeding to CLASSIFY
```

---

## PHASE 2 — CLASSIFY

For each active ReviewThread in order:

1. Read `comment_text` and `reviewer`.
2. If `file` is non-null and the file exists in the working tree, read the file with `Read(<file>)` and locate the region around `line` (±20 lines) for diff context.
3. Decide `comply` or `reject`:
   - **comply** — the reviewer's point is technically valid and the code should be changed. Set `action`: a concise description of the exact change needed, referencing file path and line number.
   - **reject** — the current implementation is correct or the reviewer lacks full context. Set `reason`: a paragraph (2–5 sentences) suitable for posting as a public reply — clear, respectful, technically grounded. No "you're wrong" framing.
4. Set `reaction`, and populate either `action` (comply) or `reason` (reject). Leave the other field null.

Proceed to PHASE 3 once all threads are classified.

---

## PHASE 3 — PRESENT

Read `skills/review-pr/references/report-format.md` for the exact terminal output template before printing.

1. Print the full classification report using the template in `report-format.md`.
2. Wait for user input.
3. Apply any adjustments the user specifies — accepted verbs: flip / change action / change reason / skip (see full table in report-format.md).
4. Re-print the updated list.
5. Ask: `"Confirmed? (yes to proceed to ACT, or make further changes)"`
6. Wait for confirmation before proceeding.

Do not proceed to ACT until the user explicitly confirms.

---

## PHASE 4 — ACT

Read `skills/review-pr/references/azure-pr-mechanics.md` before making any MCP calls.

Execute confirmed items only. Process comply items first, then reject items.

**Comply items — code edits:**

For each comply item (not skipped):
1. Read the target file.
2. Apply the edit described in `action` using Edit or Write tools.
3. Do NOT commit. Changes land in the working tree.
4. Record outcome: `done` or `failed: <reason>`.

**Reject items — Azure thread replies:**

For each reject item (not skipped):
1. Call `mcp__azure-devops__repo_reply_to_comment` with `repositoryId`, `pullRequestId`, `threadId` = `thread_id`, `content` = `reason`.
2. Do NOT call any tool that changes thread status.
3. Record outcome: `posted` or `failed: <reason>`.

Print ACT outcomes to terminal using the template in `report-format.md`.

---

## PERSIST

Read `skills/review-pr/references/report-format.md` for the vault note template before writing.

Write the vault note to:
```
AI_Codex/Agent_Reports/YYYY-MM-DD-pr-review-<PR#>.md
```

Use today's date (YYYY-MM-DD). Frontmatter and body follow the template in `report-format.md`.

Set `outcome`:
- `complete` if every non-skipped ACT item succeeded.
- `partial` if any item failed.

---

## Guardrails

- **Thread status immutability**: never call `repo_update_pull_request_thread` or any status-changing tool. `repo_reply_to_comment` only.
- **No automatic commits**: code edits land in the working tree; the user commits via `/commit-prep`.
- **Skip over MCP reply errors**: if one reply fails to post, log the failure and continue with remaining items.
- **One PR per invocation**: warn and process only the first if multiple numbers given.
- **Skipped threads**: excluded from CLASSIFY, PRESENT display, and ACT. Never acted on.
