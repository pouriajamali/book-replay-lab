"""Correctness-gated bounded flat-array experiment; Python standard library only."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import gzip
import json
import math
import os
from pathlib import Path
import platform
import random
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent
SOURCES = ['flat_depth.hpp', 'flat_depth_benchmark.cpp', 'run_flat_benchmark.py']
MASK = (1 << 64) - 1

def workload(count: int, seed: int) -> list[tuple[int, int, int]]:
    rng = random.Random(seed)
    # Populate the complete supported window before deterministic mixed updates.
    events = [(side, tick, tick + 1) for side in range(2) for tick in range(64)]
    for i in range(128, count):
        side, tick = rng.randrange(2), rng.randrange(64)
        quantity = 0 if i % 5 == 0 else rng.randint(1, 1000)
        events.append((side, tick, quantity))
    return events

def reference(events: list[tuple[int, int, int]]) -> int:
    levels: list[dict[int, int]] = [{}, {}]
    checksum = 1469598103934665603
    for side, tick, quantity in events:
        accepted = side in (0, 1) and 0 <= tick < 64 and 0 <= quantity <= 1_000_000_000
        if accepted:
            if quantity == 0:
                levels[side].pop(tick, None)
            else:
                levels[side][tick] = quantity
        bid, ask = max(levels[0], default=-1), min(levels[1], default=-1)
        for value in (bid + 1, levels[0].get(bid, 0), ask + 1, levels[1].get(ask, 0), int(accepted)):
            checksum = ((checksum ^ value) * 1099511628211) & MASK
    return checksum

def summarize(values: list[int]) -> dict:
    if not values or any(type(x) is not int or x < 0 for x in values):
        raise ValueError('nonnegative integer clock observations required')
    ordered = sorted(values)
    positive = [x for x in ordered if x > 0]
    median = ordered[math.ceil(.5 * len(values)) - 1]
    return {'count': len(values), 'p50': median if median > 0 else None,
            'p99': ordered[math.ceil(.99 * len(values)) - 1], 'min': ordered[0], 'max': ordered[-1],
            'zero_observations': values.count(0), 'smallest_positive_observation': positive[0] if positive else None,
            'median_resolution': 'RESOLUTION_LIMITED' if median == 0 else 'NONZERO_RAW_INSTRUMENTED',
            'method': 'nearest rank; raw instrumentation included'}

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiler', default='g++')
    parser.add_argument('--events', type=int, default=20_000)
    parser.add_argument('--samples', type=int, default=31)
    parser.add_argument('--warmups', type=int, default=3)
    parser.add_argument('--seed', type=int, default=20261102)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if not 128 <= args.events <= 1_000_000 or not 1 <= args.samples <= 100 or not 0 <= args.warmups <= 20 or args.events * args.samples > 1_000_000:
        parser.error('events128..1m, samples1..100, warmups0..20, total observations <=1m required')
    compiler = shutil.which(args.compiler)
    if compiler is None:
        raise RuntimeError('compiler unavailable; no result emitted')
    hashes = {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in SOURCES}
    env = dict(os.environ)
    env['PATH'] = str(Path(compiler).parent) + os.pathsep + env.get('PATH', '')
    version = subprocess.run([compiler, '--version'], capture_output=True, text=True, check=True, env=env).stdout.splitlines()[0]
    flags = ['-std=c++20', '-O2', '-Wall', '-Wextra', '-Wpedantic', '-Werror']
    events = workload(args.events, args.seed)
    payload = ''.join(f'{s} {t} {q}\n' for s,t,q in events).encode('ascii')
    work = ROOT/'.build'
    work.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='flat-', dir=work) as temporary:
        tmp = Path(temporary).resolve()
        if not tmp.is_relative_to(work.resolve()):
            raise RuntimeError('temporary directory escaped checkout')
        data = tmp/'events.txt'
        data.write_bytes(payload)
        binary = tmp/('flat.exe' if os.name == 'nt' else 'flat')
        build = subprocess.run([compiler, *flags, str(ROOT/'flat_depth_benchmark.cpp'), '-o', str(binary)], capture_output=True, text=True, env=env, timeout=60)
        if build.returncode:
            raise RuntimeError('Compilation failed: ' + build.stderr)
        raw = subprocess.run([str(binary), str(data), str(args.samples), str(args.warmups)], capture_output=True, text=True, check=True, env=env, timeout=120)
        result = json.loads(raw.stdout)
    if int(result['checksum']) != reference(events):
        raise RuntimeError('Python/C++ checksum mismatch; report discarded')
    if result['event_count'] != args.events or result['reference_checks'] != args.events or len(result['event_ns']) != args.events * args.samples or len(result['empty_clock_pair_ns']) != args.events * args.samples or len(result['batch_ns']) != args.samples:
        raise RuntimeError('measurement denominator mismatch; report discarded')
    if result['ordinary_new_calls_hot_path'] != 0:
        raise RuntimeError('hot-path ordinary new allocation found; report discarded')
    if result['allocation_probe_control_calls'] != 1:
        raise RuntimeError('allocation probe control failed; report discarded')
    if hashes != {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in SOURCES}:
        raise RuntimeError('source changed while measuring; report discarded')
    report = {
        'schema_version': 1, 'experiment': 'bounded-flat-depth', 'sample_version': '1.2.0',
        'created_at_utc': datetime.now(timezone.utc).isoformat(), 'source_sha256': hashes,
        'environment': {'platform': platform.platform(), 'architecture': platform.machine(), 'cpu': platform.processor() or None, 'logical_cpus': os.cpu_count(), 'python': platform.python_version(), 'compiler': version, 'compiler_flags': flags},
        'workload': {'synthetic': True, 'event_count_per_sample': args.events, 'samples': args.samples, 'warmups': args.warmups, 'seed': args.seed, 'sha256': hashlib.sha256(payload).hexdigest(), 'shape': '128initial upserts populate64slots per side, then uniform random replacement and20percent delete; fixed disjoint tick bands'},
        'correctness': {'edge_checks_passed': True, 'C++_ordered_map_reference_states': args.events, 'all128depth_slots_compared_each_event': True, 'Python_dictionary_checksum_matches': True},
        'method': {'single_thread': True, 'clock': 'std::chrono::steady_clock', 'timed_scope': 'one normalized array update, top-of-book read and checksum consumption between two clock calls', 'excluded': 'input generation, text parsing, allocation of workload/timing vectors, book construction and reset, reference checks, serialization, process startup', 'allocation_probe_scope': 'ordinary replaceable global new/new[] calls during instrumented and aggregate timed loops; not malloc, aligned allocation or OS memory', 'percentile_unit': 'nanoseconds per instrumented event, pooled across samples', 'instrumentation': 'empty back-to-back clock-pair distribution measured separately; no subtraction, CPU affinity or isolated host', 'aggregate_scope': 'separate full-workload loop with one clock pair per batch; median batch time divided by event count is amortized cost, not an event percentile', 'price_scope': 'bid ticks1000..1063; ask ticks1100..1163; index bands cannot cross, unsupported ticks reject without resizing'},
        'event_summary_ns': summarize(result['event_ns']), 'empty_clock_summary_ns': summarize(result['empty_clock_pair_ns']),
        'batch_summary_ns': summarize(result['batch_ns']),
        'batch_p50_amortized_ns_per_event': summarize(result['batch_ns'])['p50'] / args.events if summarize(result['batch_ns'])['p50'] is not None else None,
        'raw_results': result,
        'limits': ['A bounded normalized-data implementation experiment, not the legacy replay API or employer code.', 'Individual clock calls and checksum work affect raw event timings; clock granularity can produce zero observations.', 'No parser, network, exchange sequencing/recovery, concurrency, order submission or production HFT latency is measured.', 'No comparison against the legacy map implementation is timed, so no speedup or language ranking is established.']}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    payload_json = (json.dumps(report, indent=2) + '\n').encode('utf-8')
    if args.output.suffix == '.gz':
        compressed = gzip.compress(payload_json, mtime=0)
        args.output.write_bytes(compressed)
        metadata = {k:v for k,v in report.items() if k != 'raw_results'}
        metadata['raw_result_metadata'] = {k:v for k,v in result.items() if not isinstance(v,list)}
        metadata['full_observation_archive'] = {'file':args.output.name, 'format':'gzip-compressed UTF-8 JSON', 'compressed_bytes':len(compressed), 'compressed_sha256':hashlib.sha256(compressed).hexdigest(), 'uncompressed_bytes':len(payload_json), 'uncompressed_sha256':hashlib.sha256(payload_json).hexdigest(), 'observations_preserved':True}
        args.output.with_suffix('').with_suffix('.meta.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8')
    else:
        args.output.write_bytes(payload_json)
    print(json.dumps({'passed': True, 'output': str(args.output), 'event_summary_ns': report['event_summary_ns'], 'empty_clock_summary_ns': report['empty_clock_summary_ns'], 'ordinary_new_calls_hot_path': result['ordinary_new_calls_hot_path']}))

if __name__ == '__main__':
    main()
