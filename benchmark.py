"""Measure the same synthetic replay contract as benchmark.cpp."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import sys
import time
from book_replay import Book

def peak_resident_bytes() -> int | None:
    try:
        if os.name == 'nt':
            import ctypes
            from ctypes import wintypes
            class Counters(ctypes.Structure):
                _fields_=[('cb',wintypes.DWORD),('PageFaultCount',wintypes.DWORD)]+[(n,ctypes.c_size_t) for n in ('PeakWorkingSetSize','WorkingSetSize','QuotaPeakPagedPoolUsage','QuotaPagedPoolUsage','QuotaPeakNonPagedPoolUsage','QuotaNonPagedPoolUsage','PagefileUsage','PeakPagefileUsage')]
            info=Counters();info.cb=ctypes.sizeof(info)
            kernel=ctypes.WinDLL('kernel32',use_last_error=True)
            kernel.GetCurrentProcess.restype=wintypes.HANDLE
            psapi=ctypes.WinDLL('psapi',use_last_error=True)
            psapi.GetProcessMemoryInfo.argtypes=[wintypes.HANDLE,ctypes.POINTER(Counters),wintypes.DWORD]
            psapi.GetProcessMemoryInfo.restype=wintypes.BOOL
            if not psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(),ctypes.byref(info),info.cb):return None
            value=info.PeakWorkingSetSize
        else:
            import resource
            value=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)
        return int(value) if value>0 else None
    except (OSError,AttributeError,ImportError):
        return None

def measure(records: list[str],samples: int,warmups: int) -> dict:
    def run():
        book=Book();chars=0;last=''
        for record in records:
            last=book.process(record) or ''
            chars+=len(last)
        return chars,last
    expected=run()
    for _ in range(warmups):
        if run()!=expected:raise RuntimeError('unstable warmup')
    durations=[]
    for _ in range(samples):
        start=time.perf_counter_ns();actual=run();elapsed=time.perf_counter_ns()-start
        if actual!=expected or elapsed<=0:raise RuntimeError('unstable replay or invalid clock')
        durations.append(elapsed)
    return {'language':'Python','event_count':len(records),'output_chars':expected[0],'final_state':expected[1],'peak_resident_bytes':peak_resident_bytes(),'batch_ns':durations}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('input',type=Path);parser.add_argument('samples',type=int);parser.add_argument('warmups',type=int);args=parser.parse_args()
    if not 3<=args.samples<=1000 or not 0<=args.warmups<=100:parser.error('invalid measurement counts')
    records=[line for line in args.input.read_text(encoding='ascii').splitlines() if line]
    if not records:parser.error('empty input')
    print(json.dumps(measure(records,args.samples,args.warmups)))
