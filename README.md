# ia

Personal Claude Code tooling: one plugin marketplace (`dromanol`) with a single plugin, `common`, which
also acts as the **bootstrapper** that delivers per-project skills into whatever repo you're working in.

## Layout

```
ia/
├── .claude-plugin/marketplace.json     # marketplace catalog — lists `common` only
├── common/                             # THE plugin (keep enabled everywhere)
│   ├── .claude-plugin/plugin.json
│   ├── hooks/hooks.json                # SessionStart: global knowledge + project-skill copy
│   │                                   # PreCompact:   nudge a knowledge capture
│   ├── scripts/link_project_skills.py  # the bootstrapper (see below)
│   └── skills/
│       ├── knowledge-base/             # GLOBAL cross-project knowledge (recall/save/list)
│       ├── codex-review/               # second-opinion review via the OpenAI `codex` CLI
│       └── do/                         # feature-lifecycle orchestrator — WIP, not wired up yet
└── dd-trace-dotnet/                    # per-project SKILL SOURCE (not a plugin)
    ├── required-siblings.json          # sibling repos this project's skills need
    └── skills/
        ├── project-knowledge/          # dd-trace-dotnet-scoped knowledge base
        └── run-system-tests/           # build the Linux tracer package + run system-tests
```

## How per-project skills get delivered

Only `common` is ever installed. At session start its bootstrapper
(`common/scripts/link_project_skills.py`) looks at the repo you're in, matches its directory name
against a top-level folder here, and **copies** that folder's skills into the clone:

```
<ia>/<project>/skills/<name>/   ->   <clone>/.claude/skills/<name>/
```

Claude Code auto-discovers `.claude/skills/`, so those skills become first-class and invocable without
registering a per-project plugin or marketplace — and there is exactly **one** place to edit them: here.

Properties worth knowing:

- **Source wins.** Copies are refreshed every session; local edits to a copy are discarded. Edit in `ia`.
- Each managed copy carries a `.ia-managed` marker. A same-named directory *without* the marker is a
  foreign skill (e.g. one the repo itself commits) and is left untouched.
- Copies are added to the clone's `.git/info/exclude`, so they never show up in `git status`
  (worktree-aware: the exclude goes to the git *common* dir).
- Managed copies whose source skill disappeared are pruned.
- A newly copied skill becomes invocable on the **next** session or after `/reload-plugins` — skills are
  enumerated before the hook runs. Refreshed existing ones work immediately.
- No match for the current repo → strict no-op. Errors never block a session.

`<project>/required-siblings.json` declares repos that project's skills expect next to the clone (same
parent dir); the bootstrapper warns at session start when one is missing.

## Conventions

- **Per-project folders are skill sources, not plugins.** Do not add them to `marketplace.json`.
  Registering one as a plugin *and* letting the bootstrapper copy it would inject that project's
  knowledge index twice and create duplicate skill names.
- **Folder name must equal the repo directory name** (`dd-trace-dotnet`) — that's the match key.
- **A project's knowledge base is named `project-knowledge`**, never `knowledge-base`. The global one
  (`common`) owns `knowledge-base`; two same-named skills make `/knowledge-base` ambiguous once the
  project copy lands in `.claude/skills/`. The bootstrapper also reads
  `<project>/skills/project-knowledge/knowledge/INDEX.md` by that exact name to auto-load it.
- **Bundled scripts** are referenced at runtime via `${CLAUDE_SKILL_DIR}` so they resolve wherever the
  skill was copied. Skills that operate on a target repo resolve it from Claude's cwd, never from the
  script's own location.
- **Knowledge is written back to this repo**, not to the copy under `.claude/skills/` (which is
  overwritten). Commit `ia` to persist it.

## Adding skills for a new project

1. `mkdir -p <project>/skills/<skill-name>` (where `<project>` is the repo's directory name) and add
   `<skill-name>/SKILL.md` plus any helper scripts.
2. For a knowledge base, name the skill `project-knowledge` and seed
   `<project>/skills/project-knowledge/knowledge/INDEX.md`.
3. Optionally add `<project>/required-siblings.json` if the skills need neighbouring clones.
4. Nothing to register. Open a session in that repo and the bootstrapper copies it in.

## Install (local, no push)

```
/plugin marketplace add C:\_dd\git\ia
/plugin install common@dromanol
```

After pushing to GitHub you can instead `/plugin marketplace add dromanol/ia`, or register it in
`~/.claude/settings.json` under `extraKnownMarketplaces` with a `github` source. Overrides for the
bootstrapper: `$IA_ROOT` (canonical repo location), `$KNOWLEDGE_BASE_DIR_COMMON` (global knowledge dir).
