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
- [PR description + labels](entries/pr-description-template.md) — follow `.github/pull_request_template.md` schema, keep it short, add `area:asm` for AppSec
- [BuildAspNetIntegrationTests doesn't rebuild native/managed core](entries/build-target-doesnt-rebuild-native.md) — must run BuildTracerHome first or edits silently don't apply
- [IIS-hosted profiler: native file logging is silent](entries/iis-native-file-logging-silent.md) — spdlog file sink writes nothing under IIS-Express; use a raw std::wofstream bypass logger
- [Windows shell gotchas](entries/windows-shell-gotchas.md) — `|` in --Filter gets split by the shell; PathTooLongException on broad recursive searches
- [Benchmark bot's chronic net472 regressions](entries/benchmark-bot-chronic-net472-regressions.md) — DbCommand/HttpClient net472 throughput flagged 🟥 on nearly every PR; not your change
- [Security unit tests need the native WAF copied in](entries/appsec-unit-tests-need-native-waf-copy.md) — NRE at `Waf.Create` → run `CopyNativeFilesForAppSecUnitTests --build-configuration Debug`
- [WAF additive context lifetime](entries/appsec-waf-context-lifetime.md) — who owns it, why an ambient HttpContext gates every WAF run, and why reporting is web-root only
- [tracer/src TFMs stop at net6.0](entries/tracer-src-tfms.md) — `dotnet build -f net8.0` fails NETSDK1005; net8.0 tests run the net6.0 assembly
- [Tracer setup in unit tests](entries/tracer-unit-test-tracer-setup.md) — `TracerHelper.Create(new())`; the testing-only ctor reads no env vars
- [Branch naming convention](entries/branch-naming-convention.md) — `dani/area/nombre`, area = aap, iast, apm, ...
