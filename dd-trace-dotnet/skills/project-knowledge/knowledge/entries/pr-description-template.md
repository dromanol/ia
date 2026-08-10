---
name: pr-description-template
description: dd-trace-dotnet PR descriptions must follow .github/pull_request_template.md's schema and be kept short/concise.
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
