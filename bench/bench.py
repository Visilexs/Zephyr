"""Zephyr benchmark harness.

  python bench/bench.py run      [--runs 10] [--only a,b] [--languages c,rust,zephyr,zephyrO2]
  python bench/bench.py compare  [OLD.json NEW.json]      (default: the two newest results)
  python bench/bench.py ab       zcA.exe zcB.exe [--runs 10] [--only a,b]
  python bench/bench.py compile  [--function-count 200] [--function-depth 200] [--runs 5]

run: every workload is the same algorithm in Zephyr, C (gcc -O2) and Rust
(rustc -O). Each program prints one checksum line, and all languages must agree
before any timing is trusted. Each program gets one warm-up run, then --runs
timed runs, interleaved across languages so drift hits every language equally.
Runs are pinned to one logical CPU at high priority. The results are saved to
bench/results/<commit>-<time>.json.

ab: -O2 on the same workloads with two compilers, runs interleaved A, B, A, B.
zc reads compiler/runtime.zeph and lib/ from next to its own exe, so each
compiler must sit in its own directory with its own runtime.

compile: compile-time scaling on generated call chains (see compilegen.py), in
microseconds per generated function, plus zc compiling itself. Not pinned to a
CPU, since several of the compilers are multi-threaded.
"""
import argparse
import ctypes
import ctypes.wintypes
import datetime
import json
import os
import platform
import statistics
import subprocess
import sys
import tempfile
import time

benchDirectory = os.path.dirname(os.path.abspath(__file__))
repoRoot = os.path.dirname(benchDirectory)
resultsDirectory = os.path.join(benchDirectory, "results")
gccDirectory = r"C:\msys64\ucrt64\bin"

# name, area, workload argument, extra gcc flags. Arguments are sized so the
# fastest language runs for at least ~250 ms, well above process start-up noise.
suite = [
    ("fib", "recursion", "43", ""),
    ("matmul", "integer SIMD", "1100", ""),
    ("mandel", "float compute", "1700", "-ffp-contract=off"),
    ("sort", "sorting", "6000000", ""),
    ("strings", "alloc / GC", "4000000", ""),
    ("hashmap", "hash map", "32000000", ""),
    ("cube", "rasterization", "80000", "-ffp-contract=off -lm"),
    ("pi", "bignum", "40000", ""),
    ("liquid", "fluid / neighbours", "100", "-ffp-contract=off -lm"),
    ("shapes", "dynamic dispatch", "600000", "-ffp-contract=off -lm"),
    ("closures", "closures / HOFs", "600000", ""),
    ("wordfreq", "string hash map", "14000000", ""),
    ("nbody", "struct floats", "200", "-ffp-contract=off -lm"),
    ("lexer", "tokenizer", "2500000", ""),
    ("vectors", "small structs", "35000", "-ffp-contract=off"),
    ("dispatch", "megamorphic dispatch", "", ""),
    ("records", "struct records", "", ""),
    ("strbuild", "string building", "", ""),
    ("bintrees", "binary trees", "", ""),
]
allLanguages = ["c", "rust", "zephyr", "zephyrO2"]
languageTitles = {"c": "C", "rust": "Rust", "zephyr": "Zephyr", "zephyrO2": "Zephyr -O2"}

# ---------------------------------------------------------------------------
# Process control (Windows): high priority, pinned CPU, peak working set.

highPriorityClass = 0x00000080
pinnedCpuMask = 1 << 4  # logical CPU 4: a physical core other than core 0, which takes most interrupts


createSuspended = 0x00000004
jobKillOnClose = 0x00002000
jobExtendedLimitInformationClass = 9


class JobBasicLimitInformation(ctypes.Structure):
    _fields_ = [("perProcessUserTimeLimit", ctypes.c_int64), ("perJobUserTimeLimit", ctypes.c_int64),
                ("limitFlags", ctypes.wintypes.DWORD), ("minimumWorkingSetSize", ctypes.c_size_t),
                ("maximumWorkingSetSize", ctypes.c_size_t), ("activeProcessLimit", ctypes.wintypes.DWORD),
                ("affinity", ctypes.c_size_t), ("priorityClass", ctypes.wintypes.DWORD), ("schedulingClass", ctypes.wintypes.DWORD)]


