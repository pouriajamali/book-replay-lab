# Synthetic Book Replay — C++20 / Python, v1.1.0

[![Windows and Linux verification](https://github.com/pouriaquant91/book-replay-lab/actions/workflows/verify.yml/badge.svg)](https://github.com/pouriaquant91/book-replay-lab/actions/workflows/verify.yml)

[Release v1.1.0](https://github.com/pouriaquant91/book-replay-lab/releases/tag/v1.1.0) · [Source-only ZIP](https://github.com/pouriaquant91/book-replay-lab/releases/download/v1.1.0/book-replay-lab-v1.1.0.zip) · [Checksums](https://github.com/pouriaquant91/book-replay-lab/releases/download/v1.1.0/SHA256SUMS.txt)

New independent, AI-assisted portfolio teaching material, October 2026.
Not employer code, a reconstruction/port of a private simulator, a trading
strategy, or evidence of historical production work. No SDK, credentials,
network access, real market data, account data or order submission.

## What to review

- C++20 ordered maps versus Python dictionaries with explicit best-price selection.
- Validate first, then atomically publish an update; rejected updates retain the
  previous levels and accepted sequence but mark the book **not ready**.
- A sequence gap or disconnect gates later updates until an explicit non-regressing
  snapshot arrives. That policy is a teaching contract, not exchange recovery.
- Fixed expected-state fixtures check both programs independently. A seeded
  1,001-event comparison supplements those checks; agreement alone is not proof.

## Run the complete verification

Python 3.10+ and GNU/Clang-compatible C++20 compiler required; no Python packages.

```sh
python verify.py --compiler g++
# or supply the full path to an installed g++ / clang++ executable
```

The verifier compiles the bundled source into a temporary directory, executes
both programs, fails on any mismatch or missing compiler, and removes the temporary
binary. It never installs a compiler. `--report result.json` optionally saves a
local result. The packaged validation.json records the publisher's actual local
toolchain; it does not prove tests ran on every OS or in cloud CI.

Python-only manual replay: `python book_replay.py < input.txt`.
For C++: `g++ -std=c++20 -O2 book_replay.cpp -o book`, then `./book < input.txt`.
On Windows use `book.exe`; add your compiler's bin directory to PATH if its runtime
DLLs are needed. The verifier handles that directory for its child processes.

## Input/output contract (not an exchange wire protocol)

ASCII, whitespace-separated records; blank lines and lines beginning with `#`
are ignored. Prices are integer ticks and quantities integer lots. Values are
bounded to 1..1,000,000,000; update quantity may be zero to delete a known level.

```text
S 10 100 6 103 4     # full snapshot: seq, bid price/qty, ask price/qty
U 11 B 101 2        # replace/upsert bid price level (B or A)
U 13 A 104 5        # gap: retain last accepted book, mark not ready
S 20 100 8 104 3     # explicit full replacement permits updates again
```

Comments above explain the format; remove trailing comments before replay.
`D` marks disconnect. Snapshot sequence must not regress, but may equal the last
accepted sequence (e.g. explicit resnapshot after disconnect). Best bid must be
strictly below best ask. Empty sides after valid deletes are permitted.

Every non-comment record emits:
`reason|ready(0/1)|accepted_sequence|bid_price|bid_qty|ask_price|ask_qty`.
`-` represents an empty side, **not a zero-valued price**. Old updates are labelled
STALE and ignored; conflicting duplicate payloads require an upstream policy and
are not reconciled. Invalid input also gates the book until a valid snapshot.

## Deliberate trade-offs and exclusions

Copy-on-update prioritizes inspectability; it is not a low-allocation or
low-latency design. Python best-price selection is linear. The correctness receipt contains no timing claims. Separate benchmark reports follow the measurement contract in BENCHMARKS.md.
One instrument, one serialized normalized stream, one snapshot bid and ask level.
No concurrency, packet decoding, multi-channel sequencing, durable recovery,
incremental snapshot assembly, authentication, bounded level retention, production
feed completeness, market-by-order queue modelling, fill simulation, execution,
fees, alpha, P&L, CME conformance or production readiness.

The book may retain stale levels while not ready: consumers MUST gate on ready,
not merely the presence of a price. A snapshot is caller-supplied, not independently
authenticated. Real feed policy and reconnect behaviour must be designed separately.

## Attribution

Created with AI assistance for Pouria Jamali's portfolio; tests document only this
sample's contract. It is appropriate for code discussion, not as a substitute for
explaining personal engineering decisions. No private repository was used.


## Public repository and measurements

[Portfolio case study](https://pouriajamali.site/work/cpp-python-simulation/) · [CI runs](https://github.com/pouriaquant91/book-replay-lab/actions) · [Measurement contract](BENCHMARKS.md)

[Recorded Windows measurement and interpretation](results/README.md). This is a
machine-specific synthetic result, separate from CI correctness/smoke checks.

The core C++ implementation is in `book.hpp`; `book_replay.cpp` is the CLI adapter.
Both implementations share the documented synthetic contract, not workplace code.
Version 1.1 adds a benchmark harness, strict shared ASCII whitespace, explicit
measurement units and Windows/Linux CI. The workflow verifies correctness and a
small measurement-contract smoke test; it does not enforce a speed target.

```sh
python run_benchmark.py --compiler g++ --output results/local.json
```

The CLI reads LF-delimited binary input on both platforms. Within a record, only
ASCII space, tab, CR, LF, vertical tab and form feed are whitespace. Other control
bytes and non-ASCII characters are invalid, including inside comments. CRLF input
works. Fixed cases cover the control-byte and universal-newline edge conditions.

Inspect raw batches, workload/source hashes, environment and limitations before
interpreting results. Source hashes are captured before validation/compilation and
checked again after measurement; detected mutation discards the report. This is a
local consistency guard, not a claim of tamper-proof or atomic source storage.
Batch percentiles are not individual-event or exchange/order latency.
