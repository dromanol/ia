#requires -Version 5.1
<#
.SYNOPSIS
    Builds the Linux glibc tracer package (datadog-dotnet-apm-<version>.tar.gz) using Docker.

.DESCRIPTION
    Produces the standard glibc Linux package that system-tests consumes. Because the glibc .tar.gz
    also bundles the musl-x64 native binaries (ZipMonitoringHomeLinux forces includeMuslArtifacts on
    non-Alpine builds), the full build runs TWO Docker stages, mirroring CI:

      1. Alpine stage  -> builds the linux-musl-x64 native binaries into the shared monitoring-home.
      2. Debian stage  -> builds the linux-x64 (glibc) binaries and runs PackageTracerHome, which
                          packages BOTH arches into the tar + produces .deb / .rpm.

    Both stages bind-mount the repo, so the monitoring-home persists between them. Only the `Clean`
    target wipes the monitoring-home, so we never pass Clean to the Debian stage.

    LAYOUT: this skill is maintained in the `ia` repo and copied into each clone's
    `.claude\skills\run-system-tests\` by the `common` bootstrapper at session start. Nothing here is
    resolved relative to the script's own location; the `dd-trace-dotnet` and `system-tests` repos are
    expected as SIBLINGS under a common parent, e.g.
        <root>\dd-trace-dotnet\   <- run Claude from here (cwd)
        <root>\system-tests\
    The tracer repo is resolved from the current directory (see below); override with -DdTraceRoot.

.PARAMETER Arch
    Target architecture: x64 (default) or arm64. Determines the output folder linux-<arch>.

.PARAMETER DdTraceRoot
    Path to the dd-trace-dotnet repo. Defaults to resolving it from the current directory (walk up to
    the repo root, else a child/sibling of cwd); override with -DdTraceRoot / $env:DD_TRACE_ROOT.

.PARAMETER SkipMusl
    Skip the Alpine/musl stage and only rebuild + repackage in Debian, reusing the musl binaries from
    a previous full build. This is the fast path when iterating on tracer *code* changes.

.PARAMETER Repackage
    Only re-run ZipMonitoringHomeLinux in Debian (no compilation), reusing both already-built homes.
    Use when nothing changed and you just need the tar/deb/rpm regenerated.

.PARAMETER Clean
    Run the `Clean` target first (full mode only). Wipes the monitoring-home before rebuilding.
    Ignored with a warning when -SkipMusl or -Repackage is set (it would delete the musl binaries).

.EXAMPLE
    ./Build-LinuxPackage.ps1
    Full build (musl + glibc + package).

.EXAMPLE
    ./Build-LinuxPackage.ps1 -SkipMusl
    Rebuild glibc + repackage after a tracer code change (reuses existing musl binaries).
#>
[CmdletBinding()]
param(
    [ValidateSet('x64', 'arm64')]
    [string]$Arch = 'x64',

    [string]$DdTraceRoot,

    [switch]$SkipMusl,

    [switch]$Repackage,

    [switch]$Clean
)

$ErrorActionPreference = 'Stop'

$DOTNETSDK_VERSION = '10.0.100'

# Resolve the dd-trace-dotnet repo from the CURRENT directory, not the script location: this file is a
# managed copy under <clone>\.claude\skills\, so $PSScriptRoot says nothing about which repos to build.
# Claude normally runs inside the tracer repo (or its git root). Override with -DdTraceRoot / $env:DD_TRACE_ROOT.
function Test-DdTraceRoot([string]$p) { $p -and (Test-Path (Join-Path $p 'tracer/build/_build')) }
if (-not $DdTraceRoot) { $DdTraceRoot = $env:DD_TRACE_ROOT }
if (-not $DdTraceRoot) {
    $cwd = (Get-Location).Path
    # 1. Walk up from cwd: handles cwd == the tracer repo OR any subdirectory of it (e.g. dd-trace-dotnet\tracer).
    $dir = Get-Item -LiteralPath $cwd
    while ($dir -and -not (Test-DdTraceRoot $dir.FullName)) { $dir = $dir.Parent }
    if ($dir) { $DdTraceRoot = $dir.FullName }
    # 2. Else look for it as a child of cwd (cwd == git root) or a sibling of cwd (cwd == another repo).
    if (-not $DdTraceRoot) {
        $candidates = @(
            (Join-Path $cwd 'dd-trace-dotnet'),                       # cwd is the git root (parent of the repos)
            (Join-Path (Split-Path $cwd -Parent) 'dd-trace-dotnet')  # cwd is a sibling repo (e.g. system-tests)
        )
        $DdTraceRoot = $candidates | Where-Object { Test-DdTraceRoot $_ } | Select-Object -First 1
    }
}
if (-not (Test-DdTraceRoot $DdTraceRoot)) {
    throw "Could not locate the dd-trace-dotnet repo. Run from within it (or its git root), or pass -DdTraceRoot <path> / set `$env:DD_TRACE_ROOT."
}
$ROOT_DIR = (Resolve-Path $DdTraceRoot).Path
$BUILD_DIR = Join-Path $ROOT_DIR 'tracer/build/_build'
$ArchId = $Arch  # UnixArchitectureIdentifier: x64 / arm64
$OutputDir = Join-Path $ROOT_DIR "tracer/bin/artifacts/linux-$ArchId"

