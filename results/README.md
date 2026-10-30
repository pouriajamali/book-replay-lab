# Recorded local measurement

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
