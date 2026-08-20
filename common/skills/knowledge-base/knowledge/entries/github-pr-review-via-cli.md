---
name: github-pr-review-via-cli
description: Reading and answering PR review threads with `gh api` — three separate endpoints, anchor on diff_hunk not remembered line numbers, reply with in_reply_to, never rename the head branch.
type: howto
---

## The three endpoints hold different things

```bash
# inline review comments (the threads on code lines)
gh api repos/OWNER/REPO/pulls/N/comments --paginate \
  --jq '.[] | "=== \(.id) | \(.user.login) | \(.path):\(.line // .original_line) | in_reply_to=\(.in_reply_to_id // "-")\n\(.body)\n"'

# review summaries ("I have a bunch of questions, but ...")
gh api repos/OWNER/REPO/pulls/N/reviews --paginate --jq '.[] | select(.body != "") | ...'

# top-level PR conversation (bots: benchmarks, codex, CI)
gh api repos/OWNER/REPO/issues/N/comments --paginate --jq '...'
```

Miss one and you will miss half the feedback. `in_reply_to_id` is what stitches a thread together;
`line` is null on outdated comments, so fall back to `original_line`.

## Anchor on `diff_hunk`, never on a remembered line number

Before assessing what a comment is about, fetch the comment itself and read its `diff_hunk`:

```bash
gh api repos/OWNER/REPO/pulls/comments/COMMENT_ID \
  --jq '"\(.path):\(.line // .original_line)\n\(.diff_hunk)\n\n\(.user.login): \(.body)"'
```

Line numbers drift with every push, and a summary of "the comment about X" written earlier can be wrong.
The `diff_hunk` is frozen at the moment the comment was written — it is the ground truth for what the
reviewer was pointing at.

## Replying in-thread

```bash
gh api repos/OWNER/REPO/pulls/N/comments -X POST \
  -F in_reply_to=COMMENT_ID -F body=@reply.md --jq '"posted \(.id) -> \(.html_url)"'
```

`-F body=@file` avoids all shell-quoting problems with multi-line markdown (see
[[windows-script-file-edits]] for where to put that file).

## Gotchas

- **Renaming a PR's head branch closes the PR.** GitHub does not follow the rename. Push a new branch
  and open a fresh PR, or leave the name alone.
- To read a file from a branch, prefer `raw.githubusercontent.com/OWNER/REPO/REF/path` over
  `gh api .../contents/...` — no base64 round-trip and no size limit surprises.