class JobExtendedLimitInformation(ctypes.Structure):
    _fields_ = [("basicLimitInformation", JobBasicLimitInformation), ("ioCounters", ctypes.c_uint64 * 6),
                ("processMemoryLimit", ctypes.c_size_t), ("jobMemoryLimit", ctypes.c_size_t),
                ("peakProcessMemoryUsed", ctypes.c_size_t), ("peakJobMemoryUsed", ctypes.c_size_t)]


kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
kernel32.CreateJobObjectW.restype = ctypes.wintypes.HANDLE
kernel32.CreateJobObjectW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p]
kernel32.AssignProcessToJobObject.argtypes = [ctypes.wintypes.HANDLE, ctypes.wintypes.HANDLE]
kernel32.SetInformationJobObject.argtypes = [ctypes.wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, ctypes.wintypes.DWORD]
kernel32.QueryInformationJobObject.argtypes = [ctypes.wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, ctypes.wintypes.DWORD, ctypes.c_void_p]
kernel32.CloseHandle.argtypes = [ctypes.wintypes.HANDLE]
ntdll = ctypes.WinDLL("ntdll")
ntdll.NtResumeProcess.argtypes = [ctypes.wintypes.HANDLE]


def pinHarness():
    # Children inherit the affinity mask, so pinning the harness pins every run.
    kernel32.SetProcessAffinityMask(ctypes.wintypes.HANDLE(-1), ctypes.c_size_t(pinnedCpuMask))


def runTimed(argumentList, workingDirectory=None, timeoutSeconds=300):
    """Runs one process tree; returns (wallMs, stdout, peakKb, exitCode).

    The process starts suspended inside a job object, so peakKb is the peak
    committed memory of the whole tree (gcc's cc1, rustc's workers), and a
    timeout kills every descendant.
    """
    job = kernel32.CreateJobObjectW(None, None)
    limits = JobExtendedLimitInformation()
    limits.basicLimitInformation.limitFlags = jobKillOnClose
    kernel32.SetInformationJobObject(job, jobExtendedLimitInformationClass, ctypes.byref(limits), ctypes.sizeof(limits))
    startTime = time.perf_counter()
    process = subprocess.Popen(argumentList, cwd=workingDirectory, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               creationflags=highPriorityClass | createSuspended)
    kernel32.AssignProcessToJobObject(job, int(process._handle))
    ntdll.NtResumeProcess(int(process._handle))
    try:
        standardOutput, standardError = process.communicate(timeout=timeoutSeconds)
    except subprocess.TimeoutExpired:
        kernel32.CloseHandle(job)
        process.communicate()
        raise RuntimeError(f"timed out after {timeoutSeconds}s: {' '.join(argumentList)}")
    wallMs = (time.perf_counter() - startTime) * 1000
    kernel32.QueryInformationJobObject(job, jobExtendedLimitInformationClass, ctypes.byref(limits), ctypes.sizeof(limits), None)
    kernel32.CloseHandle(job)
    peakKb = limits.peakJobMemoryUsed // 1024
    output = standardOutput.decode(errors="replace").strip()
    if process.returncode != 0:
        output += "\n" + standardError.decode(errors="replace").strip()
    return wallMs, output, peakKb, process.returncode


def summarize(times):
    median = statistics.median(times)
    medianAbsoluteDeviation = statistics.median(abs(value - median) for value in times)
    return {"times": [round(value, 3) for value in times], "medianMs": round(median, 3), "minMs": round(min(times), 3),
            "madMs": round(medianAbsoluteDeviation, 3)}


def gitCommit():
    try:
        commit = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=repoRoot, text=True).strip()
        dirty = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", "compiler", "bench", "lib", "std"], cwd=repoRoot).returncode != 0
        return commit + ("-dirty" if dirty else "")
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def selectedSuite(onlyNames):
    if not onlyNames:
        return suite
    wanted = onlyNames.split(",")
    unknownNames = set(wanted) - {entry[0] for entry in suite}
    if unknownNames:
        sys.exit(f"unknown benchmark(s): {', '.join(sorted(unknownNames))}")
    return [entry for entry in suite if entry[0] in wanted]


