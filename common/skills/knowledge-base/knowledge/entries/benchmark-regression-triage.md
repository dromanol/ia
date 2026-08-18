---
name: benchmark-regression-triage
description: Two cheap checks that tell a real CI benchmark regression from a miscalibrated baseline — cross-PR history, and % converted to absolute ns/op.
type: howto
---

When a CI benchmark bot flags your PR as a regression, run these two checks **before** changing any code.
Together they resolve most claims in minutes.

## 1. Cross-PR history — is this metric always red?

Pull the same scenario+metric from the last 20-60 merged PRs on the base branch. A metric that regresses
on PRs that *cannot* affect it (dependency bumps, docs, config-file changes) has a miscalibrated
baseline, and your number means nothing. Compare where your delta falls in that distribution — landing
mid-range is itself evidence.

Do this even when the bot puts the metric **outside** its "known flaky" section. Flaky lists are
maintained by hand (often a regex) and lag reality, so a chronically-red benchmark can sit in the
"significant" bucket for months.

## 2. Absolute cost — is the magnitude physically possible?

Convert the reported percentage into time per operation and compare it against the instructions you
actually added:

```
baseline_ops_per_sec = reported_op/s_delta / reported_fraction_delta
ns_per_op            = 1e9 / baseline_ops_per_sec
claimed_cost         = ns_per_op * reported_fraction_delta
```

Then bound what you added from the source. A few field loads, a short string compare, a bool store and a
null check are **single-digit ns**. An uncontended `lock`/mutex acquire is ~15-25 ns. An allocation that
survives to gen0 collection is tens of ns. If the claim is two orders of magnitude above your bound, it
is noise — no amount of re-reading the diff will explain it.

Worked example: a -8.3% throughput flag on a 355k op/s benchmark = 2.82 µs/op × 8.3% ≈ **240 ns/op**,
against ~5-10 ns of added work. Not real.

## Corroborating signals

- **Only one TFM/runtime moved.** A cost in shared managed code cannot appear on only one target
  framework while the same code path is flat on the others.
- **Sibling benchmarks on the same code path are flat.** If span-close got slower, every span benchmark
  should move, not one.
- **The run contains impossible numbers.** `+150%`/`+300%` execution_time or `-47%` throughput elsewhere
  in the report means the whole run shifted environmentally (different host, noisy neighbour), so no
  metric in it is trustworthy.
- **No allocation metric moved** while a throughput metric did, and your diff adds no allocations —
  consistent with noise, not with new work.

## Reporting it

Say plainly that the flag is not attributable and show the history table plus the ns/op arithmetic.
Distinguish honestly between "the CI data proves this is chronic" (check 1) and "the magnitude is
impossible" (check 2) — a one-off flag can only be dismissed by check 2, so state which one carried the
conclusion. And do flag any *real* cost you found along the way, even if it isn't what the bot caught.
