# Measurement contract

This is an independent synthetic price-level book replay, not a broker adapter,
matching engine, employer simulator, exchange recovery implementation or production
HFT latency test. No venue, account or real market data is connected.

## Reproduce

Python 3.10+ and a GNU/Clang-compatible C++20 compiler are required. No Python
packages are installed by the code. The Windows CI job obtains an MSYS2 toolchain
from its official package registry.

```sh
python -m unittest discover -s tests -v
python run_benchmark.py --compiler g++ --output results/local.json
```

Default: 20,000 synthetic records, 31 measured batches, 3 warm-up batches, fixed
seed 20261030. Each batch uses a new book. The dataset contains one snapshot and
positive-quantity updates over 21 bid and 21 ask prices. It exercises a small valid
stream; malformed/gap/disconnect behaviour is covered by separate fixtures.

Before timing, the runner compiles and checks **each implementation** against fixed fixture scenarios and independent expected states, then compares a seeded 1,001-event replay.
It also compares complete output for the benchmark dataset outside the timed
region. Language agreement supplements the independent expected-state tests.

## Interpret the report

- `batch_ns`: book creation, ASCII parsing, state updates, status formatting,
  consumption of output lengths and book teardown. File loading, process startup,
  compilation and correctness checks are outside the timed region.
- `batch_percentiles_ns`: nearest-rank percentiles of **batch durations**. They
  are not individual-event latency, tick-to-trade latency or a venue round trip.
  With 31 samples, empirical p99 is the maximum; this is a descriptive small sample.
- `batch_p50_amortized_ns_per_event`: median batch duration divided by its record
  count, not the median of separately timed events.
- `peak_resident_bytes`: the whole process high-water resident/working set,
  including interpreter/runtime, retained input and measurement structures. It is
  not an engine-only allocation or leak measurement. `null` means unavailable.
- Dataset hash, compiler/flags, OS/CPU description, source-file hashes and raw
  batches are retained. Hostnames, account identifiers, tokens and real data are
  not collected. A source commit is recorded only when its code bytes match HEAD.

The C++ program uses ordered maps; Python uses dictionaries and explicit best-price
selection. This comparison concerns **these implementations and this workload**,
not a general ranking of languages. Runs are single-threaded, sequential C++ then
Python, without CPU pinning or an isolated machine. There is no latency SLA or
performance pass/fail threshold. Historical CI smoke runs checked the measurement
contract and correctness gate, not the published local machine's performance.
Current default CI is untimed correctness and source-package verification only;
benchmark execution remains an explicitly chosen separate task.

The default records generated input/output and machine conditions rather than
presenting a synthetic timing as evidence of historical employer results.
