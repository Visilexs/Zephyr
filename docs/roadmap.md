# Zephyr roadmap (2026-10-15)

Goals: make Zephyr sound and leak-free, good at reading and writing memory
(FFI, binary formats, other processes), and easy for LLM agents to write and
for LLM apps to be written in. Every item below comes from a reproduced audit
finding or a concrete design gap. File and line references are against
`8228a2a`.

Status legend: `[ ]` open, `[~]` in progress, `[x]` done.

## Phase 0: Linux test harness (prerequisite)

All existing runners are PowerShell/Windows. Nothing checks RC, threads, or
baseline vs `-O2` parity on Linux, which is why several of the bugs below went
unnoticed.

- [ ] `tests/linux/run.sh`: copies zc-linux, runtime and lib into a temp dir,
  then builds every self-checking test (`tests/*.zeph`, `tests/regression`,
  `tests/fixtures/{basics,threads}`, `tests/linux`) at baseline and `-O2`. It
  diffs both against `.expected` (when one exists) and against each other.
- [ ] Leak harness: a `runtimeLiveObjects()`/census builtin, and a check that
  running a body N and 2N times gives the same live-object delta at both tiers.
- [ ] Run the existing python checks (`include_path`, `assert_message_release`,
  `argument_tests`, `differential.py`) from the same script.

## Phase 1: soundness and integral fixes

### 1A Runtime and memory (`compiler/runtime.zeph`, `lib/os/linux.zeph`, `lib/std/thread.zeph`)
- [ ] **critical** `s.replace("", x)` returns its argument without a retain,
  so it is a use-after-free (runtime.zeph:1696). Also rewrite replace as a
  single pass; it currently leaks ~3k+2 objects per call and is quadratic.
- [ ] **critical** `zeros(n)`, `repeat`, list/packed allocation never
  range-check: a negative or overflowing n corrupts allocator headers.
- [ ] Thread body roots (`threadBodies`) are mutated without a lock, so
  spawning from workers crashes. Move them to an off-heap locked table.
- [ ] A collection deferred while workers run is never re-run, so threaded
  heaps grow without bound. Run it when the last worker exits. Decrement the
  unsuspendable count at thread exit, not at join.
- [ ] Per-thread string builder (64 KiB) is never freed. Free it in
  runtimeMarkThreadDone.
- [ ] readFile/writeFile/args leak their C-string or buffer temporaries.
  readFile on /proc and pipes returns "", so read until EOF instead.
- [ ] `runtimeFail` allocates on the heap, so under an address-space limit it
  recurses forever. Make it heap-free. Fall back to a smaller reservation when
  the 19 GB mmap fails.
- [ ] 64-thread hard limit: grow the registry.
- [ ] Linux `RtlCaptureContext` is a no-op, so callee-saved registers are
  never scanned. Implement it.
- [ ] Stack overflow is a silent SIGSEGV. Add a sigaltstack handler that
  panics with "stack overflow".
- [ ] Linux `args()` goes through a fake Windows command line: it splits on
  spaces, drops empty args and truncates at 4 KB. Read argv directly.
- [ ] Linux ELF outputs are written 0644. Write them 0755.

### 1B Compiler correctness (`compiler/zc.zeph`, `compiler/optimizer.zeph`)
- [ ] **critical** `tryFill`/`tryReduce` loop fast paths run on maps (their
  type guard is macOS-only), which corrupts map memory or gives wrong sums.
- [ ] Baseline moveScan treats a while-condition read as the last use and
  moves it, so the condition segfaults on its second evaluation.
- [ ] The `-O2` inliner's takeOwnership leaks an owned temporary argument when
  the callee returns that parameter on only some paths (affects
  padLeft/padRight, methods, interface dispatch).
- [ ] `INT_MIN / -1` raises SIGFPE, and constant-folding it crashes the
  compiler. Define it as wrapping.
- [ ] Polymorphic generic recursion monomorphises forever. Cap the depth and
  emit an error at the call site.
- [ ] Long expressions overflow the compiler stack, and compile time is
  quadratic in expression length.
- [ ] cloneInlineNode drops `file`, so panic sites are misattributed after
  inlining.
- [ ] Float→int out of range gives INT_MIN silently. Saturate it, and put the
  rule in the spec.
- [ ] str→int parse wraps on overflow. Panic instead.
- [ ] Float formatting is not `%.15g` (1e-16 prints 0, -0.0 sign).

## Phase 2: memory reading and writing

### 2A Primitives and FFI (now)
- [ ] **critical** `syscall` leaves unused argument registers as garbage;
  zero them. std/linux vmRead/vmWrite pass no flags, so `process_vm_readv`
  always fails with EINVAL.
