#!/usr/bin/env python3
"""Check Windows accumulator recursion outputs and optimization eligibility."""
import argparse
import os
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "tests/regression/accumulator_recursion.zeph"
EXPECTED = """fib -3 -1 0 1 1 2 5 55
sum 0 0 1 15 55
wrap 7 -9223372036854775801 8 -9223372036854775798
base -5 1 4 7 10 27
effects 6 321
global 12
float 15
mutual 15 21
subtract 3
right-not-self 15
two-parameters 30
guard-call 6 3210
base-call 13 7
next-call 6 210
guard-global 6
base-global 10
next-global 6
multiple-branches 12
""".encode("ascii")
TRANSFORMED = {"accumulatorFib", "accumulatorSum", "accumulatorWrap", "accumulatorBase"}
REPORT_PREFIX = "opt: accumulator recursion "


def run(command):
    """Bound each child process and keep compiler resource lookup at repo root."""
    return subprocess.run(
        command, cwd=ROOT, stdin=subprocess.DEVNULL, capture_output=True,
        timeout=30, check=False,
    )


def main():
    """Check results separately from reports so a missing pass has a clear failure."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compiler", required=True, type=Path)
    options = parser.parse_args()
    if os.name != "nt":
        parser.error("this experimental optimization test requires native Windows")
    compiler = options.compiler.resolve()
    passed = 0
    failed = 0
    with tempfile.TemporaryDirectory(prefix="zephyr_accumulator_") as directory:
        for tier, flags, expected_names in (
            ("baseline", [], set()),
            ("O2", ["-O2"], TRANSFORMED),
            ("O2-debug", ["-O2", "-g"], set()),
        ):
            executable = Path(directory) / (tier + ".exe")
            try:
                build = run([str(compiler), "--rt", *flags, "--opt-report", str(SOURCE), str(executable)])
                assert build.returncode == 0, f"compile exit {build.returncode}: {(build.stdout + build.stderr)[-500:]!r}"
                assert executable.is_file(), "compiler did not create executable"
                result = run([str(executable)])
                assert result.returncode == 0, f"run exit {result.returncode}: {result.stderr[:200]!r}"
                assert result.stdout == EXPECTED, f"stdout: {result.stdout!r}"
            except (AssertionError, OSError, subprocess.TimeoutExpired) as error:
                failed += 1
                print(f"FAIL {tier}:output: {error}")
                continue
            passed += 1
            print(f"PASS {tier}:output")
            report = (build.stdout + build.stderr).decode("utf-8", errors="replace")
            names = [line[len(REPORT_PREFIX):] for line in report.splitlines() if line.startswith(REPORT_PREFIX)]
            if set(names) != expected_names or len(names) != len(expected_names):
                failed += 1
                print(f"FAIL {tier}:report: got {sorted(names)}, expected {sorted(expected_names)}")
            else:
                passed += 1
                print(f"PASS {tier}:report")
    print(f"{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
