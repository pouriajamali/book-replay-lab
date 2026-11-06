# Bounded flat-array depth experiment

The additive 1.2 experiment asks what can be measured when a normalized depth
update uses fixed storage. It complements the inspectable map/dictionary replay,
without replacing that contract.

## Design and correctness

`flat_depth.hpp` stores 64 integer quantity slots per side in two `std::array`s.
The caller maps disjoint bid/ask tick windows to indices 0..63. Update replaces
a quantity, zero deletes it, and deleting the best level scans at most 64 slots.
No resize or dynamic price-window expansion occurs. Invalid side, out-of-window
index and quantity outside 0..1,000,000,000 reject without changing the book.

The runner checks empty/full windows, boundary indices, best-level replacement
and deletion, absent deletion, quantity limits and rejection/state preservation.
It then compares the top and all 128 slots against an ordered-map reference after
every generated event. A separate Python dictionary calculation checks the
output checksum. Failed correctness gates emit no measurement report.

## Reproduce

```sh
python run_flat_benchmark.py --compiler g++ --output results/local-flat.json
```

Defaults: 20,000 pre-generated events, 31 samples, 3 warm-ups, fixed seed 20261102.
The stream fills all 128 slots then performs uniform replacement with 20% deletes.
Text parsing, setup, book resets, fixture/reference checks and serialization are
outside timed loops. Each event measurement includes an update, top read,
checksum consumption and its pair of `steady_clock` calls. Separate full-batch
measurements omit per-event clock calls. Median batch duration divided by event
count is **amortized cost**, not an event latency percentile.

The report retains raw event, empty-clock-pair and batch observations,
nearest-rank p50/p99, zeros, source/workload hashes, compiler flags and environment.
Empty clock-pair timings are measured separately, not subtracted. Zero raw
observations are retained; a zero observed median becomes JSON `null` with
`median_resolution=RESOLUTION_LIMITED`, never zero-nanosecond execution.
`Clock::period` alone does not establish empirical clock resolution. The recorded
Windows p99 matches the empty-clock p99 and remains instrumentation-limited.

The allocation probe counts ordinary replaceable global `new`/`new[]` calls
during instrumented and aggregate timed loops. Workload/timing arrays allocate
first. This does not count aligned allocation, `malloc`, OS memory or whole-process
allocations; the fixed update/top/checksum path uses none of those APIs. The
checksum consumes every update and is compared with the precomputed reference
after each warm-up and measured pass. Compiler signal fences bound the timed
kernel without a hardware fence/CPU-serialization claim. A deliberately allocated
setup control must increment the allocation probe once before it is reset.

## Scope and trade-offs

Fixed windows bound memory and deletion work while rejecting unsupported prices.
They sacrifice arbitrary sparse price ranges and full exchange-book semantics.
This is single-threaded normalized data: no packet decoder, sequencing/recovery,
network, broker, exchange, fill model or order execution. Timing is host/workload
specific and includes instrumentation. No CPU affinity, isolated host, speed
threshold, HFT SLA or legacy-map speedup is claimed.

See [the Windows metadata](results/windows-flat-depth-20261102.meta.json),
[all raw observations (gzip JSON)](results/windows-flat-depth-20261102.json.gz) and
[interpretation](results/README.md). Historical CI used small measurement-contract
smokes, not reproduction of those timing values. Current Windows/Linux CI uses
`verify_flat.py` for untimed boundary/full-state/reference/Python-checksum checks
and does not invoke the benchmark. The original benchmark source stays unchanged.
