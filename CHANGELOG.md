# Changes

## 1.2.0 — 2 November 2026

- Add a separate bounded 64-price-slot-per-side C++20 depth-update experiment.
- Gate measurement on boundary/rejection checks, map-reference comparison of
  all 128 slots after every event and a Python dictionary checksum.
- Record raw per-event clocks, separate empty-clock overhead, separate aggregate
  batch durations and instrumented ordinary hot-path `new`/`new[]` calls.
- Keep empirical clock-granularity limits explicit; no speed threshold or
  low-latency/production claim.
- Add Python measurement tests and Windows/Linux CI smoke commands.
- Reorganize README around reviewable choices/contracts; consolidate scope and
  attribution while retaining legacy limits in REPLAY_CONTRACT.md.
- Existing replay implementation, fixtures and previous measurements unchanged.

## 1.1.0 — previously published

Legacy replay benchmark harness, ASCII whitespace contract and cross-platform
verification. The prior source-only release remains available in release history.
