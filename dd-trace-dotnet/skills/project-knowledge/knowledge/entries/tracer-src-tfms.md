---
name: tracer-src-tfms
description: Everything under tracer/src targets net461/netstandard2.0/netcoreapp3.1/net6.0 only — `dotnet build -f net8.0` fails NETSDK1005, and net8.0 test projects run against the net6.0 assembly.
type: gotcha
---

`tracer/src/Directory.Build.props:5` sets the TFM list for **every** project under `tracer/src`:

```xml
<TargetFrameworks>net461;netstandard2.0;netcoreapp3.1;net6.0</TargetFrameworks>
```

There is no `net8.0`/`net9.0` in there, and individual csprojs (`Datadog.Trace.csproj` included) don't
override it — they only branch *on* `$(TargetFramework)`.

## Consequences

Narrowing a build to the TFM you are testing on fails:

```
dotnet build tracer/src/Datadog.Trace/Datadog.Trace.csproj -f net8.0
error NETSDK1005: Assets file 'project.assets.json' doesn't have a target for 'net8.0'.
```

Build without `-f` (all four TFMs, still fast enough) or pass `-f net6.0`.

The **test** projects do target net8.0, and they load the `net6.0` build of the tracer — visible in the
build log of any test run:

```
Datadog.Trace -> artifacts\bin\Datadog.Trace\debug_net6.0\Datadog.Trace.dll
Datadog.Trace.Security.Unit.Tests -> artifacts\bin\Datadog.Trace.Security.Unit.Tests\debug_net8.0\...
```

So "did my source change get picked up?" is answered by the `debug_net6.0` output, not a `debug_net8.0`
one. Same trap family as [[build-target-doesnt-rebuild-native]].
