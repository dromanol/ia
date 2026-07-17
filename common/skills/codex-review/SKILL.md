---
name: codex-review
description: >-
  Use the OpenAI `codex` CLI as an independent, second-opinion code reviewer — optionally in a
  review→fix loop. Use when the user explicitly asks for a codex review, a second opinion from codex,
  an independent / adversarial review, or a "loop reviewer". Runs `codex review` headless over the
  uncommitted changes, a base branch, or a commit; in loop mode Claude applies the fixes and re-reviews
  until codex reports nothing actionable. Independent of any specific project.
argument-hint: "[--uncommitted | --base <branch> | --commit <sha>] [--loop] [--instructions <text>]"
---

# codex-review — independent review with the OpenAI Codex CLI

Runs `codex` as a second reviewer (a different model) over a diff, and optionally drives a
review → fix → re-review loop with Codex as the judge and Claude applying the fixes.

## Prerequisites

- **`codex` on PATH**: `codex --version` (this is the OpenAI Codex CLI, not a Datadog tool).
- **Authenticated**: `codex login status` prints `Logged in ...`. If not, tell the user to run
  `codex login` and stop.
- **Windows sandbox caveat**: on Windows the default Codex sandbox (`~/.codex/config.toml`
  `[windows] sandbox = "elevated"`) can fail to launch its helper
  (`codex-windows-sandbox-setup.exe ... program not found`), which makes `codex review` return
  *"No findings could be verified ... failed to launch its Windows sandbox helper"*. Work around it by
  overriding the sandbox **per invocation** (do NOT edit the user's global config):
  `-c sandbox_mode="danger-full-access"`. This is safe here because a review only reads. If it still
  fails, run codex inside WSL (its Linux sandbox works) or suggest `codex update`.

## Arguments

Arguments are available as `$ARGUMENTS`. Parse:

- **Scope** (default `--uncommitted`):
  - `--uncommitted` → review staged + unstaged + untracked changes (working tree).
  - `--base <branch>` → review the diff against `<branch>` (PR-style).
  - `--commit <sha>` → review the changes introduced by a commit.
- `--loop` → run the review→fix→re-review loop (default: single review, no edits).
- `--instructions <text>` → extra review instructions passed to codex as the prompt.

## Procedure

Run codex from the **target repository's directory** (codex reviews the repo of the current working
directory). If Claude's cwd already is that repo, run in place; otherwise `cd` there first.

### 1. Preflight

```bash
codex --version && codex login status
```

### 2. Run the review

Build and run (adjust the scope flag; append `--instructions` text as the trailing prompt argument, not
via stdin):

```bash
codex review <scope> -c sandbox_mode="danger-full-access" --title "<short title>" "<optional instructions>"
```

Examples:
```bash
codex review --uncommitted -c sandbox_mode="danger-full-access" --title "working-tree review"
codex review --base master  -c sandbox_mode="danger-full-access"
codex review --commit 1a2b3c -c sandbox_mode="danger-full-access"
```

Codex prints a review with findings. Relay the findings to the user (most severe first). If the output
is the "sandbox helper" message, apply the Windows workaround / WSL fallback from Prerequisites.

### 3. Loop mode (`--loop`)

Repeat until codex reports no actionable findings, or **max 3 iterations**:

1. Run the review (step 2).
2. If there are actionable findings, **apply the fixes** with the edit tools (Codex only reviews; it
   does not edit — Claude makes the changes).
3. Re-run the review on the same scope.

Stop early when a pass returns nothing actionable. Summarize what changed across iterations.

### 4. Report

Give the user: the confirmed findings, what was fixed (loop mode), and any findings left unaddressed
(with why).

## Notes

- **Read-only reviewer**: codex reviews and reports; it does not modify files. All edits are made by
  Claude. (`danger-full-access` disables codex's *own* sandbox so it can run `git`, but the review flow
  still only reads.)
- **Cost**: codex uses a separate model (ChatGPT auth) — each iteration costs. The loop is capped at 3.
- **Complements `/code-review`**: this is a second opinion from a different model, not a replacement.
- **Scope hygiene**: prefer `--base <branch>` or `--commit <sha>` when the working tree has unrelated
  noise (e.g. generated files), so the review focuses on the real change.
