---
name: pr-description-template
description: dd-trace-dotnet PRs must follow .github/pull_request_template.md's schema, stay short, and carry the right area:* label.
type: reference
---

PR descriptions in this repo must follow the schema in `.github/pull_request_template.md`:

```
## Summary of changes

## Reason for change

## Implementation details

## Test coverage

## Other details
<!-- Fixes #{issue} -->
```

**Keep it short.** Per `AGENTS.md`'s PR guidelines: focus on "what" and "why"; only go into "how" when
the change is genuinely complex. Don't over-explain each section — a few bullets/sentences per section
is usually enough. Long, exhaustive descriptions are not the goal even when the underlying change (e.g.
a multi-round bugfix) has a lot of history behind it — summarize, don't narrate the whole journey.

`gh` CLI may not be available in all environments — see `ddtool auth github token` +
`PATCH https://api.github.com/repos/DataDog/dd-trace-dotnet/pulls/<n>` as a fallback for editing a PR
description via the REST API directly.

## Labels

A PR carries no label until someone adds one — set it when opening the PR. Find the exact names with
`gh label list --repo DataDog/dd-trace-dotnet --limit 200`, and copy what a comparable recent PR uses
(`gh pr view <n> --json labels`) instead of guessing.

AppSec/AAP work: **`area:asm`**. Don't also add `area:asm-iast` (IAST only) or `area:asm-waf-update`
(libddwaf/ruleset version bumps only).

```bash
gh pr edit <n> --add-label area:asm
```
