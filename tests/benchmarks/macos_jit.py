#!/usr/bin/env python3
"""Run all 19 original workloads through the native Apple Silicon JIT.

Each measurement starts a fresh process. Startup, synchronous tier compilation,
and guest execution are reported separately. Guest time after subtracting
compilation pauses is mixed-tier execution, not a steady-state measurement.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import re
import signal
import statistics
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('native_bench', Path(__file__).with_name('macos.py'))
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
sys.path.insert(0, str(ROOT/'scripts'))
spec = importlib.util.spec_from_file_location('native_driver', ROOT/'scripts/macos.py')
driver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(driver)

MODES = ('c', 'aotO2', 'jitBaseline', 'jitAdaptive', 'jitO2')
TITLES = dict(c='C -O2', aotO2='AOT -O2', jitBaseline='JIT baseline', jitAdaptive='JIT adaptive', jitO2='JIT starts -O2')

# Timers surround each program's actual entry, not process/loader startup.
# The C wrapper retains the original algorithm and command-line arguments.
TIMER = r'''
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <sys/resource.h>
static struct timespec zephyr_bench_start;
static void zephyr_bench_begin(void) {
    clock_gettime(CLOCK_MONOTONIC, &zephyr_bench_start);
}
static void zephyr_bench_end(void) {
    fflush(stdout);
    struct timespec end;
    clock_gettime(CLOCK_MONOTONIC, &end);
    double ms = (end.tv_sec-zephyr_bench_start.tv_sec)*1000.0
              + (end.tv_nsec-zephyr_bench_start.tv_nsec)/1000000.0;
    const char *path = getenv("ZEPHYR_BENCH_REPORT");
    if (!path) { fputs("benchmark report path missing\n",stderr); exit(1); }
    FILE *file = fopen(path,"w");
    if (!file) { perror("benchmark report"); exit(1); }
    struct rusage usage;
    if (getrusage(RUSAGE_SELF,&usage)) { perror("benchmark memory"); exit(1); }
    fprintf(file,"{\"guest_ms\":%.9f,\"execution_excluding_compilation_ms\":%.9f,\"peak_rss_bytes\":%ld}\n",ms,ms,usage.ru_maxrss);
    if (fclose(file)) { perror("benchmark report"); exit(1); }
}
'''


def build_native(mode, name, flags, work, sources):
    output = work/f'{name}-{mode}'
    started = time.perf_counter()
    if mode == 'c':
        original = sources/f'{name}.c'
        source = original.read_text()
        if not re.search(r'\bint\s+main\s*\(int\s+argc,\s*char\s*\*\s*\*\s*argv\)',source):
            raise ValueError('C timer wrapper requires the upstream argc/argv main signature')
        wrapper = work/f'{name}-timed.c'
        wrapper.write_text(TIMER+'\n#define main zephyr_benchmark_guest\n#include '+json.dumps(str(original))+
                           '\n#undef main\nint main(int argc, char **argv) {\n'
                           'zephyr_bench_begin();\nint status=zephyr_benchmark_guest(argc,argv);\n'
                           'zephyr_bench_end();\nreturn status;\n}\n')
        subprocess.run(['clang','-arch','arm64','-O2','-fwrapv','-ffp-contract=off',*flags.split(),str(wrapper),'-o',str(output)],check=True,capture_output=True)
    else:
        assembly = work/f'{name}-aot.s'
        driver.build(sources/f'{name}.zeph',assembly,['-O2'])
        main = work/f'{name}-aot-main.c'
        main.write_text(TIMER+(ROOT/'bootstrap/macos/main.c').read_text().replace('zephyr_entry();','zephyr_bench_begin();\n    zephyr_entry();\n    zephyr_bench_end();'))
        directory = ROOT/'bootstrap/macos'
        subprocess.run(['clang','-arch','arm64','-mmacosx-version-min=13.0','-O2','-Wall','-Wextra','-Werror','-I',str(directory),
                        str(assembly),str(directory/'darwin.c'),str(main),str(directory/'entry.s'),'-o',str(output)],check=True,capture_output=True)
    if output.read_bytes()[:8] != bytes.fromhex('cffaedfe0c000001'):
        raise ValueError('Reference executable is not ARM64 Mach-O')
    return output,(time.perf_counter()-started)*1000


def measure(mode, executable, source, argument, report, timeout, threshold):
    report.unlink(missing_ok=True)
    arguments = [argument] if argument else []
    env = dict(os.environ,ZEPHYR_BENCH_REPORT=str(report))
    if mode.startswith('jit'):
        flags = {'jitBaseline':['--jit-baseline'], 'jitAdaptive':[], 'jitO2':['-O2']}[mode]
        command = [str(ROOT/'zc'),'run','--jit-threshold',str(threshold),'--jit-report',str(report),*flags,str(source),*arguments]
    else:
        command = [str(executable),*arguments]
    started = time.perf_counter()
    process = subprocess.Popen(command,cwd=ROOT,env=env,
                               stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
    try:
        stdout,stderr = process.communicate(timeout=timeout)
    except (subprocess.TimeoutExpired, KeyboardInterrupt):
        os.killpg(process.pid,signal.SIGKILL)
        process.communicate()
        raise
    elapsed = (time.perf_counter()-started)*1000
    stderr = stderr.decode(errors='replace')
    if process.returncode:
        raise RuntimeError(f'{mode} exit {process.returncode}: {stderr[-3000:]}')
    if not report.is_file():
        raise RuntimeError(f'Missing native memory/timing report: {stderr[-1000:]}')
    profile = json.loads(report.read_text())
    if profile.get('errors'):
        raise RuntimeError(f'JIT failed to optimize: {profile["errors"]}')
    if mode.startswith('jit'):
        if profile['mode'] != 'native-arm64-jit' or profile['adaptive'] != (mode=='jitAdaptive'):
            raise RuntimeError('Wrong execution mode')
    guest = profile['guest_ms']
    compilation = profile.get('optimization_ms',0)+profile.get('failed_optimization_ms',0)
    execution = profile['execution_excluding_compilation_ms']
    if guest < 0 or execution < 0 or abs(guest-compilation-execution)>0.01:
        raise RuntimeError('Invalid guest time decomposition')
    return dict(totalMs=elapsed,guestMs=guest,executionMs=execution,
                startupMs=profile.get('startup_ms'),compilationMs=compilation,
                rssBytes=profile['peak_rss_bytes'],stdout=stdout.decode(errors='replace').strip(),
                promotedFunctions=[p['function'] for p in profile.get('promotions',[])],
                codeBytes=profile.get('code_bytes'),dataBytes=profile.get('data_bytes'))


def summarize(samples):
    result = {'samples':len(samples),'raw':samples,'peakRssBytes':max(sample['rssBytes'] for sample in samples)}
    for key in ('totalMs','guestMs','executionMs','startupMs','compilationMs'):
        values = [sample[key] for sample in samples if sample[key] is not None]
        if values:
            median = statistics.median(values)
            result[key] = dict(median=median,mad=statistics.median(abs(value-median) for value in values),values=values)
    result['promotedFunctions'] = sorted({function for sample in samples for function in sample['promotedFunctions']})
    return result


def checkpoint(results, output):
    passed = [entry for entry in results['benchmarks'].values() if entry['checksumOk'] and all('executionMs' in entry['modes'].get(mode,{}) for mode in MODES)]
    if len(passed)==19:
        results['summary'] = dict(workloadsPassed=19,
            timedExecutions=sum(measurement['samples'] for entry in passed for measurement in entry['modes'].values()),
            warmupExecutions=19*len(MODES),
            workloadsWithPromotions=sum(bool(entry['modes']['jitAdaptive']['promotedFunctions']) for entry in passed),
            adaptiveVsBaselineExecutionSpeedup=statistics.geometric_mean(entry['modes']['jitBaseline']['executionMs']['median']/entry['modes']['jitAdaptive']['executionMs']['median'] for entry in passed),
            adaptiveExecutionRelativeToC=statistics.geometric_mean(entry['modes']['jitAdaptive']['executionMs']['median']/entry['modes']['c']['executionMs']['median'] for entry in passed),
            adaptiveExecutionRelativeToAotO2=statistics.geometric_mean(entry['modes']['jitAdaptive']['executionMs']['median']/entry['modes']['aotO2']['executionMs']['median'] for entry in passed),
            jitO2ExecutionRelativeToC=statistics.geometric_mean(entry['modes']['jitO2']['executionMs']['median']/entry['modes']['c']['executionMs']['median'] for entry in passed),
            adaptiveColdProcessRelativeToC=statistics.geometric_mean(entry['modes']['jitAdaptive']['totalMs']['median']/entry['modes']['c']['totalMs']['median'] for entry in passed))
    temporary = output.with_suffix('.tmp')
    temporary.write_text(json.dumps(results,indent=2)+'\n')
    temporary.replace(output)
    lines = ['# Native Apple Silicon JIT benchmark','',
             f"Started: {results['startedUtc']}. Machine: {results['machine']}; macOS {results['macos']}; native ARM64.",'',
             f"All {results['workloadsRequested']} selected original workloads use their original arguments. Every measurement launches a fresh process. JIT warm-up runs do not preserve compiled tiers into later measurements.",
             '',f"One validation/warm-up per mode; up to {results['runsRequested']} rotated, interleaved timed samples. Per-mode cold-process timing budget: 30 seconds, with at least three samples. Normal scheduling; no fixed CPU affinity.",'',
             'C and AOT entry timers surround the actual program entry and include flushing output. JIT entry timing includes tier compilation pauses. **Execution** subtracts those pauses and includes baseline-to-optimized transitions and profiling overhead; it is not steady-state timing. All measurements validate their checksum.',
             '', f"C uses Clang -O2 with signed wraparound and no floating-point contraction. Fresh AOT -O2 is a reference. JIT baseline disables profiling; JIT adaptive uses a {results['threshold']:,}-call threshold; JIT starts -O2 compiles optimized before execution and has no adaptive profiling.",
             '', 'Cold-process totals include startup and compilation for JIT. C/AOT cold-process totals execute prebuilt binaries; their build times are separate. Memory uses getrusage(RUSAGE_SELF) at guest completion; JIT host RSS excludes compiler/assembler child-process peaks. These metrics are not combined into a single memory claim.', '']
    if 'summary' in results:
        s = results['summary']
        lines += [f"{s['workloadsPassed']} workloads passed, {s['timedExecutions']} timed executions plus {s['warmupExecutions']} warm-ups. Adaptive tier transitions occurred in {s['workloadsWithPromotions']} workloads.",'',
                  f"Across all workloads, execution-only geometric means: adaptive JIT speedup over JIT baseline {s['adaptiveVsBaselineExecutionSpeedup']:.3f}×; adaptive JIT time relative to C {s['adaptiveExecutionRelativeToC']:.3f}×; adaptive JIT time relative to fresh AOT -O2 {s['adaptiveExecutionRelativeToAotO2']:.3f}×; JIT starting -O2 time relative to C {s['jitO2ExecutionRelativeToC']:.3f}×.",'']
    lines += ['| Workload | C execution ms | AOT -O2 execution ms | JIT baseline execution ms | Adaptive execution ms | JIT starts -O2 execution ms | Adaptive compile pause ms | Adaptive startup ms | Adaptive total ms | Hot functions | Checksums |',
              '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|']
    for name,entry in results['benchmarks'].items():
        def value(mode,key):
            measurement = entry['modes'].get(mode,{})
            return f"{measurement[key]['median']:.2f}" if key in measurement else '—'
        hot = len(entry['modes'].get('jitAdaptive',{}).get('promotedFunctions',[]))
        lines.append(f"| {name} | {value('c','executionMs')} | {value('aotO2','executionMs')} | {value('jitBaseline','executionMs')} | {value('jitAdaptive','executionMs')} | {value('jitO2','executionMs')} | {value('jitAdaptive','compilationMs')} | {value('jitAdaptive','startupMs')} | {value('jitAdaptive','totalMs')} | {hot} | {'ok' if entry['checksumOk'] else 'pending / failed'} |")
    lines += ['',f"Status: {results['status']}. Raw samples, build times, memory, source hashes, and promoted-function names are in the JSON.",'']
    output.with_suffix('.md').write_text('\n'.join(lines))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--revision',default='398aadd')
    parser.add_argument('--runs',type=int,default=10)
    parser.add_argument('--timeout',type=int,default=300)
    parser.add_argument('--threshold',type=int,default=1000)
    parser.add_argument('--output',type=Path,default=ROOT/'tests/benchmarks/results/apple-silicon-jit-full.json')
    parser.add_argument('--workloads',nargs='+',help='Optional focused verification; default is all 19 workloads')
    options = parser.parse_args()
    driver.require_host()
    if options.runs<3:
        parser.error('At least three timed samples are required')
    suite = base.suite_from(options.revision)
    if options.workloads:
        names = set(options.workloads)
        suite = [entry for entry in suite if entry[0] in names]
        if names != {entry[0] for entry in suite}:
            parser.error('Unknown workload')
    output = options.output.resolve()
    output.parent.mkdir(parents=True,exist_ok=True)
    files = ['zc-macos','compiler/zc.zeph','compiler/optimizer.zeph','scripts/macos.py','scripts/macos/arm64.py','scripts/macos/jit.py',
             'bootstrap/macos/jit.c','bootstrap/macos/jit-entry.s','bootstrap/macos/darwin.c','tests/benchmarks/macos_jit.py']
    results = dict(startedUtc=datetime.now(timezone.utc).isoformat(),sourceRevision=base.metadata(['git','rev-parse',options.revision]),
                   machine=base.metadata(['sysctl','-n','machdep.cpu.brand_string']),macos=platform.mac_ver()[0],architecture=platform.machine(),
                   clang=base.metadata(['clang','--version']).splitlines()[0],python=sys.version,runsRequested=options.runs,
                   threshold=options.threshold,perModeColdProcessBudgetMs=30000,minimumSamples=3,workloadsRequested=len(suite),
                   fileHashes={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in files},status='running',benchmarks={})
    checkpoint(results,output)
    print('RESULTS',output,flush=True)
    with tempfile.TemporaryDirectory(prefix='zephyr-jit-benchmark-') as directory:
        work = Path(directory)
        sources = work/'sources'
        sources.mkdir()
        for index,(name,area,argument,flags) in enumerate(suite,1):
            print(f'[{index}/{len(suite)}] {name} argument={argument or "default"}',flush=True)
            entry = dict(area=area,argument=argument,modes={},checksumOk=False,sourceHashes={})
            results['benchmarks'][name] = entry
            for suffix in ('c','zeph'):
                content = base.git_source(options.revision,f'bench/{name}.{suffix}')
                (sources/f'{name}.{suffix}').write_bytes(content)
                entry['sourceHashes'][suffix] = hashlib.sha256(content).hexdigest()
            executables = {}
            for mode in ('c','aotO2'):
                executable,elapsed = build_native(mode,name,flags,work,sources)
                executables[mode] = executable
                entry['modes'][mode] = dict(buildMs=elapsed)
            expected = None
            samples = {mode:[] for mode in MODES}
            for mode in MODES:
                measurement = measure(mode,executables.get(mode),sources/f'{name}.zeph',argument,work/'profile.json',options.timeout,options.threshold)
                checksum = measurement.pop('stdout')
                if expected is None:
                    expected = checksum
                if checksum != expected:
                    raise RuntimeError(f'{name} {mode}: checksum mismatch')
                entry['modes'].setdefault(mode,{})['warmup'] = measurement
                print(f"  warm-up {TITLES[mode]}: execution {measurement['executionMs']:.2f} ms; total {measurement['totalMs']:.0f} ms; promotions {len(measurement['promotedFunctions'])}",flush=True)
                checkpoint(results,output)
            entry['checksum'] = expected
            entry['checksumOk'] = True
            for iteration in range(options.runs):
                # Rotate which mode runs first; preserve sequential execution.
                order = MODES[iteration%len(MODES):]+MODES[:iteration%len(MODES)]
                for mode in order:
                    if len(samples[mode])>=3 and sum(sample['totalMs'] for sample in samples[mode])>30000:
                        continue
                    measurement = measure(mode,executables.get(mode),sources/f'{name}.zeph',argument,work/'profile.json',options.timeout,options.threshold)
                    if measurement.pop('stdout') != expected:
                        raise RuntimeError(f'{name} {mode}: timed checksum changed')
                    samples[mode].append(measurement)
                    entry['modes'][mode].update(summarize(samples[mode]))
                    checkpoint(results,output)
                print(f'  round {iteration+1}/{options.runs}',flush=True)
            print(f"[{index}/{len(suite)}] {name}: OK; adaptive execution {entry['modes']['jitAdaptive']['executionMs']['median']:.2f} ms; C {entry['modes']['c']['executionMs']['median']:.2f} ms",flush=True)
            checkpoint(results,output)
    results['status'] = 'complete'
    results['finishedUtc'] = datetime.now(timezone.utc).isoformat()
    checkpoint(results,output)
    print('COMPLETE',output,flush=True)


if __name__=='__main__':
    main()
