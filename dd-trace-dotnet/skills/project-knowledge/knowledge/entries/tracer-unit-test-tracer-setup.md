---
name: tracer-unit-test-tracer-setup
description: In unit tests `TracerHelper.Create(new())` is the idiomatic tracer — `new TracerSettings()` is [TestingOnly] and reads no environment variables.
type: howto
---

```csharp
await using var tracer = TracerHelper.Create(new());
```

is the preferred form in tracer unit tests (asked for in review on PR #9057), rather than the longer

```csharp
var settings = TracerSettings.Create(new Dictionary<string, object>());
await using var tracer = TracerHelper.Create(settings);
```

The non-obvious part: they are equivalent, including for env-var isolation. The parameterless
`internal TracerSettings()` is marked `[TestingOnly]` and chains with `source: null`, which resolves to
`NullConfigurationSource` — so it picks up **no** `DD_*` variables from the machine running the tests,
exactly like the empty dictionary does. Use the longer form only when you actually need to set values.

`TracerHelper.Create` returns an async-disposable tracer, hence `await using`.
