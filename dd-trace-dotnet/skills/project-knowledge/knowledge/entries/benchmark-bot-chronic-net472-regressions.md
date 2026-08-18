---
name: benchmark-bot-chronic-net472-regressions
description: Two net472 throughput benchmarks (DbCommand.ExecuteNonQuery, HttpClient.SendAsync) are flagged as significant regressions on nearly every PR regardless of content.
type: gotcha
---

The `pr-commenter` benchmark bot reports these two as **significant regressions** (🟥, *not* in the
"Known flaky benchmarks" section) on almost every PR:

- `scenario:Benchmarks.Trace.DbCommandBenchmark.ExecuteNonQuery net472` — `throughput`
- `scenario:Benchmarks.Trace.HttpClientBenchmark.SendAsync net472` — `throughput`

Measured over merged PRs in Aug 2026: DbCommand hit **20 of 24** consecutive merged PRs at -5% to -12%;
HttpClient appeared in roughly half of the last 60. That includes PRs that cannot possibly affect the
tracer hot path — e.g. #9061 (Docker image tag bump, -8.1%/-9.3%) and #9004 (`launchSettings.json`
generation, -8.7%/-9.6%). The baseline for the net472 throughput suite is miscalibrated.

**So:** a 🟥 on either of these alone is not evidence your PR regressed anything. Don't chase it, and
don't let it block review. Because they aren't in the flaky list, reviewers do occasionally raise them.

To rebut with data, scan recent merged PRs' bot comments:

```bash
for pr in $(gh pr list --repo DataDog/dd-trace-dotnet --state merged --limit 25 --json number --jq '.[].number'); do
  body=$(gh pr view $pr --repo DataDog/dd-trace-dotnet --json comments \
    --jq '[.comments[] | select(.author.login=="pr-commenter")] | last | .body')
  echo "PR $pr: $(printf '%s' "$body" | grep -A3 -E '^#### scenario:Benchmarks\.Trace\.DbCommandBenchmark\.ExecuteNonQuery net472$' \
    | grep -oE '\[-?[0-9.]+%; -?[0-9.]+%\]' | head -1)"
done
```

Corroborating signals that a whole run is environmentally shifted rather than showing real deltas: the
bot's own header counts a large number of flaky benchmarks, and the flaky section contains physically
impossible swings (`+150%`/`+300%` `execution_time`, `-47%` `throughput`). Also check whether the same
code path moved on net6.0/netcoreapp3.1 — a genuine cost in shared managed code (e.g. `TraceContext`)
cannot show up only on net472.

The general technique for validating any CI benchmark-bot claim — cross-PR history plus converting the
reported % into absolute ns/op and comparing against the instructions actually added — lives in the
global `/knowledge-base` as `benchmark-regression-triage`.
