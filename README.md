# Synthetic Book Replay — C++20 / Python

[![Windows and Linux verification](https://github.com/pouriaquant91/book-replay-lab/actions/workflows/verify.yml/badge.svg)](https://github.com/pouriaquant91/book-replay-lab/actions/workflows/verify.yml)

[Release v1.2.0](https://github.com/pouriaquant91/book-replay-lab/releases/tag/v1.2.0) · [Source ZIP](https://github.com/pouriaquant91/book-replay-lab/releases/download/v1.2.0/book-replay-lab-v1.2.0.zip) · [Checksums](https://github.com/pouriaquant91/book-replay-lab/releases/download/v1.2.0/SHA256SUMS.txt) · [Portfolio](https://pouriajamali.site/work/cpp-python-simulation/)

Two inspectable engineering exercises explore book-state correctness and bounded
storage choices. Version 1.2 preserves the published 1.1 replay API and adds a
separate flat-array experiment. The earlier source release remains available in
the [release history](https://github.com/pouriaquant91/book-replay-lab/releases).

## What to review

- **State/recovery replay:** C++ ordered maps and Python dictionaries validate
  updates before publishing them. Gaps/disconnects block later updates until an
  explicit non-regressing snapshot. Rejected changes retain levels/sequence while
  setting `ready=false`.
- **Bounded depth experiment:** two 64-slot arrays replace dynamic price-level
  storage. Boundary/rejection/deletion cases and all 128 slots are checked against
  an ordered-map reference after every generated event; a Python checksum provides
  another implementation check.
- **Measurement discipline:** keep event observations, empty-clock overhead and
  aggregate batch cost separate. Label unresolved clock readings instead of
  calling them zero-latency execution. Count ordinary hot-path `new`/`new[]` calls
  and retain source/workload hashes and raw measurements.

## Run

Python 3.10+ and an installed GNU/Clang-compatible C++20 compiler; no Python
packages or network services. Supply a full compiler path when needed.

```sh
python verify.py --compiler g++
python -m unittest discover -s tests -v
python run_flat_benchmark.py --compiler g++ --output results/local-flat.json
python run_benchmark.py --compiler g++ --output results/local-replay.json
```

The runners compile in a checkout-local temporary directory and fail closed if a
compiler, correctness gate or source-consistency check fails. They never install
a compiler. Windows/Linux CI runs correctness and small measurement-contract
smoke tests with no speed threshold.

## Contracts and recorded results

- [Legacy replay input/output and recovery contract](REPLAY_CONTRACT.md)
- [Flat-array design, allocation scope and per-event measurement](FLAT_DEPTH.md)
- [Legacy batch measurement contract](BENCHMARKS.md)
- [Actual Windows results and interpretation](results/README.md)
- [Version history](CHANGELOG.md)

The Windows flat-array run verifies full-state agreement and zero calls to the
instrumented ordinary allocation operators during timed loops. Its individual
event median is unresolved at the observed clock granularity; the p99 is also
clock-overhead limited. Separate aggregate timings are labelled amortized batch
cost, without a speedup or engine-latency claim.

## Scope and limitations

These synthetic, single-threaded experiments use normalized integer data, not
exchange packets. They contain no employer code, real market/account data,
strategy or broker connection. Replay recovery is a teaching policy; the flat
experiment has fixed disjoint price windows and no recovery protocol. Neither
sample establishes production readiness, CME conformance, HFT latency, fill
quality, fees, alpha or profitability. See the contracts for implementation
trade-offs and exact measurement boundaries.

## Attribution

Created with AI assistance for Pouria Jamali's public portfolio. No private
repository source was used. The source, tests and recorded measurements support
discussion of these examples, separate from historical employer experience.
