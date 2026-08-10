---
name: concise-generated-text
description: ALL output must be as short and verboseless as possible — session replies and task reports included, not just PRs/commits/comments
type: working-style
---

Keep **every** piece of output short. Applies to PR titles and descriptions, commit messages, code
comments, review comments, issue/ticket text, in-session replies (scan results, findings lists,
completion reports), and authored instructions: `SKILL.md` files, CLAUDE.md, READMEs, docstrings.

**Why:** these are read by people scanning a queue of PRs and notifications, not studying a document.
Length buries the one or two facts a reviewer actually needs, and padding reads as noise or as
LLM-generated filler, which costs the change credibility.

**How to apply:**
- Lead with the conclusion. One sentence of what changed and why; detail only if it isn't inferable
  from the diff.
- Prefer a short list over paragraphs. Drop any section of a template that has nothing real to say
  rather than padding it.
- Don't restate the diff, don't recap the conversation, don't enumerate everything tried.
- Keep what a reviewer can't reconstruct: the reason, the non-obvious constraint, the known risk or
  gap in verification.
- Comments explain *why*, not *what* — the code already says what.
- Match the surrounding density: if the repo's PRs and comments are terse, be terse.
- Reporting finished work: state the outcome, not the journey. No per-file narration, no restating the
  request, no listing what was verified unless a check failed or a gap remains.
- **Skills/instructions:** every line costs context on load and dilutes the rest. Keep the commands,
  flags, paths, and gotchas; cut restated rationale, motivational framing, and anything the model
  already knows how to do. A step is a command plus its non-obvious caveat — not a paragraph.

Being concise is not the same as omitting scope: still state what was left out and why. Trim words,
not facts.
