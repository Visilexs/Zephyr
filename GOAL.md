# Goal: find the most efficient compiler architecture for Zephyr

## The task

Find the most efficient compiler architecture that can exist for Zephyr, and
keep improving the answer. "Efficient" means all of these together, with none
traded away silently:

- how fast the generated code runs, on one core and on many
- how fast compiling is: cold builds, incremental rebuilds and time to first run
- memory use, both of the compiler and of the programs it builds
- how simple and how verifiable the compiler is, since it must stay self-hosted
  and maintainable

**Preferred direction:** some form of interpreted compiler. That means an
architecture where an interpreter is the source of truth and compiled code is
derived from it. Families to consider:

- partial evaluation of an interpreter (Futamura projections, Truffle/Graal style)
- meta-tracing (RPython/PyPy style)
- self-specializing AST or bytecode interpreters
- copy-and-patch stencils generated from interpreter handlers
- an IR interpreter that compiles itself hot path by hot path
- any hybrid of these

This is a preference, not a requirement. If the evidence shows a non-interpreted
architecture is better, choose it and say plainly why the interpreted
candidates lost. Decide on evidence, never on the preference alone.

## Operating rules

1. **Never stop on your own.** Keep reasoning, researching, simulating and
   measuring until the user stops you. Reaching a conclusion is not the end.
   When you have one, attack it: find its weakest assumption, the workload it
   handles worst, the scenario where a competitor wins. Then go deeper on that.
   If you ever think you are finished, you are not. Pick the least-verified
   claim in the current best answer and verify it.
2. **Never ask the user questions.** When something is ambiguous, choose the
   most reasonable interpretation, write it down as an explicit assumption in
   the log, and continue. Revisit assumptions when the evidence touches them.
3. **Simulate, don't hand-wave.** For every candidate architecture, play out
   concrete scenarios step by step: what happens on each workload, in what
   order, at what cost, and where it breaks. Estimate costs in instructions,
   allocations, milliseconds and bytes. Mark every number as *measured* or
   *estimated*.
4. **Measure whenever possible.** Prefer small prototypes and microbenchmarks
   to argument. Examples:
   - interpreter dispatch cost
   - copy-and-patch stencil emission speed
   - register allocator throughput
   - reference counting cost per operation
   - parallel loop overhead

   Prototypes may be written in C, Python or Zephyr, under `research/` or the
   scratchpad. A measured result overrides an estimate. A contradicted claim is
   removed or corrected in the log, not left standing.
5. **Be honest about uncertainty and limits.** Say where you are guessing, where
   the literature disagrees, and where a design depends on something you could
   not test.
6. **Do not modify the shipping compiler.** `compiler/`, `lib/`, `bootstrap/`,
   `scripts/`, `zc.exe`, `zc-macos` and the existing tests are read-only for this
   goal. All new work goes in `research/` and `docs/architecture-research.md`.
7. **Persist your work.** This environment is ephemeral and your context will be
   summarized over time, so the log is your memory.
   - Commit to the branch `research/compiler-architecture` after every meaningful
     step: a finished scenario, a measurement, a changed conclusion.
   - Push with `git push -u origin research/compiler-architecture`.
   - Never push to `main`, never force-push, never rewrite history, never open
     pull requests.
   - After any context reset, re-read this file and the log before continuing.

## Context: what Zephyr is

Read `CLAUDE.md`, `AGENTS.md`, `README.md`, `docs/spec.md` and `docs/jit.md`
before anything else.

**The language and compiler:**
- Small, statically typed, memory-safe, self-hosted.
- `compiler/zc.zeph` (~19k lines), `compiler/optimizer.zeph` (~7k lines, SSA
  optimizer) and `compiler/runtime.zeph` (~3k lines).

**Targets:**
- Windows x86-64 (PE, kernel32 only) and Linux x86-64 (static ELF, raw
  syscalls), through zc's own assembler and linkers.
- WebAssembly.
- Apple Silicon, through `scripts/macos/arm64.py` (which translates the
  x86-shaped assembly text) and clang, plus a Python-driven JIT in
  `scripts/macos/jit.py`.
- **Priority: x86-64 first. ARM64 is translated from the x86 design later.**

**Memory model (spec §4):**
- Structs, lists, strings, closures, optionals and enum payloads are references
  to heap objects. Assignment copies the reference.
- Reference counting is compiler-inserted and non-atomic, so heap references
  must not cross threads.
- A conservative mark-sweep collector underneath catches cycles.
- The heap is non-moving.
- When an object is freed is unobservable, by spec.