- [ ] `monotonicNanoseconds` uses syscall 299 (recvmmsg). Use 228.
- [ ] Temporaries in a call's argument list are freed before
  extern/syscall/win runs, so `f(cString(s).addr())` is a use-after-free.
  Keep argument temporaries alive until the call returns.
- [ ] memRead/memWrite don't check length against the Bytes size. Bytes
  bounds checks overflow on huge offsets.
- [ ] Complete the primitive set: `store16`, sign-extending `loadI8/I16/I32`,
  `loadF32/storeF32/loadF64/storeF64`, `copyMemory`, `fillMemory`, and
  `dataAddr(list|str|[u8])`.
- [ ] `std/mem.zeph`: process memory via process_vm_readv/writev, with typed
  reads, `/proc/pid/maps` parsing, AOB pattern scan with wildcards, and
  pointer-chain resolution. All of it returns optionals or Results, never
  panics.
- [ ] Add an `irSyscall` SSA op, so functions that use syscall can be
  optimized under `-O2`.

### 2B Types and layout (next)
- [ ] Sized scalar types `i8..i64`, `u8..u64`, `f32` as real values. Struct
  fields, extern params and returns can use them.
- [ ] `@C struct` (spec §9.1) with natural alignment, `@C(packed)`, inline
  fixed arrays, `sizeOf[T]` and `offsetOf`. Plain int/float structs already
  have C layout after the header, so this extends that.
- [ ] `ptr[T]` typed pointers and `span[T]` views over off-heap memory, with
  inline bounds checks.
- [ ] extern: f32 args and returns, narrow and unsigned types, struct by
  value, and native→Zephyr callbacks via per-signature trampolines.
- [ ] `unsafe` boundary: the raw builtins and `runtime*` symbols are allowed
  only in files marked unsafe.
- [ ] Private struct fields, so Bytes can't be broken by `memory.push()`.

## Phase 3: agentic coding (LLMs writing Zephyr)
- [ ] Diagnostics: `file:line:col: error: msg` (track columns), exit code 2,
  no `panic:` prefix, keep going and collect up to N errors,
  `--error-format=json`.
- [ ] CLI: reject unknown flags, clear errors for missing input or import
  paths, `--linux` implies `--rt`, `--help`.
- [ ] Targeted hints for other-language habits: `&& || ! ++ ; => null nil
  True len()`.
- [ ] Generic errors name the instantiation site and the expected type.
- [ ] Runtime panics include values (`index 7 out of bounds for length 3`)
  and an optional backtrace via an rbp walk plus `--map`/`.zdbg`.
- [ ] `zc run` on Linux: memfd + execveat; it implies `--linux --rt` on a
  Linux host.
- [ ] `--test`: keep going after a failure (fork per test), print a summary,
  `--test-filter`, and have `assert(a == b)` print both sides.
- [ ] `docs/llm.md`: a compact cheat sheet of syntax, gotchas and idioms for
  agents. Ship it as a pi/Claude skill.
- [ ] Later: `zc check` (front end only, fast), `zc fmt`, and an LSP server
  for hover, definitions and diagnostics.

## Phase 4: LLM apps in Zephyr (std)
- [ ] `std/utf8.zeph`: codepoints, runeCount, validate, encode, safe
  truncate and pad.
- [ ] `std/json.zeph`: parse, stringify and streaming partial fields
  (promoted from zui).
- [ ] `std/process.zeph`: spawn with pipes and wait (promoted from zui
  proc.zeph). Linux `run()` and `environmentVariable()`.
- [ ] `tryReadFile`/`tryWriteFile` returning `Result`.
- [ ] `std/http.zeph`: HTTP/1.1 client with SSE streaming. Plain TCP via
  syscalls; HTTPS via `extern` libcurl or libssl.
- [ ] A postfix `?` operator for Result and optionals.

## Phase 5: language-level memory model (larger, later)
- [ ] Release locals at scope and loop-iteration exit. Today they live until
  overwritten or the function returns.
- [ ] Stop-the-world collection on Linux with live workers (signal
  safepoints).
- [ ] Rules for sharing threads with typed references and channels (§9.3).
  Reject closures that capture mutable heap values in `spawnThread`.
- [ ] Structural `==`, hashing and printing iterate instead of recursing.
- [ ] Spec §4/§8: document atomic-once-threaded counting and `freeze()`.
  Base the `-O2` atomic decision on the same predicate the runtime uses.

## Process
- Every track works in its own git worktree off `roadmap-base`, with its own
  untracked copy of `zc-linux`. Nobody builds inside `~/repos/zephyr`.
- A compiler change is done when: `scripts/linux-selfbuild.sh` reaches the
  fixpoint, `tests/linux/run.sh` passes, and a new regression test covers it.
- Tracks don't run `scripts/embed-gen.py` (the embedded blob would conflict).
  The merge step runs it once, then self-builds.
