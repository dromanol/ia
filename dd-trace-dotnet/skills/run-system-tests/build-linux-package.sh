#!/usr/bin/env bash
#
# Builds the Linux glibc tracer package (datadog-dotnet-apm-<version>.tar.gz) using Docker.
#
# The glibc .tar.gz that system-tests consumes also bundles the musl-x64 native binaries
# (ZipMonitoringHomeLinux forces includeMuslArtifacts on non-Alpine builds), so a full build runs
# TWO Docker stages, mirroring CI:
#   1. Alpine stage -> builds linux-musl-x64 native binaries into the shared monitoring-home.
#   2. Debian stage -> builds linux-x64 (glibc) binaries and runs PackageTracerHome, which packages
#                      BOTH arches into the tar + produces .deb / .rpm.
# Both stages bind-mount the repo, so the monitoring-home persists between them. Only the `Clean`
# target wipes the monitoring-home, so we never pass Clean to the Debian stage.
#
# LAYOUT: this skill lives in the `ia` repo. dd-trace-dotnet and system-tests are expected as SIBLINGS
# under the same parent (git root). The tracer repo is resolved as <git root>/dd-trace-dotnet; override
# with the DD_TRACE_ROOT env var.
#
# Usage:
#   ./build-linux-package.sh [--arch x64|arm64] [--skip-musl] [--repackage] [--clean]
#
#   --skip-musl   Skip the Alpine/musl stage; rebuild glibc + repackage reusing existing musl
#                 binaries. Fast path when iterating on tracer code changes.
#   --repackage   Only re-run ZipMonitoringHomeLinux (no compilation), reusing both homes.
#   --clean       Run Clean first (full mode only). Ignored with --skip-musl/--repackage.
#
# The last line of stdout is the path to the produced glibc tar.gz, for programmatic capture.

set -euo pipefail

ARCH="x64"
SKIP_MUSL=0
REPACKAGE=0
CLEAN=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        --arch) ARCH="$2"; shift 2 ;;
        --skip-musl) SKIP_MUSL=1; shift ;;
        --repackage) REPACKAGE=1; shift ;;
        --clean) CLEAN=1; shift ;;
        *) echo "Unknown argument: $1" >&2; exit 2 ;;
    esac
done

if [[ "$ARCH" != "x64" && "$ARCH" != "arm64" ]]; then
    echo "Invalid --arch '$ARCH' (expected x64 or arm64)" >&2
    exit 2
fi
if [[ "$REPACKAGE" -eq 1 && "$SKIP_MUSL" -eq 1 ]]; then
    echo "--repackage and --skip-musl are mutually exclusive." >&2
    exit 2
fi
if [[ "$CLEAN" -eq 1 && ( "$SKIP_MUSL" -eq 1 || "$REPACKAGE" -eq 1 ) ]]; then
    echo "WARNING: --clean ignored (would wipe musl binaries needed for packaging)." >&2
    CLEAN=0
fi

DOTNETSDK_VERSION="10.0.100"
# Resolve the dd-trace-dotnet repo from the CURRENT directory, not the script location: when installed
# as a plugin the scripts live in a managed cache, unrelated to the repos. Claude normally runs inside
# the tracer repo (or its git root). Override with DD_TRACE_ROOT.
ROOT_DIR=""
if [[ -n "${DD_TRACE_ROOT:-}" && -d "${DD_TRACE_ROOT}/tracer/build/_build" ]]; then
    ROOT_DIR="$DD_TRACE_ROOT"
else
    # 1. Walk up from cwd: handles cwd == the tracer repo OR any subdirectory of it.
    d="$PWD"
    while [[ -n "$d" ]]; do
        if [[ -d "$d/tracer/build/_build" ]]; then ROOT_DIR="$d"; break; fi
        parent="$(dirname -- "$d")"; [[ "$parent" == "$d" ]] && break; d="$parent"
    done
    # 2. Else look as a child of cwd (git root) or a sibling of cwd (another repo).
    if [[ -z "$ROOT_DIR" ]]; then
        for cand in "$PWD/dd-trace-dotnet" "$(dirname -- "$PWD")/dd-trace-dotnet"; do
            if [[ -d "$cand/tracer/build/_build" ]]; then ROOT_DIR="$cand"; break; fi
        done
    fi
fi
if [[ -z "$ROOT_DIR" ]]; then
    echo "Could not locate the dd-trace-dotnet repo. Run from within it (or its git root), or set DD_TRACE_ROOT." >&2
    exit 1
fi
ROOT_DIR="$(cd -- "$ROOT_DIR" &> /dev/null && pwd)"
BUILD_DIR="$ROOT_DIR/tracer/build/_build"
OUTPUT_DIR="$ROOT_DIR/tracer/bin/artifacts/linux-$ARCH"

