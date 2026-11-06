# Contributing

Start with the README and the current release. A useful contribution is a small
case another developer can reproduce, with a clear expected result.

## Report a problem

Include the commit or release, OS and toolchain versions. Provide the smallest integer update/snapshot sequence, expected levels and ready/sequence state, and actual output.
Use synthetic inputs only. Remove credentials, account identifiers, personal
data and employer or proprietary source before opening an issue.

## Run the checks

Use Python 3.10+ and a GNU/Clang-compatible C++20 compiler. From the repository root:

```sh
python verify.py --compiler g++
python verify_flat.py --compiler g++
python -m unittest discover -s tests -v
```

These checks do not collect performance data. `python demo_recovery.py` provides
the short Python-only fixture replay. Benchmark runs are separate opt-in work;
keep historical report files and their measured-source hashes unchanged.

## Submit a focused change

Explain the behavior before and after the change. For a bug, add a regression
case that fails before the repair. Preserve the documented input and output
contracts, keep historical evidence intact, and update the relevant design or
format notes when the contract changes. Do not replace recorded measurements
with estimates or transfer their results to a different implementation.

Small improvements to setup instructions, fixtures and diagnostic messages are
welcome. Read the license and attribution in this repository before contributing.
