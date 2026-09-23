---
name: bash-tool-vs-powershell-syntax
description: On Windows sessions both a Bash and a PowerShell tool exist; PowerShell here-strings pasted into Bash corrupt the argument silently, with no error.
type: gotcha
---

Windows sessions expose **two** shell tools with different syntax: PowerShell (often the primary) and a
Git Bash tool. Mixing their syntax mostly errors loudly — except for a few forms that **succeed with the
wrong result**, which are the dangerous ones.

## The silent one: here-strings

PowerShell's here-string `@'…'@` in the Bash tool does not fail. Bash parses `@'…'@` as the literal `@`,
plus a single-quoted string, plus another `@` — one concatenated argument. So:

```bash
git commit -m @'
Subject line

Body.
'@
```

commits successfully with a message whose first line is `@` and whose last line is `@`. Nothing warns
you; the exit code is 0.

In the **Bash** tool use a heredoc and read from stdin:

```bash
git commit -F - <<'EOF'
Subject line

Body.
EOF
```

In the **PowerShell** tool the `@'…'@` form is correct, but the closing `'@` must be at column 0 on its
own line.

## ...but large heredocs are not reliable either

The heredoc advice above holds for short bodies. For a **long** body (~100+ lines of prose, code fences,
backticks, `$VAR` sequences), the Bash tool intermittently fails with

```
/usr/bin/bash: -c: line 57: unexpected EOF while looking for matching `''
```

even with a **quoted** delimiter (`<<'EOF'`), where nothing should be interpreted. It reproduces across
sessions and the root cause was never pinned down — don't burn time re-quoting, and don't assume your
body is malformed.

The reliable pattern for any substantial file content or script:

1. Write the content to a file with the **Write tool** (no shell parsing involved).
2. Run or consume it from Bash (`python fix.py`), then `rm` it.

This also applies to Python one-liners that embed quotes: put the script in a `.py` file and run it,
rather than fighting `python -c "…"` nesting. See [[windows-script-file-edits]] for what that script
must preserve.

**Always verify multi-line text that went through a shell**, because the corruption is invisible in the
command's own output: `git log -1 --format='%B' | cat -A`. Fix with `git commit --amend -F -` before
pushing.

## Other cross-contamination worth remembering

- `2>/dev/null` (Bash) vs `2>$null` (PowerShell) — on Windows, `>nul` can create a literal file named
  `nul` that is very hard to delete.
- `&&`/`||` chaining does not exist in Windows PowerShell 5.1; use `A; if ($?) { B }`.
- `$VAR` (Bash) vs `$env:VAR` (PowerShell); PowerShell has no inline `VAR=x cmd` prefix.
- Backslash (Bash) vs backtick (PowerShell) as the escape character.

The general rule: decide which tool you're in *before* composing the command, and prefer heredocs over
quoting gymnastics for anything multi-line. See also [[concise-generated-text]] for the message content
itself.
