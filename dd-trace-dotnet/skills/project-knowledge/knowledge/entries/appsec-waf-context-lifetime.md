---
name: appsec-waf-context-lifetime
description: Where the WAF additive context lives and dies — TraceContext owns it, an ambient HttpContext gates every WAF run, CloseWebSpan is the only reporting flush point and it is web-root only.
type: reference
---

Map of the AppSec per-request state, gathered while fixing a native-memory leak (SCRS-2370, PR #9057).

## Who owns what

- `TraceContext._appSecRequestContext` — one `AppSecRequestContext` per trace segment, lazily created.
  It holds the WAF *additive* context (`IContext`) plus triggers, WAF errors, timeouts, RASP metrics and
  stack traces.
- `TraceContext._rootSpan` **is the trace lock** (chosen in #4125 to avoid allocating a lock object). It
  guards `_spans`, `_openSpans`, `_segmentClosed`. The comment block listing what it protects sits right
  above the field — keep it updated when adding guarded state.
- Each libddwaf context owns a `monotonic_buffer_resource` freed only on destruction, so a context that
  is never disposed is **native** memory growth with a flat managed heap.
- `AppSec/Waf/Context.Dispose` is idempotent (`_disposed` guard), so a double dispose is a safe no-op.

## Running the WAF requires an ambient HttpContext

Every WAF entry point goes through `SecurityCoordinator`, and both `TryGet` overloads bail out without
one: `CoreHttpContextStore.Instance.Get()` on Core, `HttpContext.Current` on Framework. On Core the store
is cleared **one line before** the root scope is disposed
(`PlatformHelpers/AspNetCoreHttpRequestHandler.cs:267-268`), and since #8989 the `AsyncLocal` holds a
*holder* object so that clear is visible to every `ExecutionContext` captured during the request. Net
effect: after the web root span closes, nothing can reach `GetOrCreateAdditiveContext` any more.

That is why disposing the additive context at web-root close (even with children still open) is correct
and not just an optimisation — the rule itself comes from #6609, which moved the context out of
`HttpContext.Items` because the `HttpContext` gets recycled at request end.

## Reporting is web-root only

`AppSecRequestContext.CloseWebSpan` is the **only** place accumulated AppSec data is flushed onto a span,
and `TraceContext.CloseSpan` calls it only for `span.IsRootSpan && span.Type == SpanTypes.Web`. All
results are written to `SecurityCoordinator._localRootSpan`. So:

- a trace whose local root is **not** web accumulates AppSec data that is never reported (pre-existing);
- anything produced after the segment closed can't be reported either — the root is already serialized.

This is what justifies making disposal terminal instead of "reopening" the context for spans added to an
already-closed segment.

## Where the leak came from

Creation and release were asymmetric: creation only needed an HttpContext (reachable from
`EventTrackingSdk`/`EventTrackingSdkV2.RunSecurityChecksAndReport` and the ASP.NET Core Identity signup
path), release only ran for a web local root. PR #9057 moved disposal to the `_openSpans == 0` branch of
`CloseSpan`, under the trace lock.

See also [[appsec-unit-tests-need-native-waf-copy]] for running the security unit tests locally.
