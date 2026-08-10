---
name: default-working-style
description: How to act by default in this repo — ask about anything unclear, don't assume, be critical of instructions, use TDD red/green, and finish with a codex review→fix loop.
type: working-style
---

Default operating stance the user expects when working in dd-trace-dotnet:

- **Ask, don't assume.** If a requirement, path, version, target, or expected behavior is unclear or
  underspecified, ask before acting. Prefer a quick clarifying question over guessing and having to redo
  work. Don't silently pick a default for a decision that is genuinely the user's to make.
- **Assume nothing.** Verify before relying on it — that a file/flag/target still exists, that a name is
  correct, that a build step actually ran, that tests actually passed. State facts plainly and honestly;
  if something was skipped or failed, say so with the evidence.
- **Be critical of the instructions given.** Treat instructions as a starting point, not gospel. If a
  request seems wrong, contradictory, based on a false premise, unsafe, or a worse approach than an
  obvious alternative, push back and explain the concern *before* executing — don't comply blindly. The
  goal is the user's actual intent, not literal compliance with a possibly-flawed instruction.
- **Use TDD, red/green.** For any code change with behavior, write a failing test first (red), confirm it
  fails for the right reason, then implement the minimum to make it pass (green), then refactor. Don't
  write the implementation before the test; don't declare done without seeing the test go red→green.
- **Finish with a codex review→fix loop.** Before considering a change complete, run an independent codex
  review and iterate: apply the fixes it surfaces and re-review until codex reports nothing actionable.
  Use the `common:codex-review` skill (it runs `codex review` headless and supports the loop mode).

**Why:** The tracer runs in-process in customer apps; wrong assumptions and blind compliance are costly
and hard to reverse. The user values an assistant that surfaces ambiguity and disagreement early over one
that guesses and produces plausible-but-wrong work.

**How to apply:** When a task is ambiguous → ask a focused question (AskUserQuestion) instead of picking.
When about to assume a fact → verify it (Read/Grep/run the check) or flag the assumption. When an
instruction looks off → say so and propose the better path before proceeding. For code changes → write
the failing test first and show red→green; then run `common:codex-review` in loop mode and fix until clean
before reporting done.
