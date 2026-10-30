"""Correctness-gated synthetic replay measurements. Python stdlib only."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import random
import shutil
import subprocess
import sys
import tempfile
from verify import verify

ROOT=Path(__file__).resolve().parent
CODE=['book.hpp','book_replay.cpp','book_replay.py','benchmark.cpp','benchmark.py','run_benchmark.py','verify.py','fixtures.json']

def stream(count: int,seed: int) -> list[str]:
    rng=random.Random(seed);rows=['S 1 100 5 200 5']
    for seq in range(2,count+1):
        side=rng.choice(('B','A'));price=rng.randint(90,110) if side=='B' else rng.randint(190,210)
        rows.append(f'U {seq} {side} {price} {rng.randint(1,1000)}')
    return rows

def percentile(values: list[int],p: float) -> int:
    if not values or not 0<p<=1 or any(type(x) is not int or x<=0 for x in values):
        raise ValueError('positive integer timings and a valid percentile required')
    return sorted(values)[math.ceil(p*len(values))-1]

def summarize(row: dict,events: int,samples: int) -> dict:
    times=row['batch_ns']
    if row['event_count']!=events or len(times)!=samples:raise ValueError('measurement count mismatch')
    p50,p95,p99=[percentile(times,p) for p in (.5,.95,.99)]
    memory=row.get('peak_resident_bytes')
    if memory is not None and (type(memory) is not int or memory<=0):raise ValueError('invalid resident-memory reading')
    return {**row,'batch_percentiles_ns':{'p50':p50,'p95':p95,'p99':p99},
            'batch_p50_amortized_ns_per_event':p50/events,'batch_p50_events_per_second':events*1e9/p50,
            'percentile_method':f'nearest rank of {samples} batch durations; tail resolution is 1/{samples}',
            'memory_scope':'whole process peak resident/working-set bytes, including runtime and retained input; null means unavailable'}

def committed_source(hashes: dict[str,str]) -> str | None:
    try:
        for name,sha in hashes.items():
            result=subprocess.run(['git','show','HEAD:'+name],cwd=ROOT,capture_output=True,check=True)
            if hashlib.sha256(result.stdout).hexdigest()!=sha:return None
        return subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,capture_output=True,text=True,check=True).stdout.strip()
    except (OSError,subprocess.SubprocessError):return None

def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiler',default='g++');parser.add_argument('--events',type=int,default=20000)
    parser.add_argument('--samples',type=int,default=31);parser.add_argument('--warmups',type=int,default=3)
    parser.add_argument('--seed',type=int,default=20261030);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if not 1000<=args.events<=1000000 or not 3<=args.samples<=1000 or not 0<=args.warmups<=100:parser.error('counts outside documented bounds')
    compiler=shutil.which(args.compiler)
    if compiler is None:raise RuntimeError('compiler unavailable; no benchmark result is produced')
    hashes={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in CODE}
    source_commit=committed_source(hashes)
    validation=verify(compiler)
    env=dict(os.environ);env['PATH']=str(Path(compiler).parent)+os.pathsep+env.get('PATH','')
    work=ROOT/'.build';work.mkdir(exist_ok=True)
    payload=('\n'.join(stream(args.events,args.seed))+'\n').encode('ascii')
    with tempfile.TemporaryDirectory(prefix='measurement-',dir=work) as temporary:
        # This is an agent-created temporary directory within this checkout.
        temp=Path(temporary).resolve()
        if not temp.is_relative_to(work.resolve()):raise RuntimeError('temporary path escaped checkout')
        data=temp/'stream.txt';data.write_bytes(payload)
        cpp=temp/('replay.exe' if os.name=='nt' else 'replay')
        bench=temp/('bench.exe' if os.name=='nt' else 'bench')
        flags=['-std=c++20','-O2','-Wall','-Wextra','-Wpedantic','-Werror']
        for source,target in [('book_replay.cpp',cpp),('benchmark.cpp',bench)]:
            extra=['-lpsapi'] if os.name=='nt' and source=='benchmark.cpp' else []
            build=subprocess.run([compiler,*flags,str(ROOT/source),'-o',str(target),*extra],capture_output=True,env=env,timeout=60)
            if build.returncode:raise RuntimeError('Compilation failed: '+build.stderr.decode('utf-8','replace'))
        # Full untimed output parity supplements the independent fixed fixtures.
        outputs=[]
        for command in [[str(cpp)],[sys.executable,str(ROOT/'book_replay.py')]]:
            outputs.append(subprocess.run(command,input=payload,capture_output=True,check=True,env=env,timeout=60).stdout.replace(b'\r\n',b'\n'))
        if outputs[0]!=outputs[1] or len(outputs[0].splitlines())!=args.events:raise RuntimeError('full dataset replay comparison failed')
        rows=[]
        for command in [[str(bench)],[sys.executable,str(ROOT/'benchmark.py')]]:
            result=subprocess.run([*command,str(data),str(args.samples),str(args.warmups)],capture_output=True,text=True,encoding='utf-8',check=True,env=env,timeout=180)
            rows.append(summarize(json.loads(result.stdout),args.events,args.samples))
        if (rows[0]['output_chars'],rows[0]['final_state'])!=(rows[1]['output_chars'],rows[1]['final_state']):raise RuntimeError('timed replay outputs differ')
    after={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in CODE}
    if after!=hashes:raise RuntimeError('Source changed during measurement; result is discarded')
    report={'benchmark_schema_version':1,'sample_version':'1.1.0','created_at_utc':datetime.now(timezone.utc).isoformat(),
      'source_commit':source_commit,'source_sha256':hashes,
      'environment':{'platform':platform.platform(),'architecture':platform.machine(),'cpu':platform.processor() or None,'logical_cpus':os.cpu_count(),'python':platform.python_version(),'compiler':validation['compiler'],'compiler_flags':flags},
      'dataset':{'synthetic':True,'events':args.events,'seed':args.seed,'sha256':hashlib.sha256(payload).hexdigest(),'shape':'one snapshot then positive-quantity updates over 21 bid and 21 ask prices'},
      'method':{'samples':args.samples,'warmups':args.warmups,'timed_scope':'book creation, ASCII parsing, state update, status formatting, output-length consumption and book teardown; input loading and process startup excluded','execution':'single thread; sequential C++ then Python; no CPU pinning or isolated machine','percentile_scope':'batch durations, not individual-event or exchange/order latency','memory_scope':'whole process high-water resident/working set, not engine-only allocations'},
      'correctness':{'passed':True,'fixture_scenarios':validation['fixture_scenarios'],'expected_state_checks_per_language':validation['expected_state_checks_per_language'],'generated_comparison_events':validation['generated_comparison_events'],'benchmark_dataset_output_sha256':hashlib.sha256(outputs[0]).hexdigest()},
      'results':rows,'limits':['Independent synthetic teaching material, not employer code or production HFT evidence.','Results compare these implementations (ordered maps vs dictionaries), not programming languages generally.','Small-sample tail percentiles are descriptive; no latency SLA, regression threshold or venue round trip is claimed.','Process memory includes language/runtime and retained input; readings are not allocator or leak measurements.']}
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'passed':True,'report':str(args.output),'events':args.events,'samples':args.samples,'source_commit':report['source_commit']}))

if __name__=='__main__':main()