def buildExecutable(language, benchmarkName, gccFlags, outputDirectory, zephyrCompiler):
    """Compiles one workload; returns (exePath, compileMs) or (None, error)."""
    sourceBase = os.path.join(benchDirectory, benchmarkName)
    exePath = os.path.join(outputDirectory, f"{benchmarkName}_{language}.exe")
    if language == "c":
        command = [os.path.join(gccDirectory, "gcc.exe"), "-O2", *gccFlags.split(), sourceBase + ".c", "-o", exePath]
    elif language == "rust":
        command = ["rustc", "-O", sourceBase + ".rs", "-o", exePath]
    else:
        optimizeFlags = ["-O2"] if language == "zephyrO2" else []
        command = [zephyrCompiler, "--rt", *optimizeFlags, sourceBase + ".zeph", exePath]
    environment = dict(os.environ, PATH=gccDirectory + os.pathsep + os.environ["PATH"])
    startTime = time.perf_counter()
    completed = subprocess.run(command, cwd=repoRoot, capture_output=True, text=True, env=environment)
    compileMs = (time.perf_counter() - startTime) * 1000
    if completed.returncode != 0 or not os.path.exists(exePath):
        return None, (completed.stdout + completed.stderr).strip()[-500:]
    return exePath, compileMs


languageBudgetMs = 30000


def measureWorkloads(executables, workloadArgument, runCount):
    """executables: {label: exePath}. Warm-up (checksum) run, then interleaved timed runs."""
    measurements = {}
    for label, exePath in executables.items():
        _, output, _, exitCode = runTimed([exePath] + ([workloadArgument] if workloadArgument else []))
        measurements[label] = {"checksum": output if exitCode == 0 else f"EXIT {exitCode}: {output}", "times": [], "peakKb": 0}
    for _ in range(runCount):
        for label, exePath in executables.items():
            spentMs = sum(measurements[label]["times"])
            if len(measurements[label]["times"]) >= 3 and spentMs > languageBudgetMs:
                continue  # a very slow build (e.g. baseline vectors, ~17 s per run) keeps 3 samples rather than 10
            wallMs, _, peakKb, _ = runTimed([exePath] + ([workloadArgument] if workloadArgument else []))
            measurements[label]["times"].append(wallMs)
            measurements[label]["peakKb"] = max(measurements[label]["peakKb"], peakKb)
    for label, measurement in measurements.items():
        measurement.update(summarize(measurement.pop("times")))
    return measurements


def formatRatio(numerator, denominator):
    return f"{numerator / denominator:.2f}" if numerator and denominator else "-"


# ---------------------------------------------------------------------------
# run

def commandRun(options):
    zephyrCompiler = os.path.abspath(options.compiler)
    languages = options.languages.split(",")
    pinHarness()
    results = {"commit": gitCommit(), "time": datetime.datetime.now().isoformat(timespec="seconds"),
               "machine": platform.processor(), "compiler": zephyrCompiler, "runs": options.runs, "benchmarks": {}}
    anyMismatch = False
    with tempfile.TemporaryDirectory(prefix="zbench_") as outputDirectory:
        for benchmarkName, area, workloadArgument, gccFlags in selectedSuite(options.only):
            executables, compileTimes = {}, {}
            for language in languages:
                exePath, compileResult = buildExecutable(language, benchmarkName, gccFlags, outputDirectory, zephyrCompiler)
                if exePath is None:
                    print(f"  {benchmarkName}: {languageTitles[language]} build failed: {compileResult}", file=sys.stderr)
                    continue
                executables[language], compileTimes[language] = exePath, round(compileResult, 1)
            measurements = measureWorkloads(executables, workloadArgument, options.runs)
            checksums = {measurement["checksum"] for measurement in measurements.values()}
            checksumOk = len(checksums) == 1
            anyMismatch |= not checksumOk
            for language, measurement in measurements.items():
                measurement["compileMs"] = compileTimes[language]
            results["benchmarks"][benchmarkName] = {"area": area, "argument": workloadArgument, "checksumOk": checksumOk,
                                                    "languages": measurements}
            medians = "  ".join(f"{languageTitles[language]} {measurement['medianMs']:.0f}±{measurement['madMs']:.0f}"
                                for language, measurement in measurements.items())
            print(f"{benchmarkName:10} {'ok      ' if checksumOk else 'MISMATCH'} {medians}", flush=True)
            if not checksumOk:
                for language, measurement in measurements.items():
                    print(f"    {languageTitles[language]}: {measurement['checksum']}")
    os.makedirs(resultsDirectory, exist_ok=True)
    resultPath = os.path.join(resultsDirectory, f"{results['commit']}-{datetime.datetime.now():%Y%m%d-%H%M%S}.json")
    with open(resultPath, "w") as resultFile:
        json.dump(results, resultFile, indent=1)
    printRunTable(results)
    print(f"\nsaved {os.path.relpath(resultPath, repoRoot)}")
    return 1 if anyMismatch else 0


