# Legacy replay contract (unchanged in the 1.2 candidate)

`book.hpp` and `book_replay.cpp` implement C++20 ordered-map replay;
`book_replay.py` uses dictionaries with explicit best-price selection. The fixed
fixtures check each independently: 32 scenarios / 74 expected states per language,
plus a seeded 1,001-event cross-language comparison. Agreement alone is not proof.

Python manual replay: `python book_replay.py < input.txt`.
For C++: `g++ -std=c++20 -O2 book_replay.cpp -o book`, then `./book < input.txt`.
Windows uses `book.exe`; its compiler runtime DLL directory must be on PATH.
The verifier sets that directory for child processes and supports `--report`.

## Normalized input/output

ASCII whitespace-separated records; blank lines and lines beginning with `#`
are ignored. Prices are integer ticks and quantities integer lots. Values are
bounded to 1..1,000,000,000; update quantity zero deletes a known level.

```text
S 10 100 6 103 4
U 11 B 101 2
U 13 A 104 5
S 20 100 8 104 3
```

`S` is a full snapshot: sequence, bid price/quantity, ask price/quantity.
`U` is update: sequence, side (B/A), price, quantity. The gap from 11 to 13 retains
the last accepted book and marks it not ready; the explicit 20 snapshot permits
updates again. `D` marks disconnect. Snapshot sequence must not regress, but may
equal the last accepted sequence. Best bid must remain strictly below best ask.
Empty sides after valid deletes are permitted. No trailing record comments.

Every non-comment record emits:
`reason|ready(0/1)|accepted_sequence|bid_price|bid_qty|ask_price|ask_qty`.
`-` represents an empty side, not a zero-valued price. Old updates are `STALE`
and ignored. Conflicting duplicate payloads need an upstream reconciliation
policy that this example does not supply. Invalid input gates the book until a
valid snapshot. Consumers must check `ready`, not merely presence of prices.

The CLI reads LF-delimited binary input on both platforms. Within a record,
only ASCII space, tab, CR, LF, vertical tab and form feed are whitespace. Other
control bytes/non-ASCII characters are invalid, including inside comments. CRLF
works. Fixtures cover control-byte and universal-newline edge conditions.

## Implementation trade-offs

Copy-on-update prioritizes inspection and atomic rejection over allocation cost;
Python best-price selection is linear. This contract models one instrument, one
serialized normalized stream and one bid/ask level in a replacement snapshot.
A snapshot is caller-supplied and not independently authenticated. Levels can be
stale while `ready=false`.

It does not implement concurrency, packet decoding, multi-channel sequencing,
durable recovery, incremental snapshot assembly, authentication, bounded level
retention, production feed completeness, market-by-order queues or execution.
The bounded-array experiment is separate, not an exchange recovery replacement
or proof that this map implementation became low latency.

See [BENCHMARKS.md](BENCHMARKS.md) for batch timing and whole-process memory
boundaries. Batch percentiles and amortized nanoseconds are not individually
measured event or exchange/order latency. Detected source mutation discards a
measurement; hashing is a local consistency guard, not atomic/tamper-proof storage.
