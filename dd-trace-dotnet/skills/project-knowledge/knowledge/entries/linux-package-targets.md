---
name: linux-package-targets
description: Where the Linux tracer package is produced — PackageTracerHome → ZipMonitoringHome → ZipMonitoringHomeLinux (Build.Steps.cs). Output lands under tracer/bin/artifacts/linux-<arch>/. Must run inside a Linux Docker container.
type: reference
---

- Top-level target: `PackageTracerHome` (tracer/build/_build/Build.cs) depends on `ZipMonitoringHome`
  → `ZipMonitoringHomeLinux` (Build.Steps.cs; `OnlyWhenStatic(IsLinux)`, `Requires(Version)`).
- Linux package types: non-Alpine → **deb, rpm, tar** (deb/rpm via `nfpm`, tar via `tar`);
  Alpine → **tar only**, named `datadog-dotnet-apm-<version>-musl.tar.gz`.
- Output dir: `tracer/bin/artifacts/linux-<arch>/datadog-dotnet-apm-<version>.tar.gz` (+ `.deb`, `.rpm`).
- Must run inside a Linux Docker container (needs nfpm/tar + clang/cmake toolchain). Helper scripts:
  `tracer/build_in_docker.sh` / `tracer/build_in_docker.ps1` (note: those default to Alpine → musl only).

Related: [[glibc-tar-bundles-musl]], [[build-native-wrapper]]
