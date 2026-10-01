# Native Apple Silicon JIT

`./zc run program.zeph [arguments...]` executes native ARM64 code in the driver
process. It does not produce, link, or launch a temporary guest executable and
does not execute x86 instructions or use an instruction emulator.

The frontend is the self-hosted `zc-macos` compiler. The native instruction
selector remains `scripts/macos/arm64.py`. Apple Clang assembles instructions
into relocatable ARM64 objects; `scripts/macos/jit.py` resolves their symbols,
data references, and native platform calls directly into executable memory.
Clang also builds the small native host library for the current session.

## Runtime feedback and tier transitions

The default tier is baseline. Stable entries count calls to user and imported
language functions. A function becomes hot at 1,000 calls by default. At that
point execution pauses at its entry, and the frontend compiles that function
with the existing SSA optimizer. The loader retains the selected body, its
outlined helper loops, and its constants. Cold bodies are not installed at the
optimized tier. Native runtime functions stay at their original addresses.

Only future invocations switch tiers. Existing recursive frames continue
executing their original instructions. Direct calls, recursive calls, closures,
and interface method tables all refer to stable entries, so their addresses do
not become stale after promotion. Arguments, floating registers, return
addresses, and condition flags survive the compilation callback.

The two generations share the original mutable global array and runtime heap.
Each generation keeps its own constants and ownership descriptors alive until
the guest exits. The loader checks function identities and global storage size
before publication. A failed optimization disables further promotions and
continues with the already valid code. Guest panics return their exit status
through the host boundary, allowing the session to clean up and save its report.
Source/import files and the compiler seed are checked for changes before and
after compilation; a changed program is never substituted into a live session.

This implements **hotness-driven function tiering**. It does not yet profile
argument values, specialize types or constants from observed values, predict
branches, deoptimize speculative assumptions, or replace an already running
loop on the stack. A long loop in a function called once remains at baseline;
call counters are not loop-iteration counters. Existing compiler optimizations
keep their static safety checks. No speculative checks have been removed.

## Controls and reports

```sh
./zc run --jit-threshold 1000 --jit-report /tmp/profile.json program.zeph
./zc run --jit-baseline program.zeph
./zc run -O2 program.zeph
python3 tests/macos_jit.py
```

Options precede the source path. Everything after it belongs to the guest.
`--jit-baseline` uses in-memory baseline execution without collecting counters.
`-O2` uses in-memory optimized execution from the start, with no adaptive tier
transitions. Neither mode should be described as a feedback-driven measurement.
The internal compiler flag `--jit-hot LABEL` limits the optimizing tier to one
code label and is restricted to the native macOS backend.

Reports include the execution mode, threshold, observed call counts up to
promotion, transitions, compilation time, code/data usage, guest exit status,
and optimization failures. Counters stop at promotion; they do not report total
calls after a function has become hot. Counts are unavailable when profiling
is disabled. Startup and total time include compiler/assembler processes and
native host setup. Adaptive compilation is synchronous and reparses the source
with its imports, so its pause is included in total execution time.

The earlier benchmark reports in `tests/benchmarks/results/` measured AOT
executables. Their numbers are not JIT measurements. Compare JIT startup,
compilation pauses, and steady-state execution separately before claiming a
speed advantage. Native code alone does not guarantee a faster overall run.

The [native JIT benchmark](../tests/benchmarks/results/apple-silicon-jit-full.md)
now measures all 19 original workloads in baseline, adaptive, and optimized-start
JIT modes against C and a fresh AOT reference. Its execution metric subtracts
compilation pauses from the complete guest run; it remains a mixture of cold and
hot tiers, rather than steady-state timing. Reproduce it with
`python3 tests/benchmarks/macos_jit.py`.

## Native memory and scope

The host uses one 64 MiB `MAP_JIT` arena for code and a separate writable arena
for data. Writes to code pass through `bootstrap/macos/jit.c`, which disables
execution on the writing thread, copies the new instructions, re-enables
execution, and invalidates the instruction cache before publication. This
follows Apple's [JIT guidance](https://developer.apple.com/documentation/apple-silicon/porting-just-in-time-compilers-to-apple-silicon).
A hardened Python host needs the appropriate JIT entitlement; the driver fails
explicitly when executable allocation is denied. It does not change host signing
or fall back to AOT execution.

The object linker supports the ARM64 branch, page-address, page-offset, absolute
pointer, and paired-addend relocations emitted by the instruction selector.
Branches to distant native services use nearby ARM64 veneers. Unsupported
sections, symbols, relocations, and out-of-range addresses fail explicitly.
Threads, Windows libraries, and raw x86 callbacks remain unsupported.

Explicit output builds and `selfbuild` are retained for native bootstrapping,
standalone artifacts, and regression comparisons. Removing those paths would
remove the compiler's existing bootstrap mechanism; `run` now selects JIT.
