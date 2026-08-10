---
name: project-knowledge
description: >-
  Reusable knowledge base for working in the dd-trace-dotnet repo. Captures and recalls non-obvious,
  durable project knowledge (gotchas, where things live, how-tos, decisions + rationale, build/test
  pitfalls) that's worth reusing across sessions. Use when the user says "save/remember this",
  "capture knowledge", "wrap up", "end of session", asks "what do we know about <topic>", or wants to
  recall/list dd-trace-dotnet learnings. The knowledge index is also auto-loaded at session start by
  the `common` bootstrapper. For knowledge that applies to ANY repo, use `knowledge-base` instead.
argument-hint: "[save | recall <topic> | list] [--instructions <text>]"
---

# project-knowledge — dd-trace-dotnet knowledge

Curated **non-obvious, durable, reusable** knowledge for the dd-trace-dotnet repo. Cross-project facts
belong in the global `/knowledge-base` instead — the names differ so the two are never ambiguous.

- `knowledge/INDEX.md` — one-line pointers, auto-loaded every dd-trace-dotnet session. Keep it bounded.
- `knowledge/entries/<slug>.md` — one topic per file.

`$ARGUMENTS`: mode (`save` when the user asks to capture, else `recall <topic>` / `list`), plus optional
`--instructions <text>` to focus a capture.

## Resolve the store first

This skill runs as a **managed copy** under `<clone>/.claude/skills/project-knowledge/`, refreshed from
source every session — **never write knowledge there, it is overwritten.** The store lives in the
**source `ia` repo**. In order:

1. `$PROJECT_KNOWLEDGE_DIR`
2. `.dromanol.installLocation` in `~/.claude/plugins/known_marketplaces.json` →
   `<that>/dd-trace-dotnet/skills/project-knowledge/knowledge/`
3. `..\ia\dd-trace-dotnet\skills\project-knowledge\knowledge\` next to the dd-trace-dotnet repo

```powershell
$src = (Get-Content "$env:USERPROFILE\.claude\plugins\known_marketplaces.json" -Raw | ConvertFrom-Json).dromanol.installLocation
$kb  = Join-Path $src "dd-trace-dotnet\skills\project-knowledge\knowledge"
```

Entry format:
```markdown
---
name: <short-kebab-slug>
description: <one line — used for recall matching and the session-start auto-load>
type: gotcha | howto | decision | reference | location | working-style
---

<the knowledge, complete enough to reuse without redoing the work. Link others with [[slug]].>
```

## save

Curate; don't dump the transcript.

1. Read `INDEX.md` + existing `entries/` to dedupe and cross-link.
2. Keep only what is **reusable** for future dd-trace-dotnet work, **non-obvious**, and **durable** — a
   gotcha, where something lives, a recurring how-to, a decision + its rationale, a pitfall + fix. Also
   `type: working-style` guidance for this repo (the rule *and* its why). Skip secrets, ephemeral task
   state, and anything already in `CLAUDE.md`/`AGENTS.md`, the code, or git history. Applies beyond this
   repo → route to `/knowledge-base save`. Nothing qualifies → say so and stop.
3. An existing entry covers it → update that one. Merge, don't fork.
4. Write `entries/<slug>.md`, refresh its pointer in `INDEX.md` (`- [Title](entries/slug.md) — hook`),
   cross-link with `[[slug]]`. Merge or prune if the index is growing.
5. Report the slugs (one line each) and remind the user to commit `ia`.

## recall <topic>

The index is already in context. Grep `entries/` (filename, `description`, body), read the best matches,
surface the knowledge with a pointer to the file. Nothing matches → say so.

## list

Print `INDEX.md`.

## Notes

- Writes go to the source `ia` repo; the copies under `<clone>/.claude/skills/` and `${CLAUDE_SKILL_DIR}`
  are runtime snapshots that get overwritten.
- `common/scripts/link_project_skills.py` copies this skill in and injects `INDEX.md` at SessionStart. It
  keys off the repo directory name, so it only fires in dd-trace-dotnet. Entries are read live.
