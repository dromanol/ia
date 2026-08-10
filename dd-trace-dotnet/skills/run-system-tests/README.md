# run-system-tests

Build the Linux **.NET tracer** package locally with Docker, deploy it into the
[`system-tests`](https://github.com/DataDog/system-tests) repo, and run a scenario against it — to
verify that tracer changes don't break anything end-to-end.

> This skill is maintained in the **`ia`** repo at `dd-trace-dotnet/skills/run-system-tests/`, and the
> `common` plugin's SessionStart bootstrapper copies it into `dd-trace-dotnet/.claude/skills/` so it is
> invocable as `/run-system-tests` from inside the tracer repo. Edit it here in `ia`, never in the copy
> (the copy is overwritten every session). `SKILL.md` is the model-facing procedure; this README is the
> human-facing guide.

## Repo layout (required)

The skill drives two **sibling** repos under the same parent (git root):

```
<root>/ia/dd-trace-dotnet/skills/run-system-tests/   <- this skill (source of truth)
<root>/dd-trace-dotnet/                              <- the tracer repo (built)
<root>/system-tests/                                 <- the test suite
```

The build script resolves `dd-trace-dotnet` as `<root>/dd-trace-dotnet` automatically. Override with
`-DdTraceRoot <path>` (PowerShell) or `DD_TRACE_ROOT=<path>` (bash) if your layout differs.

## What it does

1. Builds the **glibc** `datadog-dotnet-apm-<version>.tar.gz` with Docker (two stages: Alpine for the
   bundled musl-x64 binaries + Debian for glibc + packaging).
2. Stages it into `<root>/system-tests/binaries/` (exactly one `datadog-dotnet-apm*.tar.gz`).
3. `./build.sh dotnet` — builds the .NET weblog image with our tracer.
4. `TEST_LIBRARY=dotnet ./run.sh DEFAULT` — runs the scenario.

Why glibc (not musl): the system-tests .NET weblog containers are Debian/glibc; `install_ddtrace.sh`
only accepts the plain (or `.arm64`) tar, never `-musl`. The glibc tar also bundles the musl-x64
binaries, which is why building it needs both Docker stages.

## Prerequisites (one-time, Windows host)

system-tests does **not** run on native Windows — its `build.sh`/`run.sh` run inside **WSL2**. The
tracer build itself runs from Windows via Docker.

- **Docker Desktop** running, with **WSL integration enabled** for the Ubuntu distro
  (Settings → Resources → WSL Integration). Verify: `wsl bash -lc "docker version"`.
- **Ubuntu WSL2** with Python 3.12 and the packages the runner venv needs (some deps build native
  wheels: `zstandard`, `Brotli`):
  ```bash
  sudo apt-get update && sudo apt-get install -y python3.12-venv python3.12-dev build-essential
  ```
  If a previous run left a broken `venv/` (created before those packages), delete it: `rm -rf venv`.
- **`dd-trace-dotnet` and `system-tests` cloned as siblings** of the `ia` repo (see layout).

## Build modes & measured timings (reference machine)

| Mode | What it does | ~Time (warm) |
|------|--------------|--------------|
| full (default) | Alpine musl (~17m) + Debian glibc + package (~25m) | **~42 min** |
| `-SkipMusl` | reuse musl home, rebuild glibc + package (one native compile) | **~25 min** |
| `-Repackage` | only `ZipMonitoringHomeLinux`, no compile | **~1.5-2 min** |
| managed-only\* | only `BuildManagedTracerHome` + package (no native) | **~6-7 min** |

`+ system-tests`: `build.sh dotnet` ~1-3 min warm (first time longer: pulls .NET base images + builds
runner venv), `run.sh DEFAULT` ~2 min. First-ever cold run (builds the Debian image incl. clang) can
reach ~60-75 min.

\* managed-only is the fast path when you only changed C# (managed is arch/libc-independent). Not yet a
script flag — see "Ideas" below.

## Run it

All commands assume the current directory is `<root>` (parent of `ia`, `dd-trace-dotnet`,
`system-tests`).

### Build the tracer package

```powershell
# PowerShell 7:
pwsh -File ia/dd-trace-dotnet/skills/run-system-tests/Build-LinuxPackage.ps1   # add -SkipMusl / -Repackage
# or Windows PowerShell:
powershell -File ia/dd-trace-dotnet/skills/run-system-tests/Build-LinuxPackage.ps1
```
Linux/WSL host: `bash ia/dd-trace-dotnet/skills/run-system-tests/build-linux-package.sh` (flags
`--skip-musl` / `--repackage`). The script prints the produced `.tar.gz` path as its last stdout line.

Equivalently, from inside `dd-trace-dotnet` the copied skill works too:
`pwsh -File .claude/skills/run-system-tests/Build-LinuxPackage.ps1` — which is what Claude invokes via
`${CLAUDE_SKILL_DIR}`. Either path runs the same script; the tracer repo is resolved from the current
directory, not from the script's location.

### Stage + build weblog + run (WSL)

```powershell
$st = wsl wslpath -a ((Resolve-Path "system-tests").Path)
$v  = (Get-Item .\dd-trace-dotnet\tracer\bin\artifacts\linux-x64\datadog-dotnet-apm-*.tar.gz | ? { $_.Name -notmatch '-musl' }).Name
$dd = wsl wslpath -a ((Resolve-Path "dd-trace-dotnet").Path)
wsl bash -lc "set -e; cd '$st'; rm -f binaries/datadog-dotnet-apm*.tar.gz; cp '$dd'/tracer/bin/artifacts/linux-x64/$v binaries/; mkdir -p /tmp/ddconfig; printf '{}' > /tmp/ddconfig/config.json; DOCKER_CONFIG=/tmp/ddconfig ./build.sh dotnet && DOCKER_CONFIG=/tmp/ddconfig TEST_LIBRARY=dotnet ./run.sh DEFAULT"
```

Default weblog is `poc` (alt `uds` via `-w uds`). Narrow the run: append `tests/<file>.py::<Class>` to
`run.sh DEFAULT`. Logs land in `system-tests/logs/`.

## Gotchas discovered while validating this

- **`DOCKER_CONFIG` workaround (required on Windows/WSL):** WSL's `~/.docker/config.json` has
  `"credsStore": "desktop.exe"`; the Python docker SDK in `run.sh` can't exec that Windows binary
  (`Exec format error`) and image pulls fail. Point `DOCKER_CONFIG` at a throwaway `{}` config (public
  images pull anonymously). **Do not** overwrite the user's real `~/.docker/config.json`.
- **Two-stage build shares the tracer repo via bind-mount**, so the CMake FetchContent subbuild for
  `libdatadog` (libc-agnostic name) leaks the wrong-libc hash between stages → "Hash mismatch".
  The scripts wipe `artifacts/native-obj` + `artifacts/profiler-build` between stages to avoid it.
- **`BuildNativeWrapper`** must be in the target list (both stages): it produces
  `Datadog.Linux.ApiWrapper.x64.so`, which packaging hardlinks. Missing it → `ln: No such file`.
- **PowerShell 5.1 + `docker`/`nuke` on stderr:** BuildKit/Nuke write progress to stderr; under
  `$ErrorActionPreference='Stop'` that surfaces as a terminating `NativeCommandError`. The script
  relaxes EAP locally in the docker-invoking functions.

## Verifying the weblog really uses your local tracer

Compare the native loader size in the image vs your build:
```bash
docker run --rm --entrypoint sh system_tests/weblog -c "stat -c %s /opt/datadog/linux-x64/Datadog.Trace.ClrProfiler.Native.so"
stat -c %s <root>/dd-trace-dotnet/artifacts/monitoring-home/linux-x64/Datadog.Trace.ClrProfiler.Native.so
```

## Ideas / not-yet-done

- Add a **`-ManagedOnly`** mode (`BuildManagedTracerHome` + `PackageTracerHome`, no native, no Alpine
  stage) for ~6-7 min iterations when only C# changed.