def printRunTable(results):
    print(f"\nMedian of {results['runs']} runs in ms (± median absolute deviation), commit {results['commit']}.\n")
    print("| area | Zephyr | -O2 | C | Rust | -O2/C | -O2/Rust | -O2 peak MB | C peak MB | checksum |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|---:|---|")
    for benchmark in results["benchmarks"].values():
        languages = benchmark["languages"]
        median = {language: languages[language]["medianMs"] if language in languages else None for language in allLanguages}
        cells = [f"{median[language]:.0f}" if median[language] else "-" for language in ("zephyr", "zephyrO2", "c", "rust")]
        peakO2 = f"{languages['zephyrO2']['peakKb'] / 1024:.1f}" if "zephyrO2" in languages else "-"
        peakC = f"{languages['c']['peakKb'] / 1024:.1f}" if "c" in languages else "-"
        print(f"| {benchmark['area']} | {' | '.join(cells)} | {formatRatio(median['zephyrO2'], median['c'])} | "
              f"{formatRatio(median['zephyrO2'], median['rust'])} | {peakO2} | {peakC} | "
              f"{'ok' if benchmark['checksumOk'] else 'MISMATCH'} |")


# ---------------------------------------------------------------------------
# compare / ab

def isSignificant(oldMeasurement, newMeasurement):
    # ponytail: a noise band of 2% or 3x the combined relative MAD, whichever is
    # bigger. It's cruder than a rank test; switch to Mann-Whitney if borderline
    # calls start to matter.
    relativeNoise = (oldMeasurement["madMs"] / oldMeasurement["medianMs"]) + (newMeasurement["madMs"] / newMeasurement["medianMs"])
    band = max(0.02, 3 * relativeNoise)
    return abs(newMeasurement["medianMs"] / oldMeasurement["medianMs"] - 1) > band


def printComparison(oldLabel, newLabel, pairs):
    """pairs: [(name, language, oldMeasurement, newMeasurement)]"""
    print(f"\n{newLabel} vs {oldLabel}: new/old median; * = beyond noise band\n")
    print("| benchmark | language | old ms | new ms | new/old | |")
    print("|---|---|---:|---:|---:|---|")
    ratios = []
    for benchmarkName, language, oldMeasurement, newMeasurement in pairs:
        ratio = newMeasurement["medianMs"] / oldMeasurement["medianMs"]
        ratios.append(ratio)
        flag = ("* faster" if ratio < 1 else "* SLOWER") if isSignificant(oldMeasurement, newMeasurement) else ""
        print(f"| {benchmarkName} | {languageTitles.get(language, language)} | {oldMeasurement['medianMs']:.1f} | "
              f"{newMeasurement['medianMs']:.1f} | {ratio:.3f} | {flag} |")
    if ratios:
        print(f"\ngeometric mean new/old: {statistics.geometric_mean(ratios):.3f}")


