---
name: windows-script-file-edits
description: Editing repo files from scripts on Windows — Git Bash `/tmp` is not Windows-Python `/tmp`, and a Python rewrite silently drops the BOM and the CRLFs.
type: gotcha
---

Three ways a scripted file edit on Windows succeeds and still leaves you with the wrong result.

## `/tmp` means two different directories

Git Bash maps `/tmp` to the **user temp dir** (`C:\Users\<you>\AppData\Local\Temp`). A Windows-native
program — `python.exe`, `node.exe`, anything not running under the MSYS runtime — resolves the same
literal string to **`C:\tmp`**.

So this sequence quietly operates on two different files:

```bash
gh pr view 9057 --json body -q .body > /tmp/pr.md   # writes to the user temp dir
python patch.py /tmp/pr.md                          # FileNotFoundError on C:\tmp\pr.md
gh pr edit 9057 --body-file /tmp/pr.md              # re-posts the UNPATCHED body, exit 0
```

The failing step is loud, but the step *after* it isn't — it happily uses the unedited file. Use a
**repo-relative** temp file (`pr9057.tmp.md`) instead, and verify the edit landed
(`grep -c "<new text>" pr9057.tmp.md`) before consuming it.

## A Python rewrite drops the BOM and the line endings

`open(p).read()` + `open(p,"w").write(s)` normalises away whatever the file had. In a repo with
`text=auto` and Windows checkouts, that turns into a whole-file diff.

Preserve the **original** state — don't guess it, read it:

```bash
git show HEAD:path/to/File.cs | head -c 3 | xxd   # ef bb bf => the file has a BOM
```

```python
s = io.open(p, encoding="utf-8-sig").read()          # strips a BOM if present
io.open(p, "w", encoding="utf-8-sig" if had_bom else "utf-8", newline="\r\n").write(s)
```

Check with `git diff --stat` afterwards: a one-line change that reports the whole file as modified means
you changed the encoding or the endings, not the content.

## A new LF-only file shows a phantom `M`

Under `text=auto`, a file you created with LF endings shows as modified right after `git add` reports
nothing to do. `git add` it once and the index normalises it; the `M` disappears.

Related: [[bash-tool-vs-powershell-syntax]] for the shell-syntax half of the same problem.
