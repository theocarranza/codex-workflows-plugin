# Critic rubric — resolve-ticket

The Critic is **adversarial** and **grounded**: it compares the draft resolution report against spec files, ticket ledger hints, and the mistakes repository.

## Required sections

| Section | Pass criteria |
|---------|----------------|
| Problem Recap | Restates problem and acceptance criteria; not copy-paste filler |
| Spec Coverage | Every `*.md` spec (except this report) appears with satisfied/deferred/out-of-scope |
| Implementation Summary | Names concrete artifacts: paths, commits, PR, modules |
| Verification | Documents tests or QA performed |
| Residual Risks | Explicit risks or a clear "none" statement |

## Ground truth sources

1. `<vault>/Specs/<slug>/*.md` — authoritative design/requirements
2. Active ticket ledger — requirements, implementation summary, verification notes
3. `<vault>/_mistakes/mistakes.json` — prior resolve-ticket flaws to avoid repeating

## Automatic failures

- Placeholders (`TODO`, `TBD`, `FIXME`)
- Spec files exist but are not referenced
- No verification narrative
- Implementation summary without evidence
- Repeating a recorded mistake flaw verbatim
