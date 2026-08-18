# dd-trace-dotnet knowledge base

Reusable, **non-obvious** knowledge for working in the dd-trace-dotnet repo. One entry per file under
`entries/`. This index is auto-loaded into context at session start (only in dd-trace-dotnet) and grows
via `/project-knowledge save`. Keep it curated and concise — prune stale entries. Knowledge that applies
to any repo belongs in the global `/knowledge-base` instead.

## Entries
- [Default working style](entries/default-working-style.md) — TDD red/green + codex review→fix loop (on top of the global never-complacent stance)
- [BuildNativeWrapper produces the LD_PRELOAD ApiWrapper](entries/build-native-wrapper.md) — omit it and Linux packaging fails with `ln: No such file`
- [glibc tar bundles musl → two-stage build](entries/glibc-tar-bundles-musl.md) — CMake libdatadog FetchContent libc-contamination gotcha
- [Where the Linux package is produced](entries/linux-package-targets.md) — PackageTracerHome / ZipMonitoringHomeLinux, output paths
- [PR description template](entries/pr-description-template.md) — follow `.github/pull_request_template.md` schema, keep it short
- [BuildAspNetIntegrationTests doesn't rebuild native/managed core](entries/build-target-doesnt-rebuild-native.md) — must run BuildTracerHome first or edits silently don't apply
- [IIS-hosted profiler: native file logging is silent](entries/iis-native-file-logging-silent.md) — spdlog file sink writes nothing under IIS-Express; use a raw std::wofstream bypass logger
- [Windows shell gotchas](entries/windows-shell-gotchas.md) — `|` in --Filter gets split by the shell; PathTooLongException on broad recursive searches
