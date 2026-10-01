# Linux build and test tools

The official build and test flows are PowerShell on Windows (`scripts/selfbuild.ps1`,
`tests/*.ps1`) and Python on Apple Silicon. These scripts run the same checks
on Linux x86-64.

| Script | Does |
|---|---|
| `embed_gen.py` | Port of `scripts/embed-gen.ps1`. `--check` exits nonzero if the EMBED section is stale. On unchanged sources it reproduces the section byte-for-byte. |
| `selfbuild.sh` | Regenerates EMBED, then checks the Windows fixpoint under Wine (seed → gen1 → gen2 → gen3; gen2 must equal gen3) and the Linux ELF fixpoint. `--install` replaces `zc.exe` with the verified gen2. Leaves a native Linux compiler at `/tmp/zr/current-zc`. |
| `suite.sh OUTDIR [suites]` | Runs `tests/run_tests.ps1`, `std_tests.ps1`, `optimizer_parity.ps1` and `run_parity.ps1` with Linux PowerShell, against the Linux target of the current compiler. |

Requirements: Wine (64-bit), PowerShell 7 for Linux (`pwsh`, or `/opt/pwsh/pwsh`).

`suite.sh` copies the checkout to `OUTDIR/tree`. There, `zc.exe` is a wrapper
around a native Linux compiler built from the current sources, and `cmd /c` is
a PowerShell function that runs the command line with bash. Checks that need
Windows itself fail by construction, so compare with a baseline run of the
unmodified tree. Baseline on the tree this was written against:

| Suite | Result | Expected failures |
|---|---|---|
| `run_tests.ps1` | 139 / 140 | `panic-location:write-file` |
| `std_tests.ps1` | 39 / 40 | `io_environment_time_run` (calls `kernel32`) |
| `optimizer_parity.ps1` | 54 / 54 | none |
| `run_parity.ps1` | 0 / 45 | all: in-process `zc run` exists only on Windows and macOS |

The Linux `zc` cannot take a path containing a space (it splits arguments on
spaces). The wrapper works around that with space-free symlinks.
