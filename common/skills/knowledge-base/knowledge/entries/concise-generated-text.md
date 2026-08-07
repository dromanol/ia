---
name: concise-generated-text
description: All generated prose (PR descriptions, commit messages, comments, chat replies) must be short and concise
type: working-style
---

Keep **every** piece of generated text short. Applies to PR titles and descriptions, commit messages,
code comments, review comments, issue/ticket text, and chat replies.

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

Being concise is not the same as omitting scope: still state what was left out and why. Trim words,
not facts.
