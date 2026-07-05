---
name: resolve-ticket
description: Resolve a ticket with Actor-Critic resolution report grounded on specs before archival.
---

# resolve-ticket

Close an active ticket by producing a **resolution report** under `<vault>/Specs/<ticket-slug>/resolution-report.md`, validated through the shared Actor-Critic reflection engine, then archive the ledger.

Read `references/critic-rubric.md` before the Critic phase.

---

## Preconditions

1. Specs exist under `<vault>/Specs/<ticket-slug>/` (from `/write-spec`).
2. Active ledger at `<vault>/Tickets/Active/<slug>.md` documents implementation summary and verification.

If the orchestrator returns `write_spec_directive`, run `/write-spec` first.

---

## ACTOR — Draft resolution report

**Inputs:** `ticket_id`, optional `implementation_summary`, `draft_content`.

1. Load `references/templates/resolution-report.md`.
2. Read all spec files in `<vault>/Specs/<ticket-slug>/` as ground truth.
3. Read `<vault>/_mistakes/mistakes.json` (and legacy `Specs/_mistakes/`) for resolve-ticket flaws to avoid.
4. Draft the report: Problem Recap, Spec Coverage (per spec file), Implementation Summary, Verification, Residual Risks.
5. No placeholders (`TODO` / `TBD`).

---

## CRITIC — Adversarial review

Submit the draft via resolve-ticket with `draft_content`. The Critic checks:

- Required section headings
- Every spec file is referenced in Spec Coverage
- Requirements mapped to satisfied/deferred outcomes
- Implementation evidence (files, commits, PR, tests)
- Verification documented
- No repetition of recorded mistakes

Revise and resubmit until critiques are empty.

---

## CIRCUIT BREAKER

After **3** failed rounds or identical critiques, mode becomes `blocked_requires_review`. The flaw is recorded in `<vault>/_mistakes/mistakes.json`.

---

## PERSIST & ARCHIVE

When the Critic is clean:

1. Write `<vault>/Specs/<ticket-slug>/resolution-report.md` with frontmatter (`type: resolution`, `ticket`, `status: accepted`).
2. Update the active ledger with resolution link and spent time / YouTrack transitions per your workflow.
3. Move the ledger to `<vault>/Tickets/Closed/` or `Resolved/` per ticket type.
