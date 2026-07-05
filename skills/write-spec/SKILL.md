---
name: write-spec
description: Generate specification files with Actor-Critic adversarial review and reflection retries.
---

# write-spec

Produce one or more specification documents under `<vault>/Specs/<ticket-slug>/` using an **Actor-Critic** reflection loop backed by the orchestrator retry state.

Literature basis (templates in `references/templates/`):
- **RFC** — proposal and feedback before decision (IETF-style internal RFC)
- **ADR** — immutable architecture decision record (Nygard / ThoughtWorks)
- **Design Doc** — Google-style system design before implementation
- **Tech Spec** — implementation-ready engineering specification
- **SRS** — ISO/IEC/IEEE 29148-inspired software requirements
- **Implementation Plan** — milestone/task breakdown
- **Bugfix Spec** — defect diagnosis and verification
- **API Contract** — endpoint/schema contract with RFC 2119 normative language

Also read `references/critic-rubric.md` before the Critic phase.

---

## ACTOR — Draft

**Inputs:** `ticket_id`, `spec_kind`, optional ticket ledger / requirements / implementation plan text.

1. Load the matching template from `skills/write-spec/references/templates/<spec_kind>.md`.
2. Read `<vault>/_mistakes/mistakes.json (legacy: Specs/_mistakes/)` and avoid recorded flaws.
3. Draft the spec using ticket description, requirements, and implementation plan sections from the active ledger.
4. Replace every template placeholder; no `TODO` / `TBD` in the final draft.

---

## CRITIC — Adversarial review

Submit the draft to the orchestrator by calling write-spec with `draft_content` set. The Critic checks:

- Required section headings for the `spec_kind`
- Placeholder-free prose
- RFC 2119 normative keywords where required (tech-spec, srs, api-contract)
- Non-Goals present for design-doc
- Rollback / mitigation for implementation-facing specs
- No repetition of entries in the mistakes repository

If critiques are returned, revise the draft and resubmit (reflection attempt increments).

---

## CIRCUIT BREAKER

After **3** failed Critic rounds, or when critiques are identical across retries, the loop trips `blocked_requires_review`. The flaw is appended to `<vault>/_mistakes/mistakes.json (legacy: Specs/_mistakes/)` for future avoidance.

---

## PERSIST

When the Critic returns no critiques, write the file:

```
<vault>/Specs/<ticket-slug>/<spec_kind>.md
```

Frontmatter:

```yaml
---
type: spec
kind: <spec_kind>
ticket: <ticket_id>
status: accepted
---
```

Link the spec path from the active ticket ledger under `## Specs`.