$AlpineImage = 'dd-trace-dotnet/alpine-base'
$DebianImage = 'dd-trace-dotnet/debian-base'

function Invoke-Checked {
    param([string]$What)
    if ($LASTEXITCODE -ne 0) {
        throw "$What failed with exit code $LASTEXITCODE"
    }
}

function Build-Image {
    param([string]$Image, [string]$Dockerfile)

    # docker/BuildKit writes progress to stderr; under EAP='Stop' (PS 5.1) that surfaces as a
    # terminating NativeCommandError. Relax locally (function-scoped) and gate on $LASTEXITCODE.
    $ErrorActionPreference = 'Continue'
    Write-Host "==> Building Docker image '$Image' from $Dockerfile (target: builder)" -ForegroundColor Cyan
    & docker build `
        --build-arg "DOTNETSDK_VERSION=$DOTNETSDK_VERSION" `
        --target builder `
        --tag $Image `
        --file (Join-Path $BUILD_DIR "docker/$Dockerfile") `
        $BUILD_DIR
    Invoke-Checked "docker build ($Image)"
}

function Clear-NativeIntermediates {
    # The Alpine (musl) and Debian (glibc) stages share the repo via bind-mount. CMake FetchContent
    # subbuilds (e.g. libdatadog-install) are named libc-agnostically, so a musl-configured subbuild
    # gets reused by the glibc stage with the WRONG expected hash -> "Hash mismatch, download failed".
    # Wipe the native *intermediate* build dirs between stages so each libc reconfigures cleanly.
    # monitoring-home is a separate dir and keeps the already-published musl binaries, so packaging
    # can still bundle them.
    foreach ($d in @('artifacts/native-obj', 'artifacts/profiler-build')) {
        $p = Join-Path $ROOT_DIR $d
        if (Test-Path $p) {
            Write-Host "==> Cleaning native intermediates: $p" -ForegroundColor DarkGray
            Remove-Item -Recurse -Force $p
        }
    }
}

function Invoke-NukeInDocker {
    param([string]$Image, [string[]]$Targets)

    # See Build-Image: relax EAP locally so native stderr from docker/Nuke isn't treated as terminating.
    $ErrorActionPreference = 'Continue'
    Write-Host "==> Running in ${Image}: $($Targets -join ' ')" -ForegroundColor Cyan
    & docker run --rm `
        --mount "type=bind,source=$ROOT_DIR,target=/project" `
        --env NugetPackageDirectory=/project/packages `
        --env artifacts=/project/tracer/bin/artifacts `
        --env DD_INSTRUMENTATION_TELEMETRY_ENABLED=0 `
        --env NUKE_TELEMETRY_OPTOUT=1 `
        $Image `
        dotnet /build/bin/Debug/_build.dll @Targets
    Invoke-Checked "docker run (${Image}: $($Targets -join ' '))"
}

