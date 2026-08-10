---
name: knowledge-base
description: >-
  Global (cross-project) reusable knowledge base. Captures and recalls non-obvious, durable knowledge
  that applies regardless of the repository — internal tools, org conventions, recurring how-tos,
  cross-project gotchas. Use when the user says "save/remember this globally", "add to global
  knowledge", "capture knowledge", asks "what do we know about <topic>", or wants to recall/list
  cross-project learnings. The global index is auto-loaded at session start by this plugin's
  SessionStart hook (in every session, everywhere). For knowledge specific to ONE repo, use that
  repo's `project-knowledge` skill instead.
argument-hint: "[save | recall <topic> | list] [--instructions <text>]"
---

# knowledge-base — global (cross-project) knowledge

Curated **non-obvious, durable, reusable** knowledge that applies in **any** repo. Repo-specific facts
belong in that repo's `/project-knowledge` store instead.

- `knowledge/INDEX.md` — one-line pointers, auto-loaded every session. Keep it bounded: context budget.
- `knowledge/entries/<slug>.md` — one topic per file.

`$ARGUMENTS`: mode (`save` when the user asks to capture, else `recall <topic>` / `list`), plus optional
`--instructions <text>` to focus a capture.

## Resolve the store first

It lives in the **source `ia` repo**, never the plugin cache (wiped on reinstall). In order:

1. `$KNOWLEDGE_BASE_DIR_COMMON`
2. `.dromanol.installLocation` in `~/.claude/plugins/known_marketplaces.json` →
   `<that>/common/skills/knowledge-base/knowledge/`
3. `..\ia\common\skills\knowledge-base\knowledge\` next to the working repo

```powershell
$src = (Get-Content "$env:USERPROFILE\.claude\plugins\known_marketplaces.json" -Raw | ConvertFrom-Json).dromanol.installLocation
$kb  = Join-Path $src "common\skills\knowledge-base\knowledge"
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
2. Keep only what is **cross-project**, **reusable**, **non-obvious**, and **durable** — a gotcha, an
   internal tool/command, where something lives, a decision + its rationale, a pitfall + fix. Also
   `type: working-style` guidance (the rule *and* its why, so it can be applied). Skip secrets,
   ephemeral task state, and anything already in the code or CLAUDE.md. Repo-specific → route to
   `/project-knowledge save`. Nothing qualifies → say so and stop.
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

- Writes go to the source `ia` repo. Never write knowledge into `${CLAUDE_SKILL_DIR}` — a runtime snapshot.
- `hooks/hooks.json` injects `INDEX.md` at SessionStart in every repo; `scripts/remind_capture.py` nudges
  a capture at PreCompact and names the current project's store too when it has one. Entries are read
  live from the source.
