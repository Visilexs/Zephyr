# archive

Superseded work, kept because it still builds and may be worth referring back to.
Nothing here is referenced by the toolchain; moving it back is just a `mv`.

## bench-runners/
`run_bench.ps1`, `run_cube.ps1`, `run_matmul.ps1` — single-benchmark drivers from
before `bench/run_suite.ps1` existed. `run_suite.ps1` now runs all eight areas
(including cube and matmul) with the same checksum verification, and is the one
`README.md` documents. `bench/time1.ps1` was **not** archived: it is a standalone
accurate single-exe timer, still the right tool when you want one number.

## vk-scaffolding/
`ffi_probe.zeph` — proved `LoadLibraryA` + `GetProcAddress` + `callptr` reached
`vulkan-1.dll` before `extern fn` existed. Superseded by `extern fn` itself.

`vk_probe.zeph` — the first instance/device/queue bring-up, written against raw
offset constants. Superseded by `Gfx.init` in `vk/gfx.zeph`; kept because it is
the only place the bring-up sequence is spelled out step by step without the
wrapper, which is useful if that path ever needs debugging.

## debugger/
`zdbg-backend.zeph` (135 lines) + `debug-design.md` (122 lines). A source-level
debugger for Zephyr, started 2026-07-19 and left at **draft**: the design doc's
compiler-internals sections were waiting on a pipeline map of `selfhost/zc.zeph`
before they could be written against real line numbers. Nothing else in the repo
imports it, so it moved cleanly.

## website/
`web-design-brief.md` — a 395-line self-contained handoff for building
zephyr-lang.org (audience, claims to substantiate, page structure). Complete as a
document; archived because the site was not built. It cites `run_cube.ps1` and
`run_matmul.ps1` as reproduction commands, which now live in `bench-runners/`
alongside it.
