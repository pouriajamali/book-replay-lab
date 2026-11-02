# Recorded local measurement

## Bounded flat-array depth experiment — 2 November 2026

[Windows/GCC13/Python3.12 metadata](windows-flat-depth-20261102.meta.json) and
[all raw observations (gzip JSON)](windows-flat-depth-20261102.json.gz), from the
additive 1.2 source candidate: 20,000 synthetic events, 31 samples, 3 warm-ups;
620,000 instrumented event observations. Before timing, C++ checks all 128 slots
against a map after each event and the Python reference checksum matches.
Instrumented ordinary global `new`/`new[]` calls during timed loops: **0**.

The individual median is **unresolved below clock granularity**, represented as
`null`/`RESOLUTION_LIMITED`. Raw p99 is 100ns, also the empty-clock-pair p99; the
smallest observed positive duration is 100ns. These values do not establish
engine latency. Separate aggregate batches retain their raw duration and
amortized cost in the report, not an individual-event percentile or speedup.

No CPU affinity or isolated host was used. See the [measurement contract](../FLAT_DEPTH.md),
raw observations and source/workload hashes. CI smoke checks validate correctness
and measurement fields, not this machine's timings. A version/code hash does not
by itself establish GitHub publication or a CI pass.

The metadata binds both compressed and decompressed SHA256 hashes. Read the full
JSON with Python's standard library: `json.loads(gzip.decompress(path.read_bytes()))`.
Compression retains all observations; it does not replace them with percentiles.

## Legacy map/dictionary replay

[Raw Windows / GCC13 / Python3.12 report](windows-gcc13-python312.json)

The report measures source commit `d106edcea322bf033a6c0f6f11ab472731571195`:
20,000 synthetic records,31 measured batches,3 warm-ups and a fixed seed.
Its correctness gate passed32 fixed scenarios /74 expected states per language,
plus a1,001-event comparison and complete output agreement for the timed dataset.
The report retains code hashes, raw batches, actual environment and dataset hash.
Later documentation/result commits do not change those measured code bytes.

Read [the measurement contract](../BENCHMARKS.md) before comparing values.
Percentiles describe batches; amortized nanoseconds per event are not individually
measured event latency. Whole-process peak memory includes runtime and retained
input. This small ordered-map/dictionary workload is neither a language ranking
nor employer, exchange, order-entry or production HFT performance evidence.
Windows/Linux CI runs a correctness and measurement-contract smoke test, not a
reproduction of this machine's timing values. No speed threshold is enforced.
