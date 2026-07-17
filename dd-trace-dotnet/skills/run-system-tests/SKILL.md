---
name: run-system-tests
description: >-
  Build the Linux .NET tracer package locally and run the system-tests suite against it to verify that
  tracer code changes don't break anything. Use when the user wants to run system-tests / system tests
  for the .NET tracer, validate changes end-to-end with the weblog apps, smoke-test a local build, or
  mentions datadog-dotnet-apm.tar.gz, the system-tests binaries/ folder, weblog, or the DEFAULT scenario.
argument-hint: "[scenario] [--repackage] [--skip-musl] [--weblog poc|uds] [--tests <path>]"
---

# Run system-tests against a local .NET tracer build

## Overview

This skill closes the loop needed to validate that a tracer change doesn't break anything:

1. **Build** the Linux **glibc** package (`datadog-dotnet-apm-<version>.tar.gz`) with Docker.
2. **Stage** it into the `system-tests` repo's `binaries/` folder.
3. **Build** the .NET weblog image and **run** a system-tests scenario against it.

### Repo layout (important)

This skill ships as a **plugin** (its files live in the plugin cache; reference them via
`${CLAUDE_SKILL_DIR}`). It drives two repos that must be **siblings** under a common parent:

```
<root>/dd-trace-dotnet/   <- the tracer repo (built)
<root>/system-tests/      <- the test suite
```

Run Claude from inside `dd-trace-dotnet` (the usual case). The build script resolves the tracer repo
from the current directory (also accepts the git root or a sibling); override with `-DdTraceRoot` /
`$env:DD_TRACE_ROOT`. `system-tests` is expected at `<dd-trace-dotnet>\..\system-tests`.

### Key facts (why it works this way)

- system-tests' .NET weblog containers are **Debian/glibc** (`mcr.microsoft.com/dotnet/aspnet:8.0`).
  `install_ddtrace.sh` only accepts `datadog-dotnet-apm-<version>.tar.gz` (or `.arm64.tar.gz`) — the
  **musl** artifact is not used, and it asserts **exactly one** `datadog-dotnet-apm*.tar.gz` in
  `binaries/`.
- The glibc `.tar.gz` also bundles the musl-x64 binaries, so producing it requires **two Docker
  stages** (Alpine for musl + Debian for glibc/packaging). `Build-LinuxPackage.ps1` handles this.
- **system-tests does not run on native Windows** (bash + Docker + Python 3.12). On Windows, run its
  build/run steps inside **WSL2** (Docker Desktop shares the daemon). The tracer build itself runs
  fine from Windows via Docker.

## Prerequisites

Verify these before starting; if one fails, tell the user what's missing and stop.

- **Docker** running: `docker info` succeeds.
- **`dd-trace-dotnet` and `system-tests`** present as siblings (see layout). The build script finds
  dd-trace-dotnet from the current dir / git root / sibling; override with `-DdTraceRoot` /
  `$env:DD_TRACE_ROOT`. system-tests is expected at `<dd-trace-dotnet>\..\system-tests`.
- **WSL2** (Windows hosts only): `wsl -l -q` lists a distro, and inside it Docker + **Python 3.12** are
  available (`wsl bash -lc "python3.12 --version && docker info"`). Docker requires **WSL integration**
  enabled for the distro (Docker Desktop → Settings → Resources → WSL Integration). The runner venv also
  needs these apt packages (some runner deps build native wheels, e.g. `zstandard`/`Brotli`):
  `sudo apt-get install -y python3.12-venv python3.12-dev build-essential`. Without `python3.12-venv`
  the venv creation fails with `ensurepip is not available`; without `build-essential`/`python3.12-dev`
  the wheel build fails with `x86_64-linux-gnu-gcc ... No such file or directory`. If a previous run
  left a broken `venv/` (created before those packages), delete it: `rm -rf venv`. If
  WSL/Python 3.12/Docker-in-WSL is not set up, print the exact commands (Steps 3-4) for the user to run
  manually in a Linux/WSL shell and stop.

## Arguments

Arguments are available as: `$ARGUMENTS`. Parse them as:

- First non-flag token = **scenario** (default `DEFAULT`).
- `--repackage` → pass `-Repackage` to the build script (only re-tar, no compile).
- `--skip-musl` → pass `-SkipMusl` (rebuild glibc + repackage, reuse existing musl binaries — the fast
  path after a **code** change).
- `--weblog poc|uds` → weblog variant (default `poc`).
- `--tests <path>` → narrow the run to a specific test target for speed.

Choosing the build mode:
- First time / after libdatadog / native profiler changes → **full** (no flag).
- Iterating on tracer **code** → `--skip-musl` (one native build instead of two).
- Nothing changed, just need the tar regenerated → `--repackage`.

