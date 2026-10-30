"""Compile C++20; verify BOTH implementations against fixed expected states.

Then run a deterministic generated comparison. No external packages or downloads.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import random
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent
SOURCES = ["book.hpp", "book_replay.cpp", "book_replay.py", "fixtures.json", "verify.py", "benchmark.cpp", "benchmark.py", "run_benchmark.py", "BENCHMARKS.md", "README.md", "LICENSE"]


def run(command: list[str], records: list[str], environment: dict[str, str]) -> list[str]:
    process = subprocess.run(command, input="\n".join(records) + "\n", text=True,
                             encoding="utf-8", capture_output=True, env=environment,
                             timeout=20, check=True)
    return process.stdout.splitlines()


def verify(compiler: str) -> dict:
    compiler_path = shutil.which(compiler)
    if compiler_path is None:
        raise RuntimeError("C++ compiler unavailable; verification is NOT complete")
    env = dict(os.environ)
    env["PATH"] = str(Path(compiler_path).parent) + os.pathsep + env.get("PATH", "")
    fixtures = json.loads((ROOT / "fixtures.json").read_text(encoding="utf-8"))
    version = subprocess.run([compiler_path, "--version"], text=True, capture_output=True,
                             encoding="utf-8", check=True, env=env).stdout.splitlines()[0]
    with tempfile.TemporaryDirectory(prefix="synthetic-book-") as temporary:
        executable = str(Path(temporary) / ("book.exe" if os.name == "nt" else "book"))
        flags = ["-std=c++20", "-O2", "-Wall", "-Wextra", "-Wpedantic", "-Werror"]
        subprocess.run([compiler_path, *flags, str(ROOT / "book_replay.cpp"), "-o", executable],
                       capture_output=True, text=True, encoding="utf-8", check=True,
                       timeout=60, env=env)
        cpp = [executable]
        python = [sys.executable, str(ROOT / "book_replay.py")]
        for fixture in fixtures:
            for language, command in (("C++20", cpp), ("Python", python)):
                actual = run(command, fixture["input"], env)
                if actual != fixture["expected"]:
                    raise AssertionError(f"{language}: {fixture['name']}\n{actual}\n!=\n{fixture['expected']}")
        # This comparison is supplementary: independent expected states above
        # prevent language agreement alone from being labelled correctness.
        randomizer = random.Random(20261029)
        generated = ["S 1 100 5 200 5"]
        for sequence in range(2, 1002):
            side = randomizer.choice(("B", "A"))
            price = randomizer.randint(90, 110) if side == "B" else randomizer.randint(190, 210)
            generated.append(f"U {sequence} {side} {price} {randomizer.randint(1, 1000)}")
        cpp_output, python_output = run(cpp, generated, env), run(python, generated, env)
        if cpp_output != python_output or len(cpp_output) != len(generated):
            raise AssertionError("Generated cross-language comparison failed")
        if any(line.split("|")[1] != "1" for line in cpp_output):
            raise AssertionError("Generated valid stream lost readiness")
    return {
        "sample_version": "1.1.0", "passed": True,
        "platform": sys.platform, "compiler": version,
        "python": sys.version.split()[0], "compiler_flags": flags,
        "fixture_scenarios": len(fixtures),
        "expected_state_checks_per_language": sum(len(f["expected"]) for f in fixtures),
        "generated_comparison_events": len(generated),
        "source_sha256": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in SOURCES},
        "trace": next(f for f in fixtures if f["name"] == "gap then snapshot recovery"),
        "boundary": "Synthetic local tests; not production, latency, exchange conformance or profitability evidence."
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compiler", default="g++", help="GNU/Clang-compatible C++20 compiler path")
    parser.add_argument("--report", type=Path, help="Optional local JSON result path")
    args = parser.parse_args()
    result = verify(args.compiler)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
