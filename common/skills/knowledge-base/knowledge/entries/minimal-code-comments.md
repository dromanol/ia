---
name: minimal-code-comments
description: Default to writing NO code comments; add one only for a why the code cannot show, and keep it to one line
type: working-style
---

Write no comment unless its absence would cost a reader real time. The bar is a **why** the code cannot
express: a non-obvious constraint, a race, a platform/TFM quirk, a deliberate omission, a reason a
tempting simpler form is wrong. Everything else is deleted, not shortened.

Delete on sight: restatements of the next line, section banners (`// --- setup ---`), XML doc on private
or test-only members, comments naming what a well-named symbol already says, TODOs without an owner,
narration of a diff ("now uses CAS instead of..."), and any comment that repeats the commit message or
PR body.

**Why:** comments are the first thing to rot and the loudest tell of generated code. A wrong comment is
worse than none, and a wall of them buries the one line that actually mattered.

**How to apply:**
- Default is zero. Adding one is a decision that needs a reason.
- One line. If the why genuinely needs more, two — never a paragraph.
- Put it on the branch or statement it explains, not as a preamble to a whole method.
- Say the constraint, not the mechanism: `// TryRemove(KeyValuePair<,>) does not exist on net461`
  beats three lines explaining compare-and-remove semantics.
- Match the file's existing density; do not out-comment the surrounding code.
- Reviewing your own diff: reread every comment you added and delete the ones that only describe.

Applies to code comments specifically; see [[concise-generated-text]] for output length in general.
