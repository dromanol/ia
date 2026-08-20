---
name: branch-naming-convention
description: Branches created in dd-trace-dotnet must follow dani/area/nombre (area = aap, iast, apm, ...)
type: feedback
---

Branch names in this repo follow `dani/area/nombre`, where `area` is the relevant product area
(`aap`, `iast`, `apm`, ...) and `nombre` describes the change.

**Why:** user-specified naming convention for branches created in this repo.

**How to apply:** when creating a branch here, name it `dani/<area>/<nombre>` — pick `area` from the
product the change touches (e.g. `aap` for AppSec/AAP, `iast` for IAST, `apm` for core tracing).