# --- Preflight ------------------------------------------------------------------------------------
# Probe Docker with ErrorActionPreference relaxed: in PS 5.1, merging a native command's stderr while
# ErrorActionPreference='Stop' would raise a NativeCommandError instead of letting us check $LASTEXITCODE.
$prevEap = $ErrorActionPreference
$ErrorActionPreference = 'Continue'
& docker info 2>&1 | Out-Null
$dockerRunning = ($LASTEXITCODE -eq 0)
$ErrorActionPreference = $prevEap
if (-not $dockerRunning) {
    throw 'Docker does not appear to be running. Start Docker Desktop (with the Linux engine) and retry.'
}

if ($Repackage -and $SkipMusl) {
    throw '-Repackage and -SkipMusl are mutually exclusive.'
}
if ($Clean -and ($SkipMusl -or $Repackage)) {
    Write-Warning '-Clean ignored: it would wipe the musl binaries needed for packaging. Only valid in full mode.'
    $Clean = $false
}

Write-Host "Using dd-trace-dotnet at: $ROOT_DIR" -ForegroundColor DarkGray

# BuildNativeWrapper (Linux-only) produces + publishes Datadog.Linux.ApiWrapper.x64.so (the LD_PRELOAD
# continuous-profiler wrapper) into the monitoring-home. Packaging hardlinks it, so it must be built in
# BOTH stages (the glibc tar also bundles the musl wrapper). CI builds it alongside BuildNativeLoader.
$buildBinaries = @('BuildTracerHome', 'BuildProfilerHome', 'BuildNativeLoader', 'BuildNativeWrapper')

# --- Stage 1: musl binaries (Alpine) --------------------------------------------------------------
if (-not $SkipMusl -and -not $Repackage) {
    Clear-NativeIntermediates  # start from a clean native configure (defends against prior-run state)
    Build-Image -Image $AlpineImage -Dockerfile 'alpine.dockerfile'
    $muslTargets = @()
    if ($Clean) { $muslTargets += 'Clean' }
    $muslTargets += $buildBinaries
    Invoke-NukeInDocker -Image $AlpineImage -Targets $muslTargets

    # Drop the musl-configured native intermediates so the glibc stage reconfigures with the gnu hash.
    Clear-NativeIntermediates
}

# --- Stage 2: glibc build + package (Debian) ------------------------------------------------------
Build-Image -Image $DebianImage -Dockerfile 'debian.dockerfile'
if ($Repackage) {
    $debianTargets = @('ZipMonitoringHomeLinux')
} else {
    $debianTargets = $buildBinaries + @('PackageTracerHome')
}
Invoke-NukeInDocker -Image $DebianImage -Targets $debianTargets

# --- Report ---------------------------------------------------------------------------------------
Write-Host ''
Write-Host '==> Artifacts:' -ForegroundColor Green
$tar = $null
if (Test-Path $OutputDir) {
    Get-ChildItem -Path $OutputDir -Filter 'datadog-dotnet-apm*' | ForEach-Object {
        Write-Host "    $($_.FullName)"
    }
    $tar = Get-ChildItem -Path $OutputDir -Filter 'datadog-dotnet-apm-*.tar.gz' |
        Where-Object { $_.Name -notmatch '-musl' } |
        Select-Object -First 1
}

if ($null -eq $tar) {
    throw "No glibc tar.gz found in $OutputDir. If packaging complained about missing musl files, re-run a full build (without -SkipMusl)."
}

Write-Host ''
Write-Host "glibc package: $($tar.FullName)" -ForegroundColor Green
# Emit the tar path on the last line so callers can capture it programmatically.
$tar.FullName
