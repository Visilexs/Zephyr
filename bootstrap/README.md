# bootstrap/ — the historical C seed (not the live toolchain)

Zephyr is self-hosted: the compiler (`../zc.exe`, built from
`../compiler/zc.zeph`) and its runtime (`../runtime.zeph`) are written in
Zephyr, and `../selfbuild.ps1` rebuilds the compiler using only itself — no gcc,
no C.

But a self-hosting compiler is a binary that builds itself, so it needs a
*first* binary to exist — the same chicken-and-egg every self-hosted language
has (rustc is built by rustc; Go by Go). This folder is that seed, kept only so
the whole toolchain can be reconstructed from source if `zc.exe` is ever
lost. Nothing here runs in day-to-day use.

| file | what it is |
|------|------------|
| `zephyr.c` | the original Zephyr compiler, written in C |
| `runtime.c` | the C runtime (`zephyr_rt.dll`) — optimized GC, full float support |
| `build.ps1` | gcc builds the C seed, then emits the first `../zc.exe` |
| `bootstrap.ps1` | verifies the self-host fixpoint (gcc path + native path) |
| `nocc.ps1` | proves the loop is self-sustaining with zero gcc and zero C |
| `zephyr.exe`, `zephyr_rt.dll`, `runtime.o` | the built C artifacts |

## Re-seeding from scratch (needs gcc)

```powershell
.\bootstrap\build.ps1     # rebuilds the C seed and re-emits zc.exe
```

After that, forget this folder exists and use `.\selfbuild.ps1`.