ALPINE_IMAGE="dd-trace-dotnet/alpine-base"
DEBIAN_IMAGE="dd-trace-dotnet/debian-base"

build_image() {
    local image="$1" dockerfile="$2"
    echo "==> Building Docker image '$image' from $dockerfile (target: builder)"
    docker build \
        --build-arg "DOTNETSDK_VERSION=$DOTNETSDK_VERSION" \
        --target builder \
        --tag "$image" \
        --file "$BUILD_DIR/docker/$dockerfile" \
        "$BUILD_DIR"
}

clear_native_intermediates() {
    # The Alpine (musl) and Debian (glibc) stages share the repo via bind-mount. CMake FetchContent
    # subbuilds (e.g. libdatadog-install) are named libc-agnostically, so a musl-configured subbuild
    # gets reused by the glibc stage with the WRONG expected hash -> "Hash mismatch, download failed".
    # Wipe the native *intermediate* build dirs between stages so each libc reconfigures cleanly.
    # monitoring-home is separate and keeps the already-published musl binaries for packaging.
    local d
    for d in "artifacts/native-obj" "artifacts/profiler-build"; do
        if [[ -d "$ROOT_DIR/$d" ]]; then
            echo "==> Cleaning native intermediates: $ROOT_DIR/$d"
            rm -rf "$ROOT_DIR/${d:?}"
        fi
    done
}

nuke_in_docker() {
    local image="$1"; shift
    echo "==> Running in ${image}: $*"
    docker run --rm \
        --mount "type=bind,source=$ROOT_DIR,target=/project" \
        --env NugetPackageDirectory=/project/packages \
        --env artifacts=/project/tracer/bin/artifacts \
        --env DD_INSTRUMENTATION_TELEMETRY_ENABLED=0 \
        --env NUKE_TELEMETRY_OPTOUT=1 \
        "$image" \
        dotnet /build/bin/Debug/_build.dll "$@"
}

# --- Preflight -----------------------------------------------------------------------------------
if ! docker info > /dev/null 2>&1; then
    echo "Docker does not appear to be running. Start Docker and retry." >&2
    exit 1
fi

echo "Using dd-trace-dotnet at: $ROOT_DIR"

# BuildNativeWrapper (Linux-only) produces + publishes Datadog.Linux.ApiWrapper.x64.so (the LD_PRELOAD
# continuous-profiler wrapper) into the monitoring-home. Packaging hardlinks it, so it must be built in
# BOTH stages (the glibc tar also bundles the musl wrapper). CI builds it alongside BuildNativeLoader.
BUILD_BINARIES=(BuildTracerHome BuildProfilerHome BuildNativeLoader BuildNativeWrapper)

# --- Stage 1: musl binaries (Alpine) -------------------------------------------------------------
if [[ "$SKIP_MUSL" -eq 0 && "$REPACKAGE" -eq 0 ]]; then
    clear_native_intermediates  # start from a clean native configure
    build_image "$ALPINE_IMAGE" "alpine.dockerfile"
    musl_targets=()
    [[ "$CLEAN" -eq 1 ]] && musl_targets+=(Clean)
    musl_targets+=("${BUILD_BINARIES[@]}")
    nuke_in_docker "$ALPINE_IMAGE" "${musl_targets[@]}"

    # Drop the musl-configured native intermediates so the glibc stage reconfigures with the gnu hash.
    clear_native_intermediates
fi

# --- Stage 2: glibc build + package (Debian) -----------------------------------------------------
build_image "$DEBIAN_IMAGE" "debian.dockerfile"
if [[ "$REPACKAGE" -eq 1 ]]; then
    debian_targets=(ZipMonitoringHomeLinux)
else
    debian_targets=("${BUILD_BINARIES[@]}" PackageTracerHome)
fi
nuke_in_docker "$DEBIAN_IMAGE" "${debian_targets[@]}"

# --- Report --------------------------------------------------------------------------------------
echo ""
echo "==> Artifacts:"
ls -1 "$OUTPUT_DIR"/datadog-dotnet-apm* 2>/dev/null || true

TAR="$(ls -1 "$OUTPUT_DIR"/datadog-dotnet-apm-*.tar.gz 2>/dev/null | grep -v -- '-musl' | head -n 1 || true)"
if [[ -z "$TAR" ]]; then
    echo "No glibc tar.gz found in $OUTPUT_DIR. If packaging complained about missing musl files, re-run a full build (without --skip-musl)." >&2
    exit 1
fi

echo ""
echo "glibc package: $TAR"
# Last line = tar path, for programmatic capture.
echo "$TAR"