def commandCompare(options):
    if options.files:
        if len(options.files) != 2:
            sys.exit("compare takes two result files (or none for the two newest)")
        oldPath, newPath = options.files
    else:
        resultFiles = sorted((os.path.join(resultsDirectory, name) for name in os.listdir(resultsDirectory) if name.endswith(".json")),
                             key=os.path.getmtime)
        if len(resultFiles) < 2:
            sys.exit("need at least two results in bench/results")
        oldPath, newPath = resultFiles[-2:]
    with open(oldPath) as oldFile, open(newPath) as newFile:
        oldResults, newResults = json.load(oldFile), json.load(newFile)
    pairs = []
    for benchmarkName, newBenchmark in newResults["benchmarks"].items():
        oldBenchmark = oldResults["benchmarks"].get(benchmarkName)
        if not oldBenchmark or oldBenchmark["argument"] != newBenchmark["argument"]:
            continue
        for language in ("zephyr", "zephyrO2"):
            if language in newBenchmark["languages"] and language in oldBenchmark["languages"]:
                pairs.append((benchmarkName, language, oldBenchmark["languages"][language], newBenchmark["languages"][language]))
    printComparison(os.path.basename(oldPath), os.path.basename(newPath), pairs)
    return 0


def commandAb(options):
    compilers = [os.path.abspath(options.compilerA), os.path.abspath(options.compilerB)]
    for compiler in compilers:
        compilerDirectory = os.path.dirname(compiler)
        if not os.path.exists(os.path.join(compilerDirectory, "compiler", "runtime.zeph")) or not os.path.isdir(os.path.join(compilerDirectory, "lib")):
            sys.exit(f"{compiler}: needs compiler/runtime.zeph and lib/ beside it (zc reads its runtime from there)")
    if os.path.dirname(compilers[0]) == os.path.dirname(compilers[1]):
        print("warning: both compilers share a directory, so they share one runtime.zeph", file=sys.stderr)
    pinHarness()
    pairs = []
    with tempfile.TemporaryDirectory(prefix="zbench_ab_") as outputDirectory:
        for benchmarkName, _, workloadArgument, _ in selectedSuite(options.only):
            executables = {}
            for label, compiler in zip(("A", "B"), compilers):
                exePath = os.path.join(outputDirectory, f"{benchmarkName}_{label}.exe")
                completed = subprocess.run([compiler, "--rt", "-O2", os.path.join(benchDirectory, benchmarkName + ".zeph"), exePath],
                                           cwd=repoRoot, capture_output=True, text=True)
                if completed.returncode != 0 or not os.path.exists(exePath):
                    print(f"  {benchmarkName}: compiler {label} failed: {(completed.stdout + completed.stderr).strip()[-300:]}", file=sys.stderr)
                    break
                executables[label] = exePath
            if len(executables) < 2:
                continue
            measurements = measureWorkloads(executables, workloadArgument, options.runs)
            if measurements["A"]["checksum"] != measurements["B"]["checksum"]:
                print(f"  {benchmarkName}: CHECKSUM MISMATCH  A={measurements['A']['checksum']}  B={measurements['B']['checksum']}")
            pairs.append((benchmarkName, "zephyrO2", measurements["A"], measurements["B"]))
            print(f"{benchmarkName:10} A {measurements['A']['medianMs']:.1f}  B {measurements['B']['medianMs']:.1f}", flush=True)
    printComparison("A " + compilers[0], "B " + compilers[1], pairs)
    return 0


# ---------------------------------------------------------------------------
# compile

