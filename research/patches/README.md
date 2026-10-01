# Scratch patches used by the research

None of these are applied to the shipping compiler. Each one was applied to a
copy in `/tmp` to run an experiment, and is kept here so the experiment can be
reproduced. Apply one with `patch -p0` in a copy of `compiler/`, then build a
zc whose `compiler/` directory points at that copy. zc resolves the runtime
next to its own binary.

| Patch | Used in | Effect |
|---|---|---|
| `zc-elf-symbol-map.patch` | M3 and every profile | `--map` also for `--linux` (ELF text sits at 0x400000 + 4096 + offset) |
| `runtime-formatter.patch` | M7, M22 | integer formatting on positive values, so `/10` uses the multiply path |
| `runtime-no-cycle-collection.patch` | M36 | skip the cycle collector (valid only for acyclic programs) |
| `optimizer-no-kernel-bail.patch` | M34 | optimize functions that hold a baseline native-kernel loop |
| `runtime-lifetimes.patch` | M43 | record the stack pointer at allocation and free (object lifetime vs frame) |
