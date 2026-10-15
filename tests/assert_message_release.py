#!/usr/bin/env python3
"""Check that an assert's message temporary is never released on the ok path (Linux x86-64)."""
import argparse
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "tests/regression/assert_message_release.zeph"
EXPECTED = b"runs 1 1001 2099 50\nvalues 2 4 6\n"
# functions whose only reference work is the message (fail path) and the returned list
NO_RELEASE = ("checkedRun", "checkedValue")


def run(command):
    """Bound each child process and keep compiler resource lookup at repo root."""
    return subprocess.run(command, cwd=ROOT, stdin=subprocess.DEVNULL, capture_output=True,
                          timeout=60, check=False)


def function_body(assembly, name):
    """The text between a function's label and the next function label."""
    match = re.search(rf"^lm_{name}:\n(.*?)^lm_\w+:", assembly, re.S | re.M)
    return match.group(1) if match else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compiler", type=Path, default=ROOT / "zc-linux")
    compiler = str(parser.parse_args().compiler.resolve())
    failed = 0
    with tempfile.TemporaryDirectory(prefix="zephyr_assert_release_") as directory:
        for tier, flags in (("baseline", []), ("O2", ["-O2"])):
            executable = Path(directory) / tier
            build = run([compiler, "--linux", "--rt", *flags, str(SOURCE), str(executable)])
            if build.returncode == 0:
                executable.chmod(0o755)                         # zc does not mark its output executable
            result = run([str(executable)]) if build.returncode == 0 else None
            if result is None or result.returncode != 0 or result.stdout != EXPECTED:
                failed += 1
                detail = build.stderr[-300:] if result is None else result.stdout + result.stderr[-300:]
                print(f"FAIL {tier}:output: {detail!r}")
            else:
                print(f"PASS {tier}:output")
        assembly_path = Path(directory) / "O2.s"
        build = run([compiler, "--linux", "--rt", "-O2", str(SOURCE), str(assembly_path)])
        assembly = assembly_path.read_text() if build.returncode == 0 else ""
        for name in NO_RELEASE:
            body = function_body(assembly, name)
            if body is None:
                failed += 1
                print(f"FAIL O2:{name}: function not found in assembly")
            elif "runtimeReleaseReference" in body:
                failed += 1
                print(f"FAIL O2:{name}: releases a value on the assert's ok path")
            else:
                print(f"PASS O2:{name}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
