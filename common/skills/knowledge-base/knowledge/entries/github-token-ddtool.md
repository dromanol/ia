---
name: github-token-ddtool
description: Generate a GitHub token with `ddtool auth github token` (defaults to the DataDog org).
type: reference
---

To generate a GitHub token, use the internal Datadog CLI:

```
ddtool auth github token
```

Defaults to the **DataDog** org. Use this instead of manually creating a PAT when a command or
script needs GitHub auth in a Datadog context (e.g. `gh` operations, cloning private repos, API
calls against DataDog-org repositories).
