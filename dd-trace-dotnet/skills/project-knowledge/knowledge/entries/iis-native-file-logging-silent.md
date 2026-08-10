---
name: iis-native-file-logging-silent
description: trace::Logger (spdlog) file sink produces zero log output for IIS-Express-hosted CLR-profiler test scenarios on Windows dev machines — use a raw std::wofstream bypass logger instead
type: gotcha
---

On at least one Windows dev machine, the native `trace::Logger` (spdlog-based file sink) produces
**zero file output** for any test scenario where the profiler is hosted inside an IIS-Express-launched
process (e.g. `tracer/test/Datadog.Trace.Security.IntegrationTests/IAST/*` via `IisFixture`) — for ALL
test classes, not just one. Confirmed not a path-resolution issue: even an explicit
`DD_TRACE_LOG_DIRECTORY` override (`Configuration.ConfigurationKeys.LogDirectory` set in the test
constructor) to a custom writable directory still produced zero files. `DD_TRACE_DEBUG=1` also has no
effect on this. Root cause unknown (plausibly some interaction between spdlog's file sink and
IIS-Express's process/user context or working directory), but reproducible.

**Workaround for native-side debug logging in this scenario**: bypass `trace::Logger` entirely with a
raw `std::wofstream`-based helper appending to a fixed path, e.g. in
`tracer/src/Datadog.Tracer.Native/iast/dataflow.cpp`:

```cpp
static void RawDebugLog(const std::wstring& msg)
{
    auto now = std::chrono::system_clock::now();
    auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(now.time_since_epoch()).count();
    std::wofstream f(L"C:\\dd_debug_logs\\native_debug.log", std::ios::app);
    if (f) f << L"[" << ms << L"] [tid=" << ::GetCurrentThreadId() << L"] " << msg << std::endl;
}
```

This reliably creates and populates the log file where `trace::Logger` does not. Prefixing with a
Unix-epoch-millisecond timestamp lets native-side events be correlated against managed-side timestamps
(`DateTimeOffset.UtcNow.ToUnixTimeMilliseconds()`) for timing/race investigations — both clocks are UTC
epoch millis, directly comparable with no timezone conversion needed.

This is purely a debugging workaround — remove all `RawDebugLog` calls/helper before finalizing any PR;
it is not a substitute for fixing (or filing) the underlying spdlog file-sink bug.

See [[build-target-doesnt-rebuild-native]] for the related rebuild-sequencing gotcha encountered in the
same investigation.
