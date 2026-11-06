"""Check the unchanged flat book/reference with no clocks or performance output."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from run_flat_benchmark import reference, workload

ROOT = Path(__file__).resolve().parent
SOURCES = ("flat_depth.hpp", "verify_flat.cpp", "verify_flat.py", "run_flat_benchmark.py")

def verify(compiler: str) -> dict:
    executable = shutil.which(compiler)
    if executable is None:
        raise RuntimeError("C++ compiler unavailable; flat correctness is NOT complete")
    before = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in SOURCES}
    environment = dict(os.environ)
    environment["PATH"] = str(Path(executable).parent) + os.pathsep + environment.get("PATH", "")
    version = subprocess.run([executable, "--version"], capture_output=True, text=True,
                             check=True, env=environment, timeout=15).stdout.splitlines()[0]
    # These are bounded correctness fixtures, not a timing workload or new dataset.
    events = workload(1000, 20261102) + [
        (-1, 0, 1), (2, 0, 1), (0, -1, 1), (0, 64, 1),
        (1, 0, -1), (1, 0, 1000000001)]
    build_root = ROOT / ".build"
    build_root.mkdir(exist_ok=True)
    flags = ["-std=c++20", "-O2", "-Wall", "-Wextra", "-Wpedantic", "-Werror"]
    with tempfile.TemporaryDirectory(prefix="flat-correctness-", dir=build_root) as temporary:
        directory = Path(temporary).resolve()
        if not directory.is_relative_to(build_root.resolve()):
            raise RuntimeError("Temporary directory escaped checkout")
        binary = directory / ("flat-check.exe" if os.name == "nt" else "flat-check")
        data = directory / "fixture.txt"
        data.write_bytes("".join(f"{side} {tick} {quantity}\n" for side, tick, quantity in events).encode("ascii"))
        build = subprocess.run([executable, *flags, str(ROOT / "verify_flat.cpp"), "-o", str(binary)],
                               capture_output=True, text=True, env=environment, timeout=60)
        if build.returncode:
            raise RuntimeError("Flat correctness compilation failed:\n" + build.stderr)
        run = subprocess.run([str(binary), str(data)], capture_output=True, text=True,
                             env=environment, timeout=30)
        if run.returncode:
            raise RuntimeError("Flat correctness check failed:\n" + run.stderr)
        result = json.loads(run.stdout)
    if result != {"events": 1006, "depth_slots_per_event": 128, "edge_checks_passed": True,
                  "checksum": str(reference(events))}:
        raise RuntimeError("C++ full-state checks / independent Python checksum mismatch")
    if before != {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in SOURCES}:
        raise RuntimeError("Source changed during correctness verification")
    return {"schema": "flat-depth-untimed-correctness-v1", "passed": True,
            "events": 1006, "depth_slots_per_event": 128, "edge_checks_passed": True,
            "python_dictionary_checksum_matches": True, "checksum": result["checksum"],
            "compiler": version, "compiler_flags": flags, "source_sha256": before,
            "boundary": "Untimed synthetic full-state/reference checks only; no allocation, latency, profile or production claim."}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compiler", default="g++", help="Existing GNU/Clang-compatible C++20 compiler or full path")
    parser.add_argument("--report", type=Path, help="Optional correctness receipt, not a measurement")
    args = parser.parse_args()
    report = verify(args.compiler)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
