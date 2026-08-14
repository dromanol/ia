---
name: default-working-style
description: dd-trace-dotnet working style on top of the global stance — TDD red/green for any behavior change, and finish with a codex review→fix loop.
type: working-style
---

Repo-specific additions to the global [[never-complacent]] stance (ask, don't assume; be critical of the
instructions; verify before claiming) — which applies here with extra force.

- **TDD, red/green.** Any change with behavior: write the failing test first, confirm it fails for the
  right reason, implement the minimum to pass, then refactor. Never the implementation before the test;
  never "done" without having seen red→green.
- **Finish with a codex review→fix loop.** Before calling a change complete, run `common:codex-review` in
  loop mode and iterate until codex reports nothing actionable.

**Why:** the tracer runs in-process in customer apps, so wrong assumptions and untested behavior changes
are costly and hard to reverse.
