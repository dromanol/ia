---
name: build-native-wrapper
description: The Datadog.Linux.ApiWrapper.x64.so (LD_PRELOAD continuous-profiler wrapper) is produced by the BuildNativeWrapper Nuke target, not BuildTracerHome. Linux packaging hardlinks it, so if it's missing the tar/deb/rpm build fails with "ln: No such file".
type: gotcha
---

Building a Linux monitoring-home with `BuildTracerHome BuildProfilerHome BuildNativeLoader` alone omits
`Datadog.Linux.ApiWrapper.x64.so`. `PrepareMonitoringHomeLinuxForPackaging` (tracer/build/_build/Build.Steps.cs)
hardlinks that file into the package layout, so packaging fails with:
`/bin/ln: failed to access '.../Datadog.Linux.ApiWrapper.x64.so': No such file or directory`.

Fix: include the **`BuildNativeWrapper`** target (Linux-only; = CompileNativeWrapper + TestNativeWrapper +
PublishNativeWrapper). CI builds it alongside `BuildNativeLoader`. Full sequence for a complete Linux
home: `BuildTracerHome BuildProfilerHome BuildNativeLoader BuildNativeWrapper` (then `PackageTracerHome`).
It must be built in BOTH libc stages because the glibc tar also bundles the musl wrapper.

Related: [[linux-package-targets]], [[glibc-tar-bundles-musl]]