def commandCompile(options):
    sys.path.insert(0, benchDirectory)
    import compilegen

    # Not pinned: javac, rustc and csc use several threads, and one CPU would misstate their wall time.
    zephyrCompiler = os.path.abspath(options.compiler)
    compilegen.zephyrCompiler = zephyrCompiler  # operations read it when called
    seed = int(time.time())  # fresh constants every invocation, so no compiler cache can help
    print(f"{options.function_count} chains x {options.function_depth} deep, median of {options.runs} runs\n")
    print("| language | operation | functions | us/function | total ms | peak KB/function |")
    print("|---|---|---:|---:|---:|---:|")
    with tempfile.TemporaryDirectory(prefix="zbench_compile_") as workDirectory:
        for language, description in compilegen.LANGUAGES.items():
            if options.languages and language not in options.languages.split(","):
                continue
            if not description["available"]:
                print(f"| {language} | - | - | toolchain not found | | |")
                continue
            functionCount, functionDepth = options.function_count, options.function_depth
            maximumSize = description["maximumSize"]  # a cap on count x depth (Java's constant pool)
            if maximumSize and functionCount * functionDepth > maximumSize:
                shrink = (maximumSize / (functionCount * functionDepth)) ** 0.5
                functionCount, functionDepth = int(functionCount * shrink), int(functionDepth * shrink)
            functionTotal = functionCount * functionDepth
            languageDirectory = os.path.join(workDirectory, language)
            os.makedirs(languageDirectory)
            sourcePath = os.path.join(languageDirectory, "generated" + description["extension"])
            with open(sourcePath, "w") as sourceFile:
                sourceFile.write(description["generate"](functionCount, functionDepth, seed))
            for operationName, makeCommand in description["operations"].items():
                argumentList, _ = makeCommand(sourcePath, languageDirectory)
                times, peakKb, failure = [], 0, None
                for _ in range(options.runs):
                    wallMs, output, runPeakKb, exitCode = runTimed(argumentList, workingDirectory=repoRoot if language == "zephyr" else languageDirectory)
                    if exitCode != 0:
                        failure = output[-200:]
                        break
                    times.append(wallMs)
                    peakKb = max(peakKb, runPeakKb)
                if failure:
                    print(f"| {language} | {operationName} | {functionTotal} | failed: {failure.splitlines()[-1] if failure else ''} | | |")
                    continue
                medianMs = statistics.median(times)
                print(f"| {language} | {operationName} | {functionTotal} | {medianMs * 1000 / functionTotal:.1f} | {medianMs:.0f} | "
                      f"{peakKb / functionTotal:.2f} |", flush=True)

        print("\nzc compiling itself (compiler/zc.zeph):\n")
        print("| build | median ms | min ms | peak MB |")
        print("|---|---:|---:|---:|")
        for label, optimizeFlags in (("baseline", []), ("-O2", ["-O2"])):
            exePath = os.path.join(workDirectory, "zc_self.exe")
            times, peakKb = [], 0
            for _ in range(options.runs):
                wallMs, output, runPeakKb, exitCode = runTimed([zephyrCompiler, "--rt", *optimizeFlags, "compiler/zc.zeph", exePath], workingDirectory=repoRoot)
                if exitCode != 0:
                    sys.exit(f"self-compile failed: {output[-300:]}")
                times.append(wallMs)
                peakKb = max(peakKb, runPeakKb)
            print(f"| {label} | {statistics.median(times):.0f} | {min(times):.0f} | {peakKb / 1024:.0f} |")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    subcommands = parser.add_subparsers(dest="command", required=True)
    defaultCompiler = os.environ.get("ZEPHYR_COMPILER", os.path.join(repoRoot, "zc.exe"))

    runParser = subcommands.add_parser("run")
    runParser.add_argument("--runs", type=int, default=10)
    runParser.add_argument("--only")
    runParser.add_argument("--languages", default=",".join(allLanguages))
    runParser.add_argument("--compiler", default=defaultCompiler)

    compareParser = subcommands.add_parser("compare")
    compareParser.add_argument("files", nargs="*")

    abParser = subcommands.add_parser("ab")
    abParser.add_argument("compilerA")
    abParser.add_argument("compilerB")
    abParser.add_argument("--runs", type=int, default=10)
    abParser.add_argument("--only")

    compileParser = subcommands.add_parser("compile")
    compileParser.add_argument("--function-count", type=int, default=200)
    compileParser.add_argument("--function-depth", type=int, default=200)
    compileParser.add_argument("--runs", type=int, default=5)
    compileParser.add_argument("--languages")
    compileParser.add_argument("--compiler", default=defaultCompiler)

    sys.stdout.reconfigure(encoding="utf-8")
    options = parser.parse_args()
    handlers = {"run": commandRun, "compare": commandCompare, "ab": commandAb, "compile": commandCompile}
    sys.exit(handlers[options.command](options))


if __name__ == "__main__":
    main()