## Procedure

Commands assume Claude runs from the `dd-trace-dotnet` repo (cwd). The build script is bundled with this
skill — invoke it via `${CLAUDE_SKILL_DIR}` so it resolves regardless of where the plugin is installed.

### Step 1 — Build the glibc tracer package

```powershell
pwsh -File "$env:CLAUDE_SKILL_DIR/Build-LinuxPackage.ps1"   # add -SkipMusl or -Repackage
```

If `pwsh` (PowerShell 7) is not installed, use Windows PowerShell (`powershell`) with the same
arguments. You may first need to allow local script execution for the session
(`Set-ExecutionPolicy -Scope Process RemoteSigned`).

On a Linux/WSL host use the bash sibling instead:

```bash
bash "$CLAUDE_SKILL_DIR/build-linux-package.sh"          # add --skip-musl or --repackage
```

The script prints the produced package path (last line of stdout), e.g.
`...\dd-trace-dotnet\tracer\bin\artifacts\linux-x64\datadog-dotnet-apm-<version>.tar.gz`. Capture it. If
the build fails complaining about missing musl files, re-run **without** `--skip-musl`.

> This is a heavy build the first time (two native compilations). `--skip-musl` roughly halves it.

### Step 2 — Stage the package into system-tests

The installer requires **exactly one** `datadog-dotnet-apm*.tar.gz` in `binaries/`. Remove any old one,
then copy the freshly built tar (from `dd-trace-dotnet`, a sibling of `system-tests`):

```powershell
$dst = "..\system-tests\binaries"   # system-tests is a sibling of dd-trace-dotnet (cwd)
Remove-Item "$dst\datadog-dotnet-apm*.tar.gz" -ErrorAction SilentlyContinue
Copy-Item <TAR_PATH_FROM_STEP_1> $dst
```

### Step 3 — Build the .NET weblog image

Resolve the system-tests path in WSL form and build. On Windows, shell into WSL. Also create a
throwaway Docker config: WSL's `~/.docker/config.json` usually has `"credsStore": "desktop.exe"`, and
the Python docker SDK used by `run.sh` can't exec that Windows binary (fails with `Exec format error`
when pulling images). Pointing `DOCKER_CONFIG` at an empty config makes pulls anonymous (all images
here are public) without touching the user's real config:

```powershell
$stWin = (Resolve-Path "..\system-tests").Path   # system-tests is a sibling of dd-trace-dotnet (cwd)
$st = wsl wslpath -a "$stWin"
wsl bash -lc "mkdir -p /tmp/ddconfig && printf '{}' > /tmp/ddconfig/config.json && cd '$st' && DOCKER_CONFIG=/tmp/ddconfig ./build.sh dotnet"   # add -w uds for the uds weblog
```

On a Linux/WSL host, just `cd` into system-tests and run `./build.sh dotnet` directly (the
`DOCKER_CONFIG` workaround is only needed when the credential helper is `desktop.exe`).

`./build.sh dotnet` installs the tar from `binaries/` into the weblog image (look for the log line
`Install ddtrace from datadog-dotnet-apm-<version>.tar.gz`) and also builds the Python runner venv.

### Step 4 — Run the scenario

```powershell
wsl bash -lc "cd '$st' && DOCKER_CONFIG=/tmp/ddconfig TEST_LIBRARY=dotnet ./run.sh <SCENARIO>"    # append <test path> if given
```

- Default `<SCENARIO>` = `DEFAULT` (broad smoke: spawns weblog + Postgres + agent, runs most tests).
- To narrow: `TEST_LIBRARY=dotnet ./run.sh DEFAULT tests/<file>.py::<Class>`.

### Step 5 — Report results

Summarize pytest pass/fail. Logs are written under system-tests `logs/` (for `DEFAULT`) or
`logs_<scenario>/`. On failure, point to the relevant log and the failing test names.

## Notes

- Weblog variants for dotnet: `poc` (default), `uds`. There is no `SMOKE` scenario; use `DEFAULT`
  (optionally narrowed with `--tests`) for a quick check.
- If `docker login ghcr.io` errors appear during `build.sh`, the user needs to authenticate to GHCR
  (see system-tests `docs/execute/build.md`). The .NET base images (mcr.microsoft.com) need no auth.
- **`Exec format error: docker-credential-desktop.exe`** during `run.sh` → the WSL `~/.docker/config.json`
  uses the Windows credential helper; use the `DOCKER_CONFIG=/tmp/ddconfig` workaround from Step 3
  (do **not** overwrite the user's `~/.docker/config.json`).
- This skill only orchestrates existing Docker/Nuke/system-tests tooling; it does not modify the build
  or the tracer source.
