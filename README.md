# ia

Personal Claude Code tooling, published as a **plugin marketplace** (`dromanol`).

## Layout

```
ia/
├── .claude-plugin/marketplace.json   # the marketplace catalog (lists the plugins below)
├── common/                            # plugin: cross-project skills (keep enabled everywhere)
│   ├── .claude-plugin/plugin.json
│   └── skills/
└── dd-trace-dotnet/                   # plugin: skills for the dd-trace-dotnet repo
    ├── .claude-plugin/plugin.json
    └── skills/
        └── run-system-tests/          # build the Linux tracer package + run system-tests
```

## Convention

- **One plugin per project**, named after the repo it targets (`dd-trace-dotnet`, and later
  `system-tests`, etc.). Its skills carry repo-specific `description` triggers.
- **`common`** holds cross-project skills and stays enabled everywhere.
- **Scoping is by skill `description`** (native Claude Code behaviour): a plugin's skills are only
  model-invoked when the task matches, so project plugins don't fire outside their repo even while
  enabled. (Claude Code does not auto-load plugins by working-directory name; description-based
  relevance is the mechanism.)

## Adding a new project plugin

1. `mkdir -p <project>/skills/<skill-name>` and add `<skill-name>/SKILL.md` (+ helper scripts).
2. Create `<project>/.claude-plugin/plugin.json` (`name` = `<project>`).
3. Add `{ "name": "<project>", "source": "./<project>" }` to `.claude-plugin/marketplace.json`.

Bundled scripts inside a skill are referenced at runtime via `${CLAUDE_SKILL_DIR}` (works regardless
of where the plugin is installed). Skills that operate on a target repo resolve it from the current
working directory (Claude's cwd), not from the plugin's install location.

## Install (local, no push)

```
/plugin marketplace add C:\_dd\git\ia
/plugin install common@dromanol
/plugin install dd-trace-dotnet@dromanol
```

After pushing to GitHub you can instead `/plugin marketplace add dromanol/ia`, or register it in
`~/.claude/settings.json` under `extraKnownMarketplaces` with a `github` source.
