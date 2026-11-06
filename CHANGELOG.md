# Changes

## 1.2.1-preview.1 — verification and onboarding

- Add a Python-only six-row recovery demo using the unchanged fixed fixture.
- Expose the existing flat reference/edge checks through a standalone untimed
  C++/Python verifier; compare all 128 slots per event and the Python checksum.
- Make default Windows/Linux CI correctness-only; benchmark runners remain
  opt-in and retain their exact historical source and measurement files.
- Add exact clean-Git source packaging, member manifest and package inspection;
  compare both operating systems' actual products without rebuilding.
- Document source download, public-key fingerprint, signature/hash verification
  and the explicit separation between verification and performance experiments.
- Preserve original cores/APIs, fixtures, nine unit checks, historical raw data
  and all older release assets/tags. No new performance result or binary.

## Unreleased - documentation

- Add a Markdown synthetic bug-report template matching the existing contribution
  checklist, with separate example input/expected state and a Python-only path.
  No runtime change, new measurement or replacement release asset.
- Include that exact template path in the strict source-package member allowlist;
  unknown members and symlinks remain rejected. Existing release assets stay unchanged.
- Clarify the source quick start and expected result, and link focused contribution guidance. Runtime behavior, release assets and recorded measurements are unchanged.


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
