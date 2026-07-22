---
name: knowledge-base
description: >-
  Global (cross-project) reusable knowledge base. Captures and recalls non-obvious, durable knowledge
  that applies regardless of the repository — internal tools, org conventions, recurring how-tos,
  cross-project gotchas. Use when the user says "save/remember this globally", "add to global
  knowledge", "capture knowledge", asks "what do we know about <topic>", or wants to recall/list
  cross-project learnings. The global index is auto-loaded at session start by this plugin's
  SessionStart hook (in every session, everywhere).
argument-hint: "[save | recall <topic> | list] [--instructions <text>]"
---

# knowledge-base — global (cross-project) reusable knowledge

A growing, curated store of **non-obvious, durable, reusable** knowledge that applies **regardless of
the repository** you're working in (internal tools, org conventions, recurring how-tos, cross-project
gotchas). Two tiers, mirroring Claude Code's native memory format:

- `knowledge/INDEX.md` — curated one-line pointers (auto-loaded at session start; keep it concise).
- `knowledge/entries/<slug>.md` — one topic per file, with frontmatter.

**Repo-specific knowledge does NOT belong here** — it goes in that repo's plugin (e.g. the
`dd-trace-dotnet` plugin's own knowledge base). Only save something here if it is useful in more than
one project.

## Where the knowledge lives (resolve this first)

The store lives in the **SOURCE `ia` repo** (NOT the plugin cache — the cache is wiped on reinstall).
Resolve the knowledge dir, in order:

1. `$KNOWLEDGE_BASE_DIR_COMMON` if set.
2. The `dromanol` marketplace source from `~/.claude/plugins/known_marketplaces.json`
   (`.dromanol.installLocation`) → `<that>/common/skills/knowledge-base/knowledge/`.
3. Sibling fallback: `..\ia\common\skills\knowledge-base\knowledge\` relative to the working repo (cwd).

Quick resolve (PowerShell):
```powershell
$src = (Get-Content "$env:USERPROFILE\.claude\plugins\known_marketplaces.json" -Raw | ConvertFrom-Json).dromanol.installLocation
$kb  = Join-Path $src "common\skills\knowledge-base\knowledge"
```

An entry file:
```markdown
---
name: <short-kebab-slug>
description: <one-line summary — used for recall matching and the SessionStart auto-load>
type: gotcha | howto | decision | reference | location | working-style
---

<the knowledge, concise but complete enough to reuse without redoing the work. Link related
entries with [[other-slug]].>
```

## Arguments

`$ARGUMENTS`: first token = mode (`save` default when the user asks to capture, else `recall`/`list`);
`recall` takes a `<topic>`; `--instructions <text>` passes extra focus for capture.

## Mode: save (capture)

Extract knowledge from the current session and add it to the store. Do NOT just dump the transcript —
curate.

1. **Resolve** the knowledge dir (above). Read `INDEX.md` and the existing `entries/` so you can
   dedupe and cross-link.
2. **Select** what to save — only knowledge that is:
   - **Cross-project** — useful in more than one repo. Repo-specific facts go in that repo's plugin.
   - **Reusable** for future work (not one-off to this task).
   - **Non-obvious** — a gotcha, a hard-won fact, an internal tool/command, where something lives, how
     to do a recurring task, a decision + its rationale, a pitfall and its fix.
   - **Durable** — unlikely to change next week.
   - **Working-style guidance** (`type: working-style`) — how the user wants me to behave/operate in
     general. Capture the rule + the *why* so it can be applied, not just recited.
   **Do NOT save** secrets, or ephemeral task state. If nothing qualifies, say so and stop — an empty
   save is fine.
3. **Dedupe**: if an existing entry covers it, update that entry instead of creating a duplicate.
   Merge, don't fork.
4. **Write** each new/updated entry to `entries/<slug>.md` with the frontmatter above. Add/refresh its
   one-line pointer in `INDEX.md` (`- [Title](entries/slug.md) — hook`). Cross-link related entries
   with `[[slug]]`.
5. **Keep INDEX.md bounded** — it is loaded into every session everywhere, so it is a context-budget
   item. Curate/merge/prune aggressively.
6. **Report** what you added/updated (slugs + one-line each), and remind the user to **commit the `ia`
   repo** to persist and share the knowledge.

## Mode: recall <topic>

The INDEX is already auto-loaded at session start. For details: grep `entries/` for the topic
(filename, `description`, and body), read the best matches, and surface the relevant knowledge with a
pointer to the entry file. If nothing matches, say so.

## Mode: list

Print `INDEX.md` (the catalog of what's known).

## Notes

- **Persistence:** capture writes to the source `ia` repo; the user commits it there. The plugin cache
  copy is just a runtime snapshot — never write knowledge into `${CLAUDE_SKILL_DIR}` (the cache).
- **Auto-load:** the SessionStart hook (`hooks/hooks.json` → `scripts/session_start.py`) injects the
  global `INDEX.md` into **every** session, in any repo. New entries appear in the next session (or
  after the current one — they're read live from the source).
- This is the **global / cross-project** knowledge base. Repo-specific knowledge belongs in that
  repo's own plugin.
