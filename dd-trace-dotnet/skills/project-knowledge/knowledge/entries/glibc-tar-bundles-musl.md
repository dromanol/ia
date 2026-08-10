---
name: glibc-tar-bundles-musl
description: The glibc Linux package (datadog-dotnet-apm-<version>.tar.gz) also bundles the musl-x64 binaries, so producing it needs BOTH an Alpine (musl) and a Debian (glibc) Docker build. Sharing the repo between stages contaminates the CMake libdatadog FetchContent subbuild.
type: gotcha
---

`ZipMonitoringHomeLinux` sets `includeMuslArtifacts = !IsAlpine`, so the glibc `.tar.gz` hardlinks files
from the `linux-musl-x64` folder — those musl binaries must already be in the monitoring-home. Producing
the standard glibc tar therefore requires two Docker stages (Alpine builds musl-x64, then Debian builds
glibc + packages), exactly like CI.

Gotcha: both stages bind-mount the same repo, and the CMake FetchContent subbuild `libdatadog-install`
is named libc-agnostically. The Debian stage reuses the Alpine-configured subbuild with the WRONG (musl)
expected hash → `CMake Error ... Hash mismatch, download failed`. Fix: wipe `artifacts/native-obj` and
`artifacts/profiler-build` between the two stages so each libc reconfigures cleanly (the monitoring-home
is a separate dir and keeps the already-published musl binaries for packaging).

Related: [[linux-package-targets]], [[build-native-wrapper]]
