# Synthetic Book Replay — C++20 / Python

<!-- reviewer-entry:begin -->
## Start with the implementation

C++ implements book state and the bounded flat-array experiment. Python provides a separate implementation, reference checks and the small recovery demo; the catalogue labels both languages.

[book.hpp](book.hpp) → [book_replay.cpp](book_replay.cpp) → [demo_recovery.py](demo_recovery.py)

[Preview releases](https://github.com/pouriajamali/book-replay-lab/releases)

The existing setup, validation results and release boundaries continue below.
<!-- reviewer-entry:end -->

[![Windows and Linux verification](https://github.com/pouriajamali/book-replay-lab/actions/workflows/verify.yml/badge.svg)](https://github.com/pouriajamali/book-replay-lab/actions/workflows/verify.yml)

[Release v1.2.1-preview.1](https://github.com/pouriajamali/book-replay-lab/releases/tag/v1.2.1-preview.1) · [Source ZIP](https://github.com/pouriajamali/book-replay-lab/releases/download/v1.2.1-preview.1/book-replay-lab-v1.2.1-preview.1.zip) · [Checksums](https://github.com/pouriajamali/book-replay-lab/releases/download/v1.2.1-preview.1/SHA256SUMS.txt) · [Portfolio](https://pouriajamali.site/work/book-replay-lab/)

Two inspectable engineering exercises explore book-state correctness and bounded
storage choices. Version 1.2 preserves the published 1.1 replay API and adds a
separate flat-array experiment. The earlier source release remains available in
the [release history](https://github.com/pouriajamali/book-replay-lab/releases).

The 1.2.1 preview adds untimed verification, a short recovery demo and source
package proof. Original cores, APIs, fixtures, benchmark runners and historical
measurement bytes are unchanged. No new performance run was made for this release.

## Try recovery in one minute

With a supported, patched Python release installed (see setup guidance below),
download the source ZIP above, extract the whole folder and open a terminal there:

```sh
python demo_recovery.py
```

No compiler, Python package, account or network service is needed for this
Python-only demo. Sequence 13 creates a gap after 11: prices stay visible but
`ready=0`, and the next update is blocked. Snapshot 20 restores readiness;
update 21 then applies. The final line starts with `PASS`. Prices alone do not
mean a usable book. Full verification below checks both language implementations.

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

## Verify correctness without measuring performance

Use a supported, patched Python release and a GNU/Clang-compatible C++20 compiler
from a maintained platform toolchain; no Python packages or network services are
required.

```sh
python verify.py --compiler g++
python verify_flat.py --compiler g++
python -m unittest discover -s tests -v
```

Use a full existing compiler path if `g++` is not on PATH, for example
`"C:\path\to\mingw\bin\g++.exe"` on Windows. The verifiers do not install
tools. Compiler subprocesses have finite timeouts; missing tools or failed
checks exit unsuccessfully instead of substituting a result.

**Expected results:** the legacy verifier reports `passed: true` after 32 fixed
scenarios / 74 expected states per language and a 1,001-event comparison. The flat
verifier reports `passed: true`, 1,006 reference states, all 128 depth slots
checked per event, edge checks and an independently matched Python checksum.
It has no clocks or allocation probe. The nine Python unit checks use synthetic
literals rather than newly measured timing data. See [Contributing](CONTRIBUTING.md).

Default Windows/Linux CI runs these untimed checks and compares actual source
packages to Git and each other. It does not run benchmark entry points.

## Supported setup

As checked on 17 November 2026, Python 3.10 is end-of-life. Its historical
syntax-compatibility floor is unchanged, but it is no longer a recommended setup.
Use a maintained release with security updates from its provider; the
[official Python support table](https://devguide.python.org/versions/) lists
supported branches. Python 3.12 remains in security support through October 2028.

The existing Linux CI uses Ubuntu 24.04's system Python 3.12 and GCC in explicit
C++20 mode; [Ubuntu 24.04 maintenance](https://ubuntu.com/about/release-cycle)
continues through May 2029. Windows keeps the existing UCRT64 GCC/Python packages
with [MSYS2 update enabled](https://github.com/msys2/setup-msys2#update).
Keep those maintained routes; this documentation repair does not install or
upgrade a compiler, change CI, add CMake or requalify arbitrary newer toolchains.
Historical measurements and downloaded release bytes retain their original
toolchain identities and are not evidence for a newly selected local runtime.

## Optional measurements are a separate task

The original runners remain available for an explicitly chosen local experiment:

```sh
python run_flat_benchmark.py --compiler g++ --output .build/local-flat.json
python run_benchmark.py --compiler g++ --output .build/local-replay.json
```

These generate new machine-dependent observations and are unnecessary for the
demo or correctness checks. Read the measurement contracts first. Do not overwrite
published historical files or treat local results as a speed threshold, language
ranking or exchange latency.

## Verify downloaded files

The preview has five files: source ZIP, `SOURCE-MANIFEST.json`,
`SIGNING-PUBLIC-KEY.pub`, `SHA256SUMS.txt` and `SHA256SUMS.txt.sig`. The manifest
records the exact source commit/tree and every source file's size and SHA-256;
the ZIP embeds the same manifest. Packaging uses an explicit clean Git allowlist.

With OpenSSH available, check the public key against an independently trusted
fingerprint before relying on it:

```sh
ssh-keygen -lf SIGNING-PUBLIC-KEY.pub
```

Expected ED25519 fingerprint:
`SHA256:AgU5bZlJSjUu0KsWMmVEEr+BfXpcMVNroTA33bHcQdU`.
A key downloaded beside a signature does not establish trust by itself.

Linux, from the folder containing all five downloads:

```sh
printf 'pouriajamali ' > allowed_signers
cat SIGNING-PUBLIC-KEY.pub >> allowed_signers
ssh-keygen -Y verify -f allowed_signers -I pouriajamali -n file -s SHA256SUMS.txt.sig < SHA256SUMS.txt
sha256sum --check SHA256SUMS.txt
```

Windows PowerShell, with OpenSSH available:

```powershell
("pouriajamali " + (Get-Content -Raw .\SIGNING-PUBLIC-KEY.pub).Trim()) | Set-Content -Encoding ascii .\allowed_signers
cmd /c "ssh-keygen -Y verify -f allowed_signers -I pouriajamali -n file -s SHA256SUMS.txt.sig < SHA256SUMS.txt"
if ($LASTEXITCODE -ne 0) { throw 'Checksum signature verification failed' }
Get-Content .\SHA256SUMS.txt | ForEach-Object {
    $parts = $_ -split '  ', 2
    if ((Get-FileHash -Algorithm SHA256 -LiteralPath $parts[1]).Hash.ToLowerInvariant() -ne $parts[0]) { throw "Checksum mismatch: $($parts[1])" }
}
```

Expect a `Good "file" signature` for `pouriajamali` and matching file hashes.
Integrity/provenance do not establish performance or production readiness.
Earlier releases retain their original assets and checksums.

Maintainers with a clean Git checkout can reproduce and inspect the package:

```sh
python scripts/source_package.py build --commit FULL_40_CHARACTER_HEAD_SHA
python scripts/source_package.py check --commit FULL_40_CHARACTER_HEAD_SHA --repository .
```

Use `git rev-parse HEAD` for the SHA. Existing output folders are never
overwritten; use a fresh `--directory` for another build. The checker compares
source members, manifest, public key and hashes. SSH verification is separate;
without `--repository`, the checker proves manifest integrity rather than Git bytes.

## Read the readiness state

For the legacy normalized replay, check `ready` before using retained levels.
The reason describes the processed record; visible prices alone do not establish
readiness. The existing [replay contract](REPLAY_CONTRACT.md) defines each field.

| Reason | `ready` | Meaning and next step |
| --- | --- | --- |
| `SNAPSHOT` or `UPDATE` | `1` | The record was accepted. Continue normalized replay; a side may be empty after valid deletes. |
| `STALE` | `1` | Ignore the old update; keep the accepted sequence and levels. |
| `GAP` or `DISCONNECTED` | `0` | Retained prices may be stale. Updates stay blocked until a valid non-regressing snapshot. |
| `NOT_READY` | `0` | The update was not applied. Supply an explicit valid snapshot. |
| `STALE_SNAPSHOT` | `0` | The snapshot regressed and was rejected; it did not restore readiness. |
| `INVALID`, `CROSSED` or `UNKNOWN_DELETE` | `0` | Keep accepted levels and sequence; require a valid snapshot before further updates. |

A valid snapshot may have the **same** sequence as the last accepted record;
it must not have a lower sequence. Valid deletes can leave a side empty while
`ready=1`, so missing prices alone do not mean the book is not ready either.
In the existing [recovery fixture](fixtures.json), both the gap and the blocked
next update retain sequence 11 and the same prices:

```text
GAP|0|11|101|2|103|4
NOT_READY|0|11|101|2|103|4
```

The explicit snapshot at 20 restores readiness, and update 21 then applies.
This flag expresses the synthetic teaching policy; it does not authenticate a
feed or establish production readiness. The separate flat-array experiment has
no recovery protocol. No new runtime or performance result is introduced here.

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

For a small reproducible problem, start with the
[synthetic bug-report template](https://github.com/pouriajamali/book-replay-lab/issues/new?template=synthetic-bug-report.md)
and [contribution guide](CONTRIBUTING.md). Use synthetic data only.
The template is a contribution aid; the existing runtime release and measurements are unchanged.

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

[CI resource policy](docs/CI-POLICY.md): documentation-only changes get real lightweight document/pipeline checks; source, tag and manual runs retain native validation. Published runtime tags and release assets remain unchanged.
