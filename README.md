# Synthetic Book Replay — C++20 / Python

[![Windows and Linux verification](https://github.com/pouriajamali/book-replay-lab/actions/workflows/verify.yml/badge.svg)](https://github.com/pouriajamali/book-replay-lab/actions/workflows/verify.yml)

[Release v1.2.1-preview.1](https://github.com/pouriajamali/book-replay-lab/releases/tag/v1.2.1-preview.1) · [Source ZIP](https://github.com/pouriajamali/book-replay-lab/releases/download/v1.2.1-preview.1/book-replay-lab-v1.2.1-preview.1.zip) · [Checksums](https://github.com/pouriajamali/book-replay-lab/releases/download/v1.2.1-preview.1/SHA256SUMS.txt) · [Portfolio](https://pouriajamali.site/work/cpp-python-simulation/)

Two inspectable engineering exercises explore book-state correctness and bounded
storage choices. Version 1.2 preserves the published 1.1 replay API and adds a
separate flat-array experiment. The earlier source release remains available in
the [release history](https://github.com/pouriajamali/book-replay-lab/releases).

The 1.2.1 preview adds untimed verification, a short recovery demo and source
package proof. Original cores, APIs, fixtures, benchmark runners and historical
measurement bytes are unchanged. No new performance run was made for this release.

## Try recovery in one minute

With Python 3.10+ installed, download the source ZIP above, extract the whole
folder and open a terminal there:

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

Install Python 3.10+ and a GNU/Clang-compatible C++20 compiler; no Python packages
or network services are required.

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
