---
name: Synthetic bug report
about: Report a small reproducible replay or demo problem using synthetic inputs only
title: ""
labels: ""
assignees: ""
---

Please read [CONTRIBUTING.md](https://github.com/pouriajamali/book-replay-lab/blob/main/CONTRIBUTING.md).
Remove credentials, personal/account/employer data and proprietary code before posting.
Use synthetic inputs only; do not attach live feeds, real account traces or private source.
No benchmark or performance result is required for a correctness report.

## Version and environment

- Release tag or commit SHA:
- OS and architecture:
- Python version:
- Compiler and version (optional for the Python-only demo):

## Exact command

Include the working directory relative to the repository root and the command used.
For the Python-only recovery demo: `python demo_recovery.py`.

## Minimal synthetic input

Replace this example with your smallest reproduction. Input syntax and policy:
[REPLAY_CONTRACT.md](https://github.com/pouriajamali/book-replay-lab/blob/main/REPLAY_CONTRACT.md).

Example input (two independent records in order):

```text
S 10 100 6 103 4
U 11 B 101 2
```

## Expected result

State the reason, readiness, accepted sequence and bid/ask levels and quantities.
The output format is `reason|ready|accepted_sequence|bid|qty|ask|qty`.
Expected output for the example above (not input):

```text
SNAPSHOT|1|10|100|6|103|4
UPDATE|1|11|101|2|103|4
```

## Actual output

Paste the smallest relevant output or error, including the exit code if available.
If reporting the Python demo, identify the differing input/output row.

## Before submitting

- [ ] I used synthetic data and removed credentials, identifiers and private source.
- [ ] I included the version, command, smallest input, expected state and actual output.
