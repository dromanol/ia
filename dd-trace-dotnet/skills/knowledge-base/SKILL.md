---
name: knowledge-base
description: >-
  Reusable knowledge base for working in the dd-trace-dotnet repo. Captures and recalls non-obvious,
  durable project knowledge (gotchas, where things live, how-tos, decisions + rationale, build/test
  pitfalls) that's worth reusing across sessions. Use when the user says "save/remember this",
  "capture knowledge", "wrap up", "end of session", asks "what do we know about <topic>", or wants to
  recall/list dd-trace-dotnet learnings. The knowledge index is also auto-loaded at session start by
  this plugin's SessionStart hook.
argument-hint: "[save | recall <topic> | list] [--instructions <text>]"
---

# knowledge-base — dd-trace-dotnet reusable knowledge

A growing, curated store of **non-obvious, durable, reusable** knowledge for working in the
dd-trace-dotnet repo. Two tiers, mirroring Claude Code's native memory format:

- `knowledge/INDEX.md` — curated one-line pointers (auto-loaded at session start; keep it concise).
- `knowledge/entries/<slug>.md` — one topic per file, with frontmatter.

## Where the knowledge lives (resolve this first)

The store lives in the **SOURCE `ia` repo** (NOT the plugin cache — the cache is wiped on reinstall).
Resolve the knowledge dir, in order:

1. `$KNOWLEDGE_BASE_DIR` if set.
2. The `dromanol` marketplace source from `~/.claude/plugins/known_marketplaces.json`
   (`.dromanol.installLocation`) → `<that>/dd-trace-dotnet/skills/knowledge-base/knowledge/`.
3. Sibling fallback: `..\ia\dd-trace-dotnet\skills\knowledge-base\knowledge\` relative to the
   dd-trace-dotnet repo (cwd).

Quick resolve (PowerShell):
```powershell
$src = (Get-Content "$env:USERPROFILE\.claude\plugins\known_marketplaces.json" -Raw | ConvertFrom-Json).dromanol.installLocation
$kb  = Join-Path $src "dd-trace-dotnet\skills\knowledge-base\knowledge"
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
   - **Reusable** for future dd-trace-dotnet work (not one-off to this task).
   - **Non-obvious** — a gotcha, a hard-won fact, where something lives, how to do a recurring task, a
     decision + its rationale, a pitfall and its fix.
   - **Durable** — unlikely to change next week.
   - **Working-style guidance** (`type: working-style`) — how the user wants me to behave/operate when
     working in this repo (e.g. ask when unclear, don't assume, be critical of instructions). Capture the
     rule + the *why* so it can be applied, not just recited.
   **Do NOT save** things already in `CLAUDE.md`/`AGENTS.md`, the code, or git history; secrets; or
   ephemeral task state. If nothing qualifies, say so and stop — an empty save is fine.
3. **Dedupe**: if an existing entry covers it, update that entry instead of creating a duplicate. Merge,
   don't fork.
4. **Write** each new/updated entry to `entries/<slug>.md` with the frontmatter above. Add/refresh its
   one-line pointer in `INDEX.md` (`- [Title](entries/slug.md) — hook`). Cross-link related entries
   with `[[slug]]`.
5. **Keep INDEX.md bounded** — if it's getting long, curate/merge/prune stale entries (the index is
   loaded into every dd-trace-dotnet session, so it's a context-budget item).
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
- **Auto-load:** the SessionStart hook (`hooks/hooks.json` → `scripts/session_start.py`) injects
  `INDEX.md` only when cwd is the dd-trace-dotnet repo. New entries appear in the next session (or after
  the current one — they're read live from the source).
- This is scoped to **dd-trace-dotnet**; cross-project knowledge belongs in the `common` plugin.
