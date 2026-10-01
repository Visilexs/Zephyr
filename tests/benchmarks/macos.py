#!/usr/bin/env python3
"""Run the upstream 19-workload suite on native Apple Silicon.

Sources are recovered into temporary storage from the original Git revision,
keeping auxiliary applications out of the cleaned checkout. Requires Clang;
Rust is included only when rustc is installed. No CPU affinity is claimed on
macOS. RSS is the maximum resident set of one workload process, not Windows
peak committed memory. Results checkpoint after every workload.
"""
import argparse
import ast
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import signal
import statistics
import subprocess
import tempfile
import time

ROOT=Path(__file__).resolve().parents[2]
LANGUAGES=('c','rust','zephyr','zephyrO2')
TITLES={'c':'C','rust':'Rust','zephyr':'Zephyr','zephyrO2':'Zephyr -O2'}

def git_source(revision,path):
    return subprocess.check_output(['git','show',f'{revision}:{path}'],cwd=ROOT)

def suite_from(revision):
    tree=ast.parse(git_source(revision,'bench/bench.py'))
    for item in tree.body:
        if isinstance(item,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='suite' for t in item.targets):
            return ast.literal_eval(item.value)
    raise ValueError('Original benchmark suite not found')

def metadata(command):
    result=subprocess.run(command,capture_output=True,text=True)
    return result.stdout.strip() if result.returncode==0 else 'unavailable'

def timed_run(executable,argument,timeout):
    start=time.perf_counter()
    process=subprocess.Popen(['/usr/bin/time','-l',str(executable),*([argument] if argument else [])],
                             stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
    try:
        stdout,stderr=process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid,signal.SIGKILL);process.communicate()
        raise RuntimeError(f'Exceeded {timeout}s per-process timeout')
    except BaseException:
        if process.poll() is None:
            os.killpg(process.pid,signal.SIGKILL);process.communicate()
        raise
    milliseconds=(time.perf_counter()-start)*1000
    stdout=stdout.decode(errors='replace').strip()
    stderr=stderr.decode(errors='replace')
    rss=re.search(r'^\s*(\d+)\s+maximum resident set size\s*$',stderr,re.M)
    if process.returncode:
        raise RuntimeError(f'Exit {process.returncode}: {stderr[-2000:]}')
    if not rss:
        raise RuntimeError(f'Native memory measurement unavailable: {stderr[-1000:]}')
    return {'ms':milliseconds,'stdout':stdout,'rssBytes':int(rss.group(1))}

def build(language,name,flags,work,sources):
    executable=work/f'{name}-{language}'
    if language=='c':
        # Define signed wraparound and prevent FMA contraction: Zephyr's integer
        # and scalar-float operations use those semantics.
        command=['clang','-arch','arm64','-O2','-fwrapv','-ffp-contract=off',*flags.split(),str(sources/f'{name}.c'),'-o',str(executable)]
    elif language=='rust':
        command=['rustc','-O','--target','aarch64-apple-darwin',str(sources/f'{name}.rs'),'-o',str(executable)]
    else:
        command=[str(ROOT/'zc'),'--rt',*(['-O2'] if language=='zephyrO2' else []),str(sources/f'{name}.zeph'),str(executable)]
    start=time.perf_counter()
    result=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,timeout=600)
    elapsed=(time.perf_counter()-start)*1000
    if result.returncode or not executable.exists():
        raise RuntimeError((result.stdout+result.stderr)[-3000:])
    with executable.open('rb') as file:
        if file.read(8)!=bytes.fromhex('cffaedfe0c000001'):
            raise RuntimeError('Build did not produce native ARM64 Mach-O')
    return executable,elapsed

def summarize(samples):
    values=[s['ms'] for s in samples]
    median=statistics.median(values)
    return {'medianMs':median,'madMs':statistics.median(abs(v-median) for v in values),
            'minMs':min(values),'timesMs':values,'samples':len(values),
            'peakRssBytes':max(s['rssBytes'] for s in samples)}

