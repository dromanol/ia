---
name: windows-shell-gotchas
description: PowerShell/cmd pipe-character-in---Filter splitting, and PathTooLongException on broad Get-ChildItem -Recurse over C:\ or C:\ProgramData
type: gotcha
---

Two recurring Windows-shell gotchas when driving `tracer/build.cmd`/`build.ps1` or searching the
filesystem from PowerShell/bash on this repo's dev machines:

**1. `|` in a `--Filter` value gets split by the shell.** Passing a filter like
`"FullyQualifiedName~Foo|FullyQualifiedName~Bar"` to `.\tracer\build.cmd` via PowerShell or bash causes
shell-level splitting on the pipe character, breaking the intended single argument. Fix: run separate
sequential build/test invocations, one per filter clause, instead of trying to OR them in one
`--Filter` string.

**2. `Get-ChildItem -Recurse` over `C:\` or `C:\ProgramData` can throw `PathTooLongException`** on deeply
nested paths (e.g. under `IntuneManagementExtension` or NuGet package caches). Mitigate by scoping
searches to specific known candidate directories individually rather than recursing the whole drive or
`C:\ProgramData` wholesale.
