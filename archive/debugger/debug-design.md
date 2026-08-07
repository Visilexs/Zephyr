# Zephyr source-level debugging — design

Status: **draft**. Compiler-internals sections (⧗) are pending a pipeline map of
`selfhost/zc.zeph` and will be finalized against real line numbers.

## Goal

Breakpoints, step (over/into/out), stop-on-panic, and — later — variable
inspection, for `.zeph` programs, in VS Code (and any DAP client). Windows
x86-64 only, matching the compiler's target.

## The three pieces

```
 VS Code ──DAP(json/stdio)──▶  zdap (Node, in the extension)
                                   │  spawns + drives
                                   ▼
                              zdbg-backend.exe  ──Win32 debug API──▶  target app.exe
                              (written in Zephyr)         (int3 breakpoints, CONTEXT)
                                   ▲
                                   │ reads
                              app.zdbg  (line-info table, emitted by zc -g)
```

1. **`.zdbg` line-info** — emitted by the compiler under a new `-g` flag, next to
   the exe. Maps code addresses ⇄ source `file:line`, plus function ranges. This
   is the foundation; everything else is inert without it.
2. **`zdbg-backend`** — a native Windows debugger loop. Written **in Zephyr**,
   using the kernel32 debug APIs the language already FFIs to (`DebugActiveProcess`,
   `WaitForDebugEvent`, `ContinueDebugEvent`, `Read/WriteProcessMemory`,
   `Get/SetThreadContext`). Speaks a tiny line protocol over stdio.
3. **`zdap`** — a Debug Adapter (Node, added to `../zephyr-vscode`) translating
   VS Code's DAP requests into backend commands and events back.

Why a Zephyr backend instead of a Node native addon: Node can't call
`WaitForDebugEvent` without a native module; Zephyr already has the exact
kernel32 FFI needed, so the backend dogfoods the language and stays dependency-free.

## Status

- **Increment 1 — `zc -g` emits `.zdbg`: DONE & verified.** `zc.exe --rt -g app.zeph app.exe`
  writes `app.exe.zdbg`; verified on fizzbuzz (8 line entries, lines 1–5, RVAs land in
  `.text`, exe still runs, compiler self-reproduces byte-identically). Dumper:
  `tools/zdbg-dump.js`. Correctness relied on two compiler fixes: `clone_node` now
  preserves `Node.file`, and codegen gates markers on `g_cur_user` (the function body's
  origin file) plus the per-node file — so runtime/std/monomorphised code is excluded.
- **Increment 2 — backend launch + run: DONE & verified.** `debugger/zdbg-backend.zeph`
  (compiled to `zdbg-backend.exe`) launches a target with `CreateProcessA` +
  `DEBUG_ONLY_THIS_PROCESS`, pumps `WaitForDebugEvent`/`ContinueDebugEvent`, lets the
  inherited stdout flow through, and reads the exit code from `EXIT_PROCESS_DEBUG_EVENT`.
  Verified running `fbtarget.exe` (fizzbuzz) end-to-end → exit code 0. Key gotcha: a
  Zephyr list is `{len; cap; data}`, so a scratch `[int]` buffer's raw bytes are at
  `load64(addr(list)+16)`, not `addr(list)` — Win32 structs must use the data pointer.
- Increments 3–7: not started.

## `.zdbg` format (as implemented)

Design constraints already known:
- Addresses recorded as **RVA** (offset from PE ImageBase), because Windows may
  rebase the image; the backend adds the actual module base from the
  `CREATE_PROCESS_DEBUG_EVENT` at load time.
- Must map **both** directions: line→address (to plant a breakpoint) and
  address→line (to report a stop).
- One entry per statement boundary is enough for line breakpoints; column
  granularity only if the compiler already tracks columns.

Tentative layout (little-endian; revised once emission is real):

```
magic   "ZDBG" u32
version u16
imagebase u64            # the compiler's ImageBase, for sanity-checking
strtab  : u32 count, then count × (u16 len, bytes)   # file paths, deduped
lines   : u32 count, then count × { u32 rva, u32 fileIdx, u32 line }  # sorted by rva
funcs   : u32 count, then count × { u32 rvaStart, u32 rvaEnd, u32 nameIdx }
```

`lines` sorted by rva lets the backend binary-search address→line; a line→rva
lookup scans for the lowest rva whose fileIdx/line matches.

## Backend protocol (stdio, one command per line)

Request examples (adapter→backend):
```
launch <exe-path>
bp add <rva>          # returns: ok <id>
bp del <id>
cont
step                  # single source line (step-over via range stepping)
stepin | stepout
eval <expr>           # later; needs variable location info
quit
```
Events (backend→adapter):
```
stopped bp <rva> tid <n>
stopped step <rva>
stopped panic <msg>
exited <code>
output <text>         # forwarded target stdout/stderr
```

Stepping = set breakpoints on the RVAs of the next source lines in range and
continue (classic range-stepping), rather than hardware single-step per
instruction, to stay at source granularity cheaply.

## Increments (each independently verifiable)

1. **`-g` emits `.zdbg`** for a known program; verify by dumping the table and
   checking a couple of `file:line`→rva entries against the `.s` listing. ← start here
2. **Backend: launch + run to exit**, forwarding stdout and reporting exit code.
   No breakpoints yet. Verify it runs `fizzbuzz.exe` end to end.
3. **Backend: one breakpoint** (write int3, catch it, report rva, restore, resume).
4. **`zdap` + VS Code launch.json** — F5 runs to completion in the Debug Console.
5. **Breakpoints wired** — set a line breakpoint, hit it, show the stop line.
6. **Step over/into/out.**
7. **Variables** — needs the compiler to also record local storage locations
   (stack offset / register) per scope. Separate, larger; deferred.

Gate: increment 1 is the whole risk. If the compiler can't cheaply record
statement rva→line, the rest is blocked and we revisit.
```
