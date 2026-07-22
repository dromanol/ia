# global knowledge base (cross-project)

Reusable, **non-obvious** knowledge that applies regardless of the repository you're working in. One
entry per file under `entries/`. This index is auto-loaded into context at session start (every
session, everywhere) and grows via `/knowledge-base save`. Keep it curated and concise — prune stale
entries. Repo-specific knowledge belongs in that repo's plugin, not here.

## Entries
- [GitHub token via ddtool](entries/github-token-ddtool.md) — `ddtool auth github token` (defaults to DataDog org)
