# Decisions (DR / ADR / FDR)

The handbook supports three decision artifacts:

- DR (Decision Register): a bounded decision with two options + recommendation
- ADR (Architecture Decision Record): a project-level architecture decision
- FDR (Feature Decision Record): a feature-scoped decision record

## DR-first workflow

In most cases, start with a DR:

```bash
ph dr add --id DR-0001 --title "Decision needed: ..."
```

After the direction is approved, formalize it as:

```bash
ph adr add --id ADR-0001 --title "..." --dr DR-0001 --status draft
ph fdr add --feature foo --id FDR-0001 --title "..." --dr DR-0001
```

## Where decision files live

Project scope:

- DR: `.project-handbook/decision-register/DR-0001-<slug>.md`
- ADR: `.project-handbook/adr/0001-<slug>.md` (front matter contains `id: ADR-0001`)
- FDR: `.project-handbook/features/<feature>/fdr/0001-<slug>.md` (front matter contains `id: FDR-0001`)

DRs can also be feature-scoped (created under a feature’s `decision-register/`) depending on how you run `ph dr add`.

## Conventions and validation

The CLI enforces conventions around:

- IDs (`DR-0001`, `ADR-0001`, `FDR-0001`)
- filenames (numeric prefix + kebab-case slug)
- required headings in ADR/FDRs (Context / Decision / Consequences / Acceptance Criteria)
- DR linkage: ADR/FDR creation requires `--dr DR-0001`

If you’re blocked on a decision, capture the operator question explicitly with `ph question add`.

