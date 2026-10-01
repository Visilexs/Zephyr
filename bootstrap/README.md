# Compiler bootstrap and native runtime

The normal self-hosting loop starts from the root compiler seeds: `zc.exe` on
Windows and `zc-macos` on Apple Silicon. Rebuild them with
`scripts/selfbuild.ps1` and `./zc selfbuild`, respectively.

`zephyr.c` and `runtime.c` preserve the historical Windows C bootstrap sources.
On Windows with GCC, `bootstrap/build.ps1` rebuilds the C seed and attempts to
seed the current compiler. The historical seed has fewer language features than
the live compiler; this recovery path has not been validated by the native Mac
checks. Generated C binaries, objects, and the copied runtime are build products.

`macos/darwin.c`, `main.c`, `native.h`, and `entry.s` are required native Darwin
runtime and entry-point sources. The Apple Silicon driver links them into every
generated executable. They are part of the active toolchain.
