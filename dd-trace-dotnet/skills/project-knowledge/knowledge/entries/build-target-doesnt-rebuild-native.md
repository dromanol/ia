---
name: build-target-doesnt-rebuild-native
description: BuildAspNetIntegrationTests does NOT rebuild native/managed tracer core — use BuildTracerHome first or changes silently don't take effect
type: gotcha
---

`BuildAspNetIntegrationTests` (and similar `Build*IntegrationTests` Nuke targets) only build the test
project and sample apps — they do NOT rebuild `Datadog.Trace.dll` or the native profiler
(`Datadog.Tracer.Native.dll`). If you've edited native (`.cpp`/`.h` under
`tracer/src/Datadog.Tracer.Native`) or core managed (`tracer/src/Datadog.Trace`) code and only run
`BuildAspNetIntegrationTests`, the test run silently uses the STALE dll/native binary — no error, just
confusing "my fix didn't change behavior" results.

Correct rebuild+test sequence after touching native/managed core code:
1. `./tracer/build.cmd BuildTracerHome -Framework net48` (rebuilds native + managed core; verify via
   nonzero `CompileTracerNativeSrcWindows`/`CompileManagedSrc` durations in the build log, not just
   "Succeeded")
2. `./tracer/build.cmd BuildAspNetIntegrationTests -Framework net48` (rebuilds test project + IIS
   sample apps against the just-built home)
3. `./tracer/build.cmd RunWindowsTracerIisIntegrationTests -Framework net48 --Filter "FullyQualifiedName~<Class>[.<Method>]"`

When genuinely unsure whether a change took effect, add a unique, build-specific marker string to a log
line (e.g. a line like `DEBUGMARKER-<date>-<n>`) and grep the output for it — cheaper than re-deriving
timestamps from build logs.

Also: `BuildAspNetIntegrationTests`'s `PublishIisSamples` step has been observed to fail transiently
with `MSB4226: The imported project "...Microsoft.WebApplication.targets" was not found` — this
resolved on an immediate unchanged retry both times it was seen, so retry once before treating it as a
real regression.

See [[iis-native-file-logging-silent]] for a related debugging-infrastructure gotcha in the same test
scenario.