def write_results(results,path):
    complete=results['status']=='complete'
    if complete:
        benchmarks=list(results['benchmarks'].values())
        results['summary']={
            'workloadsPassed':len(benchmarks),
            'timedExecutions':sum(m['samples'] for b in benchmarks for m in b['languages'].values()),
            'optimizedSpeedupGeometricMean':statistics.geometric_mean(b['languages']['zephyr']['medianMs']/b['languages']['zephyrO2']['medianMs'] for b in benchmarks),
            'optimizedRuntimeRelativeToCGeometricMean':statistics.geometric_mean(b['languages']['zephyrO2']['medianMs']/b['languages']['c']['medianMs'] for b in benchmarks),
        }
    temporary=path.with_suffix('.tmp')
    temporary.write_text(json.dumps(results,indent=2)+'\n');temporary.replace(path)
    report=path.with_suffix('.md')
    lines=['# Native Apple Silicon benchmark','',f"Run: {results['startedUtc']}. Machine: {results['machine']}. macOS {results['macos']}.",'']
    if complete:
        summary=results['summary']
        lines += [f"All {summary['workloadsPassed']} workloads passed with matching checksums over {summary['timedExecutions']} timed executions and one warm-up per build. Optimized Zephyr was {summary['optimizedSpeedupGeometricMean']:.2f}× faster than its baseline; C was {summary['optimizedRuntimeRelativeToCGeometricMean']:.2f}× faster than optimized Zephyr. These comparisons use geometric means across workloads.",'']
    lines += [
           f"All 19 upstream workloads use their original arguments. One warm-up and up to {results['runsRequested']} interleaved timed runs per build; the original 30-second accumulated timing budget allows a minimum of three samples for slow builds.",
           '', 'C uses Apple Clang -O2, defined signed wraparound, and disabled floating-point contraction. Zephyr uses the native ARM64 driver. Rust is included when installed. Processes use normal scheduling, without fixed CPU affinity. Memory is peak resident memory of each workload process.',
           '', 'Compile times include the complete build, including the native driver, instruction selection, assembly, and linking. Runtime times include process startup. Timings are valid only where every checksum agrees.',
           '', '| Workload | Zephyr ms | -O2 ms | C ms | Rust ms | -O2/C | -O2 RSS MB | Samples Z/Z-O2/C/R | Checksums |',
           '|---|---:|---:|---:|---:|---:|---:|---|---|']
    for name,b in results['benchmarks'].items():
        measurements=b['languages']
        def ms(language):
            return f"{measurements[language]['medianMs']:.1f}" if 'medianMs' in measurements.get(language,{}) else '—'
        z=measurements.get('zephyrO2',{});c=measurements.get('c',{})
        valid=b.get('checksumOk',False)
        ratio=f"{z['medianMs']/c['medianMs']:.2f}" if valid and 'medianMs' in z and 'medianMs' in c else '—'
        peak=f"{z['peakRssBytes']/1048576:.1f}" if 'peakRssBytes' in z else '—'
        samples='/'.join(str(measurements.get(l,{}).get('samples','—')) for l in ('zephyr','zephyrO2','c','rust'))
        state='ok' if valid else 'FAILED'
        lines.append(f"| {name} | {ms('zephyr')} | {ms('zephyrO2')} | {ms('c')} | {ms('rust')} | {ratio} | {peak} | {samples} | {state} |")
    lines += ['',f"Status: {results['status']}. Rust: {results['toolchains']['rust']}.",'','Errors and raw samples are recorded in the accompanying JSON. Windows results use different compiler, instruction-set, scheduling, and memory measurements and should not be compared directly.','']
    report.write_text('\n'.join(lines))

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--revision',default='398aadd')
    parser.add_argument('--runs',type=int,default=10)
    parser.add_argument('--timeout',type=int,default=300)
    parser.add_argument('--output',type=Path)
    options=parser.parse_args()
    if platform.system()!='Darwin' or platform.machine()!='arm64':
        parser.error('Requires native Apple Silicon macOS')
    if options.runs<3: parser.error('Use at least three timed runs')
    revision=subprocess.check_output(['git','rev-parse',options.revision],cwd=ROOT,text=True).strip()
    suite=suite_from(revision)
    assert len(suite)==19
    languages=[language for language in LANGUAGES if language!='rust' or shutil.which('rustc')]
    output=options.output or ROOT/'tests/benchmarks/results'/f"macos-{datetime.now():%Y%m%d-%H%M%S}.json"
    output=output.resolve();output.parent.mkdir(parents=True,exist_ok=True)
    results={'startedUtc':datetime.now(timezone.utc).isoformat(),'sourceRevision':revision,
             'seedSha256':hashlib.sha256((ROOT/'zc-macos').read_bytes()).hexdigest(),
             'machine':metadata(['sysctl','-n','machdep.cpu.brand_string']),
             'macos':platform.mac_ver()[0],'architecture':platform.machine(),
             'memoryBytes':metadata(['sysctl','-n','hw.memsize']),
             'runsRequested':options.runs,'perLanguageBudgetMs':30000,'minimumBudgetSamples':3,
             'cpuAffinity':'not fixed','scheduling':'normal','memoryMetric':'process peak resident set in bytes',
             'toolchains':{'c':metadata(['clang','--version']).splitlines()[0],
                           'rust':metadata(['rustc','--version']) if shutil.which('rustc') else 'unavailable; rustc not installed'},
             'status':'running','benchmarks':{}}
    write_results(results,output)
    print('RESULTS',output,flush=True)
    print(f"Machine: {results['machine']}; languages: {', '.join(languages)}; all {len(suite)} workloads",flush=True)
    with tempfile.TemporaryDirectory(prefix='zephyr-native-benchmark-') as directory:
        work=Path(directory);sources=work/'sources';sources.mkdir()
        for index,(name,area,argument,flags) in enumerate(suite,1):
            print(f'[{index}/{len(suite)}] {name} argument={argument or "default"}: building',flush=True)
            entry={'area':area,'argument':argument,'languages':{},'checksumOk':False}
            results['benchmarks'][name]=entry
            executables={}
            for language in languages:
                suffix={'c':'c','rust':'rs'}.get(language,'zeph')
                source=sources/f'{name}.{suffix}'
                if not source.exists(): source.write_bytes(git_source(revision,f'bench/{name}.{suffix}'))
                try:
                    executable,compile_ms=build(language,name,flags,work,sources)
                    warmup=timed_run(executable,argument,options.timeout)
                    entry['languages'][language]={'compileMs':compile_ms,'checksum':warmup['stdout'],'warmupMs':warmup['ms'],'warmupRssBytes':warmup['rssBytes']}
                    executables[language]=executable
                    checksum=warmup['stdout']
                    preview=checksum if len(checksum)<=120 else f"sha256:{hashlib.sha256(checksum.encode()).hexdigest()} ({len(checksum)} characters)"
                    print(f"  {TITLES[language]}: warm-up {warmup['ms']:.0f} ms; checksum {preview}",flush=True)
                except (RuntimeError,subprocess.TimeoutExpired) as error:
                    entry['languages'][language]={'error':str(error)}
                    print(f'  FAILED {TITLES[language]}: {error}',flush=True)
                write_results(results,output)
            checksums={v.get('checksum') for v in entry['languages'].values() if 'checksum' in v}
            entry['checksumOk']=len(executables)==len(languages) and len(checksums)==1
            samples={language:[] for language in executables}
            for run in range(options.runs):
                for language,executable in executables.items():
                    if 'error' in entry['languages'][language]: continue
                    if len(samples[language])>=3 and sum(s['ms'] for s in samples[language])>30000: continue
                    try:
                        sample=timed_run(executable,argument,options.timeout)
                        if sample['stdout']!=entry['languages'][language]['checksum']:
                            raise RuntimeError(f"Checksum changed during timed run: {sample['stdout']}")
                        samples[language].append(sample)
                        entry['languages'][language].update(summarize(samples[language]))
                    except RuntimeError as error:
                        entry['languages'][language]['error']=str(error);entry['checksumOk']=False
                        print(f'  FAILED timed {language}: {error}',flush=True)
                write_results(results,output)
                if run in (2,5,9): print(f'  timing round {run+1}/{options.runs}',flush=True)
            summary='; '.join(f"{TITLES[l]} {m['medianMs']:.1f}±{m['madMs']:.1f} ms ({m['samples']} samples)" for l,m in entry['languages'].items() if 'medianMs' in m)
            print(f"[{index}/{len(suite)}] {name}: {'OK' if entry['checksumOk'] else 'FAILED'}; {summary}",flush=True)
            write_results(results,output)
    results['status']='complete' if all(b['checksumOk'] for b in results['benchmarks'].values()) else 'complete with failures'
    results['finishedUtc']=datetime.now(timezone.utc).isoformat()
    write_results(results,output)
    print(results['status'].upper(),output,flush=True)
    return 0 if results['status']=='complete' else 1

if __name__=='__main__': raise SystemExit(main())