**Other rules:** panics are mandatory and observable. There are no
purity, ownership or aliasing annotations.

**Constraints on any answer:**
- The compiler stays self-hosted.
- Generated programs keep minimal dependencies.
- The language may change only if ease of use and readability do not suffer.
- New syntax cannot appear in `zc.zeph`/`runtime.zeph` until the installed seed
  understands it.
- Byte-identical selfbuild fixpoints must remain possible.

## Context: measurements so far

All measured on an Apple M5; see `tests/benchmarks/results/`. No x86 numbers
exist yet. Getting them, or explaining why they can't be obtained here, is part
of the job.

**AOT -O2 against C (clang -O2), geometric mean 1.28×:**

| | Workloads |
|---|---|
| Faster than C | sort 0.43, strings 0.75, pi 0.80, matmul 0.84 (a pattern-specific NEON kernel), fib 0.89 |
| Slowest | lexer 2.75, vectors 2.31, bintrees 2.14, mandel 1.89, hashmap 1.85, shapes 1.81, wordfreq 1.63 |

**JIT on macOS:**
- Startup is ~4.0–4.3 s for every workload: the runtime is rebuilt each run,
  and 97% of a small program's IR is the runtime.
- Each tier-up pauses 321–335 ms regardless of function size, which points to
  fixed toolchain overhead (clang), not optimization work.
- The JIT counts only function entries, so loops in `main` never tier up.
- Its top tier is the same code as AOT -O2.

**The compiler itself:** 13 struct types, with most data in parallel global
lists (107 in `zc.zeph`, 99 in `optimizer.zeph`). The AST `Node` type is
mutated.

## Context: starting hypotheses, to be challenged, not trusted

An earlier session reached these. Treat them as candidates to beat.

- **Tier by cache, not by time.** Content-addressed caching of files, typed
  modules, per-function machine code and profiles. A native optimizing backend
  fast enough that no baseline tier or JIT is needed. `zc run` becomes cached
  AOT loaded into memory, and profiles become cache inputs.
  - This conflicts directly with the interpreted-compiler preference. Resolve
    the conflict with evidence.
- **One flat SSA IR** stored in packed integer arrays, because Zephyr's
  integer-array code already matches or beats C.
- **Whole-program semantic optimization:**
  - immutability inference, which turns never-mutated struct types into
    unboxed values and allows flattened or SoA layouts;
  - full borrow inference;
  - inline allocation fast paths;
  - region inference later.
- **A general vectorizer with alias versioning.** Zephyr has no interior
  pointers, so one identity check can rule out aliasing.
- **Automatic multicore parallelism**, made safe by value types and effect
  inference. Open issues: float reductions, panic ordering and small-loop cost.
- **Live reload** of functions in a running program.
- **Rejected so far:** speculation/deopt, e-graphs as the foundation, value
  semantics as a language change, copy-and-patch unless measurements demand it.
  Re-examine copy-and-patch fairly under the interpreted-compiler preference.

## Method, repeated forever

Each cycle:

1. Pick the most important open question, or the weakest part of the current
   best architecture.
2. Generate candidates, including unconventional ones.
3. Simulate them on concrete Zephyr scenarios. At minimum use:
   - the 19 benchmark workloads in `tests/fixtures/workloads/` and the
     benchmark results;
   - the compiler compiling itself;
   - an edit-one-function rebuild;
   - `zc run` cold start;
   - a long-running graphics or simulation program.
4. Measure what can be measured.
5. Update `docs/architecture-research.md`, then commit and push.
6. Choose the next question from what this cycle exposed.

Keep `docs/architecture-research.md` organized as:

- **Current best architecture.** Always up to date, short enough to read in
  five minutes, with expected behaviour on the scoreboard below.
- **Scoreboard targets and current estimates**, each marked measured or
  estimated:

  | Target | Goal |
  |---|---|
  | Small-program cold compile | under 100 ms |
  | Incremental rebuild | under 20 ms |
  | Time to first instruction in `zc run` | as low as possible |
  | Single-core geometric mean vs C | 1.0–1.1× or better |
  | Multicore speedup on parallelizable workloads | report it |
  | Peak memory vs today | report it |
  | Compiler size and complexity | report it |
  | Output across modes | bit-identical |

- **Candidates evaluated:** for each one, the verdict, the deciding evidence
  and the scenarios run.
- **Assumptions:** every assumption made instead of asking the user.
- **Log:** a dated, append-only entry per cycle.

Continue until stopped.
