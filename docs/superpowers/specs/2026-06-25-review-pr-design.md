# review-pr Skill — Design Spec

**Date:** 2026-06-25
**Status:** approved

---

## Overview

`review-pr` is a four-phase skill that retrieves Azure DevOps pull request review threads, classifies each comment as comply or reject, presents a consolidated report for user review, then acts on the confirmed decisions — applying code edits for comply items and posting rejection replies to Azure DevOps threads for reject items. Results are persisted to the AI Codex vault.

---

## Invocation

```
/review-pr <PR-number>
```

The repo and active branch are always inferred from the current working tree:

- Repo: parsed from `git remote get-url origin`
- Branch: read from `git branch --show-current`

No additional arguments are required. The Azure DevOps org (`bhave-tecnologia-comportamental`) and project are already configured in the workspace `.mcp.json`.

---

## Skill Location

```
codex-workflows-plugin/skills/review-pr/SKILL.md
```

Follows the same SKILL.md frontmatter pattern used by existing skills in this plugin and in `agile-workflow-marketplace`.

---

## MCP Server Setup

Identical to `agile-workflow-marketplace/.mcp.json`:

```json
{
  "mcpServers": {
    "azure-devops": {
      "command": "npx",
      "args": ["-y", "@azure-devops/mcp", "bhave-tecnologia-comportamental"]
    }
  }
}
```

---

## Data Model

Each active review thread is normalized into a **ReviewThread** record:

```
{
  thread_id:    int
  file:         string | null      // file path the thread anchors to
  line:         int | null         // line number within that file
  reviewer:     string             // display name of comment author
  comment_text: string             // full text of the root comment
  status:       string             // current Azure thread status
  reaction:     "comply" | "reject"
  reason:       string | null      // reject only — posted as Azure reply
  action:       string | null      // comply only — describes the required code edit
}
```

Threads whose status is `resolved` or `won't fix` are skipped — they are already closed out and require no action.

---

## Phases

### PHASE 1 — INGEST

1. Infer repo name and active branch from git.
2. Fetch PR metadata via `git_get_pull_request`: title, description, target branch, author.
3. Fetch all review threads via `git_get_pull_request_threads`.
4. Fetch PR diff via `git_get_pull_request_iterations` and `git_get_pull_request_iteration_changes`.
5. Filter out threads with status `resolved` or `won't fix`.
6. Normalize remaining threads into ReviewThread records (reaction and reason/action fields left empty at this stage).

If the MCP call fails, stop and report the error — do not proceed to CLASSIFY.

---

### PHASE 2 — CLASSIFY

For each active ReviewThread:

1. Read the comment text.
2. Locate and read the diff hunk for the anchored file and line (if available).
3. Decide `comply` or `reject`:
   - **Comply**: the reviewer's point is technically valid and should be addressed. Write a concise `action` describing the exact code change needed (file, line, what to change).
   - **Reject**: the current implementation is intentional or the reviewer lacks full context. Write a `reason` paragraph suitable for posting as a public reply — clear, respectful, technically grounded.
4. Populate `reaction`, `reason`, and `action` on the ReviewThread record.

---

### PHASE 3 — PRESENT

Print a structured terminal report grouped by reaction:

```
PR #<n> — "<title>"
Branch: <branch> → <target>
<N> threads fetched · <S> skipped (resolved/won't fix) · <A> active

════════════════════════════════════════════════════════════
COMPLY (<count>)
════════════════════════════════════════════════════════════
[1] <file>:<line>  @<reviewer>
    <comment_text (truncated to 120 chars)>
    ACTION: <action>

...

════════════════════════════════════════════════════════════
REJECT (<count>)
════════════════════════════════════════════════════════════
[n] <file>:<line>  @<reviewer>
    <comment_text (truncated to 120 chars)>
    REASON: <reason>

...
────────────────────────────────────────────────────────────
Review the list above. Tell me which items to change before I proceed.
(e.g. "flip 3 to reject, reason: ...", "change action on 7 to ...", "skip 10")
```

The agent waits for user input. Accepted adjustments:

| Command | Effect |
|---------|--------|
| "looks good" / "proceed" | Accept all as-is |
| "flip \<n\> to comply, action: \<text\>" | Change reaction + set action |
| "flip \<n\> to reject, reason: \<text\>" | Change reaction + set reason |
| "change action on \<n\> to \<text\>" | Update action text only |
| "change reason on \<n\> to \<text\>" | Update reason text only |
| "skip \<n\>" | Exclude item from ACT entirely |

The agent applies all adjustments and re-confirms the final list before proceeding to ACT.

---

### PHASE 4 — ACT

Executed only after user confirms the final classification.

**Comply items — code edits:**

1. For each comply thread, apply the code edit described in `action` to the working tree.
2. No automatic commit — changes are left staged/unstaged for the user to review and commit via `/commit-prep`.
3. Record outcome: `done` or `failed: <reason>`.

**Reject items — Azure thread replies:**

1. For each reject thread, post the `reason` text as a reply to the existing thread using `git_create_pull_request_thread_comment` (or equivalent MCP tool).
2. **Thread status must not be changed** — only a reply is added. Do not resolve, close, or mark won't-fix.
3. Record outcome: `posted` or `failed: <reason>`.

---

### PERSIST

After ACT completes, write a vault note to:

```
AI_Codex/Agent_Reports/YYYY-MM-DD-pr-review-<PR#>.md
```

**Frontmatter:**

```yaml
---
date: YYYY-MM-DD
type: report
pr: <number>
repo: <inferred repo name>
branch: <active branch>
outcome: complete | partial
---
```

- `complete`: all ACT items succeeded.
- `partial`: one or more items failed (noted in body).

**Body:** the full confirmed classification table followed by an ACT outcomes section listing each item's result.

---

## Guardrails

- **Thread status immutability**: never resolve, close, or update the status of any Azure thread. Replies only.
- **No automatic commits**: code edits land in the working tree; the user commits them.
- **Skip over MCP errors**: if a single thread's reply fails to post, log the failure and continue with remaining items.
- **One PR per invocation**: if multiple PR numbers are passed, process only the first and warn.
- **Skipped threads are never acted on**: resolved and won't-fix threads are fully excluded from CLASSIFY, PRESENT, and ACT.
