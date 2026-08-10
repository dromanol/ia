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

Build the Linux **glibc** package → stage it into `system-tests/binaries/` → build the .NET weblog image
and run a scenario. This skill only orchestrates existing Docker/Nuke/system-tests tooling.

## Layout

Two repos must be **siblings**; run Claude from `dd-trace-dotnet` (the usual case):

```
<root>/dd-trace-dotnet/   <- the tracer repo (built)
<root>/system-tests/      <- the test suite
```

The build script resolves the tracer repo from the current directory (also accepts the git root or a
sibling); override with `-DdTraceRoot` / `$env:DD_TRACE_ROOT`. `system-tests` is expected at
`<dd-trace-dotnet>\..\system-tests`. This skill is maintained in the `ia` repo and copied into the clone
by the `common` bootstrapper — always invoke its bundled scripts via `${CLAUDE_SKILL_DIR}`.

## Why it works this way

- The .NET weblog containers are **Debian/glibc** (`mcr.microsoft.com/dotnet/aspnet:8.0`).
  `install_ddtrace.sh` only accepts `datadog-dotnet-apm-<version>.tar.gz` (or `.arm64.tar.gz`) — the
  **musl** artifact is unused — and asserts **exactly one** `datadog-dotnet-apm*.tar.gz` in `binaries/`.
- That glibc tar still bundles the musl-x64 binaries, so building it needs **two Docker stages** (Alpine
  for musl + Debian for glibc/packaging). `Build-LinuxPackage.ps1` handles this.
- **system-tests does not run on native Windows** (needs bash + Docker + Python 3.12) — run its steps in
  **WSL2** (Docker Desktop shares the daemon). The tracer build itself runs fine from Windows via Docker.

## Prerequisites

If one fails, tell the user what's missing and stop.

- `docker info` succeeds.
- Both repos present as siblings (see Layout).
- **Windows hosts:** `wsl -l -q` lists a distro and
  `wsl bash -lc "python3.12 --version && docker info"` succeeds (needs Docker Desktop → Settings →
  Resources → **WSL Integration** enabled for the distro). The runner venv also needs:
  ```bash
  sudo apt-get install -y python3.12-venv python3.12-dev build-essential
  ```
  Without `python3.12-venv` venv creation fails with `ensurepip is not available`; without
  `build-essential`/`python3.12-dev` native wheels (`zstandard`, `Brotli`) fail with
  `x86_64-linux-gnu-gcc ... No such file or directory`. A `venv/` left over from before those packages is
  broken — `rm -rf venv`. If WSL/Python 3.12/Docker-in-WSL isn't set up, print the Step 3-4 commands for
  the user to run manually and stop.

## Arguments

`$ARGUMENTS`: first non-flag token = **scenario** (default `DEFAULT`); `--repackage` → `-Repackage`;
`--skip-musl` → `-SkipMusl`; `--weblog poc|uds` (default `poc`); `--tests <path>` to narrow the run.

Build mode: **full** (no flag) first time or after libdatadog/native-profiler changes; `--skip-musl` when
iterating on tracer **code** (one native build instead of two); `--repackage` to only regenerate the tar.

## Step 1 — Build the glibc package

```powershell
pwsh -File "$env:CLAUDE_SKILL_DIR/Build-LinuxPackage.ps1"   # add -SkipMusl or -Repackage
```

No `pwsh`? Use `powershell` with the same arguments; you may first need
`Set-ExecutionPolicy -Scope Process RemoteSigned`. On a Linux/WSL host:

```bash
bash "$CLAUDE_SKILL_DIR/build-linux-package.sh"             # add --skip-musl or --repackage
```

Capture the package path from the **last line of stdout**, e.g.
`...\tracer\bin\artifacts\linux-x64\datadog-dotnet-apm-<version>.tar.gz`. Heavy the first time (two
native compilations); `--skip-musl` roughly halves it. Failing on missing musl files → re-run without it.

## Step 2 — Stage it into system-tests

`binaries/` must hold **exactly one** `datadog-dotnet-apm*.tar.gz`:

```powershell
$dst = "..\system-tests\binaries"   # sibling of dd-trace-dotnet (cwd)
Remove-Item "$dst\datadog-dotnet-apm*.tar.gz" -ErrorAction SilentlyContinue
Copy-Item <TAR_PATH_FROM_STEP_1> $dst
```

## Step 3 — Build the .NET weblog image

```powershell
$stWin = (Resolve-Path "..\system-tests").Path
$st = wsl wslpath -a "$stWin"
wsl bash -lc "mkdir -p /tmp/ddconfig && printf '{}' > /tmp/ddconfig/config.json && cd '$st' && DOCKER_CONFIG=/tmp/ddconfig ./build.sh dotnet"   # add -w uds for the uds weblog
```

The throwaway `DOCKER_CONFIG` is required: WSL's `~/.docker/config.json` usually sets
`"credsStore": "desktop.exe"`, which the Python docker SDK in `run.sh` can't exec (`Exec format error` on
image pulls). An empty config makes pulls anonymous — all images here are public. **Never overwrite the
user's real config.** On a Linux/WSL host just `cd` into system-tests and run `./build.sh dotnet`.

`build.sh dotnet` installs the tar into the weblog image (log line
`Install ddtrace from datadog-dotnet-apm-<version>.tar.gz`) and builds the Python runner venv.

## Step 4 — Run the scenario

```powershell
wsl bash -lc "cd '$st' && DOCKER_CONFIG=/tmp/ddconfig TEST_LIBRARY=dotnet ./run.sh <SCENARIO>"   # append a test path if given
```

`DEFAULT` is the broad smoke run (weblog + Postgres + agent, most tests). There is **no `SMOKE`
scenario** — narrow instead: `./run.sh DEFAULT tests/<file>.py::<Class>`.

## Step 5 — Report

Summarize pytest pass/fail. Logs land in system-tests `logs/` (`DEFAULT`) or `logs_<scenario>/`; on
failure point to the relevant log and the failing test names.

`docker login ghcr.io` errors during `build.sh` → the user must authenticate to GHCR (system-tests
`docs/execute/build.md`). The .NET base images (mcr.microsoft.com) need no auth.
