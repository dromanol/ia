---
name: appsec-unit-tests-need-native-waf-copy
description: Security unit tests NRE at Waf.Create when the native ddwaf isn't in the test bin — fix is the CopyNativeFilesForAppSecUnitTests Nuke target, with --build-configuration matching your bin folder.
type: gotcha
---

## Symptom

Most tests in `Datadog.Trace.Security.Unit.Tests` fail with a bare
`System.NullReferenceException` at `Waf.Create` (`Waf.cs`), typically after running the tests via
`dotnet test` / the IDE rather than through Nuke. Only the tests that never touch the WAF pass.

The NRE comes from `WafLibraryRequiredTest`'s **static constructor**
(`tracer/test/Datadog.Trace.Security.Unit.Tests/Utils/WafLibraryRequiredTest.cs`): it calls
`WafLibraryInvoker.Initialize(...)`, that fails to load the native library, and the resulting
`WafLibraryInvoker` is null — nothing reports the load failure to the test output, so the NRE is the
only visible symptom.

## Fix

```powershell
.\tracer\build.cmd CopyNativeFilesForAppSecUnitTests --build-configuration Debug
```

**Pass `--build-configuration` explicitly.** Nuke defaults to `Release`, and the target copies into
`artifacts/bin/Datadog.Trace.Security.Unit.Tests/<config>_<tfm>/`, so omitting it populates the
`release_*` folders and your `debug_*` test run keeps failing identically.

The target (`tracer/build/_build/Build.Steps.cs`) copies `artifacts/monitoring-home/<arch>` into each
TFM's test bin folder, plus every version in `OlderLibDdwafVersions` as `ddwaf-<version>.dll` (the WAF
version-compatibility tests need those). So `artifacts/monitoring-home` must already be populated —
run `BuildTracerHome` / `DownloadLibDdwaf` first if it isn't; the target is only `.After(DownloadLibDdwaf)`,
not `.DependsOn`, so it won't fetch anything for you.

On Windows it copies into the **arch sub-folder** (`win-x64`, `win-x86`); on Linux/macOS into the bin
**root**, because loading the WAF there needs the native tracer side by side as a PInvoke proxy.

## Why CI never hits this, and why the env var is not the fix

`CompileManagedUnitTests` has `.DependsOn(CopyNativeFilesForAppSecUnitTests)`, so any Nuke-driven build
is fine. The target is `.Unlisted()`, so it doesn't show up in `build.cmd --help` — you have to know it
exists.

Setting `DD_DOTNET_TRACER_HOME=<repo>/artifacts/monitoring-home` also makes the tests pass, but it's a
workaround that hides a broken bin folder. `LibraryLocationHelper.AddHomeFolders` always appends
`AppDomain.CurrentDomain.BaseDirectory` and `<BaseDirectory>/<runtimeId>` to the probe list regardless
of the home setting — which is exactly why copying into the test bin is sufficient and no env var is
needed. Verified: with `DD_DOTNET_TRACER_HOME` unset, `AppSecContextTests` goes 12/12 after running the
target.

Same family of trap as [[build-target-doesnt-rebuild-native]]: a Nuke target quietly supplies native
files that a plain `dotnet build`/`dotnet test` never provides.
