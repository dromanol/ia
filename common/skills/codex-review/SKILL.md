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

A second reviewer (different model) over a diff. Codex only reads and reports; **Claude makes all edits.**
Complements `/code-review`, doesn't replace it. Run from the target repo's directory.

`$ARGUMENTS`:
- Scope, default `--uncommitted` (working tree: staged + unstaged + untracked) | `--base <branch>`
  (PR-style) | `--commit <sha>`
- `--loop` → review→fix→re-review (default: single review, no edits)
- `--instructions <text>` → extra review focus, passed as the trailing prompt argument (not stdin)

## 1. Preflight

```bash
codex --version && codex login status
```
Not logged in → tell the user to run `codex login` and stop.

## 2. Review

```bash
codex review --uncommitted -c sandbox_mode="danger-full-access" --title "working-tree review"
codex review --base master  -c sandbox_mode="danger-full-access"
codex review --commit 1a2b3c -c sandbox_mode="danger-full-access"
```

`-c sandbox_mode="danger-full-access"` is required on Windows: the default `[windows] sandbox = "elevated"`
often can't launch `codex-windows-sandbox-setup.exe`, and the review returns *"No findings could be
verified ... failed to launch its Windows sandbox helper"*. Set it **per invocation** — never edit the
user's `~/.codex/config.toml`. Safe here: it disables codex's own sandbox so it can run `git`; the review
still only reads. Still failing → run codex inside WSL (its Linux sandbox works) or suggest `codex update`.

Relay findings, most severe first.

## 3. Loop mode (`--loop`)

Repeat until a pass returns nothing actionable, **max 3 iterations**: review → apply fixes with the edit
tools → re-review the same scope. Each iteration costs a separate model, hence the cap.

## 4. Report

Confirmed findings, what was fixed, and anything left unaddressed with why.

Prefer `--base <branch>` or `--commit <sha>` when the working tree has unrelated noise (e.g. generated
files) so the review focuses on the real change.
