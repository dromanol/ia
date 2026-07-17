# dd-trace-dotnet knowledge base

Reusable, **non-obvious** knowledge for working in the dd-trace-dotnet repo. One entry per file under
`entries/`. This index is auto-loaded into context at session start (only in dd-trace-dotnet) and grows
via `/knowledge-base save`. Keep it curated and concise — prune stale entries.

## Entries
- [Default working style](entries/default-working-style.md) — ask when unclear, assume nothing, be critical of instructions, TDD red/green, codex review→fix loop
- [BuildNativeWrapper produces the LD_PRELOAD ApiWrapper](entries/build-native-wrapper.md) — omit it and Linux packaging fails with `ln: No such file`
- [glibc tar bundles musl → two-stage build](entries/glibc-tar-bundles-musl.md) — CMake libdatadog FetchContent libc-contamination gotcha
- [Where the Linux package is produced](entries/linux-package-targets.md) — PackageTracerHome / ZipMonitoringHomeLinux, output paths
